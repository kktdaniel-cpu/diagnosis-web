-- Prepared for life2-master-v2 dev. Apply together with the RC API change.
-- UNKNOWN/INVALID/STALE facts keep Awareness PARTIAL and Findings OPEN.
-- Existing history is not rewritten. Review legacy confirmed rows separately.
-- Signature, SECURITY INVOKER, internal gate and privileges are unchanged.
CREATE OR REPLACE FUNCTION public.rpc_action_complete(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_action_catalog_id text, p_question_id text, p_fact_rows jsonb, p_new_top3 jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_action public.action_instances%rowtype;
  v_run public.awareness_runs%rowtype;
  v_fact jsonb;
  v_item jsonb;
  v_dashboard jsonb;
  v_fact_keys jsonb := '[]'::jsonb;
  v_top3_before jsonb := '[]'::jsonb;
  v_top3_after jsonb := '[]'::jsonb;
  v_event_id uuid;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select * into v_action
  from public.action_instances a
  where a.action_instance_id=p_action_instance_id
    and a.user_id=v_user_id
  for update;

  if v_action.action_instance_id is null then
    raise exception 'action not found' using errcode='P0002';
  end if;

  if v_action.action_catalog_id <> p_action_catalog_id then
    raise exception 'action catalog mismatch' using errcode='22023';
  end if;

  if v_action.status in ('SELF_REPORTED_DONE','VERIFIED_DONE') then
    v_dashboard := public.rpc_member_dashboard(p_internal_secret,p_auth_subject);
    return jsonb_build_object('idempotent',true,'dashboard',v_dashboard);
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.user_id=v_user_id
  order by coalesce(r.attached_at,r.created_at) desc
  limit 1
  for update;

  if v_run.run_id is null then
    raise exception 'awareness not found' using errcode='P0002';
  end if;

  select coalesce(jsonb_agg(to_jsonb(x->>'fact_key')),'[]'::jsonb)
  into v_fact_keys
  from jsonb_array_elements(coalesce(p_fact_rows,'[]'::jsonb)) x;

  select coalesce(jsonb_agg(to_jsonb(x->>'action_catalog_id')),'[]'::jsonb)
  into v_top3_before
  from jsonb_array_elements(coalesce(v_run.top3_json,'[]'::jsonb)) x;

  select coalesce(jsonb_agg(to_jsonb(x->>'action_catalog_id')),'[]'::jsonb)
  into v_top3_after
  from jsonb_array_elements(coalesce(p_new_top3,'[]'::jsonb)) x;

  for v_fact in select value from jsonb_array_elements(coalesce(p_fact_rows,'[]'::jsonb))
  loop
    insert into public.facts(
      user_id,fact_key,status,value_json,unit,source_type,source_ref,
      verification_level,confirmed_at,updated_at
    ) values (
      v_user_id,
      v_fact->>'fact_key',
      coalesce(v_fact->>'status','KNOWN'),
      v_fact->'value',
      v_fact->>'unit',
      v_fact->>'source_type',
      v_fact->>'source_ref',
      coalesce(v_fact->>'verification_level','SELF_REPORTED'),
      now(),
      now()
    )
    on conflict (user_id,fact_key)
    do update set
      status=excluded.status,
      value_json=excluded.value_json,
      unit=excluded.unit,
      source_type=excluded.source_type,
      source_ref=excluded.source_ref,
      verification_level=excluded.verification_level,
      confirmed_at=excluded.confirmed_at,
      updated_at=now();
  end loop;

  update public.action_instances
  set status='SELF_REPORTED_DONE',
      completed_at=now(),
      draft_json='{}'::jsonb,
      updated_at=now()
  where action_instance_id=p_action_instance_id;

  update public.awareness_answers
  set response=case when jsonb_array_length(coalesce(p_fact_rows,'[]'::jsonb)) > 0
        and not exists (
          select 1 from jsonb_array_elements(coalesce(p_fact_rows,'[]'::jsonb)) f
          where coalesce(f->>'status','KNOWN') not in ('KNOWN','NOT_APPLICABLE')
        ) then 'CONFIRMED' else 'PARTIAL' end,
      created_at=now()
  where run_id=v_run.run_id
    and question_id=p_question_id;

  update public.findings
  set status='RESOLVED',
      resolved_at=now()
  where user_id=v_user_id
    and status='OPEN'
    and source_refs @> jsonb_build_array(p_question_id)
    and not exists (
      select 1 from public.awareness_answers aa
      where aa.run_id=v_run.run_id and aa.question_id=p_question_id
        and aa.response <> 'CONFIRMED'
    );

  update public.awareness_runs
  set top3_json=coalesce(p_new_top3,'[]'::jsonb)
  where run_id=v_run.run_id;

  for v_item in select value from jsonb_array_elements(coalesce(p_new_top3,'[]'::jsonb))
  loop
    if not exists (
      select 1 from public.action_instances a
      where a.user_id=v_user_id
        and a.action_catalog_id=v_item->>'action_catalog_id'
        and a.status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE')
    ) then
      insert into public.action_instances(
        user_id,action_catalog_id,status,mode,priority_class
      ) values (
        v_user_id,
        v_item->>'action_catalog_id',
        'NOT_STARTED',
        coalesce(v_item->>'mode','CREATE'),
        v_item->>'priority_class'
      );
    end if;
  end loop;

  insert into public.activity_log(
    user_id,event_type,entity_type,entity_id,summary_code,metadata_json
  ) values (
    v_user_id,
    'ACTION_COMPLETED',
    'action_instance',
    p_action_instance_id::text,
    v_action.action_catalog_id,
    jsonb_build_object(
      'question_id',p_question_id,
      'awareness_response',(select aa.response from public.awareness_answers aa where aa.run_id=v_run.run_id and aa.question_id=p_question_id),
      'fact_keys',v_fact_keys,
      'top3_before',v_top3_before,
      'top3_after',v_top3_after,
      'top3_changed',v_top3_before <> v_top3_after
    )
  )
  returning event_id into v_event_id;

  v_dashboard := public.rpc_member_dashboard(p_internal_secret,p_auth_subject);
  return jsonb_build_object(
    'idempotent',false,
    'event_id',v_event_id,
    'dashboard',v_dashboard
  );
end
$function$
;

