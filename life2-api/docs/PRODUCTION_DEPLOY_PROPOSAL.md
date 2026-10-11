# LIFE 2.0 production commissioning record

Status: PRODUCTION DB, API AND WEB LIVE after user approval on 2026-10-11 KST.
Release: main `893ad487507e116c4d8207a1bce8362138ce5d7e`.

## Resources

- Supabase: life2-prod / zqnxnaxgmfhzxqtflppw, life20co Free organization, Seoul.
- API: srv-db561uid0e5s73eb1rn0, https://life2-api-prod.onrender.com, Python 3.12.8, Singapore, free.
- Web: srv-db56220473hc73a0qq10, https://life2-web-prod.onrender.com, static.
- Both services track main with automatic deployment disabled.
- API live deploy: dep-db562v4s728c73c02ifg. Web live deploy: dep-db56228473hc73a0qqng.
- Initial API builds failed using default Python 3.14 with the pinned pydantic-core dependency. Setting PYTHON_VERSION=3.12.8 produced a successful live deployment. The reference YAML now records that pin.
- render.production.yaml is a configuration reference, not an applied root Blueprint. Official JSON Schema validation passed before commissioning; no CLI/server-side Blueprint application was performed.

## Database and runtime connection

The approved production-schema-snapshot.sql bootstrap was applied as one migration transaction. Repository SQL 004–017 contain documentary placeholders and are insufficient for a complete fresh bootstrap.

Verified: 12 tables, 25 functions, 37 constraints, 12 nonconstraint indexes, 19 RLS policies, and one Auth provisioning trigger. No public application tables lack RLS; no public application functions are SECURITY DEFINER. Security Advisor returned zero findings. Invalid internal-secret RPC and anonymous direct INSERT were rejected. Auth provisioning was tested in a rollback transaction.

The schema-only snapshot includes no dev data, accounts, FACTs, or secret rows. A newly generated production internal secret was provisioned through API environment configuration; only its matching SHA256 hash is stored in private.api_secrets. Plaintext is absent from Git and frontend configuration.

API CORS uses https://life2-web-prod.onrender.com. The web build uses the production API URL and production Supabase publishable key. Built assets were checked for production references and absence of the dev project reference.

Supabase Auth Site URL: https://life2-web-prod.onrender.com
Allowed confirmation redirect: https://life2-web-prod.onrender.com/?auth=confirmed

## Verification

- API /health: HTTP 200, storage=supabase.
- Couple question catalog: HTTP 200, 12 questions.
- Production web-origin CORS preflight: HTTP 200 with matching allowed origin.
- Actual production browser flow: 12 anonymous synthetic unknown responses, first result with three recommended actions.
- Database confirmed latest run COMPLETED, completed_at present, answer_count=12, top3_count=3.
- Production Auth users remain zero. Signup email delivery, registered-user sign-in, claim, draft restoration, PARTIAL replacement and registered cross-user isolation have NOT yet been verified in production. The equivalent RC tests passed in dev; that does not establish production verification.

## Remaining scope

Complete production signup and registered-user acceptance testing before opening registration to users. The user must create any new account credentials directly.

PR #25 remains draft and unmerged. Custom domains remain HOLD. Existing legacy production services, Google Master DB, diagnosis Ver32.42, and dev identities were not migrated or changed.

## Rollback

Record matching API/web revisions and RPC definitions before any later release. If commissioning fails, stop exposing the newly created services and restore the recorded revision as applicable. Do not delete user data or rewrite history as an implicit rollback action.
