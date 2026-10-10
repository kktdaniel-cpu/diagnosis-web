-- Anonymous Awareness uses opaque one-time tokens.
-- Only SHA-256 hashes are persisted.

alter table public.awareness_runs
  add column if not exists run_token_hash text,
  add column if not exists handoff_token_hash text,
  add column if not exists expires_at timestamptz not null default (now() + interval '4 hours'),
  add column if not exists completed_at timestamptz;

create unique index if not exists uq_awareness_runs_run_token_hash
  on public.awareness_runs(run_token_hash)
  where run_token_hash is not null;

create unique index if not exists uq_awareness_runs_handoff_token_hash
  on public.awareness_runs(handoff_token_hash)
  where handoff_token_hash is not null;
