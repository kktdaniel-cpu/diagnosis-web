-- Supabase Auth provisioning + RLS/user isolation.
-- Applied to life2-master-v2 as migration 002.

create schema if not exists private;

create or replace function private.current_life_user_id()
returns uuid
language sql
stable
security definer
set search_path = ''
as $$
  select ai.user_id
  from public.auth_identities ai
  where ai.provider = 'supabase'
    and ai.provider_subject = (select auth.uid())::text
  limit 1
$$;

revoke all on function private.current_life_user_id() from public;
grant execute on function private.current_life_user_id() to authenticated;

create or replace function private.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  v_user_id uuid;
begin
  insert into public.users default values returning user_id into v_user_id;
  insert into public.auth_identities(user_id, provider, provider_subject)
  values (v_user_id, 'supabase', new.id::text)
  on conflict (provider, provider_subject) do nothing;
  return new;
end
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute function private.handle_new_auth_user();

create index if not exists idx_awareness_runs_user_id on public.awareness_runs(user_id);
create index if not exists idx_facts_user_id on public.facts(user_id);
create index if not exists idx_findings_user_id on public.findings(user_id);
create index if not exists idx_action_instances_user_id on public.action_instances(user_id);
create index if not exists idx_activity_log_user_id on public.activity_log(user_id);
create index if not exists idx_legacy_claim_audit_user_id on public.legacy_claim_audit(user_id);
create index if not exists idx_legacy_claim_audit_link_id on public.legacy_claim_audit(legacy_link_id);

alter table public.users enable row level security;
alter table public.auth_identities enable row level security;
alter table public.awareness_runs enable row level security;
alter table public.awareness_answers enable row level security;
alter table public.facts enable row level security;
alter table public.findings enable row level security;
alter table public.action_instances enable row level security;
alter table public.activity_log enable row level security;
alter table public.idempotency_keys enable row level security;
alter table public.legacy_source_links enable row level security;
alter table public.legacy_claim_audit enable row level security;

create policy "users_select_self" on public.users
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "auth_identities_select_self" on public.auth_identities
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "awareness_runs_select_self" on public.awareness_runs
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "awareness_answers_select_self" on public.awareness_answers
for select to authenticated
using (
  exists (
    select 1 from public.awareness_runs ar
    where ar.run_id = awareness_answers.run_id
      and ar.user_id = (select private.current_life_user_id())
  )
);

create policy "facts_select_self" on public.facts
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "findings_select_self" on public.findings
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "action_instances_select_self" on public.action_instances
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "activity_log_select_self" on public.activity_log
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "legacy_source_links_select_self" on public.legacy_source_links
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "legacy_claim_audit_select_self" on public.legacy_claim_audit
for select to authenticated
using (user_id = (select private.current_life_user_id()));

create policy "idempotency_no_client_access" on public.idempotency_keys
for all to authenticated
using (false)
with check (false);

revoke all on public.idempotency_keys from anon, authenticated;
