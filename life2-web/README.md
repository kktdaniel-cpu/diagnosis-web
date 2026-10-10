# LIFE 2.0 Web

MVP-1 includes the landing page, household selection, Awareness 12, Top 3, Supabase sign-in/signup, result claim, MY LIFE dashboard, A1–A12 action forms, draft restore, external verification waiting and change summaries.

## Configuration and build

Set `VITE_API_BASE`, `VITE_SUPABASE_URL` and `VITE_SUPABASE_PUBLISHABLE_KEY` before building. Vite embeds these public values in the bundle; never place a server secret in a VITE variable.

```sh
npm install
npm run build
```

The repository does not contain a package lock; `npm ci` is not the current build command.

## Verified dev behavior

On 2026-10-11 KST, the deployed dev frontend/API and SQL 018 were exercised with synthetic data in the existing signed-in test account. Unknown insurance and work health-insurance values retained confirmed counts and displayed 확인 이어가기. Confirmed replacements advanced the count to 12/12 and removed the completed follow-up from Top 3.

Validation errors show the Korean field label. Partial-save messages describe remaining unknown information rather than claiming full confirmation.

Production deployment, main merge and domain changes remain on hold pending explicit approval.
