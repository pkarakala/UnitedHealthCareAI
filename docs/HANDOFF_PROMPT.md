# Session Handoff Prompt

Copy-paste the block below into a new Claude Code session to continue this work.

---

I'm working on the Prior Authorization AI Platform at `~/Desktop/project`
(repo: github.com/pkarakala/UnitedHealthCareAI, deployed as usahealthcare.ai —
backend on Railway, frontend on Vercel, marketing site on GoDaddy).

A comprehensive startup-grade review was just completed. The full findings and
tracked checklist are in **docs/IMPROVEMENT_PLAN.md** — read that first; it is
the source of truth. Key context:

- Goals: professional/startup-grade, and must NOT look AI-generated.
- The biggest issue: several agents have Claude fabricate clinical facts,
  approval decisions, and submission confirmations that get written to the DB
  as real state. Auth, PHI encryption, and audit logging all exist as code but
  have ZERO call sites. HIPAA_COMPLIANCE.md overclaims badly.
- Frontend has two inconsistent design generations (teal vs emerald), emoji
  icons on older pages, a fake login, and API errors rendered as empty states.
- Execution order is at the bottom of the plan: Session A = P0 safety items,
  Session B = backend hardening, Session C = frontend design unification,
  Session D = ops features/polish.
- Cost constraint: ~$100 of Anthropic API credit; agents use
  claude-haiku (default_model in backend/app/config.py). Keep it cheap.
- Frontend is Next.js 16 — read frontend/app/AGENTS.md before writing frontend
  code (bundled docs in node_modules/next/dist/docs/).
- Brand reference: usahealthcare.ai (teal on clinical white/slate, stat cards,
  status badges). The dark-sidebar dashboard shell is on-brand; standardize on teal.
- Update the checkboxes and Progress log in docs/IMPROVEMENT_PLAN.md as you land
  changes. Commit style: conventional commits (feat:/fix:), push only when asked.

Start with Session A (P0 items) unless I say otherwise.

---

*Generated 2026-07-22 during the review session. Delete this file once the plan is underway.*
