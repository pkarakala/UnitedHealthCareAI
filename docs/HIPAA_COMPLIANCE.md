# HIPAA Compliance — Current Status

**This platform is not yet HIPAA-compliant and must not process real PHI.**

This document is an honest inventory of security controls: what is implemented
and enforced, what exists as code but is only partially wired, and what is
planned. It replaces an earlier version that described intended controls as if
they were in place.

Last reviewed: 2026-07-22.

## What would be PHI in this system

If real patient data were loaded, these fields would be PHI and require full
protection: patient names, dates of birth, phone/email, member IDs,
prescription details, diagnosis codes, lab values, clinical notes, insurance
information.

**Today the system should only ever hold synthetic/demo data.** Several agents
generate simulated clinical data (see `simulation_mode` in
`backend/app/config.py`); PAs touched by them are flagged `is_simulated`.

## Control status

| Control | Status | Reality |
|---|---|---|
| JWT authentication | **Implemented** | All API routes require a bearer token except `/health`, `/auth/login`, and signature-verified webhooks. Login resolves to a DB user (`users` table); inactive users are rejected. |
| Role-based access control | **Partial** | Users carry a role (admin/pharmacist/technician/readonly) and `require_role()` exists, but only user-creation is role-gated. Data endpoints do not yet differentiate by role. |
| Webhook authentication | **Implemented** | Inbound webhooks require an HMAC-SHA256 signature (`X-Webhook-Signature`); rejected if `WEBHOOK_SECRET` is unset. |
| Audit logging | **Partial** | `AuditLog` model and `AuditService` exist; only logins are currently audited. PHI reads/writes are **not** yet logged. No immutability guarantee — rows live in the same Postgres DB with the same credentials. |
| Field-level PHI encryption | **Not wired** | `encrypt_phi`/`decrypt_phi` (Fernet) exist in `backend/app/utils/encryption.py` but **no model or endpoint calls them**. Patient fields are stored in plaintext. The KDF also uses a hardcoded salt. |
| Encryption in transit | **Partial** | Railway/Vercel terminate TLS in deployment. Nothing in the app enforces HTTPS; local compose runs plain HTTP. |
| Encryption at rest (disk) | **Inherited** | Whatever the hosting provider (Railway Postgres) does. No application-level guarantee. |
| Secrets hygiene | **Implemented** | App refuses to boot in production (`APP_ENV=production`) with default `SECRET_KEY`/`ENCRYPTION_KEY`, `DEBUG=true`, or dev DB credentials. |
| Minimum-necessary for AI calls | **Partial** | `AgentContext` passes only IDs; agents load what they query. But prompts do include patient name/DOB where used, and there is no redaction layer. |
| BAA with Anthropic | **Not in place** | Required before any real PHI goes to the Claude API. |
| Data retention / deletion | **Not implemented** | No retention automation exists. The retention schedule below is a target, not a behavior. |
| Breach notification procedures | **Not implemented** | No policy documents exist. |

## Gaps to close before real PHI (in priority order)

1. Wire `encrypt_phi` into PHI columns (or document a deliberate decision to
   rely on disk-level encryption + access controls), fix the hardcoded KDF
   salt, cache the Fernet instance.
2. Call `AuditService.log` from every PHI-touching endpoint (reads and writes),
   and move audit logs somewhere append-only.
3. Apply `require_role` to data endpoints (e.g. readonly can't mutate PAs).
4. Sign a BAA with Anthropic; strip direct identifiers from prompts.
5. Retention automation, breach-notification policy, staff training, risk
   assessment — the administrative safeguards.
6. HTTPS enforcement at the app layer (HSTS, secure cookies if sessions are
   added).

## Administrative requirements not yet started

Privacy policy, security policy, breach notification policy, BAAs (Anthropic,
Railway, Vercel, any fax/SMS vendor), access-control policy, training program,
annual risk assessment.

## Relevant HIPAA rules

- **Privacy Rule** (45 CFR 160, 164 A/E) — use and disclosure of PHI
- **Security Rule** (45 CFR 160, 164 A/C) — technical safeguards for ePHI
- **Breach Notification Rule** (45 CFR 164 D)
- **HITECH Act** — extends requirements to business associates
