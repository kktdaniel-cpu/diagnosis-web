-- Member-only receipt; not a booking or outbound message.
create function public.rpc_consultation_request(p_internal_secret text,p_auth_subject uuid,p_preparation_id uuid,p_request_id uuid,p_topic text)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare v_user uuid; v_old jsonb; v_result jsonb;
begin
 if private.valid_internal_secret(p_internal_secret) is not true or private.request_is_internal() is not true then raise exception 'forbidden'; end if;
 select ai.user_id into v_user from public.auth_identities ai join public.users u on ai.user_id=u.user_id
 where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text and u.status='ACTIVE';
 if v_user is null or not exists(select 1 from public.income_gap_preparations where preparation_id=p_preparation_id and user_id=v_user) then raise exception 'gap preparation not found'; end if;
 if p_topic not in ('CALENDAR','PENSION','BUDGET','WORK') then raise exception 'gap invalid facts'; end if;
 perform pg_advisory_xact_lock(hashtextextended(v_user::text,0));
 select metadata_json into v_old from public.activity_log where user_id=v_user and event_type='CONSULTATION_REQUESTED' and entity_id=p_request_id::text limit 1;
 if v_old is not null then
  if v_old->>'preparation_id'<>p_preparation_id::text or v_old->>'topic'<>p_topic then raise exception 'consultation conflict'; end if;
  return v_old||jsonb_build_object('idempotent',true);
 end if;
 if (select count(*) from public.activity_log where user_id=v_user and event_type='CONSULTATION_REQUESTED')>=20 then raise exception 'consultation limit'; end if;
 v_result:=jsonb_build_object('request_id',p_request_id,'preparation_id',p_preparation_id,'topic',p_topic,'status','RECEIVED','notification_status','NOT_CONFIGURED','idempotent',false);
 insert into public.activity_log(user_id,event_type,entity_type,entity_id,summary_code,metadata_json)
 values(v_user,'CONSULTATION_REQUESTED','CONSULTATION_REQUEST',p_request_id::text,'RECEIVED',v_result);
 return v_result;
end $$;
revoke all on function public.rpc_consultation_request(text,uuid,uuid,uuid,text) from public;
grant execute on function public.rpc_consultation_request(text,uuid,uuid,uuid,text) to anon;
