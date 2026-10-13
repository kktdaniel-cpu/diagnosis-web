-- Dev-only scoped monthly review. Existing Awareness/legacy FACT keys untouched.
alter table public.income_gap_preparations
  add column revision integer not null default 0 check(revision>=0),
  add column confirmations jsonb not null default '{}' check(jsonb_typeof(confirmations)='object'),
  add column review_requests jsonb not null default '{}' check(jsonb_typeof(review_requests)='object');

create function public.rpc_gap_review_get(p_internal_secret text,p_auth_subject uuid,p_preparation_id uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_user uuid; v_result jsonb;
begin
 if private.valid_internal_secret(p_internal_secret) is not true or private.request_is_internal() is not true then raise exception 'forbidden'; end if;
 select ai.user_id into v_user from public.auth_identities ai join public.users u on ai.user_id=u.user_id
 where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text and u.status='ACTIVE';
 select jsonb_build_object('preparation_id',preparation_id,'answers',answers,'saved_at',saved_at,
   'revision',revision,'confirmations',confirmations,'review_requests',review_requests) into v_result
 from public.income_gap_preparations where preparation_id=p_preparation_id and user_id=v_user;
 if v_result is null then raise exception 'gap preparation not found'; end if;
 return v_result;
end $$;

create or replace function public.rpc_gap_preparation_get(p_internal_secret text,p_auth_subject uuid)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_user uuid; v_id uuid;
begin
 if private.valid_internal_secret(p_internal_secret) is not true or private.request_is_internal() is not true then raise exception 'forbidden'; end if;
 select ai.user_id into v_user from public.auth_identities ai join public.users u on ai.user_id=u.user_id
 where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text and u.status='ACTIVE';
 if v_user is null then raise exception 'forbidden'; end if;
 select preparation_id into v_id from public.income_gap_preparations where user_id=v_user order by saved_at desc,created_at desc limit 1;
 if v_id is null then return null; end if;
 return public.rpc_gap_review_get(p_internal_secret,p_auth_subject,v_id);
end $$;

create function public.rpc_gap_review_confirm(p_internal_secret text,p_auth_subject uuid,p_preparation_id uuid,
 p_group text,p_expected_revision integer,p_request_id uuid,p_request_hash text,p_answers jsonb,p_digest text,
 p_status text,p_fact_rows jsonb,p_top3_before jsonb,p_top3_after jsonb,p_invalidated_groups jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_user uuid; v_row public.income_gap_preparations; v_previous jsonb; v_response jsonb;
 v_action uuid; v_fact jsonb; v_keys jsonb; v_revision integer; v_group text;
begin
 if private.valid_internal_secret(p_internal_secret) is not true or private.request_is_internal() is not true then raise exception 'forbidden'; end if;
 select ai.user_id into v_user from public.auth_identities ai join public.users u on ai.user_id=u.user_id
 where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text and u.status='ACTIVE';
 select * into v_row from public.income_gap_preparations where preparation_id=p_preparation_id and user_id=v_user for update;
 if not found then raise exception 'gap preparation not found'; end if;
 v_previous:=v_row.review_requests->p_request_id::text;
 if v_previous is not null then
   if v_previous->>'hash'<>p_request_hash then raise exception 'gap request conflict'; end if;
   return (v_previous->'response')||jsonb_build_object('idempotent',true);
 end if;
 if v_row.revision<>p_expected_revision then raise exception 'gap revision conflict'; end if;
 if (select count(*) from jsonb_object_keys(v_row.review_requests))>=100 then raise exception 'gap review limit'; end if;
 if p_group not in ('RETIREMENT','NPS','BUDGET','BRIDGE') or p_status not in ('DONE','PARTIAL')
    or p_request_hash !~ '^[0-9a-f]{64}$' or p_digest !~ '^[0-9a-f]{64}$'
    or jsonb_typeof(p_fact_rows)<>'array' or jsonb_array_length(p_fact_rows)=0 then raise exception 'gap invalid facts'; end if;
 if p_status='DONE' and exists(select 1 from jsonb_array_elements(p_fact_rows) f where f->>'status'='UNKNOWN') then raise exception 'gap invalid facts'; end if;
 for v_group in select jsonb_array_elements_text(p_invalidated_groups) loop
   if v_group not in ('RETIREMENT','NPS','BUDGET','BRIDGE') or v_group=p_group then raise exception 'gap invalid facts'; end if;
   update public.facts set status='STALE',updated_at=now() where user_id=v_user and source_ref='GAP_REVIEW:'||p_preparation_id::text||':'||v_group;
   update public.action_instances set status='REVIEW_DUE',updated_at=now() where user_id=v_user
     and action_instance_id=(v_row.confirmations->v_group->>'action_instance_id')::uuid and action_catalog_id='GAP_V1_'||v_group;
 end loop;
 for v_fact in select value from jsonb_array_elements(p_fact_rows) loop
   if left(v_fact->>'fact_key',length('gap.v1.'||p_preparation_id::text||'.'))<>'gap.v1.'||p_preparation_id::text||'.'
      or v_fact->>'status' not in ('KNOWN','UNKNOWN','NOT_APPLICABLE')
      or v_fact->>'source_ref'<>'GAP_REVIEW:'||p_preparation_id::text||':'||p_group
      or v_fact->>'source_type' not in ('USER_CONFIRMED','RULE_DERIVED')
      or (v_fact->>'status'='KNOWN' and (v_fact->'value' is null or v_fact->'value'='null'::jsonb))
      or (v_fact->>'status' in ('UNKNOWN','NOT_APPLICABLE') and v_fact->'value'<>'null'::jsonb)
   then raise exception 'gap invalid facts'; end if;
   insert into public.facts(user_id,fact_key,status,value_json,unit,source_type,source_ref,verification_level,confirmed_at,updated_at)
   values(v_user,v_fact->>'fact_key',v_fact->>'status',v_fact->'value',v_fact->>'unit',v_fact->>'source_type',v_fact->>'source_ref','SELF_REPORTED',now(),now())
   on conflict(user_id,fact_key) do update set status=excluded.status,value_json=excluded.value_json,unit=excluded.unit,
     source_type=excluded.source_type,source_ref=excluded.source_ref,verification_level=excluded.verification_level,confirmed_at=excluded.confirmed_at,updated_at=now();
 end loop;
 v_action:=(v_row.confirmations->p_group->>'action_instance_id')::uuid;
 if v_action is null then
   insert into public.action_instances(user_id,action_catalog_id,status,mode,started_at)
   values(v_user,'GAP_V1_'||p_group,'IN_PROGRESS','VERIFY',now()) returning action_instance_id into v_action;
 end if;
 update public.action_instances set status=case when p_status='DONE' then 'SELF_REPORTED_DONE' else 'IN_PROGRESS' end,
   completed_at=case when p_status='DONE' then now() else null end,draft_json='{}',updated_at=now()
 where action_instance_id=v_action and user_id=v_user and action_catalog_id='GAP_V1_'||p_group;
 if not found then raise exception 'gap preparation not found'; end if;
 v_revision:=v_row.revision+1;
 v_response:=jsonb_build_object('idempotent',false,'group',p_group,'status',p_status,'revision',v_revision,'action_instance_id',v_action);
 update public.income_gap_preparations set answers=p_answers,revision=v_revision,
   confirmations=confirmations||jsonb_build_object(p_group,jsonb_build_object('status',p_status,'digest',p_digest,'action_instance_id',v_action)),
   review_requests=review_requests||jsonb_build_object(p_request_id::text,jsonb_build_object('hash',p_request_hash,'response',v_response))
 where preparation_id=p_preparation_id;
 select jsonb_agg(x->>'fact_key') into v_keys from jsonb_array_elements(p_fact_rows) x;
 insert into public.activity_log(user_id,event_type,entity_type,entity_id,summary_code,metadata_json)
 values(v_user,'GAP_REVIEW_CONFIRMED','GAP_PREPARATION',p_preparation_id::text,p_status,
   jsonb_build_object('group',p_group,'fact_keys',v_keys,'top3_before',p_top3_before,'top3_after',p_top3_after,'revision',v_revision,'invalidated_groups',p_invalidated_groups));
 return v_response;
end $$;
revoke all on function public.rpc_gap_review_get(text,uuid,uuid) from public;
revoke all on function public.rpc_gap_review_confirm(text,uuid,uuid,text,integer,uuid,text,jsonb,text,text,jsonb,jsonb,jsonb,jsonb) from public;
grant execute on function public.rpc_gap_review_get(text,uuid,uuid) to anon;
grant execute on function public.rpc_gap_review_confirm(text,uuid,uuid,text,integer,uuid,text,jsonb,text,text,jsonb,jsonb,jsonb,jsonb) to anon;
