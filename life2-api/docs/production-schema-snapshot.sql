-- Schema-only dev catalog snapshot. Proposal; not yet applied to life2-prod.

-- No table rows, Auth users, secret hashes, or runtime credentials are included.

-- Target must be a new empty LIFE 2.0 database; do not replay repository placeholders.

BEGIN;

SET LOCAL search_path = public, extensions;

SET LOCAL check_function_bodies = off;

DO $$ BEGIN IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema IN ('public','private')) THEN RAISE EXCEPTION 'Target is not empty'; END IF; END $$;

CREATE SCHEMA IF NOT EXISTS private;

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

CREATE TABLE "public"."users" (
  "user_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "status" text DEFAULT 'ACTIVE'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "deleted_at" timestamp with time zone
);

CREATE TABLE "public"."legacy_source_links" (
  "legacy_link_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "source_system" text NOT NULL,
  "source_record_key" text NOT NULL,
  "record_type" text NOT NULL,
  "source_version" text,
  "claim_status" text DEFAULT 'PENDING'::text NOT NULL,
  "match_method" text,
  "access_mode" text DEFAULT 'READ_ONLY'::text NOT NULL,
  "claimed_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."legacy_claim_audit" (
  "audit_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "legacy_link_id" uuid,
  "user_id" uuid NOT NULL,
  "event_type" text NOT NULL,
  "metadata_json" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "occurred_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."action_instances" (
  "action_instance_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "action_catalog_id" text NOT NULL,
  "status" text NOT NULL,
  "mode" text NOT NULL,
  "priority_class" text,
  "started_at" timestamp with time zone,
  "completed_at" timestamp with time zone,
  "verification_level" text DEFAULT 'SELF_REPORTED'::text NOT NULL,
  "next_review_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
  "draft_json" jsonb DEFAULT '{}'::jsonb NOT NULL
);

CREATE TABLE "private"."api_secrets" (
  "name" text NOT NULL,
  "secret_hash" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "rotated_at" timestamp with time zone
);

