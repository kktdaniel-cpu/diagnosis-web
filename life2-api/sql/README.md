# LIFE 2.0 Master DB v2 migrations

Supabase project: `life2-master-v2` (Seoul region).

Applied order:
1. `001_init.sql` — Master DB v2 core + Legacy bridge tables
2. `002_auth_provision_and_security.sql` — Supabase Auth provisioning, RLS, user isolation
3. `003_awareness_secure_tokens.sql` — hashed anonymous/handoff token storage

Security status after migration 002:
- Supabase security advisor: **0 findings**
- Public member tables: RLS enabled
- `idempotency_keys`: explicit no-client-access policy
- New Supabase Auth users auto-provision an internal LIFE `user_id`

Important:
- Existing Google Sheets/GAS Master DB is **not migrated or modified**.
- Legacy records remain read-only until explicit verified claim.
- Service-role credentials must never be committed to Git.
