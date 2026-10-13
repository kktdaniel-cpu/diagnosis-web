-- DEV: preparation drafts only. No existing FACT/Action/Legacy schema changes.
create table public.income_gap_preparations (
  preparation_id uuid primary key default gen_random_uuid(),
  contract_version text not null default 'INCOME_GAP_PREPARATION_V1',
  token_hash text not null unique check (token_hash ~ '^[0-9a-f]{64}$'),
  answers jsonb not null check (jsonb_typeof(answers)='object'),
  user_id uuid references public.users(user_id) on delete cascade,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null default now()+interval '24 hours',
  saved_at timestamptz,
  check ((user_id is null and saved_at is null) or (user_id is not null and saved_at is not null))
);
create index income_gap_preparations_owner on public.income_gap_preparations(user_id,saved_at desc);
alter table public.income_gap_preparations enable row level security;
revoke all on public.income_gap_preparations from public,anon,authenticated;
grant select,insert,update,delete on public.income_gap_preparations to anon;
grant select on public.income_gap_preparations to authenticated;
create policy gap_internal on public.income_gap_preparations for all to anon
  using ((select private.request_is_internal())) with check ((select private.request_is_internal()));
create policy gap_owner_read on public.income_gap_preparations for select to authenticated
  using (user_id=(select private.current_life_user_id()));

create function public.rpc_gap_preparation_create(p_internal_secret text,p_token_hash text,p_answers jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_expires timestamptz;
begin
  if not private.valid_internal_secret(p_internal_secret) or not private.request_is_internal() then
    raise exception 'forbidden';
  end if;
  -- Opportunistic bounded expiry cleanup. Claimed drafts remain until account deletion.
  delete from public.income_gap_preparations where preparation_id in (
    select preparation_id from public.income_gap_preparations
    where user_id is null and expires_at<now() order by expires_at limit 100
  );
  insert into public.income_gap_preparations(token_hash,answers)
    values(p_token_hash,p_answers) returning expires_at into v_expires;
  return jsonb_build_object('expires_at',v_expires);
end $$;

create function public.rpc_gap_preparation_claim(p_internal_secret text,p_token_hash text,p_auth_subject uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_user uuid; v_row public.income_gap_preparations; v_repeated boolean;
begin
  if not private.valid_internal_secret(p_internal_secret) or not private.request_is_internal() then
    raise exception 'forbidden';
  end if;
  select ai.user_id into v_user from public.auth_identities ai join public.users u on u.user_id=ai.user_id
    where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text and u.status='ACTIVE';
  if v_user is null then raise exception 'forbidden'; end if;
  select * into v_row from public.income_gap_preparations where token_hash=p_token_hash for update;
  if not found then raise exception 'handoff not found'; end if;
  if v_row.user_id is not null and v_row.user_id<>v_user then raise exception 'handoff already claimed'; end if;
  v_repeated:=v_row.user_id=v_user;
  if v_row.user_id is null then
    if v_row.expires_at<now() then raise exception 'handoff expired'; end if;
    update public.income_gap_preparations set user_id=v_user,saved_at=now() where preparation_id=v_row.preparation_id;
  end if;
  return jsonb_build_object('claimed',true,'idempotent',coalesce(v_repeated,false),'preparation_id',v_row.preparation_id);
end $$;

create function public.rpc_gap_preparation_get(p_internal_secret text,p_auth_subject uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_user uuid; v_result jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) or not private.request_is_internal() then
    raise exception 'forbidden';
  end if;
  select ai.user_id into v_user from public.auth_identities ai join public.users u on u.user_id=ai.user_id
    where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text and u.status='ACTIVE';
  if v_user is null then raise exception 'forbidden'; end if;
  select jsonb_build_object('preparation_id',preparation_id,'answers',answers,'saved_at',saved_at)
    into v_result from public.income_gap_preparations where user_id=v_user order by saved_at desc,created_at desc limit 1;
  return v_result;
end $$;
revoke all on function public.rpc_gap_preparation_create(text,text,jsonb) from public;
revoke all on function public.rpc_gap_preparation_claim(text,text,uuid) from public;
revoke all on function public.rpc_gap_preparation_get(text,uuid) from public;
grant execute on function public.rpc_gap_preparation_create(text,text,jsonb) to anon;
grant execute on function public.rpc_gap_preparation_claim(text,text,uuid) to anon;
grant execute on function public.rpc_gap_preparation_get(text,uuid) to anon;
