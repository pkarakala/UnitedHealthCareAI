# Improvement Plan — Startup-Grade Review (2026-07-22)

Comprehensive review of the full repo (backend, frontend, docs, infra) with two goals:
make it **professional / startup-grade** and make it **not look AI-generated**.
This doc is the tracked source of truth for that work. Check items off as they land.

Review method: full read of backend (~90 py files), frontend (23 ts/tsx files),
all docs, deploy configs, plus the live marketing site (usahealthcare.ai) as brand
reference. Severity: 🔴 critical · 🟠 high · 🟡 medium · ⚪ polish.

---

## The honest one-paragraph assessment

The workflow engine, state machine, DB schema, typed API client, and StatusBadge
system are a genuinely good skeleton. But **every external touchpoint is simulated**
(auth, payer APIs, EHR, ePA submission, SMS/fax, file storage), and — the single
worst issue — several agents have Claude *invent* clinical facts and approval
decisions which are then **written to the database as real state**. Auth, PHI
encryption, and audit logging all exist as code but have **zero call sites**. The
docs (esp. HIPAA_COMPLIANCE.md) describe the codebase you intended, not the one
that exists. For a healthcare startup, the gap between claims and reality is the
#1 thing a technical advisor, pilot pharmacy, or investor would flag.

---

## P0 — Trust & safety (do these before showing anyone)

- [x] 🔴 **Stop persisting LLM-invented facts as real state.**
  - `agents/status_monitoring.py:64-90` — prompt says "Simulate a status check";
    Claude's guess is written to `pa.decision` as approved/denied.
  - `agents/patient_record.py:76-92` — "generate a realistic clinical profile";
    fabricated labs feed the medical-necessity letter.
  - `agents/submission.py:70-85` — "Generate a realistic confirmation number";
    sets `submitted_at` on a submission that never happened.
  - `agents/insurance_verification.py` — Claude invents copays/coverage.
  - Fix: add a `simulation_mode` flag (config) — mark all simulated writes
    (`is_simulated` column or metadata), badge them in the UI, and hard-fail
    these agents in production mode until real integrations exist.
- [x] 🔴 **Wire up authentication.** `security.py` has complete JWT machinery with
  zero call sites; there is no login endpoint and no User model. Every endpoint
  (PHI reads, PA mutations, `/trigger/{agent}`) is public. Add User model +
  `/auth/login` + `Depends(get_current_user)` on all routers.
- [x] 🔴 **Frontend login is theatrical** (`login/page.tsx:9-12` just router.push,
  prefilled demo creds) and claims "Secured with end-to-end encryption" (line 67)
  — a false security claim. Wire it to real auth; remove the claim until true.
- [x] 🔴 **Webhooks are unauthenticated** (`api/v1/webhooks.py`) — anyone who can
  guess a pa_number can POST `{"status": "approved"}` and flip a PA to approved.
  Add signature verification (or shared secret) before any state transition.
- [x] 🔴 **`POST /health/seed-demo` runs a subprocess unauthenticated**
  (`api/v1/health.py:37-47`, comment says "Remove in production"). Remove it or
  gate behind auth + env check.
- [x] 🔴 **Make HIPAA_COMPLIANCE.md honest.** It claims field-level PHI encryption,
  immutable audit logs, JWT auth with RBAC — none are wired
  (`encrypt_phi`/`decrypt_phi`: zero call sites; `AuditService`: zero call sites;
  auth: zero call sites). Rewrite as "Implemented / Partially implemented /
  Planned" table. Healthcare startups get burned by overclaiming.
- [x] 🟠 **Actually use `encrypt_phi` on PHI columns** (patient name/DOB/phone/email,
  clinical summaries) or explicitly document the decision not to. Also fix the
  hardcoded KDF salt (`encryption.py:14`) and cache the Fernet instance.
  *(Session B: `EncryptedString` type on Patient.phone/email +
  PriorAuth.clinical_summary/medical_necessity_letter; name/member_id left
  plaintext for search — documented in the model; salt → `ENCRYPTION_SALT`;
  Fernet cached; migration 004 widens phone/email to TEXT.)*
- [x] 🟠 **Actually call `AuditService.log`** from PHI-touching endpoints.
  *(Session B: request-scoped `AuditContext` dep captures user + IP; wired on
  patient/PA create/read/update, PA timeline, cancel/escalate, doc download.)*
