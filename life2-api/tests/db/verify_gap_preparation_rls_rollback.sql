BEGIN;
DO $$
DECLARE ua uuid:=gen_random_uuid(); ub uuid:=gen_random_uuid(); sa uuid:=gen_random_uuid(); sb uuid:=gen_random_uuid();
BEGIN
 PERFORM set_config('gap_test.ua',ua::text,true);
 PERFORM set_config('gap_test.ub',ub::text,true);
 PERFORM set_config('gap_test.sa',sa::text,true);
 PERFORM set_config('gap_test.sb',sb::text,true);
 INSERT INTO public.users(user_id) VALUES(ua),(ub);
 INSERT INTO public.auth_identities(user_id,provider,provider_subject) VALUES(ua,'supabase',sa::text),(ub,'supabase',sb::text);
 INSERT INTO public.income_gap_preparations(token_hash,answers,user_id,saved_at)
 VALUES(repeat('a',64),'{"budget_monthly_10k":0,"nps_self":{"monthly_10k":null}}',ua,now()),
       (repeat('b',64),'{"budget_monthly_10k":999}',ub,now());
 PERFORM set_config('request.jwt.claim.sub',sa::text,true);
 PERFORM set_config('request.jwt.claims',jsonb_build_object('sub',sa::text,'role','authenticated')::text,true);
 PERFORM set_config('request.headers','{}',true);
END $$;
SET LOCAL ROLE authenticated;
DO $$ DECLARE n integer; denied boolean:=false;
BEGIN
 SELECT count(*) INTO n FROM public.income_gap_preparations; ASSERT n=1,'Owner isolation';
 ASSERT (SELECT answers->'budget_monthly_10k'='0'::jsonb AND answers->'nps_self'->'monthly_10k'='null'::jsonb FROM public.income_gap_preparations),'UNKNOWN/zero';
 BEGIN UPDATE public.income_gap_preparations SET answers='{}'; EXCEPTION WHEN insufficient_privilege THEN denied:=true; END;
 ASSERT denied,'Client write must be denied';
 PERFORM set_config('request.jwt.claim.sub',current_setting('gap_test.sb'),true);
 PERFORM set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('gap_test.sb'),'role','authenticated')::text,true);
 SELECT count(*) INTO n FROM public.income_gap_preparations; ASSERT n=1,'Second owner isolation';
 ASSERT (SELECT answers->'budget_monthly_10k'='999'::jsonb FROM public.income_gap_preparations),'Foreign data modified';
END $$;
RESET ROLE;
DO $$ BEGIN
 PERFORM set_config('request.jwt.claim.sub','',true); PERFORM set_config('request.jwt.claims','{}',true);
 PERFORM set_config('request.headers','{}',true);
END $$;
SET LOCAL ROLE anon;
DO $$ DECLARE n integer; denied boolean:=false;
BEGIN
 SELECT count(*) INTO n FROM public.income_gap_preparations; ASSERT n=0,'Anonymous exposure';
 BEGIN INSERT INTO public.income_gap_preparations(token_hash,answers) VALUES(repeat('c',64),'{}');
 EXCEPTION WHEN insufficient_privilege THEN denied:=true; END; ASSERT denied,'Anonymous direct insert';
 denied:=false;
 BEGIN PERFORM public.rpc_gap_preparation_create('invalid',repeat('d',64),'{}');
 EXCEPTION WHEN raise_exception THEN ASSERT SQLERRM='forbidden','Expected forbidden'; denied:=true; END;
 ASSERT denied,'Internal RPC guard';
END $$;
RESET ROLE;
SELECT 'PASS: two owners isolated, zero/null retained, client writes and anonymous/RPC access blocked' AS result;
ROLLBACK;