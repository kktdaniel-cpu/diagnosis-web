# life2-web bootstrap

Current slice:
- Landing
- household selection
- Awareness 12
- Top 3 result

Set `VITE_API_BASE` to the LIFE 2.0 API URL.

Next slice:
- Supabase Auth
- one-time Awareness claim
- MY LIFE dashboard

The frontend build was not dependency-installed in the isolated build container; CI must run `npm install && npm run build` before this branch is eligible for merge.