- [x] 🟠 **Fail startup on default secrets in prod** — `config.py` ships
  `secret_key="change-me-in-production"`, default DB creds, `debug=True`.
  Add a prod-mode validator that refuses to boot with defaults.

## P1 — Correctness & production-readiness (backend)

- [x] 🟠 **Orchestrator recursion is unbounded** (`orchestrator.py:274-347`):
  `advance()` recurses on conditions; PENDING_REVIEW self-transitions on
  "pending" → potential infinite Claude-call loop (unbounded token spend).
  Convert to a loop with max-depth + cycle guard.
  *(Done in Session A: max-depth guard of 8, hit in practice by a webhook test.)*
- [x] 🟠 **Workflow runs synchronously inside the HTTP request**
  (`prescriptions.py:64-69`): 4+ sequential Claude calls, no timeout, no
  idempotency. Dispatch to Celery (it's already in the stack, unused for this).
  *(Session B: `run_pa_workflow` task; intake splits `create_pa` (fast) from
  `run_intake` (slow). Opt-in via `ASYNC_WORKFLOW` — defaults to inline
  because Railway runs only uvicorn, no worker. Fixed task registration to
  use `Celery(include=[...])`.)*
- [x] 🟠 **Retry logic is a docstring** (`base.py:139` claims it; none exists;
  tenacity is in requirements, imported nowhere). Add tenacity retry on 429/529
  to `call_claude`. *(Session B: exponential backoff, 4 attempts, retries
  429/529/connection/timeout; predicate keys on instance status_code since
  anthropic 0.42 surfaces 529 as a generic APIStatusError.)*
- [x] 🟠 **Status mutated before agent runs, commits scattered mid-workflow**
  (`orchestrator.py:302-305`, `base.py:128`, per-agent commits) — a failed agent
  strands the PA in the new status. Move status write after success; single
  transaction boundary per transition. *(Session B: agent runs BEFORE the
  status write; failure/requires_human holds the transition;
  `_commit_transition` writes status+current_agent in one commit. Also fixed a
  latent bug where the approval agent mislabeled appeal_approved as approved.)*
- [x] 🟠 **File uploads silently discard bytes** (`prescriptions.py:38-41`,
  `documents.py:20-40`) — DB row created, file never written. Write to disk/S3
  or return 501 honestly. *(Session B: `LocalStorage` service with traversal
  guard + size cap; documents persist bytes and download streams them;
  prescription image persisted. Railway-ephemeral caveat documented.)*
- [x] 🟠 **Concurrent transitions unguarded** — webhook + Celery beat + manual
  advance can race on the same PA. Add row locking (`SELECT ... FOR UPDATE`)
  or optimistic versioning. *(Session B: both — `lock_version` column
  (migration 005) with version-checked conditional UPDATE, plus
  `SELECT ... FOR UPDATE` on read (Postgres; no-op on SQLite).)*
- [x] 🟡 **Celery async misuse**: shared module-level asyncpg engine across
  `asyncio.run()` loops will hit "attached to a different loop" errors.
  Create engine per task or use a sync engine in workers. *(Session B:
  `app/tasks/worker_db.py run_task` gives each task a fresh loop-local engine;
  all 4 existing tasks refactored onto it.)*
- [x] 🟡 `call_claude_json` fence-stripping is fragile (`base.py:189-195`) — no
  schema validation of Claude output before DB writes; `float(revenue)` can
  raise (`approval.py:88`). Validate with Pydantic; retry on parse failure.
  *(Session B: retries on parse failure, guarantees a dict, optional Pydantic
  schema, robust fence stripping; `float(revenue)` → `_coerce_money`.)*
- [ ] 🟡 Error-path conditions are dead code — agents return `success=False` with
  a condition, but `advance()` only advances on success → silent stalls.
- [x] 🟡 `crontab(minute="*/120")` (`celery_app.py:26`) is invalid (minutes 0-59);
  runs hourly, not every 2h. *(Session B: `crontab(minute=0, hour="*/2")`.)*
- [x] 🟡 `PriorAuthUpdate` allows arbitrary status/decision writes via PUT,
  bypassing the state machine. Restrict mutable fields. *(Session B: reduced to
  notes/assigned_to/priority with extra="forbid"; frontend type synced.)*
- [x] 🟡 Deployment bypasses Alembic (`start.sh` uses `create_all`, continues on
  failure) — run `alembic upgrade head` in the container instead.
  *(Done in Session A: start.sh stamps legacy create_all DBs at 001, then upgrades.)*
- [x] 🟡 `/health` hardcodes `redis="connected"`; actually ping Redis.
- [ ] 🟡 Missing FK indexes (communications/documents/appeals/agent_executions
  → prior_auth_id); add a migration.
- [ ] 🟡 Analytics endpoints return hardcoded/fabricated numbers
  (`analytics.py:48-56, 80-87`; "approved_today" is actually all-time). Compute
  real values or label clearly.
- [ ] ⚪ Delete committed `backend/test.db` / `test_integration.db`; they're in
  .gitignore's spirit but tracked.
- [ ] ⚪ Test suite is 20 trivial tests; one asserts the insurance stub returns
  stub data. Add tests for: auth, webhooks, JSON-parse failure, orchestrator
  cycle guard, encryption round-trip.
- [ ] ⚪ Docker runs as root; add non-root user, `.dockerignore` (venv/test DBs
  currently baked into the image via `COPY . .`), and a HEALTHCHECK. No CI at
  all — add GitHub Actions (lint + tests + docker build on PR).
- [ ] 🟡 **README claims OCR/Vision but no image bytes are ever sent to Claude** —
  `prescription_intake.py` builds a plain-text prompt; uploads are never written
  to disk; Dockerfile installs tesseract/poppler that no code uses. Implement
  vision intake (Claude supports image blocks) or drop the claim.
- [ ] 🟡 **No backup story** — single pgdata volume; `make clean` runs
  `docker compose down -v` and silently destroys all data. Add a pg_dump
  target + warning prompt on clean.
- [ ] 🟡 Compose gaps: no healthcheck/restart policy on api/celery services,
  celery depends_on api instead of db/redis health, `--reload` dev server is
  the only config, pgAdmin `admin/admin` bundled in "full stack".

## P2 — Frontend: professionalism & de-AI-ification

**Brand reference (usahealthcare.ai):** teal accent on clinical white/slate,
stat cards, status/phase badges, initials avatars, dense confident copy.
The dashboard's dark-slate sidebar + teal is on-brand — standardize on it.

- [x] 🟠 **Kill the emoji icons** — the loudest AI tell in the app:
  `communications/page.tsx:26-32,59` (📠 📧 💬 📞 🖥️ 📨) and
  `prior-auths/page.tsx:90` (⚠️). Use lucide-react (already installed).
  *(Session C: replaced all emoji with lucide-react icons.)*
- [x] 🟠 **Unify the two design generations.** Half the pages use teal accent +
  `p-8` + micro type scale; the other half (prior-auths, appeals,
  communications, analytics, settings) use **emerald** + `p-6` + `text-sm`.
  Two accent colors on adjacent pages reads as iterative AI generation.
  Pick teal, one spacing scale, one type scale.
  *(Session C: all pages now use teal accent, `p-6`, `text-[13px]`,
  consistent table headers `text-[11px] uppercase tracking-wider`.)*
- [x] 🟠 **Replace the dashboard hero banner** (`dashboard/page.tsx:64-74`) —
  gradient panel with floating blurred orbs + "let AI agents handle the heavy
  lifting" copy is a top-tier AI-generated tell and wastes 140px. Replace with
  a dense "Needs attention" queue (escalated + stalled PAs).
  *(Session C: replaced with amber "Needs Attention" banner showing
  escalated/stalled PAs with case-age display.)*
- [x] 🟠 **Surface API errors.** Every page catches errors with `console.error`
  and renders empty-state UI — backend down looks identical to "no data" ($0
  revenue, "No prior authorizations yet"). Dangerous for an ops tool. Use the
  existing (unused) `ApiError` class; add error banners + retry.
  *(Session C: ErrorBanner component with retry on every page; error state
  tracked separately from empty state.)*
- [x] 🟠 **PA queue shows no patient or drug names** — columns are UUID, status,
  agent, priority, date (`prior-auths/page.tsx:58-91`, dashboard table). A
  pharmacist can't tell which row is which patient/med. Add patient, drug,
  payer, case-age columns.
  *(Session C: replaced raw date with case-age (< 1h / 3h / 2d format);
  added PriorityBadge with High/Med/Low labels instead of raw numbers;
  added escalated filter. NOTE: patient/drug names require backend join —
  deferred to Session D API changes.)*
- [x] 🟠 **Confirm destructive actions** — "Mark Approved" / "Cancel" / "Escalate"
  fire on single click, no confirm, no try/catch, then `window.location.reload()`
  (`prior-auths/[id]/page.tsx:79-105`).
  *(Session C: ConfirmDialog component with per-action copy; actions use
  try/catch and reload data instead of `window.location.reload()`.)*
- [x] 🟡 **De-fake the chrome**: search button and notification bell do nothing
  (`Header.tsx:10-21`); "Online" badge never checks health; hardcoded
  "Pharmacy Staff / staff@pharmacy.com" (`Sidebar.tsx:80-81`); Settings page
  entirely inert; dashboard trend arrows hardcoded `trend="up"`. Wire or remove.
  *(Session C: Header shows real user name/initials from `/auth/me`; removed
  fake search, bell, "Online" badge. Sidebar user section removed (logout
  moved to Header). Settings page kept as-is — still inert but no false
  claims.)*
- [x] 🟡 **Extract components**: Input, Button, Table, EmptyState, Spinner —
  the ~120-char input className is pasted ~15×; table scaffold duplicated 6×;
  status-prettifier regex duplicated 5×. Wire the dead CSS variables in
  `globals.css:6-11` (defined, never referenced) into these components.
  *(Session C: created Button, Input, Spinner, EmptyState, ErrorBanner,
  ConfirmDialog, DataTable, PriorityBadge components with barrel export.
  Settings page uses Input component. CSS variables wired via @theme.)*
- [x] 🟡 **Delete create-next-app boilerplate**: stock `app/README.md`, unused
  `public/*.svg` (next, vercel, globe, window, file), unused `framer-motion`
  dep. Delete duplicated `frontend/api-client/` (byte-identical copy of
  `src/lib/` that will drift).
  *(Session C: all deleted — README, 5 SVGs, framer-motion dep,
  frontend/api-client/ directory.)*
- [ ] 🟡 **Accessibility pass**: zero aria attributes in the app; logout is a
  bare icon (not a button, does nothing); 11-12px slate-400 text fails WCAG AA
  contrast; sidebar renders on /login (covered visually, still in tab order).
- [ ] 🟡 **Ops-tool table stakes**: pagination (hard limit:50), sorting, search
  on the queue, date filters, polling/refresh (statuses change constantly —
  the premise of the product), debounced patient search (currently fires per
  keystroke, race-prone).
- [ ] 🟡 Intake form demands a raw patient UUID (`intake/page.tsx:87`) — needs a
  patient typeahead. No document upload UI despite `awaiting_records` status
  and a ready client method. Appeals page is read-only (can't create one).
- [ ] ⚪ Fix `NEXT_PUBLIC_API_URL` fallback (`lib/api.ts:4`) — deployed build
  silently calls localhost:8000. Fail loudly or use relative URLs.
- [ ] ⚪ Encode query params in `client.ts:229,234,242` (bare string interpolation).
- [ ] ⚪ Status filter chips cover 5 of 22 statuses; add the human-action states
  (awaiting_records, doctor_outreach). Priority shown as bare 1-10 number —
  add a legend or High/Med/Low label.

**Keep (already good):** StatusBadge (all 22 statuses, consistent), lib/client.ts
architecture, lib/types.ts domain modeling, dark-sidebar shell, Geist + mono for
IDs, KPI selection on dashboard, illustrated empty states, agent timeline concept.

## P3 — Docs, honesty, and optics

- [ ] 🟡 README architecture/feature claims vs reality — add an explicit
  "Current status: X real, Y simulated" section. Silently-fake features are
  worse optics than an honest roadmap (the marketing site already does
  phase-labels well — mirror that).
- [ ] 🟡 The "16 agents" are one agent class with 16 prompts; `get_tools()` is a
  dead hook, `agents/tools/` is empty, revenue_analytics is registered but in
  no workflow transition. Either differentiate them or consolidate honestly
  (~6 real components). At minimum stop instantiating all 16 (each with its own
  Anthropic client) per request.
- [ ] 🟡 Repo is named `UnitedHealthCareAI` but the product is `usahealthcare.ai`.
  UnitedHealthcare is a real insurer with active trademarks — rename the repo
  to avoid trademark exposure and confusion.
- [ ] 🟡 **ARCHITECTURE.md claims components that don't exist**: "JWT/API Key
  auth, rate limiting, audit logging" at the gateway (main.py has only CORS);
  Langfuse service on port 3001 (not in compose, never initialized);
  "pgvector formulary embeddings for RAG" (zero vector code — pip dep only).
  Fix the diagram or build the pieces.
- [ ] 🟡 **Reconcile the migration story**: DEPLOYMENT.md says `RUN alembic
  upgrade head` in the Dockerfile (build-time — can never work); actual deploy
  uses undocumented `start.sh` with `create_all`. Also SETUP.md/HANDOFF.md tell
  a new dev to autogenerate the initial migration that already exists
  (`alembic/versions/001_initial_schema.py`) — following the docs creates a
  broken duplicate.
- [ ] 🟡 **Unify model naming across docs**: HANDOFF.md says Sonnet 4 (3 places,
  with Sonnet pricing), config/.env say `claude-haiku-4-5-20251001`, and a
  commit message says "Haiku 3.5". Fix HANDOFF's model + cost estimates.
- [ ] 🟡 WORKFLOW.md presents "~59 min saved per PA" / "20 hours daily" as
  measured fact for a system with simulated integrations. Reframe as projected.
- [ ] ⚪ Frontend onboarding is undocumented — README calls `frontend/` a
  "reference", but it's the deployed app. Document `npm run dev`; note that
  `frontend/api-client/` is a stale duplicate slated for deletion.
- [ ] ⚪ `make health` pipes to `python -m json.tool` — fails on stock macOS
  (only `python3` exists). Use `python3`.
- [ ] ⚪ DEPLOYMENT.md is honest and good; move the Railway/Vercel env-var lists
  into .env.example comments so they can't drift.

---

## Suggested execution order

1. **Session A (safety):** P0 items — simulation flagging, auth wiring
   (User model, login, protect routes, wire frontend login), webhook auth,
   remove seed-demo, honest HIPAA doc.
2. **Session B (backend hardening):** orchestrator loop guard, Celery dispatch,
   retry, transactions, file storage, locking.
3. **Session C (frontend unification):** one design system pass — kill emojis,
   unify teal, extract components, replace hero, error surfacing, queue columns.
4. **Session D (ops features + polish):** pagination/search/polling, a11y,
   CI, tests, docs truth pass.

## Progress log

- 2026-07-22 — Review completed; this plan created. Nothing checked off yet.
- 2026-07-22 — **Session A (P0 safety) complete.** Commits f083723..b5926ad:
  - Simulation flagging: `simulation_mode` setting; status_monitoring,
    submission, patient_record, insurance_verification are marked
    `simulates_external_calls` and refuse to run (requires_human) when it's
    off. PAs they touch get `is_simulated` + `simulated_agents` (migration
    002) with amber badges in the queue and detail UI.
  - Auth end to end: User model + migration 003, `/auth/login` (audit-logged),
    `/auth/me`, admin-only `/auth/users`, `scripts/create_user.py` bootstrap.
    All routers behind `get_current_user` except health/auth/webhooks.
    passlib replaced with direct bcrypt (passlib 1.7.4 breaks on bcrypt 5).
    Frontend login posts real credentials, stores JWT (localStorage), shows
    errors, logout works, 401 → redirect to /login. False "end-to-end
    encryption" claim removed.
  - Webhooks: HMAC-SHA256 signature required on all three endpoints
    (`WEBHOOK_SECRET`), constant-time compare, 503 when unconfigured; unknown
    statuses no longer advance the workflow.
  - Orchestrator: max auto-advance depth 8 (was unbounded recursion —
    PENDING_REVIEW/pending self-loop confirmed by test).
  - seed-demo endpoint deleted; `/health` actually pings Redis.
  - start.sh: `alembic upgrade head` (stamps legacy DBs at 001) instead of
    `create_all`; alembic env strips DATABASE_URL whitespace.
  - HIPAA_COMPLIANCE.md rewritten as honest status table + gap list.
  - Tests 20 → 31 (auth + webhooks), all passing. Frontend `tsc` + `next build`
    clean.
  - **Deploy notes:** set `WEBHOOK_SECRET` on Railway; run
    `python scripts/create_user.py <email> <password> --role admin` once;
    remaining P0 stragglers → Session B: wire `encrypt_phi` (+salt fix),
    `AuditService.log` on PHI endpoints.
- 2026-07-22 — **Session B (backend hardening) complete.** Commits
  8b91100..3b295d7 (10 commits). Both P0 stragglers + 8 P1 items:
  - **PHI encryption at rest** (`8b91100`): `EncryptedString` type on
    Patient.phone/email + PriorAuth.clinical_summary/medical_necessity_letter;
    name/member_id left plaintext for ILIKE search (documented); salt →
    `ENCRYPTION_SALT`; Fernet cached; migration 004 widens phone/email.
  - **Audit logging** (`a6edaf3`): request-scoped `AuditContext` dep (user +
    IP) on patient/PA create/read/update, PA timeline, cancel/escalate, doc
    download. `get_current_user` stashes user on `request.state`.
  - **Celery workflow dispatch + per-task engine** (`c3bffc7`): `run_pa_workflow`
    task; intake splits create_pa/run_intake; opt-in `ASYNC_WORKFLOW`
    (default inline — Railway has no worker); `Celery(include=[...])` fixes
    registration; `worker_db.run_task` fixes the loop-binding bug across all
    4 tasks.
  - **call_claude retry** (`410bb78`): tenacity, 429/529/conn/timeout, 4
    attempts.
  - **Status-after-success** (`b7a7fba`): agent runs before status write;
    failure holds the transition; one commit per transition; fixes the
    appeal-mislabel bug.
  - **File persistence** (`0c2d7fb`): `LocalStorage` (traversal guard, size
    cap); documents/images actually written; download streams bytes;
    Railway-ephemeral caveat in DEPLOYMENT.md.
  - **Concurrency guard** (`cee93c1`): `lock_version` (migration 005) +
    version-checked conditional UPDATE + `SELECT ... FOR UPDATE`.
  - **call_claude_json validation** (`f22a016`): retry on parse failure,
    dict guarantee, optional Pydantic schema; `_coerce_money` fixes the
    `float(revenue)` crash.
  - **Beat schedule + PriorAuthUpdate** (`3b295d7`): valid every-2h crontab;
    PUT restricted to notes/assigned_to/priority (`extra="forbid"`).
  - Tests 31 → 64, all passing. Frontend tsc clean. New migrations 004/005
    (hand-written, chain 001→005, single head).
  - **Deploy notes (new this session):** set `ENCRYPTION_SALT` on Railway
    (constant forever — changing it breaks PHI decryption). Do NOT set
    `ASYNC_WORKFLOW=true` unless a Celery worker service is added. Uploads
    are on ephemeral disk — add a volume or S3 for durable PHI retention.
  - **Not done (deferred):** error-path conditions are dead code
    (`advance()` only advances on success) — left as its own item; touches
    workflow routing semantics and deserves a focused pass.
- 2026-07-23 — **Session C (frontend unification) complete:**
  - **Shared component library:** Button, Input, Spinner, EmptyState,
    ErrorBanner, ConfirmDialog, DataTable, PriorityBadge — barrel export at
    `components/ui/index.ts`. All pages consume these instead of inline markup.
  - **Design unified to teal:** All emerald accent usage replaced; consistent
    type scale (`text-[13px]` body, `text-[11px] uppercase tracking-wider`
    table headers, `text-[12px]` secondary), `p-6` page padding, `rounded-xl`
    cards, `border-slate-200/80` borders.
  - **Dashboard hero replaced:** Gradient-orb banner removed. New "Needs
    Attention" panel (amber) shows escalated/error/stalled PAs with case-age.
  - **Error surfacing:** Every page has error state tracked separately from
    empty state; ErrorBanner with retry button renders when API fails.
  - **Emoji icons killed:** Communications page uses lucide-react icons
    (Printer, Mail, MessageCircle, Phone, Monitor). Prior-auths escalated
    indicator uses AlertTriangle icon.
  - **Destructive action confirmation:** PA detail Approve/Escalate/Cancel
    now show ConfirmDialog with action-specific copy; no more bare
    `window.location.reload()`.
  - **Chrome de-faked:** Header shows real user (from `/auth/me`) with
    initials avatar; fake search/bell/"Online" badge removed; hardcoded
    "Pharmacy Staff" removed from sidebar (logout moved to header).
  - **Priority display:** Raw 1-10 numbers replaced with High/Med/Low
    colored badges via PriorityBadge component.
  - **Case age column:** Raw dates replaced with relative age (< 1h / 3h / 2d)
    on dashboard and queue pages.
  - **Boilerplate deleted:** stock README.md, 5 public/*.svg files,
    `framer-motion` dep, duplicate `frontend/api-client/` directory.
  - **Sidebar tightened:** 260px → 240px; removed user section (now in header).
  - `tsc --noEmit` clean, `next build` clean, all pages static/dynamic as
    expected.
  - **Still remaining (Session D):** pagination/sorting/search on queue,
    patient/drug columns (requires backend join), a11y pass, CI, docs truth
    pass, patient typeahead on intake, polling/refresh.
