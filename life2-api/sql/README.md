# LIFE 2.0 Master DB v2 SQL

Target dev project: `life2-master-v2` / `bikvcuchdlreqkqypwcr` (Seoul). Existing Google Sheets/GAS Master DB and diagnosis Ver32.42 are outside this change.

## SQL sequence

| File | Purpose |
| --- | --- |
| 001 | Core tables and legacy bridge |
| 002 | Auth provisioning, RLS and user isolation |
| 003 | Hashed anonymous/handoff tokens |
| 004 | Protected persistence RPCs |
| 005 | Idempotent Awareness finalize |
| 007 | Claim idempotency |
| 008 | Private privileged RPC implementations |
| 010 | Action start/draft/complete and dashboard |
| 011 | Action instance/catalog guard |
| 012 | Action completion idempotency |
| 013 | Member FACT reads |
| 014 | Change-summary events |
| 015 | Waiting-external action state |
| 016 | Account deletion |
| 017 | Hardened account-deletion RPC |
| 018 | Partial information confirmation |

Numbers follow existing repository conventions. Runtime secret rotation is an operational step, not a plaintext SQL secret stored here. Verify the target's migration history and function definitions before applying files; this list is not an instruction to replay every migration.

## Dev status: 2026-10-11 KST

SQL 018 is applied to the named dev project alongside API/web commit `d0fdc300fc95cb358c901077c499143d9860ba10` on `mvp/life2-bootstrap`. Both Render dev services are LIVE. `rpc_action_complete` remains SECURITY INVOKER with an empty search_path and the existing internal gate; no grants were widened.

Actual UI/DB checks with synthetic data:

- Insurance unknown completion: 10/12 retained, PARTIAL answer and VERIFY follow-up.
- Confirmed insurance replacement: 11/12, health domain 2/2.
- Work health-insurance unknown completion: 11/12 retained, UNKNOWN/null FACT and OPEN Finding.
- Confirmed work replacement: 12/12 and empty Top 3.
- Existing historical confirmed rows were not backfilled.

Security Advisor currently reports one warning: leaked-password protection is disabled. Earlier claims of zero findings are obsolete. Remediation: https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection

## Release and rollback

Main merge, production deployment and domain changes require separate explicit approval. Draft PR #24 is the review unit. The current evidence proves the named dev environment; it does not establish that a production environment is configured.

Before an approved release, identify the production database and service targets, compare existing function definitions/grants, preserve the previous RPC definition and API/web commit references, and confirm runtime origins and server-only secrets. Apply SQL 018 with the matching API/frontend, then verify health, sign-in, claim, draft restore, partial completion and confirmed replacement.

If rollback is required, restore the recorded previous RPC definition and matching API/frontend versions together. Historical data is not automatically rewritten on rollback. Do not delete FACTs or change confirmed history as an implicit rollback step.
