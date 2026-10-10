# LIFE 2.0 API

MVP-1 provides anonymous Awareness 12, deterministic Top 3, Supabase Auth verification and one-time claim, member dashboards, A1–A12 action forms, drafts, waiting-external state, FACT persistence, change summaries and account deletion.

## Runtime

- Test/default: `LIFE2_STORAGE_BACKEND=memory`
- Persistent environments: `LIFE2_STORAGE_BACKEND=supabase`
- Required persistent runtime variables: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` (or legacy `SUPABASE_ANON_KEY`), `LIFE2_INTERNAL_RPC_SECRET`
- Configure `CORS_ORIGINS` for the intended frontend origin.
- The internal RPC secret is server-only; never commit it or expose it to the browser.

Run checks from this directory:

```sh
pip install -r requirements.txt
PYTHONPATH=. pytest -q
```

## Completion contract

Action execution and information confirmation are separate. UNKNOWN, INVALID or STALE facts leave the Awareness answer PARTIAL, exclude it from confirmed counts, retain an OPEN Finding and produce VERIFY follow-up. Only nonempty facts that are all KNOWN or NOT_APPLICABLE confirm the answer. Duplicate completion preserves the stored result.

Deploy matching API, frontend and `sql/018_partial_action_completion.sql` together. See `sql/README.md` for dev evidence and release boundaries. Existing diagnosis-api Ver32.42 remains separate.
