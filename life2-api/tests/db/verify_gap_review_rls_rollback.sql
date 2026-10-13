BEGIN;
DO $$
DECLARE ua uuid:=gen_random_uuid(); ub uuid:=gen_random_uuid(); sa uuid:=gen_random_uuid(); sb uuid:=gen_random_uuid(); pa uuid:=gen_random_uuid(); pb uuid:=gen_random_uuid();
BEGIN
 PERFORM set_config('gap_review_test.sa',sa::text,true); PERFORM set_config('gap_review_test.sb',sb::text,true);
 INSERT INTO public.users(user_id) VALUES(ua),(ub);
 INSERT INTO public.auth_identities(user_id,provider,provider_subject) VALUES(ua,'supabase',sa::text),(ub,'supabase',sb::text);
 INSERT INTO public.income_gap_preparations(preparation_id,token_hash,answers,user_id,saved_at,revision)
 VALUES(pa,repeat('e',64),'{"budget_monthly_10k":0}',ua,now(),1),(pb,repeat('f',64),'{"budget_monthly_10k":99}',ub,now(),1);
 INSERT INTO public.facts(user_id,fact_key,status,value_json,source_type,source_ref)
 VALUES(ua,'gap.v1.'||pa::text||'.budget_monthly_10k','KNOWN','0','USER_CONFIRMED','GAP_REVIEW_RLS_TEST'),
       (ua,'gap.v1.'||pa::text||'.nps_self.monthly_10k','UNKNOWN','null','USER_CONFIRMED','GAP_REVIEW_RLS_TEST'),
       (ub,'gap.v1.'||pb::text||'.budget_monthly_10k','KNOWN','99','USER_CONFIRMED','GAP_REVIEW_RLS_TEST');
 INSERT INTO public.action_instances(user_id,action_catalog_id,status,mode)
 VALUES(ua,'GAP_V1_BUDGET','SELF_REPORTED_DONE','VERIFY'),(ub,'GAP_V1_BUDGET','SELF_REPORTED_DONE','VERIFY');
 INSERT INTO public.activity_log(user_id,event_type) VALUES(ua,'GAP_REVIEW_RLS_TEST'),(ub,'GAP_REVIEW_RLS_TEST');
 PERFORM set_config('request.jwt.claim.sub',sa::text,true);
 PERFORM set_config('request.jwt.claims',jsonb_build_object('sub',sa::text,'role','authenticated')::text,true);
 PERFORM set_config('request.headers','{}',true);
END $$;
SET LOCAL ROLE authenticated;
DO $$ DECLARE n integer; denied boolean:=false; changed integer:=0;
BEGIN
 SELECT count(*) INTO n FROM public.income_gap_preparations; ASSERT n=1,'Prep isolation';
 SELECT count(*) INTO n FROM public.facts; ASSERT n=2,'Fact isolation';
 ASSERT (SELECT count(*) FROM public.facts WHERE status='UNKNOWN' AND value_json='null'::jsonb)=1,'UNKNOWN lost';
 ASSERT (SELECT count(*) FROM public.facts WHERE status='KNOWN' AND value_json='0'::jsonb)=1,'Zero lost';
 ASSERT (SELECT count(*) FROM public.action_instances)=1,'Action isolation';
 ASSERT (SELECT count(*) FROM public.activity_log)=1,'Activity isolation';
 BEGIN UPDATE public.facts SET value_json='999'; GET DIAGNOSTICS changed=ROW_COUNT; EXCEPTION WHEN insufficient_privilege THEN denied:=true; END;
 ASSERT denied or changed=0,'Direct FACT write';
 PERFORM set_config('request.jwt.claim.sub',current_setting('gap_review_test.sb'),true);
 PERFORM set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('gap_review_test.sb'),'role','authenticated')::text,true);
 ASSERT (SELECT count(*) FROM public.facts)=1,'Second owner isolation';
 ASSERT (SELECT value_json='99'::jsonb FROM public.facts),'Foreign data changed';
END $$;
RESET ROLE;
DO $$ BEGIN PERFORM set_config('request.jwt.claim.sub','',true);PERFORM set_config('request.jwt.claims','{}',true);PERFORM set_config('request.headers','{}',true); END $$;
SET LOCAL ROLE anon;
DO $$ DECLARE denied boolean:=false;
BEGIN
 ASSERT (SELECT count(*) FROM public.facts)=0,'Anonymous FACT exposure';
 ASSERT (SELECT count(*) FROM public.income_gap_preparations)=0,'Anonymous prep exposure';
 BEGIN PERFORM public.rpc_gap_review_confirm('invalid',gen_random_uuid(),gen_random_uuid(),'RETIREMENT',0,gen_random_uuid(),repeat('0',64),'{}',repeat('0',64),'PARTIAL','[]','[]','[]','[]');
 EXCEPTION WHEN raise_exception THEN ASSERT SQLERRM='forbidden','Invalid internal guard';denied:=true;END;
 ASSERT denied,'Unprotected review RPC';
END $$;
RESET ROLE;
SELECT 'PASS: scoped monthly FACT/Action/Activity RLS, UNKNOWN/zero, two owners, direct write and invalid RPC blocked; SQL role simulation only' as verification;
ROLLBACK;