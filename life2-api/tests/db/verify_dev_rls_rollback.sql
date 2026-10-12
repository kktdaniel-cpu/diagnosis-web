-- DEV ONLY: life2-master-v2 / bikvcuchdlreqkqypwcr.
-- Run as a single SQL batch. No schema/policy/credential changes.
-- Simulates JWT subjects at SQL level, NOT a signed login/API session.
-- All synthetic users, identity mappings and records are rolled back.
BEGIN;
SET LOCAL statement_timeout = '20s';
SET LOCAL lock_timeout = '3s';
DO $$
DECLARE
  ua uuid := gen_random_uuid(); ub uuid := gen_random_uuid();
  sa uuid := gen_random_uuid(); sb uuid := gen_random_uuid();
  ra uuid := gen_random_uuid(); rb uuid := gen_random_uuid();
  la uuid := gen_random_uuid(); lb uuid := gen_random_uuid();
BEGIN
  PERFORM set_config('life2_test.owner',ua::text,true);
  PERFORM set_config('life2_test.observer',ub::text,true);
  PERFORM set_config('life2_test.owner_subject',sa::text,true);
  PERFORM set_config('life2_test.observer_subject',sb::text,true);
  INSERT INTO public.users(user_id) VALUES (ua),(ub);
  INSERT INTO public.auth_identities(user_id,provider,provider_subject)
    VALUES (ua,'supabase',sa::text),(ub,'supabase',sb::text);
  INSERT INTO public.awareness_runs(run_id,user_id,age_band,household_type)
    VALUES (ra,ua,'50_55','single'),(rb,ub,'50_55','couple');
  INSERT INTO public.awareness_answers(run_id,question_id,response)
    VALUES (ra,'AWR_Q08_HOUSING','PARTIAL'),(rb,'AWR_Q08_HOUSING','CONFIRMED');
  INSERT INTO public.facts(user_id,fact_key,status,value_json,source_type,source_ref)
    VALUES (ua,'housing.reverse_mortgage_plan_q19','UNKNOWN','null'::jsonb,'USER_CONFIRMED','DB_ROLLBACK_TEST'),
           (ub,'housing.reverse_mortgage_plan_q19','KNOWN','"NO_PLAN"'::jsonb,'USER_CONFIRMED','DB_ROLLBACK_TEST');
  INSERT INTO public.findings(user_id,finding_type,status,source_refs)
    VALUES (ua,'DB_ROLLBACK_TEST','OPEN','["AWR_Q08_HOUSING"]'),
           (ub,'DB_ROLLBACK_TEST','OPEN','["AWR_Q08_HOUSING"]');
  INSERT INTO public.action_instances(user_id,action_catalog_id,status,mode)
    VALUES (ua,'ACT_DEFINE_HOUSING_PLAN','IN_PROGRESS','CREATE'),
           (ub,'ACT_DEFINE_HOUSING_PLAN','NOT_STARTED','CREATE');
  INSERT INTO public.activity_log(user_id,event_type,summary_code)
    VALUES (ua,'DB_ROLLBACK_TEST','OWNER'),(ub,'DB_ROLLBACK_TEST','OBSERVER');
  INSERT INTO public.legacy_source_links(legacy_link_id,user_id,source_system,source_record_key,record_type)
    VALUES (la,ua,'DB_ROLLBACK_TEST',ra::text,'DRAFT'),(lb,ub,'DB_ROLLBACK_TEST',rb::text,'DRAFT');
  INSERT INTO public.legacy_claim_audit(legacy_link_id,user_id,event_type)
    VALUES (la,ua,'SEARCHED'),(lb,ub,'SEARCHED');
  INSERT INTO public.idempotency_keys(user_id,key,response_json)
    VALUES (ua,'DB_ROLLBACK_TEST','{}'),(ub,'DB_ROLLBACK_TEST','{}');
  PERFORM set_config('request.jwt.claim.sub',sa::text,true);
  PERFORM set_config('request.jwt.claims',jsonb_build_object('sub',sa::text,'role','authenticated')::text,true);
