# LIFE 2.0 production deployment proposal

Status: PRODUCTION DB EXISTS; SCHEMA APPLY AND RENDER DEPLOY NOT YET APPROVED. Main baseline: PR #24 merge `893ad487507e116c4d8207a1bce8362138ce5d7e`.

## Reviewable scope

- Create dedicated Render `life2-api-prod` (Python, Singapore, free proposal) and `life2-web-prod` (static).
- Use main with automatic deploy disabled. Manual releases only.
- Production DB `life2-prod` / `zqnxnaxgmfhzxqtflppw` exists in user-selected life20co, Seoul. ACTIVE_HEALTHY and no public/private tables confirmed on 2026-10-11 KST. Organization plan: Free. User completed database-password entry and project creation. Dev project is separate.
- No domain binding or edits to existing lpp20-new / my-diagnosis-server.
- No migration of Google Master DB, existing diagnosis records, dev accounts or synthetic FACTs.

`render.production.yaml` passed the official Render JSON Schema using Draft 2020-12. Render CLI is not installed; server-side Blueprint validation/application has not run. This nested file is a proposal, not an automatically applied root Blueprint.

## Execution order after approval

1. Target only `zqnxnaxgmfhzxqtflppw`; recheck it is empty before applying schema. Preserve dev.
2. After separate schema approval, apply `production-schema-snapshot.sql` as one transaction. Repository SQL 004–017 include documentary placeholders and must not be used as a complete fresh bootstrap. Provision a new internal secret and its matching private DB hash through secure runtime configuration; never commit plaintext.
3. Create the two services with the reviewed commands and environment keys. Confirm actual assigned URLs rather than assuming names are available.
4. Set API CORS to the actual web origin; set VITE_API_BASE and both production Supabase public values before the frontend build. Keep the internal secret API-only.
5. Confirm Supabase Auth URL/email configuration for the actual production origin. Production users register or sign in to the production project; dev identities do not carry over automatically.
6. Deploy manually. Verify API health uses Supabase storage, sign-in, claim, draft restore, unknown PARTIAL retention, confirmed replacement and cross-user isolation.
7. Review before opening registration to users. Custom-domain changes require separate approval.

## Rollback

No existing production service is replaced by this proposal. If commissioning fails, stop exposing the new service and restore the recorded matching API/web revisions and RPC definition as applicable. Do not remove user data or rewrite history as an implicit rollback action.

## Schema snapshot review

The schema-only catalog snapshot has 12 tables, 25 functions, 37 constraints, 12 nonconstraint indexes, 19 RLS policies and one Auth provisioning trigger. PostgreSQL syntax parser accepted 582 statements and object counts matched. The target has matching required extensions. All public application functions are SECURITY INVOKER; privileged helpers stay in private.

The snapshot contains no table rows, Auth accounts, secret hash values or dev FACTs. private.api_secrets is created empty. Function grants, schema grants, table grants and RLS policies are retained from the working dev catalog. An empty-target guard rejects application to a nonempty database. Public/private schemas are the only copied application schemas; managed Auth tables and extension objects are not copied.

Validation is static parsing and catalog comparison only. It has not been executed against production, and function-body behavior/grants must be verified after an approved apply. Render creation/deploy and custom domains remain separate approval steps.
