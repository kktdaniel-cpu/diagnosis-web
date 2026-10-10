create extension if not exists pgcrypto;

create table if not exists public.users (
  id text primary key default ('USR_' || replace(gen_random_uuid()::text, '-', '')),
  auth_subject uuid not null unique references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

create table if not exists public.awareness_runs (
  id text primary key default ('AWR_' || replace(gen_random_uuid()::text, '-', '')),
  user_id text references public.users(id) on delete cascade,
  age_band text not null,
  household_type text not null check (household_type in ('single','couple')),
  completed_at timestamptz,
  claimed_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.awareness_answers (
  run_id text not null references public.awareness_runs(id) on delete cascade,
  question_id text not null,
  response text not null check (response in ('CONFIRMED','PARTIAL','UNKNOWN_OR_NOT_PREPARED','NOT_APPLICABLE')),
  updated_at timestamptz not null default now(),
  primary key (run_id, question_id)
);

create table if not exists public.facts (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.users(id) on delete cascade,
  fact_key text not null,
  status text not null check (status in ('KNOWN','UNKNOWN','NOT_APPLICABLE','INVALID','STALE')),
  value_json jsonb,
  unit text,
  source_type text not null,
  source_ref text,
  verification_level text not null default 'SELF_REPORTED',
  confirmed_at timestamptz,
  review_due_at timestamptz,
  schema_version text not null default '1.0',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, fact_key)
);

create table if not exists public.findings (
  id uuid primary key default gen_random_uuid(),
  user_id text not null references public.users(id) on delete cascade,
  finding_type text not null,
  status text not null check (status in ('OPEN','RESOLVED','SUPPRESSED','NOT_APPLICABLE')),
  source_refs jsonb not null default '[]'::jsonb,
  recommended_action_catalog_id text,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table if not exists public.action_instances (
  id text primary key default ('ACTI_' || replace(gen_random_uuid()::text, '-', '')),
  user_id text not null references public.users(id) on delete cascade,
  action_catalog_id text not null,
  status text not null check (status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','SELF_REPORTED_DONE','VERIFIED_DONE','REVIEW_DUE','NOT_APPLICABLE')),
  mode text not null check (mode in ('CREATE','VERIFY')),
  priority_class text,
  verification_level text not null default 'SELF_REPORTED',
  started_at timestamptz,
  completed_at timestamptz,
  next_review_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.activity_log (
  id text primary key default ('EVT_' || replace(gen_random_uuid()::text, '-', '')),
  user_id text not null references public.users(id) on delete cascade,
  event_type text not null,
  entity_type text,
  entity_id text,
  summary_code text,
  metadata_json jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);

create table if not exists public.idempotency_keys (
  user_id text not null references public.users(id) on delete cascade,
  key text not null,
  operation text not null,
  response_json jsonb,
  created_at timestamptz not null default now(),
  primary key (user_id, key, operation)
);

alter table public.users enable row level security;
alter table public.awareness_runs enable row level security;
alter table public.facts enable row level security;
alter table public.findings enable row level security;
alter table public.action_instances enable row level security;
alter table public.activity_log enable row level security;

create policy "users_self" on public.users
for all using (auth_subject = auth.uid()) with check (auth_subject = auth.uid());

create policy "awareness_member_self" on public.awareness_runs
for all using (user_id in (select id from public.users where auth_subject = auth.uid()))
with check (user_id in (select id from public.users where auth_subject = auth.uid()));

create policy "facts_self" on public.facts
for all using (user_id in (select id from public.users where auth_subject = auth.uid()))
with check (user_id in (select id from public.users where auth_subject = auth.uid()));

create policy "findings_self" on public.findings
for all using (user_id in (select id from public.users where auth_subject = auth.uid()))
with check (user_id in (select id from public.users where auth_subject = auth.uid()));

create policy "actions_self" on public.action_instances
for all using (user_id in (select id from public.users where auth_subject = auth.uid()))
with check (user_id in (select id from public.users where auth_subject = auth.uid()));

create policy "activity_self" on public.activity_log
for select using (user_id in (select id from public.users where auth_subject = auth.uid()));
