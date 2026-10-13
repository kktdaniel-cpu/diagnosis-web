-- Dev member lookup: same internal secret gate as auth_identities; no public writes.
create policy internal_server_users_read on public.users for select to anon using ((select private.request_is_internal()));
