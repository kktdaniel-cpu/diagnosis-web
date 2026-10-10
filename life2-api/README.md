# life2-api bootstrap

MVP foundation for LIFE 2.0.

Current slice:
- Awareness 12 catalog
- anonymous Awareness run
- answer validation
- deterministic Top 3 draft
- one-time handoff token creation
- PostgreSQL migration draft
- backend unit/API tests

Development store is in-memory only. Production deploy is blocked until:
- Supabase Auth verification
- PostgreSQL repository implementation
- RLS + API user isolation
- Signup handoff claim
- member dashboard/action APIs
- AI server-side context layer

Tested locally in the build environment: **5 passed**.

Run:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
