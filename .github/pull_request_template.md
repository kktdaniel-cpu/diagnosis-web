## Change summary

Issue:
Owner approval reference:

## Scope

Allowed files:
- 

Files changed:
- 

Out-of-scope changes: **NONE / STOP**

## Logic impact

- Backend: NO
- Financial engine: NO
- Schema: NO
- Score: NO
- Curve/depletion: NO
- Screen: NO/YES
- Print/PDF: NO/YES
- CSS/layout: NO/YES

If any item above is YES unexpectedly, stop and request owner approval.

## Contracts

- [ ] No new formula, threshold, assumption, or unsupported inference
- [ ] U remains U; no coercion to 0
- [ ] No direct `null`, `undefined`, or `NaN` display
- [ ] No unrelated refactor
- [ ] Existing canonical helpers reused where applicable
- [ ] New issue discovered during work was not silently fixed

## Verification

- [ ] `diagnosis-verify` workflow PASS
- [ ] Relevant regression tests PASS
- [ ] Print/PDF contract PASS when applicable
- [ ] Changed-file scope check PASS
- [ ] Production code was not deployed from this PR

## Agent post-flight

Root cause:

Before → After:

Tests:

Remaining risks:

New issues found:

## Owner gate

- [ ] Owner approved patch scope
- [ ] Owner approved merge
- [ ] Owner approved deploy (separate from merge when required)
