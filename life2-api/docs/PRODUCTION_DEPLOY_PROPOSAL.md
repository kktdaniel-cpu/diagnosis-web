# LIFE 2.0 production deployment proposal

Status: PREPARED, NOT APPROVED OR APPLIED. Main baseline: PR #24 merge `893ad487507e116c4d8207a1bce8362138ce5d7e`.

## Reviewable scope

- Create dedicated Render `life2-api-prod` (Python, Singapore, free proposal) and `life2-web-prod` (static).
- Use main with automatic deploy disabled. Manual releases only.
- Configure a separate Supabase production project. Its creation, region, organization, available plan and any cost must be confirmed before provisioning. No existing dev project is promoted or reused implicitly.
- No domain binding or edits to existing lpp20-new / my-diagnosis-server.
- No migration of Google Master DB, existing diagnosis records, dev accounts or synthetic FACTs.

`render.production.yaml` passed the official Render JSON Schema using Draft 2020-12. Render CLI is not installed; server-side Blueprint validation/application has not run. This nested file is a proposal, not an automatically applied root Blueprint.

## Execution order after approval

1. Confirm production DB target and available plan; preserve existing dev configuration.
2. Provision isolated production DB and review migrations 001–018 in repository order (gaps are intentional). Set a new internal secret through secure runtime configuration and its matching private DB hash; never commit plaintext.
3. Create the two services with the reviewed commands and environment keys. Confirm actual assigned URLs rather than assuming names are available.
4. Set API CORS to the actual web origin; set VITE_API_BASE and both production Supabase public values before the frontend build. Keep the internal secret API-only.
5. Confirm Supabase Auth URL/email configuration for the actual production origin. Production users register or sign in to the production project; dev identities do not carry over automatically.
6. Deploy manually. Verify API health uses Supabase storage, sign-in, claim, draft restore, unknown PARTIAL retention, confirmed replacement and cross-user isolation.
7. Review before opening registration to users. Custom-domain changes require separate approval.

## Rollback

No existing production service is replaced by this proposal. If commissioning fails, stop exposing the new service and restore the recorded matching API/web revisions and RPC definition as applicable. Do not remove user data or rewrite history as an implicit rollback action.
