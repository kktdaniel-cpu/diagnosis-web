# LIFE 2.0 MVP-1 Release Gate v0.1

Status: **DEV IMPLEMENTATION COMPLETE / PRODUCTION MERGE NOT APPROVED**

This gate covers the MVP-1 development branch only.

## Core Loop
- Awareness 12
- deterministic Top 3
- signup handoff
- MY LIFE dashboard
- A1~A12 Action forms
- FACT/FINDING/ACTION persistence
- WAITING_EXTERNAL / resume
- Action completion -> recompute
- AI Context / Explain / Help
- Basic Change Summary
- Precision Entry to existing diag
- account deletion path

## Safety / Privacy
- UNKNOWN != 0
- UNKNOWN FACT value is null
- cross-user action access denied
- member APIs require bearer auth
- expired auth session rejected
- Digital secret-shaped fields rejected
- Supabase member tables use RLS
- existing diag / root production files are not modified by this branch

## Regression
CI must fail if this branch changes any path outside:
- life2-api/**
- life2-web/**
- .github/workflows/life2-mvp-verify.yml

## Golden Path
Automated test:
Awareness -> Claim -> A1 -> A2 -> A4 -> A5 activation -> A5 completion ->
FACT read -> Dashboard update -> Delete.

## Release Boundary
Closing MVP-1 implementation issues does **not** authorize:
- merge to main
- production domain cutover
- production deploy
- modification of diagnosis-api Ver32.42