END $$;
SET LOCAL ROLE authenticated;
DO $$
DECLARE t text; n bigint; changed bigint; denied boolean := false;
BEGIN
  ASSERT current_user = 'authenticated', 'RLS test must not run as admin';
  ASSERT auth.uid() = current_setting('life2_test.owner_subject')::uuid, 'Subject mismatch';
  ASSERT private.current_life_user_id() = current_setting('life2_test.owner')::uuid, 'Identity mapping mismatch';
  FOREACH t IN ARRAY ARRAY['users','auth_identities','awareness_runs','awareness_answers','facts','findings','action_instances','activity_log','legacy_source_links','legacy_claim_audit'] LOOP
    EXECUTE format('select count(*) from public.%I',t) INTO n;
    ASSERT n = 1, 'Owner RLS row isolation failed: ' || t;
  END LOOP;
  ASSERT (SELECT status='UNKNOWN' AND value_json='null'::jsonb FROM public.facts), 'UNKNOWN became a value';
  BEGIN
    INSERT INTO public.facts(user_id,fact_key,status,value_json,source_type)
      VALUES (current_setting('life2_test.owner')::uuid,'DB_ROLLBACK_TEST_CLIENT_WRITE','KNOWN','0','USER_CONFIRMED');
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
  ASSERT denied, 'Client direct FACT insert unexpectedly allowed';
  BEGIN
    UPDATE public.facts SET value_json='0' WHERE user_id=current_setting('life2_test.observer')::uuid;
    GET DIAGNOSTICS changed = ROW_COUNT;
    ASSERT changed=0, 'Foreign FACT update succeeded';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  BEGIN
    DELETE FROM public.action_instances WHERE user_id=current_setting('life2_test.observer')::uuid;
    GET DIAGNOSTICS changed = ROW_COUNT;
    ASSERT changed=0, 'Foreign Action delete succeeded';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
  denied := false;
  BEGIN
    EXECUTE 'select count(*) from public.idempotency_keys' INTO n;
    ASSERT n=0, 'Internal idempotency rows exposed';
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
END $$;
DO $$
BEGIN
  PERFORM set_config('request.jwt.claim.sub',current_setting('life2_test.observer_subject'),true);
  PERFORM set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('life2_test.observer_subject'),'role','authenticated')::text,true);
END $$;
DO $$
DECLARE t text; n bigint;
BEGIN
  ASSERT private.current_life_user_id()=current_setting('life2_test.observer')::uuid, 'Observer identity mismatch';
  FOREACH t IN ARRAY ARRAY['users','auth_identities','awareness_runs','awareness_answers','facts','findings','action_instances','activity_log','legacy_source_links','legacy_claim_audit'] LOOP
    EXECUTE format('select count(*) from public.%I',t) INTO n;
    ASSERT n=1, 'Observer RLS row isolation failed: ' || t;
  END LOOP;
  ASSERT (SELECT value_json='"NO_PLAN"'::jsonb AND status='KNOWN' FROM public.facts), 'Foreign modification changed observer FACT';
END $$;
RESET ROLE;
DO $$
BEGIN
  PERFORM set_config('request.jwt.claim.sub','',true);
  PERFORM set_config('request.jwt.claims','{}',true);
  PERFORM set_config('request.headers','{}',true);
END $$;
SET LOCAL ROLE anon;
DO $$
DECLARE t text; n bigint;
BEGIN
  ASSERT current_user='anon', 'Anonymous test must not run as admin';
  FOREACH t IN ARRAY ARRAY['users','auth_identities','awareness_runs','awareness_answers','facts','findings','action_instances','activity_log','legacy_source_links','legacy_claim_audit','idempotency_keys'] LOOP
    BEGIN
      EXECUTE format('select count(*) from public.%I',t) INTO n;
      ASSERT n=0, 'Anonymous rows exposed: ' || t;
    EXCEPTION WHEN insufficient_privilege THEN NULL;
    END;
  END LOOP;
END $$;
RESET ROLE;
SELECT 'PASS: two SQL subjects, ten member tables, UNKNOWN/null, forbidden client write, foreign mutations, anonymous and internal idempotency isolation' AS verification;
ROLLBACK;
