# LIFE 2.0 Master DB v2 migrations

Supabase project: `life2-master-v2` (Seoul region).

Applied order:
1. `001_init.sql` — Master DB v2 core + Legacy bridge tables
2. `002_auth_provision_and_security.sql` — Supabase Auth provisioning, RLS, user isolation
3. `003_awareness_secure_tokens.sql` — hashed anonymous/handoff token storage
4. `004_internal_rpc_persistence.sql` — protected persistent Awareness/claim/dashboard RPC
5. `005_idempotent_awareness_finalize.sql` — idempotent completion/handoff
6. runtime secret rotation — hash only in private DB state; plaintext never committed
7. `007_claim_idempotency_contract.sql` — same-user claim idempotency
8. `008_hide_security_definer_rpc.sql` — move privileged implementations to private schema

Current DB security state:
- Supabase Security Advisor: **0 findings**
- Public member tables: RLS enabled
- Public RPC endpoints: SECURITY INVOKER wrappers
- Privileged RPC implementations: private, non-exposed schema
- `idempotency_keys`: explicit no-client-access policy
- New Supabase Auth users auto-provision an internal LIFE `user_id`

Important:
- Existing Google Sheets/GAS Master DB is **not migrated or modified**.
- Legacy records remain read-only until explicit verified claim.
- Runtime/internal secrets must never be committed to Git.

4. `010_a1_a2_action_core.sql` — A1/A2 start/draft/complete core and dashboard recompute
5. `011_action_complete_catalog_guard.sql` — action-instance/catalog mismatch guard

Current dev security:
- Supabase security advisor: 0 findings
- Public member tables: RLS enabled
- Internal server Data API path: custom header + private secret verification + internal-only RLS
- Browser never receives the internal server secret
