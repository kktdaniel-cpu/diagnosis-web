-- LIFE 2.0 Master DB v2 schema draft.
-- IMPORTANT: Draft branch only. Apply to Supabase only after environment review.
-- Existing Google Sheets/GAS Master DB remains a read-only Legacy Diagnosis Store.

create extension if not exists pgcrypto;

create table if not exists users (
  user_id uuid primary key default gen_random_uuid(),
  status text not null default 'ACTIVE' check (status in ('ACTIVE','DELETED')),
  created_at timestamptz not null default now(),
  deleted_at timestamptz
);

create table if not exists auth_identities (
  auth_identity_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(user_id) on delete cascade,
  provider text not null,
  provider_subject text not null,
  created_at timestamptz not null default now(),
  unique(provider, provider_subject)
);

create index if not exists idx_auth_identities_user_id on auth_identities(user_id);

create table if not exists awareness_runs (
  run_id uuid primary key default gen_random_uuid(),
  user_id uuid references users(user_id) on delete cascade,
  age_band text not null,
  household_type text not null check (household_type in ('single','couple')),
  status text not null default 'IN_PROGRESS',
  created_at timestamptz not null default now(),
  attached_at timestamptz
);

create table if not exists awareness_answers (
  run_id uuid not null references awareness_runs(run_id) on delete cascade,
  question_id text not null,
  response text not null check (response in ('CONFIRMED','PARTIAL','UNKNOWN_OR_NOT_PREPARED','NOT_APPLICABLE')),
  created_at timestamptz not null default now(),
  primary key (run_id, question_id)
);

create table if not exists facts (
  fact_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(user_id) on delete cascade,
  fact_key text not null,
  status text not null check (status in ('KNOWN','UNKNOWN','NOT_APPLICABLE','INVALID','STALE')),
  value_json jsonb,
  unit text,
  source_type text not null,
  source_ref text,
  verification_level text not null default 'SELF_REPORTED',
  confirmed_at timestamptz,
  review_due_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(user_id, fact_key)
);

create table if not exists findings (
  finding_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(user_id) on delete cascade,
  finding_type text not null,
  status text not null check (status in ('OPEN','RESOLVED','SUPPRESSED','NOT_APPLICABLE')),
  source_refs jsonb not null default '[]'::jsonb,
  recommended_action_catalog_id text,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);

create table if not exists action_instances (
  action_instance_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(user_id) on delete cascade,
  action_catalog_id text not null,
  status text not null check (status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','SELF_REPORTED_DONE','VERIFIED_DONE','REVIEW_DUE','NOT_APPLICABLE')),
  mode text not null check (mode in ('CREATE','VERIFY')),
  priority_class text,
  started_at timestamptz,
  completed_at timestamptz,
  verification_level text not null default 'SELF_REPORTED',
  next_review_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists activity_log (
  event_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(user_id) on delete cascade,
  event_type text not null,
  entity_type text,
  entity_id text,
  summary_code text,
  metadata_json jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);

create table if not exists idempotency_keys (
  user_id uuid not null references users(user_id) on delete cascade,
  key text not null,
  response_json jsonb,
  created_at timestamptz not null default now(),
  primary key(user_id,key)
);

create table if not exists legacy_source_links (
  legacy_link_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(user_id) on delete cascade,
  source_system text not null,
  source_record_key text not null,
  record_type text not null check (record_type in ('FULL_DIAGNOSIS','QUICK_DIAGNOSIS','DRAFT')),
  source_version text,
  claim_status text not null default 'PENDING' check (claim_status in ('UNCLAIMED','PENDING','VERIFIED','REJECTED')),
  match_method text,
  access_mode text not null default 'READ_ONLY' check (access_mode in ('READ_ONLY')),
  claimed_at timestamptz,
  created_at timestamptz not null default now(),
  unique(source_system, record_type, source_record_key)
);

create index if not exists idx_legacy_source_links_user_id on legacy_source_links(user_id);

create table if not exists legacy_claim_audit (
  audit_id uuid primary key default gen_random_uuid(),
  legacy_link_id uuid references legacy_source_links(legacy_link_id) on delete set null,
  user_id uuid not null references users(user_id) on delete cascade,
  event_type text not null check (event_type in ('SEARCHED','CANDIDATE_PRESENTED','CLAIM_REQUESTED','VERIFIED','REJECTED','UNLINKED')),
  metadata_json jsonb not null default '{}'::jsonb,
  occurred_at timestamptz not null default now()
);
