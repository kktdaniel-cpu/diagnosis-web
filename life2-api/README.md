# life2-api bootstrap

MVP foundation for LIFE 2.0.

Current slice:
- Awareness 12 catalog
- anonymous Awareness run
- deterministic Top 3
- Supabase Auth verification
- signup handoff
- MY LIFE dashboard
- Supabase PostgreSQL persistence via protected internal RPC
- backend tests

Storage modes:
- default/test: `LIFE2_STORAGE_BACKEND=memory`
- dev/prod: `LIFE2_STORAGE_BACKEND=supabase`

Required Supabase runtime env:
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY` (or legacy `SUPABASE_ANON_KEY`)
- `LIFE2_INTERNAL_RPC_SECRET`

The internal RPC secret is runtime-only and must never be committed to Git.

Existing `diagnosis-api Ver32.42` remains separate and unchanged.
