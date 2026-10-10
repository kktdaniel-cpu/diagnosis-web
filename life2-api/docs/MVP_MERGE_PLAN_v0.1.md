# LIFE 2.0 MVP-1 Merge Plan v0.1

Status: **PREPARED / MERGE NOT YET AUTHORIZED**

## 1. Merge Target

Repository:
`kktdaniel-cpu/diagnosis-web`

PR:
`#18 [MVP-1 RC] LIFE 2.0 Core Loop + Release Gate`

Base:
`main`

Head:
`mvp/life2-bootstrap`

## 2. Freeze Rule

From RC approval forward:
- no new MVP features
- only merge-prep documentation, CI/reproducibility hardening, or release-blocking defect fixes
- any functional behavior change requires a fresh RC verification run
- exact head SHA must be recorded immediately before merge

## 3. Required Pre-Merge Checks

All must be PASS:
- PR open and Ready for review
- mergeable = true
- branch behind `main` = 0
- unresolved review threads = 0
- exact-head GitHub Actions = success
- API tests = PASS
- Web build = PASS
- Legacy production path guard = PASS
- Supabase live smoke = PASS
- Supabase Security Advisor = 0 findings
- changed paths limited to:
  - `life2-api/**`
  - `life2-web/**`
  - `.github/workflows/life2-mvp-verify.yml`
- no production secret committed

## 4. Merge Method

Recommended:
**Squash merge**

Reason:
- RC branch contains a long implementation history
- `main` should receive one auditable MVP-1 commit
- rollback becomes one revert operation

Proposed squash title:
`feat(life2): add MVP-1 Awareness-to-Action core loop`

Proposed body:
- Awareness 12 + deterministic Top 3
- Supabase Auth / Master DB v2 persistence
- MY LIFE dashboard + A1~A12 Action flow
- FACT / Finding / Action / Activity
- AI safe-mode explain/help/change summary
- Precision entry bridge
- release/security/regression gates

## 5. Merge Is Not Production Cutover

After merge:
- existing root production UI remains unchanged
- existing `diag.lpp20.com` remains unchanged
- existing `diagnosis-api Ver32.42` remains authoritative
- current LIFE 2.0 dev services remain dev
- no production DNS/domain cutover without separate approval

## 6. Rollback Plan

If the merge itself must be rolled back before production cutover:
1. revert the single squash merge commit on `main`
2. do not delete Supabase data/project
3. do not alter existing `diag` production
4. keep dev Render services available for diagnosis
5. reopen a defect branch from the reverted main state

If a later production cutover is approved, its deployment rollback plan is a separate gate.

## 7. Post-Merge Hold

After merge and before production deployment:
- verify `main` contains only the approved LIFE 2.0 paths
- verify no accidental legacy production diff
- record merge commit SHA
- prepare production environment/DNS checklist
- request separate owner production-deploy approval

## 8. Current Owner Boundary

Approved:
- RC
- merge preparation

Not yet approved:
- actual merge
- production deploy
- production domain cutover