CREATE TABLE "public"."activity_log" (
  "event_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "event_type" text NOT NULL,
  "entity_type" text,
  "entity_id" text,
  "summary_code" text,
  "metadata_json" jsonb DEFAULT '{}'::jsonb NOT NULL,
  "occurred_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."idempotency_keys" (
  "user_id" uuid NOT NULL,
  "key" text NOT NULL,
  "response_json" jsonb,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."awareness_runs" (
  "run_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid,
  "age_band" text NOT NULL,
  "household_type" text NOT NULL,
  "status" text DEFAULT 'IN_PROGRESS'::text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "attached_at" timestamp with time zone,
  "run_token_hash" text,
  "handoff_token_hash" text,
  "expires_at" timestamp with time zone DEFAULT (now() + '04:00:00'::interval) NOT NULL,
  "completed_at" timestamp with time zone,
  "top3_json" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "findings_json" jsonb DEFAULT '[]'::jsonb NOT NULL
);

CREATE TABLE "public"."awareness_answers" (
  "run_id" uuid NOT NULL,
  "question_id" text NOT NULL,
  "response" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."auth_identities" (
  "auth_identity_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "provider" text NOT NULL,
  "provider_subject" text NOT NULL,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."facts" (
  "fact_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "fact_key" text NOT NULL,
  "status" text NOT NULL,
  "value_json" jsonb,
  "unit" text,
  "source_type" text NOT NULL,
  "source_ref" text,
  "verification_level" text DEFAULT 'SELF_REPORTED'::text NOT NULL,
  "confirmed_at" timestamp with time zone,
  "review_due_at" timestamp with time zone,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "updated_at" timestamp with time zone DEFAULT now() NOT NULL
);

CREATE TABLE "public"."findings" (
  "finding_id" uuid DEFAULT gen_random_uuid() NOT NULL,
  "user_id" uuid NOT NULL,
  "finding_type" text NOT NULL,
  "status" text NOT NULL,
  "source_refs" jsonb DEFAULT '[]'::jsonb NOT NULL,
  "recommended_action_catalog_id" text,
  "created_at" timestamp with time zone DEFAULT now() NOT NULL,
  "resolved_at" timestamp with time zone
);

ALTER TABLE "public"."action_instances" ADD CONSTRAINT "action_instances_pkey" PRIMARY KEY (action_instance_id);

ALTER TABLE "public"."activity_log" ADD CONSTRAINT "activity_log_pkey" PRIMARY KEY (event_id);

ALTER TABLE "public"."users" ADD CONSTRAINT "users_status_check" CHECK ((status = ANY (ARRAY['ACTIVE'::text, 'DELETED'::text])));

ALTER TABLE "public"."users" ADD CONSTRAINT "users_pkey" PRIMARY KEY (user_id);

ALTER TABLE "public"."auth_identities" ADD CONSTRAINT "auth_identities_pkey" PRIMARY KEY (auth_identity_id);

ALTER TABLE "public"."auth_identities" ADD CONSTRAINT "auth_identities_provider_provider_subject_key" UNIQUE (provider, provider_subject);

ALTER TABLE "public"."awareness_runs" ADD CONSTRAINT "awareness_runs_household_type_check" CHECK ((household_type = ANY (ARRAY['single'::text, 'couple'::text])));

ALTER TABLE "public"."awareness_runs" ADD CONSTRAINT "awareness_runs_pkey" PRIMARY KEY (run_id);

ALTER TABLE "public"."idempotency_keys" ADD CONSTRAINT "idempotency_keys_pkey" PRIMARY KEY (user_id, key);

ALTER TABLE "public"."awareness_answers" ADD CONSTRAINT "awareness_answers_response_check" CHECK ((response = ANY (ARRAY['CONFIRMED'::text, 'PARTIAL'::text, 'UNKNOWN_OR_NOT_PREPARED'::text, 'NOT_APPLICABLE'::text])));

ALTER TABLE "public"."awareness_answers" ADD CONSTRAINT "awareness_answers_pkey" PRIMARY KEY (run_id, question_id);

ALTER TABLE "public"."facts" ADD CONSTRAINT "facts_status_check" CHECK ((status = ANY (ARRAY['KNOWN'::text, 'UNKNOWN'::text, 'NOT_APPLICABLE'::text, 'INVALID'::text, 'STALE'::text])));

ALTER TABLE "public"."facts" ADD CONSTRAINT "facts_pkey" PRIMARY KEY (fact_id);

ALTER TABLE "public"."facts" ADD CONSTRAINT "facts_user_id_fact_key_key" UNIQUE (user_id, fact_key);

ALTER TABLE "public"."findings" ADD CONSTRAINT "findings_status_check" CHECK ((status = ANY (ARRAY['OPEN'::text, 'RESOLVED'::text, 'SUPPRESSED'::text, 'NOT_APPLICABLE'::text])));

ALTER TABLE "public"."findings" ADD CONSTRAINT "findings_pkey" PRIMARY KEY (finding_id);

ALTER TABLE "public"."action_instances" ADD CONSTRAINT "action_instances_status_check" CHECK ((status = ANY (ARRAY['NOT_STARTED'::text, 'IN_PROGRESS'::text, 'WAITING_EXTERNAL'::text, 'SELF_REPORTED_DONE'::text, 'VERIFIED_DONE'::text, 'REVIEW_DUE'::text, 'NOT_APPLICABLE'::text])));

ALTER TABLE "public"."action_instances" ADD CONSTRAINT "action_instances_mode_check" CHECK ((mode = ANY (ARRAY['CREATE'::text, 'VERIFY'::text])));

ALTER TABLE "public"."legacy_source_links" ADD CONSTRAINT "legacy_source_links_record_type_check" CHECK ((record_type = ANY (ARRAY['FULL_DIAGNOSIS'::text, 'QUICK_DIAGNOSIS'::text, 'DRAFT'::text])));

ALTER TABLE "public"."legacy_source_links" ADD CONSTRAINT "legacy_source_links_claim_status_check" CHECK ((claim_status = ANY (ARRAY['UNCLAIMED'::text, 'PENDING'::text, 'VERIFIED'::text, 'REJECTED'::text])));

ALTER TABLE "public"."legacy_source_links" ADD CONSTRAINT "legacy_source_links_access_mode_check" CHECK ((access_mode = 'READ_ONLY'::text));

ALTER TABLE "public"."legacy_source_links" ADD CONSTRAINT "legacy_source_links_pkey" PRIMARY KEY (legacy_link_id);

ALTER TABLE "public"."legacy_source_links" ADD CONSTRAINT "legacy_source_links_source_system_record_type_source_record_key" UNIQUE (source_system, record_type, source_record_key);

ALTER TABLE "public"."legacy_claim_audit" ADD CONSTRAINT "legacy_claim_audit_event_type_check" CHECK ((event_type = ANY (ARRAY['SEARCHED'::text, 'CANDIDATE_PRESENTED'::text, 'CLAIM_REQUESTED'::text, 'VERIFIED'::text, 'REJECTED'::text, 'UNLINKED'::text])));

ALTER TABLE "public"."legacy_claim_audit" ADD CONSTRAINT "legacy_claim_audit_pkey" PRIMARY KEY (audit_id);

ALTER TABLE "private"."api_secrets" ADD CONSTRAINT "api_secrets_pkey" PRIMARY KEY (name);

ALTER TABLE "public"."action_instances" ADD CONSTRAINT "action_instances_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."activity_log" ADD CONSTRAINT "activity_log_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."auth_identities" ADD CONSTRAINT "auth_identities_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."awareness_runs" ADD CONSTRAINT "awareness_runs_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."idempotency_keys" ADD CONSTRAINT "idempotency_keys_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."awareness_answers" ADD CONSTRAINT "awareness_answers_run_id_fkey" FOREIGN KEY (run_id) REFERENCES awareness_runs(run_id) ON DELETE CASCADE;

ALTER TABLE "public"."facts" ADD CONSTRAINT "facts_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."findings" ADD CONSTRAINT "findings_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."legacy_source_links" ADD CONSTRAINT "legacy_source_links_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

ALTER TABLE "public"."legacy_claim_audit" ADD CONSTRAINT "legacy_claim_audit_legacy_link_id_fkey" FOREIGN KEY (legacy_link_id) REFERENCES legacy_source_links(legacy_link_id) ON DELETE SET NULL;

ALTER TABLE "public"."legacy_claim_audit" ADD CONSTRAINT "legacy_claim_audit_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;

CREATE UNIQUE INDEX uq_action_active_per_user_catalog ON public.action_instances USING btree (user_id, action_catalog_id) WHERE (status = ANY (ARRAY['NOT_STARTED'::text, 'IN_PROGRESS'::text, 'WAITING_EXTERNAL'::text, 'REVIEW_DUE'::text]));

CREATE INDEX idx_awareness_runs_user_id ON public.awareness_runs USING btree (user_id);

CREATE INDEX idx_legacy_source_links_user_id ON public.legacy_source_links USING btree (user_id);

CREATE UNIQUE INDEX uq_awareness_runs_run_token_hash ON public.awareness_runs USING btree (run_token_hash) WHERE (run_token_hash IS NOT NULL);

CREATE INDEX idx_findings_user_id ON public.findings USING btree (user_id);

CREATE INDEX idx_activity_log_user_id ON public.activity_log USING btree (user_id);

CREATE INDEX idx_action_instances_user_id ON public.action_instances USING btree (user_id);

CREATE INDEX idx_auth_identities_user_id ON public.auth_identities USING btree (user_id);

CREATE INDEX idx_legacy_claim_audit_link_id ON public.legacy_claim_audit USING btree (legacy_link_id);

CREATE INDEX idx_facts_user_id ON public.facts USING btree (user_id);

CREATE UNIQUE INDEX uq_awareness_runs_handoff_token_hash ON public.awareness_runs USING btree (handoff_token_hash) WHERE (handoff_token_hash IS NOT NULL);

CREATE INDEX idx_legacy_claim_audit_user_id ON public.legacy_claim_audit USING btree (user_id);

CREATE OR REPLACE FUNCTION private.current_life_user_id()
 RETURNS uuid
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  select ai.user_id
  from public.auth_identities ai
  where ai.provider = 'supabase'
    and ai.provider_subject = (select auth.uid())::text
  limit 1
$function$;

CREATE OR REPLACE FUNCTION private.handle_new_auth_user()
 RETURNS trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
begin
  insert into public.users default values returning user_id into v_user_id;
  insert into public.auth_identities(user_id, provider, provider_subject)
  values (v_user_id, 'supabase', new.id::text)
  on conflict (provider, provider_subject) do nothing;
  return new;
end
$function$;

CREATE OR REPLACE FUNCTION private.valid_internal_secret(p_secret text)
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  select exists (
    select 1
    from private.api_secrets s
    where s.name = 'life2_rpc'
      and s.secret_hash = encode(extensions.digest(coalesce(p_secret,'')::bytea, 'sha256'), 'hex')
  )
$function$;

CREATE OR REPLACE FUNCTION public.rpc_awareness_put_answer(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text)
 RETURNS jsonb
 LANGUAGE sql
 SET search_path TO ''
AS $function$ select private.rpc_awareness_put_answer($1,$2,$3,$4,$5); $function$;

CREATE OR REPLACE FUNCTION public.rpc_awareness_get(p_internal_secret text, p_run_id uuid, p_run_token text)
 RETURNS jsonb
 LANGUAGE sql
 SET search_path TO ''
AS $function$ select private.rpc_awareness_get($1,$2,$3); $function$;

CREATE OR REPLACE FUNCTION private.rpc_awareness_create(p_internal_secret text, p_age_band text, p_household_type text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_run_id uuid;
  v_token text;
  v_token_hash text;
  v_expires timestamptz;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  if p_household_type not in ('single','couple') then
    raise exception 'invalid household_type' using errcode='22023';
  end if;

  v_token := encode(extensions.gen_random_bytes(32),'hex');
  v_token_hash := encode(extensions.digest(v_token::bytea,'sha256'),'hex');
  v_expires := now() + interval '4 hours';

  insert into public.awareness_runs(age_band, household_type, run_token_hash, expires_at)
  values (p_age_band, p_household_type, v_token_hash, v_expires)
  returning run_id into v_run_id;

  return jsonb_build_object(
    'run_id', v_run_id,
    'run_token', v_token,
    'expires_at', v_expires
  );
end
$function$;

CREATE OR REPLACE FUNCTION private.rpc_awareness_put_answer(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_count int;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  if p_response not in ('CONFIRMED','PARTIAL','UNKNOWN_OR_NOT_PREPARED','NOT_APPLICABLE') then
    raise exception 'invalid response' using errcode='22023';
  end if;

  if not exists (
    select 1 from public.awareness_runs r
    where r.run_id = p_run_id
      and r.run_token_hash = encode(extensions.digest(p_run_token::bytea,'sha256'),'hex')
      and r.completed_at is null
      and r.expires_at > now()
  ) then
    raise exception 'invalid or expired run' using errcode='42501';
  end if;

  insert into public.awareness_answers(run_id, question_id, response)
  values (p_run_id, p_question_id, p_response)
  on conflict (run_id, question_id)
  do update set response = excluded.response, created_at = now();

  select count(*) into v_count
  from public.awareness_answers
  where run_id = p_run_id;

  return jsonb_build_object('saved', true, 'answered', v_count, 'total', 12);
end
$function$;

CREATE OR REPLACE FUNCTION private.rpc_awareness_get(p_internal_secret text, p_run_id uuid, p_run_token text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_run public.awareness_runs%rowtype;
  v_answers jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.run_id = p_run_id
    and r.run_token_hash = encode(extensions.digest(p_run_token::bytea,'sha256'),'hex');

  if v_run.run_id is null then
    raise exception 'run not found' using errcode='P0002';
  end if;

  select coalesce(jsonb_object_agg(a.question_id, a.response), '{}'::jsonb)
  into v_answers
  from public.awareness_answers a
  where a.run_id = p_run_id;

  return jsonb_build_object(
    'run_id', v_run.run_id,
    'age_band', v_run.age_band,
    'household_type', v_run.household_type,
    'answers', v_answers,
    'completed', v_run.completed_at is not null,
    'expires_at', v_run.expires_at,
    'top3', v_run.top3_json,
    'findings', v_run.findings_json
  );
end
$function$;

CREATE OR REPLACE FUNCTION private.rpc_awareness_finalize(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_handoff text;
  v_run public.awareness_runs%rowtype;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.run_id = p_run_id
    and r.run_token_hash = encode(extensions.digest(p_run_token::bytea,'sha256'),'hex')
    and r.expires_at > now()
  for update;

  if v_run.run_id is null then
    raise exception 'invalid or expired run' using errcode='42501';
  end if;

  if (select count(*) from public.awareness_answers where run_id = p_run_id) <> 12 then
    raise exception 'awareness incomplete' using errcode='23514';
  end if;

  v_handoff := encode(
    extensions.hmac(p_run_token::bytea, p_internal_secret::bytea, 'sha256'),
    'hex'
  );

  if v_run.completed_at is null then
    update public.awareness_runs
    set completed_at = now(),
        status = 'COMPLETED',
        handoff_token_hash = encode(extensions.digest(v_handoff::bytea,'sha256'),'hex'),
        top3_json = coalesce(p_top3,'[]'::jsonb),
        findings_json = coalesce(p_findings,'[]'::jsonb)
    where run_id = p_run_id;
  end if;

  return jsonb_build_object(
    'handoff_token', v_handoff,
    'top3', case when v_run.completed_at is null then coalesce(p_top3,'[]'::jsonb) else v_run.top3_json end,
    'findings', case when v_run.completed_at is null then coalesce(p_findings,'[]'::jsonb) else v_run.findings_json end,
    'idempotent', v_run.completed_at is not null
  );
end
$function$;

CREATE OR REPLACE FUNCTION private.rpc_awareness_claim(p_internal_secret text, p_handoff_token text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_run public.awareness_runs%rowtype;
  v_item jsonb;
  v_idempotent boolean := false;
  v_dashboard jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject = p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.handoff_token_hash = encode(extensions.digest(p_handoff_token::bytea,'sha256'),'hex')
    and r.completed_at is not null
    and r.expires_at > now()
  for update;

  if v_run.run_id is null then
    raise exception 'handoff not found or expired' using errcode='P0002';
  end if;

  if v_run.user_id is not null and v_run.user_id <> v_user_id then
    raise exception 'handoff already claimed' using errcode='23505';
  end if;

  if v_run.user_id = v_user_id then
    v_idempotent := true;
  else
    update public.awareness_runs
    set user_id = v_user_id, attached_at = now(), status='CLAIMED'
    where run_id = v_run.run_id;

    for v_item in select value from jsonb_array_elements(v_run.findings_json)
    loop
      insert into public.findings(user_id, finding_type, status, source_refs, recommended_action_catalog_id)
      values (
        v_user_id,
        v_item->>'finding_type',
        coalesce(v_item->>'status','OPEN'),
        jsonb_build_array(v_item->>'source_ref'),
        null
      );
    end loop;

    for v_item in select value from jsonb_array_elements(v_run.top3_json)
    loop
      insert into public.action_instances(
        user_id, action_catalog_id, status, mode, priority_class
      )
      values (
        v_user_id,
        v_item->>'action_catalog_id',
        'NOT_STARTED',
        coalesce(v_item->>'mode','CREATE'),
        v_item->>'priority_class'
      );
    end loop;

    insert into public.activity_log(user_id,event_type,entity_type,entity_id,summary_code)
    values(v_user_id,'AWARENESS_COMPLETED','awareness_run',v_run.run_id::text,'AWARENESS_COMPLETED');
  end if;

  v_dashboard := public.rpc_member_dashboard(p_internal_secret, p_auth_subject);

  return jsonb_build_object(
    'claimed', true,
    'idempotent', v_idempotent,
    'dashboard', v_dashboard
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_awareness_claim(p_internal_secret text, p_handoff_token text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE sql
 SET search_path TO ''
AS $function$ select private.rpc_awareness_claim($1,$2,$3); $function$;

CREATE OR REPLACE FUNCTION private.rpc_member_dashboard(p_internal_secret text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_run public.awareness_runs%rowtype;
  v_confirmed int := 0;
  v_top3 jsonb := '[]'::jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject = p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.user_id = v_user_id
  order by coalesce(r.attached_at,r.created_at) desc
  limit 1;

  if v_run.run_id is not null then
    select count(*) into v_confirmed
    from public.awareness_answers a
    where a.run_id = v_run.run_id and a.response='CONFIRMED';

    select coalesce(jsonb_agg(
      jsonb_build_object(
        'action_catalog_id', ai.action_catalog_id,
        'mode', ai.mode,
        'priority_class', ai.priority_class,
        'status', ai.status
      )
      order by ai.created_at
    ), '[]'::jsonb)
    into v_top3
    from public.action_instances ai
    where ai.user_id = v_user_id
      and ai.status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE');
  end if;

  return jsonb_build_object(
    'confirmed_awareness_count', v_confirmed,
    'awareness_total', 12,
    'top3', v_top3,
    'in_progress', '[]'::jsonb,
    'recent_changes', '[]'::jsonb
  );
end
$function$;

CREATE OR REPLACE FUNCTION private.request_is_internal()
 RETURNS boolean
 LANGUAGE sql
 STABLE SECURITY DEFINER
 SET search_path TO ''
AS $function$
  select private.valid_internal_secret(
    coalesce(current_setting('request.headers', true)::json->>'x-life2-internal-secret','')
  )
$function$;

CREATE OR REPLACE FUNCTION public.rpc_awareness_create(p_internal_secret text, p_age_band text, p_household_type text)
 RETURNS jsonb
 LANGUAGE sql
 SET search_path TO ''
AS $function$ select private.rpc_awareness_create($1,$2,$3); $function$;

CREATE OR REPLACE FUNCTION public.rpc_awareness_finalize(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb)
 RETURNS jsonb
 LANGUAGE sql
 SET search_path TO ''
AS $function$ select private.rpc_awareness_finalize($1,$2,$3,$4,$5); $function$;

CREATE OR REPLACE FUNCTION public.rpc_member_dashboard(p_internal_secret text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_run public.awareness_runs%rowtype;
  v_confirmed int := 0;
  v_top3 jsonb := '[]'::jsonb;
  v_in_progress jsonb := '[]'::jsonb;
  v_recent jsonb := '[]'::jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.user_id=v_user_id
  order by coalesce(r.attached_at,r.created_at) desc
  limit 1;

  if v_run.run_id is not null then
    select count(*) into v_confirmed
    from public.awareness_answers a
    where a.run_id=v_run.run_id and a.response='CONFIRMED';

    select coalesce(jsonb_agg(
      x.item || jsonb_build_object(
        'status',
        coalesce((
          select ai.status
          from public.action_instances ai
          where ai.user_id=v_user_id
            and ai.action_catalog_id=x.item->>'action_catalog_id'
            and ai.status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE')
          order by ai.updated_at desc
          limit 1
        ),'NOT_STARTED')
      )
      order by x.ord
    ),'[]'::jsonb)
    into v_top3
    from jsonb_array_elements(v_run.top3_json) with ordinality as x(item,ord);

    select coalesce(jsonb_agg(jsonb_build_object(
      'action_instance_id',a.action_instance_id,
      'action_catalog_id',a.action_catalog_id,
      'status',a.status,
      'mode',a.mode,
      'updated_at',a.updated_at
    ) order by a.updated_at desc),'[]'::jsonb)
    into v_in_progress
    from public.action_instances a
    where a.user_id=v_user_id
      and a.status in ('IN_PROGRESS','WAITING_EXTERNAL');

    select coalesce(jsonb_agg(jsonb_build_object(
      'event_type',l.event_type,
      'summary_code',l.summary_code,
      'occurred_at',l.occurred_at
    ) order by l.occurred_at desc),'[]'::jsonb)
    into v_recent
    from (
      select * from public.activity_log
      where user_id=v_user_id
      order by occurred_at desc
      limit 5
    ) l;
  end if;

  return jsonb_build_object(
    'confirmed_awareness_count',v_confirmed,
    'awareness_total',12,
    'top3',v_top3,
    'in_progress',v_in_progress,
    'recent_changes',v_recent
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_member_awareness(p_internal_secret text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_run public.awareness_runs%rowtype;
  v_answers jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select * into v_run
  from public.awareness_runs r
  where r.user_id=v_user_id
  order by coalesce(r.attached_at,r.created_at) desc
  limit 1;

  if v_run.run_id is null then
    raise exception 'awareness not found' using errcode='P0002';
  end if;

  select coalesce(jsonb_object_agg(a.question_id,a.response),'{}'::jsonb)
  into v_answers
  from public.awareness_answers a
  where a.run_id=v_run.run_id;

  return jsonb_build_object(
    'run_id',v_run.run_id,
    'household_type',v_run.household_type,
    'age_band',v_run.age_band,
    'answers',v_answers
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_action_start(p_internal_secret text, p_auth_subject uuid, p_action_catalog_id text, p_mode text)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_action public.action_instances%rowtype;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  if p_mode not in ('CREATE','VERIFY') then
    raise exception 'invalid mode' using errcode='22023';
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
  where a.user_id=v_user_id
    and a.action_catalog_id=p_action_catalog_id
    and a.status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE')
  order by a.created_at desc
  limit 1
  for update;

  if v_action.action_instance_id is null then
    insert into public.action_instances(
      user_id, action_catalog_id, status, mode, started_at
    ) values (
      v_user_id, p_action_catalog_id, 'IN_PROGRESS', p_mode, now()
    )
    returning * into v_action;
  else
    update public.action_instances
    set status='IN_PROGRESS',
        started_at=coalesce(started_at,now()),
        updated_at=now()
    where action_instance_id=v_action.action_instance_id
    returning * into v_action;
  end if;

  if not exists (
    select 1 from public.activity_log l
    where l.user_id=v_user_id
      and l.event_type='ACTION_STARTED'
      and l.entity_id=v_action.action_instance_id::text
  ) then
    insert into public.activity_log(
      user_id,event_type,entity_type,entity_id,summary_code
    ) values (
      v_user_id,'ACTION_STARTED','action_instance',
      v_action.action_instance_id::text,p_action_catalog_id
    );
  end if;

  return jsonb_build_object(
    'action_instance_id',v_action.action_instance_id,
    'action_catalog_id',v_action.action_catalog_id,
    'status',v_action.status,
    'mode',v_action.mode,
    'draft',v_action.draft_json
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_action_submit(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_draft jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_action public.action_instances%rowtype;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase' and ai.provider_subject=p_auth_subject::text
  limit 1;

  update public.action_instances
  set draft_json=coalesce(p_draft,'{}'::jsonb),
      status='IN_PROGRESS',
      updated_at=now()
  where action_instance_id=p_action_instance_id
    and user_id=v_user_id
    and status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE')
  returning * into v_action;

  if v_action.action_instance_id is null then
    raise exception 'action not found' using errcode='P0002';
  end if;

  return jsonb_build_object(
    'action_instance_id',v_action.action_instance_id,
    'status',v_action.status,
    'draft',v_action.draft_json
  );
end
$function$;

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
$function$;

CREATE OR REPLACE FUNCTION public.rpc_member_facts(p_internal_secret text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_result jsonb;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select coalesce(
    jsonb_object_agg(
      f.fact_key,
      jsonb_build_object(
        'fact_key',f.fact_key,
        'status',f.status,
        'value',f.value_json,
        'unit',f.unit,
        'source_type',f.source_type,
        'source_ref',f.source_ref,
        'verification_level',f.verification_level,
        'confirmed_at',f.confirmed_at,
        'review_due_at',f.review_due_at
      )
    ),
    '{}'::jsonb
  )
  into v_result
  from public.facts f
  where f.user_id=v_user_id;

  return v_result;
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_action_change_event(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_event public.activity_log%rowtype;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  select * into v_event
  from public.activity_log l
  where l.user_id=v_user_id
    and l.event_type='ACTION_COMPLETED'
    and l.entity_type='action_instance'
    and l.entity_id=p_action_instance_id::text
  order by l.occurred_at desc
  limit 1;

  if v_event.event_id is null then
    raise exception 'change event not found' using errcode='P0002';
  end if;

  return jsonb_build_object(
    'event_id',v_event.event_id,
    'action_instance_id',p_action_instance_id,
    'action_catalog_id',v_event.summary_code,
    'metadata',v_event.metadata_json,
    'occurred_at',v_event.occurred_at
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_action_wait(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
  v_action public.action_instances%rowtype;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is null then
    raise exception 'user not provisioned' using errcode='P0002';
  end if;

  update public.action_instances
  set status='WAITING_EXTERNAL',
      updated_at=now()
  where action_instance_id=p_action_instance_id
    and user_id=v_user_id
    and status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE')
  returning * into v_action;

  if v_action.action_instance_id is null then
    raise exception 'action not found' using errcode='P0002';
  end if;

  if not exists (
    select 1 from public.activity_log l
    where l.user_id=v_user_id
      and l.event_type='ACTION_WAITING_EXTERNAL'
      and l.entity_id=p_action_instance_id::text
      and l.occurred_at > now() - interval '1 minute'
  ) then
    insert into public.activity_log(
      user_id,event_type,entity_type,entity_id,summary_code
    ) values (
      v_user_id,'ACTION_WAITING_EXTERNAL','action_instance',
      p_action_instance_id::text,v_action.action_catalog_id
    );
  end if;

  return jsonb_build_object(
    'action_instance_id',v_action.action_instance_id,
    'action_catalog_id',v_action.action_catalog_id,
    'status',v_action.status,
    'mode',v_action.mode,
    'draft',v_action.draft_json
  );
end
$function$;

CREATE OR REPLACE FUNCTION private.delete_account_core(p_internal_secret text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_user_id uuid;
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;

  select ai.user_id into v_user_id
  from public.auth_identities ai
  where ai.provider='supabase'
    and ai.provider_subject=p_auth_subject::text
  limit 1;

  if v_user_id is not null then
    delete from public.users where user_id=v_user_id;
  end if;

  delete from auth.users where id=p_auth_subject;

  return jsonb_build_object(
    'deleted',true,
    'had_life_user',v_user_id is not null
  );
end
$function$;

CREATE OR REPLACE FUNCTION public.rpc_delete_account(p_internal_secret text, p_auth_subject uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO ''
AS $function$
begin
  if not private.valid_internal_secret(p_internal_secret) then
    raise exception 'forbidden' using errcode='42501';
  end if;
  return private.delete_account_core(p_internal_secret,p_auth_subject);
end
$function$;

ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."legacy_source_links" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."legacy_claim_audit" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."action_instances" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "private"."api_secrets" DISABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."activity_log" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."idempotency_keys" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."awareness_runs" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."awareness_answers" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."auth_identities" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."facts" ENABLE ROW LEVEL SECURITY;

ALTER TABLE "public"."findings" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_select_self" ON "public"."users" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "legacy_source_links_select_self" ON "public"."legacy_source_links" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "legacy_claim_audit_select_self" ON "public"."legacy_claim_audit" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "internal_server_actions" ON "public"."action_instances" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "action_instances_select_self" ON "public"."action_instances" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "internal_server_activity" ON "public"."activity_log" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "activity_log_select_self" ON "public"."activity_log" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "internal_server_idempotency" ON "public"."idempotency_keys" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "idempotency_no_client_access" ON "public"."idempotency_keys" AS PERMISSIVE FOR ALL TO "authenticated" USING (false) WITH CHECK (false);

CREATE POLICY "internal_server_awareness_runs" ON "public"."awareness_runs" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "awareness_runs_select_self" ON "public"."awareness_runs" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "internal_server_awareness_answers" ON "public"."awareness_answers" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "awareness_answers_select_self" ON "public"."awareness_answers" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((EXISTS ( SELECT 1
   FROM awareness_runs ar
  WHERE ((ar.run_id = awareness_answers.run_id) AND (ar.user_id = ( SELECT private.current_life_user_id() AS current_life_user_id))))));

CREATE POLICY "internal_server_auth_identities_read" ON "public"."auth_identities" AS PERMISSIVE FOR SELECT TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "auth_identities_select_self" ON "public"."auth_identities" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "internal_server_facts" ON "public"."facts" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "facts_select_self" ON "public"."facts" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE POLICY "internal_server_findings" ON "public"."findings" AS PERMISSIVE FOR ALL TO "anon" USING (( SELECT private.request_is_internal() AS request_is_internal)) WITH CHECK (( SELECT private.request_is_internal() AS request_is_internal));

CREATE POLICY "findings_select_self" ON "public"."findings" AS PERMISSIVE FOR SELECT TO "authenticated" USING ((user_id = ( SELECT private.current_life_user_id() AS current_life_user_id)));

CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION private.handle_new_auth_user();

REVOKE ALL ON TABLE "public"."users" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."users" TO "postgres";

GRANT SELECT ON TABLE "public"."users" TO "postgres";

GRANT UPDATE ON TABLE "public"."users" TO "postgres";

GRANT DELETE ON TABLE "public"."users" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."users" TO "postgres";

GRANT REFERENCES ON TABLE "public"."users" TO "postgres";

GRANT TRIGGER ON TABLE "public"."users" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."users" TO "postgres";

GRANT INSERT ON TABLE "public"."users" TO "anon";

GRANT SELECT ON TABLE "public"."users" TO "anon";

GRANT UPDATE ON TABLE "public"."users" TO "anon";

GRANT DELETE ON TABLE "public"."users" TO "anon";

GRANT TRUNCATE ON TABLE "public"."users" TO "anon";

GRANT REFERENCES ON TABLE "public"."users" TO "anon";

GRANT TRIGGER ON TABLE "public"."users" TO "anon";

GRANT MAINTAIN ON TABLE "public"."users" TO "anon";

GRANT INSERT ON TABLE "public"."users" TO "authenticated";

GRANT SELECT ON TABLE "public"."users" TO "authenticated";

GRANT UPDATE ON TABLE "public"."users" TO "authenticated";

GRANT DELETE ON TABLE "public"."users" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."users" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."users" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."users" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."users" TO "authenticated";

GRANT INSERT ON TABLE "public"."users" TO "service_role";

GRANT SELECT ON TABLE "public"."users" TO "service_role";

GRANT UPDATE ON TABLE "public"."users" TO "service_role";

GRANT DELETE ON TABLE "public"."users" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."users" TO "service_role";

GRANT REFERENCES ON TABLE "public"."users" TO "service_role";

GRANT TRIGGER ON TABLE "public"."users" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."users" TO "service_role";

REVOKE ALL ON TABLE "public"."legacy_source_links" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT SELECT ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT UPDATE ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT DELETE ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT REFERENCES ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT TRIGGER ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."legacy_source_links" TO "postgres";

GRANT INSERT ON TABLE "public"."legacy_source_links" TO "anon";

GRANT SELECT ON TABLE "public"."legacy_source_links" TO "anon";

GRANT UPDATE ON TABLE "public"."legacy_source_links" TO "anon";

GRANT DELETE ON TABLE "public"."legacy_source_links" TO "anon";

GRANT TRUNCATE ON TABLE "public"."legacy_source_links" TO "anon";

GRANT REFERENCES ON TABLE "public"."legacy_source_links" TO "anon";

GRANT TRIGGER ON TABLE "public"."legacy_source_links" TO "anon";

GRANT MAINTAIN ON TABLE "public"."legacy_source_links" TO "anon";

GRANT INSERT ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT SELECT ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT UPDATE ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT DELETE ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."legacy_source_links" TO "authenticated";

GRANT INSERT ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT SELECT ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT UPDATE ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT DELETE ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT REFERENCES ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT TRIGGER ON TABLE "public"."legacy_source_links" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."legacy_source_links" TO "service_role";

REVOKE ALL ON TABLE "public"."legacy_claim_audit" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT SELECT ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT UPDATE ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT DELETE ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT REFERENCES ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT TRIGGER ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."legacy_claim_audit" TO "postgres";

GRANT INSERT ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT SELECT ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT UPDATE ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT DELETE ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT TRUNCATE ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT REFERENCES ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT TRIGGER ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT MAINTAIN ON TABLE "public"."legacy_claim_audit" TO "anon";

GRANT INSERT ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT SELECT ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT UPDATE ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT DELETE ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."legacy_claim_audit" TO "authenticated";

GRANT INSERT ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT SELECT ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT UPDATE ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT DELETE ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT REFERENCES ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT TRIGGER ON TABLE "public"."legacy_claim_audit" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."legacy_claim_audit" TO "service_role";

REVOKE ALL ON TABLE "public"."action_instances" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."action_instances" TO "postgres";

GRANT SELECT ON TABLE "public"."action_instances" TO "postgres";

GRANT UPDATE ON TABLE "public"."action_instances" TO "postgres";

GRANT DELETE ON TABLE "public"."action_instances" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."action_instances" TO "postgres";

GRANT REFERENCES ON TABLE "public"."action_instances" TO "postgres";

GRANT TRIGGER ON TABLE "public"."action_instances" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."action_instances" TO "postgres";

GRANT INSERT ON TABLE "public"."action_instances" TO "anon";

GRANT SELECT ON TABLE "public"."action_instances" TO "anon";

GRANT UPDATE ON TABLE "public"."action_instances" TO "anon";

GRANT DELETE ON TABLE "public"."action_instances" TO "anon";

GRANT TRUNCATE ON TABLE "public"."action_instances" TO "anon";

GRANT REFERENCES ON TABLE "public"."action_instances" TO "anon";

GRANT TRIGGER ON TABLE "public"."action_instances" TO "anon";

GRANT MAINTAIN ON TABLE "public"."action_instances" TO "anon";

GRANT INSERT ON TABLE "public"."action_instances" TO "authenticated";

GRANT SELECT ON TABLE "public"."action_instances" TO "authenticated";

GRANT UPDATE ON TABLE "public"."action_instances" TO "authenticated";

GRANT DELETE ON TABLE "public"."action_instances" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."action_instances" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."action_instances" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."action_instances" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."action_instances" TO "authenticated";

GRANT INSERT ON TABLE "public"."action_instances" TO "service_role";

GRANT SELECT ON TABLE "public"."action_instances" TO "service_role";

GRANT UPDATE ON TABLE "public"."action_instances" TO "service_role";

GRANT DELETE ON TABLE "public"."action_instances" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."action_instances" TO "service_role";

GRANT REFERENCES ON TABLE "public"."action_instances" TO "service_role";

GRANT TRIGGER ON TABLE "public"."action_instances" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."action_instances" TO "service_role";

REVOKE ALL ON TABLE "private"."api_secrets" FROM PUBLIC, anon, authenticated, service_role;

REVOKE ALL ON TABLE "public"."activity_log" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."activity_log" TO "postgres";

GRANT SELECT ON TABLE "public"."activity_log" TO "postgres";

GRANT UPDATE ON TABLE "public"."activity_log" TO "postgres";

GRANT DELETE ON TABLE "public"."activity_log" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."activity_log" TO "postgres";

GRANT REFERENCES ON TABLE "public"."activity_log" TO "postgres";

GRANT TRIGGER ON TABLE "public"."activity_log" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."activity_log" TO "postgres";

GRANT INSERT ON TABLE "public"."activity_log" TO "anon";

GRANT SELECT ON TABLE "public"."activity_log" TO "anon";

GRANT UPDATE ON TABLE "public"."activity_log" TO "anon";

GRANT DELETE ON TABLE "public"."activity_log" TO "anon";

GRANT TRUNCATE ON TABLE "public"."activity_log" TO "anon";

GRANT REFERENCES ON TABLE "public"."activity_log" TO "anon";

GRANT TRIGGER ON TABLE "public"."activity_log" TO "anon";

GRANT MAINTAIN ON TABLE "public"."activity_log" TO "anon";

GRANT INSERT ON TABLE "public"."activity_log" TO "authenticated";

GRANT SELECT ON TABLE "public"."activity_log" TO "authenticated";

GRANT UPDATE ON TABLE "public"."activity_log" TO "authenticated";

GRANT DELETE ON TABLE "public"."activity_log" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."activity_log" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."activity_log" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."activity_log" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."activity_log" TO "authenticated";

GRANT INSERT ON TABLE "public"."activity_log" TO "service_role";

GRANT SELECT ON TABLE "public"."activity_log" TO "service_role";

GRANT UPDATE ON TABLE "public"."activity_log" TO "service_role";

GRANT DELETE ON TABLE "public"."activity_log" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."activity_log" TO "service_role";

GRANT REFERENCES ON TABLE "public"."activity_log" TO "service_role";

GRANT TRIGGER ON TABLE "public"."activity_log" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."activity_log" TO "service_role";

REVOKE ALL ON TABLE "public"."idempotency_keys" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT SELECT ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT UPDATE ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT DELETE ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT REFERENCES ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT TRIGGER ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."idempotency_keys" TO "postgres";

GRANT INSERT ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT SELECT ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT UPDATE ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT DELETE ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT REFERENCES ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT TRIGGER ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."idempotency_keys" TO "service_role";

GRANT INSERT ON TABLE "public"."idempotency_keys" TO "anon";

GRANT SELECT ON TABLE "public"."idempotency_keys" TO "anon";

GRANT UPDATE ON TABLE "public"."idempotency_keys" TO "anon";

REVOKE ALL ON TABLE "public"."awareness_runs" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."awareness_runs" TO "postgres";

GRANT SELECT ON TABLE "public"."awareness_runs" TO "postgres";

GRANT UPDATE ON TABLE "public"."awareness_runs" TO "postgres";

GRANT DELETE ON TABLE "public"."awareness_runs" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."awareness_runs" TO "postgres";

GRANT REFERENCES ON TABLE "public"."awareness_runs" TO "postgres";

GRANT TRIGGER ON TABLE "public"."awareness_runs" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."awareness_runs" TO "postgres";

GRANT INSERT ON TABLE "public"."awareness_runs" TO "anon";

GRANT SELECT ON TABLE "public"."awareness_runs" TO "anon";

GRANT UPDATE ON TABLE "public"."awareness_runs" TO "anon";

GRANT DELETE ON TABLE "public"."awareness_runs" TO "anon";

GRANT TRUNCATE ON TABLE "public"."awareness_runs" TO "anon";

GRANT REFERENCES ON TABLE "public"."awareness_runs" TO "anon";

GRANT TRIGGER ON TABLE "public"."awareness_runs" TO "anon";

GRANT MAINTAIN ON TABLE "public"."awareness_runs" TO "anon";

GRANT INSERT ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT SELECT ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT UPDATE ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT DELETE ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."awareness_runs" TO "authenticated";

GRANT INSERT ON TABLE "public"."awareness_runs" TO "service_role";

GRANT SELECT ON TABLE "public"."awareness_runs" TO "service_role";

GRANT UPDATE ON TABLE "public"."awareness_runs" TO "service_role";

GRANT DELETE ON TABLE "public"."awareness_runs" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."awareness_runs" TO "service_role";

GRANT REFERENCES ON TABLE "public"."awareness_runs" TO "service_role";

GRANT TRIGGER ON TABLE "public"."awareness_runs" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."awareness_runs" TO "service_role";

REVOKE ALL ON TABLE "public"."awareness_answers" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."awareness_answers" TO "postgres";

GRANT SELECT ON TABLE "public"."awareness_answers" TO "postgres";

GRANT UPDATE ON TABLE "public"."awareness_answers" TO "postgres";

GRANT DELETE ON TABLE "public"."awareness_answers" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."awareness_answers" TO "postgres";

GRANT REFERENCES ON TABLE "public"."awareness_answers" TO "postgres";

GRANT TRIGGER ON TABLE "public"."awareness_answers" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."awareness_answers" TO "postgres";

GRANT INSERT ON TABLE "public"."awareness_answers" TO "anon";

GRANT SELECT ON TABLE "public"."awareness_answers" TO "anon";

GRANT UPDATE ON TABLE "public"."awareness_answers" TO "anon";

GRANT DELETE ON TABLE "public"."awareness_answers" TO "anon";

GRANT TRUNCATE ON TABLE "public"."awareness_answers" TO "anon";

GRANT REFERENCES ON TABLE "public"."awareness_answers" TO "anon";

GRANT TRIGGER ON TABLE "public"."awareness_answers" TO "anon";

GRANT MAINTAIN ON TABLE "public"."awareness_answers" TO "anon";

GRANT INSERT ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT SELECT ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT UPDATE ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT DELETE ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."awareness_answers" TO "authenticated";

GRANT INSERT ON TABLE "public"."awareness_answers" TO "service_role";

GRANT SELECT ON TABLE "public"."awareness_answers" TO "service_role";

GRANT UPDATE ON TABLE "public"."awareness_answers" TO "service_role";

GRANT DELETE ON TABLE "public"."awareness_answers" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."awareness_answers" TO "service_role";

GRANT REFERENCES ON TABLE "public"."awareness_answers" TO "service_role";

GRANT TRIGGER ON TABLE "public"."awareness_answers" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."awareness_answers" TO "service_role";

REVOKE ALL ON TABLE "public"."auth_identities" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."auth_identities" TO "postgres";

GRANT SELECT ON TABLE "public"."auth_identities" TO "postgres";

GRANT UPDATE ON TABLE "public"."auth_identities" TO "postgres";

GRANT DELETE ON TABLE "public"."auth_identities" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."auth_identities" TO "postgres";

GRANT REFERENCES ON TABLE "public"."auth_identities" TO "postgres";

GRANT TRIGGER ON TABLE "public"."auth_identities" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."auth_identities" TO "postgres";

GRANT INSERT ON TABLE "public"."auth_identities" TO "anon";

GRANT SELECT ON TABLE "public"."auth_identities" TO "anon";

GRANT UPDATE ON TABLE "public"."auth_identities" TO "anon";

GRANT DELETE ON TABLE "public"."auth_identities" TO "anon";

GRANT TRUNCATE ON TABLE "public"."auth_identities" TO "anon";

GRANT REFERENCES ON TABLE "public"."auth_identities" TO "anon";

GRANT TRIGGER ON TABLE "public"."auth_identities" TO "anon";

GRANT MAINTAIN ON TABLE "public"."auth_identities" TO "anon";

GRANT INSERT ON TABLE "public"."auth_identities" TO "authenticated";

GRANT SELECT ON TABLE "public"."auth_identities" TO "authenticated";

GRANT UPDATE ON TABLE "public"."auth_identities" TO "authenticated";

GRANT DELETE ON TABLE "public"."auth_identities" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."auth_identities" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."auth_identities" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."auth_identities" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."auth_identities" TO "authenticated";

GRANT INSERT ON TABLE "public"."auth_identities" TO "service_role";

GRANT SELECT ON TABLE "public"."auth_identities" TO "service_role";

GRANT UPDATE ON TABLE "public"."auth_identities" TO "service_role";

GRANT DELETE ON TABLE "public"."auth_identities" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."auth_identities" TO "service_role";

GRANT REFERENCES ON TABLE "public"."auth_identities" TO "service_role";

GRANT TRIGGER ON TABLE "public"."auth_identities" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."auth_identities" TO "service_role";

REVOKE ALL ON TABLE "public"."facts" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."facts" TO "postgres";

GRANT SELECT ON TABLE "public"."facts" TO "postgres";

GRANT UPDATE ON TABLE "public"."facts" TO "postgres";

GRANT DELETE ON TABLE "public"."facts" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."facts" TO "postgres";

GRANT REFERENCES ON TABLE "public"."facts" TO "postgres";

GRANT TRIGGER ON TABLE "public"."facts" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."facts" TO "postgres";

GRANT INSERT ON TABLE "public"."facts" TO "anon";

GRANT SELECT ON TABLE "public"."facts" TO "anon";

GRANT UPDATE ON TABLE "public"."facts" TO "anon";

GRANT DELETE ON TABLE "public"."facts" TO "anon";

GRANT TRUNCATE ON TABLE "public"."facts" TO "anon";

GRANT REFERENCES ON TABLE "public"."facts" TO "anon";

GRANT TRIGGER ON TABLE "public"."facts" TO "anon";

GRANT MAINTAIN ON TABLE "public"."facts" TO "anon";

GRANT INSERT ON TABLE "public"."facts" TO "authenticated";

GRANT SELECT ON TABLE "public"."facts" TO "authenticated";

GRANT UPDATE ON TABLE "public"."facts" TO "authenticated";

GRANT DELETE ON TABLE "public"."facts" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."facts" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."facts" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."facts" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."facts" TO "authenticated";

GRANT INSERT ON TABLE "public"."facts" TO "service_role";

GRANT SELECT ON TABLE "public"."facts" TO "service_role";

GRANT UPDATE ON TABLE "public"."facts" TO "service_role";

GRANT DELETE ON TABLE "public"."facts" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."facts" TO "service_role";

GRANT REFERENCES ON TABLE "public"."facts" TO "service_role";

GRANT TRIGGER ON TABLE "public"."facts" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."facts" TO "service_role";

REVOKE ALL ON TABLE "public"."findings" FROM PUBLIC, anon, authenticated, service_role;

GRANT INSERT ON TABLE "public"."findings" TO "postgres";

GRANT SELECT ON TABLE "public"."findings" TO "postgres";

GRANT UPDATE ON TABLE "public"."findings" TO "postgres";

GRANT DELETE ON TABLE "public"."findings" TO "postgres";

GRANT TRUNCATE ON TABLE "public"."findings" TO "postgres";

GRANT REFERENCES ON TABLE "public"."findings" TO "postgres";

GRANT TRIGGER ON TABLE "public"."findings" TO "postgres";

GRANT MAINTAIN ON TABLE "public"."findings" TO "postgres";

GRANT INSERT ON TABLE "public"."findings" TO "anon";

GRANT SELECT ON TABLE "public"."findings" TO "anon";

GRANT UPDATE ON TABLE "public"."findings" TO "anon";

GRANT DELETE ON TABLE "public"."findings" TO "anon";

GRANT TRUNCATE ON TABLE "public"."findings" TO "anon";

GRANT REFERENCES ON TABLE "public"."findings" TO "anon";

GRANT TRIGGER ON TABLE "public"."findings" TO "anon";

GRANT MAINTAIN ON TABLE "public"."findings" TO "anon";

GRANT INSERT ON TABLE "public"."findings" TO "authenticated";

GRANT SELECT ON TABLE "public"."findings" TO "authenticated";

GRANT UPDATE ON TABLE "public"."findings" TO "authenticated";

GRANT DELETE ON TABLE "public"."findings" TO "authenticated";

GRANT TRUNCATE ON TABLE "public"."findings" TO "authenticated";

GRANT REFERENCES ON TABLE "public"."findings" TO "authenticated";

GRANT TRIGGER ON TABLE "public"."findings" TO "authenticated";

GRANT MAINTAIN ON TABLE "public"."findings" TO "authenticated";

GRANT INSERT ON TABLE "public"."findings" TO "service_role";

GRANT SELECT ON TABLE "public"."findings" TO "service_role";

GRANT UPDATE ON TABLE "public"."findings" TO "service_role";

GRANT DELETE ON TABLE "public"."findings" TO "service_role";

GRANT TRUNCATE ON TABLE "public"."findings" TO "service_role";

GRANT REFERENCES ON TABLE "public"."findings" TO "service_role";

GRANT TRIGGER ON TABLE "public"."findings" TO "service_role";

GRANT MAINTAIN ON TABLE "public"."findings" TO "service_role";

REVOKE ALL ON FUNCTION "private"."current_life_user_id"() FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."current_life_user_id"() TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."current_life_user_id"() TO "authenticated";

REVOKE ALL ON FUNCTION "private"."handle_new_auth_user"() FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."handle_new_auth_user"() TO PUBLIC;

REVOKE ALL ON FUNCTION "private"."valid_internal_secret"(p_secret text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."valid_internal_secret"(p_secret text) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."valid_internal_secret"(p_secret text) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "anon";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "service_role";

REVOKE ALL ON FUNCTION "public"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "anon";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "service_role";

REVOKE ALL ON FUNCTION "private"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "service_role";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "anon";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "authenticated";

REVOKE ALL ON FUNCTION "private"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "service_role";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "anon";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_put_answer"(p_internal_secret text, p_run_id uuid, p_run_token text, p_question_id text, p_response text) TO "authenticated";

REVOKE ALL ON FUNCTION "private"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "service_role";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "anon";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_get"(p_internal_secret text, p_run_id uuid, p_run_token text) TO "authenticated";

REVOKE ALL ON FUNCTION "private"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "service_role";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "anon";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "authenticated";

REVOKE ALL ON FUNCTION "private"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "anon";

GRANT EXECUTE ON FUNCTION "private"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "authenticated";

REVOKE ALL ON FUNCTION "public"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "anon";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_claim"(p_internal_secret text, p_handoff_token text, p_auth_subject uuid) TO "service_role";

REVOKE ALL ON FUNCTION "private"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "private"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "anon";

GRANT EXECUTE ON FUNCTION "private"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "authenticated";

REVOKE ALL ON FUNCTION "private"."request_is_internal"() FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."request_is_internal"() TO PUBLIC;

GRANT EXECUTE ON FUNCTION "private"."request_is_internal"() TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."request_is_internal"() TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "anon";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_create"(p_internal_secret text, p_age_band text, p_household_type text) TO "service_role";

REVOKE ALL ON FUNCTION "public"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "anon";

GRANT EXECUTE ON FUNCTION "public"."rpc_awareness_finalize"(p_internal_secret text, p_run_id uuid, p_run_token text, p_top3 jsonb, p_findings jsonb) TO "service_role";

REVOKE ALL ON FUNCTION "public"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "anon";

GRANT EXECUTE ON FUNCTION "public"."rpc_member_dashboard"(p_internal_secret text, p_auth_subject uuid) TO "service_role";

REVOKE ALL ON FUNCTION "public"."rpc_member_awareness"(p_internal_secret text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_member_awareness"(p_internal_secret text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_member_awareness"(p_internal_secret text, p_auth_subject uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_member_awareness"(p_internal_secret text, p_auth_subject uuid) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_action_start"(p_internal_secret text, p_auth_subject uuid, p_action_catalog_id text, p_mode text) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_action_start"(p_internal_secret text, p_auth_subject uuid, p_action_catalog_id text, p_mode text) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_start"(p_internal_secret text, p_auth_subject uuid, p_action_catalog_id text, p_mode text) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_start"(p_internal_secret text, p_auth_subject uuid, p_action_catalog_id text, p_mode text) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_action_submit"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_draft jsonb) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_action_submit"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_draft jsonb) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_submit"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_draft jsonb) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_submit"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_draft jsonb) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_action_complete"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_action_catalog_id text, p_question_id text, p_fact_rows jsonb, p_new_top3 jsonb) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_action_complete"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_action_catalog_id text, p_question_id text, p_fact_rows jsonb, p_new_top3 jsonb) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_complete"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_action_catalog_id text, p_question_id text, p_fact_rows jsonb, p_new_top3 jsonb) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_complete"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid, p_action_catalog_id text, p_question_id text, p_fact_rows jsonb, p_new_top3 jsonb) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_member_facts"(p_internal_secret text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_member_facts"(p_internal_secret text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_member_facts"(p_internal_secret text, p_auth_subject uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_member_facts"(p_internal_secret text, p_auth_subject uuid) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_action_change_event"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_action_change_event"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_change_event"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_change_event"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_action_wait"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_action_wait"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_wait"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_action_wait"(p_internal_secret text, p_auth_subject uuid, p_action_instance_id uuid) TO "anon";

REVOKE ALL ON FUNCTION "private"."delete_account_core"(p_internal_secret text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "private"."delete_account_core"(p_internal_secret text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "private"."delete_account_core"(p_internal_secret text, p_auth_subject uuid) TO "anon";

REVOKE ALL ON FUNCTION "public"."rpc_delete_account"(p_internal_secret text, p_auth_subject uuid) FROM PUBLIC, anon, authenticated, service_role;

GRANT EXECUTE ON FUNCTION "public"."rpc_delete_account"(p_internal_secret text, p_auth_subject uuid) TO "postgres";

GRANT EXECUTE ON FUNCTION "public"."rpc_delete_account"(p_internal_secret text, p_auth_subject uuid) TO "service_role";

GRANT EXECUTE ON FUNCTION "public"."rpc_delete_account"(p_internal_secret text, p_auth_subject uuid) TO "anon";

REVOKE ALL ON SCHEMA private FROM PUBLIC, anon, authenticated, service_role;

GRANT USAGE ON SCHEMA private TO "postgres";

GRANT CREATE ON SCHEMA private TO "postgres";

GRANT USAGE ON SCHEMA private TO "anon";

GRANT USAGE ON SCHEMA private TO "authenticated";

-- private.api_secrets is intentionally empty. Internal RPC remains unavailable until a new production secret hash is provisioned.

COMMIT;
