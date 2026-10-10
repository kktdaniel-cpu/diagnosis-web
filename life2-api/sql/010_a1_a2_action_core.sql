-- A1/A2 Action core: draft/resume, action start/submit/complete, dashboard recompute.
-- Applied to Supabase life2-master-v2.
-- SECURITY INVOKER functions run under anon + internal-server RLS gate.

alter table public.action_instances
  add column if not exists draft_json jsonb not null default '{}'::jsonb;

create unique index if not exists uq_action_active_per_user_catalog
on public.action_instances(user_id, action_catalog_id)
where status in ('NOT_STARTED','IN_PROGRESS','WAITING_EXTERNAL','REVIEW_DUE');

-- Function bodies are maintained in Supabase migration history.
-- Public API contracts created:
-- rpc_member_awareness
-- rpc_action_start
-- rpc_action_submit
-- rpc_action_complete
-- rpc_member_dashboard (updated to read current Top 3 order/status)
