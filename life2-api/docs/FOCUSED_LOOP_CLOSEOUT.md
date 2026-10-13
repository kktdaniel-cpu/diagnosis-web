# Focused monthly loop closeout

Monthly reviews now project seven scoped Findings. Confirm transaction resolves only the reviewed group when DONE, keeps PARTIAL open, and reopens invalidated dependent Findings. Existing Awareness Findings are untouched. The database writes FACT/Action/Finding/Activity/revision together.

Read-only member context uses persisted gap.v1 FACT only: KNOWN included, UNKNOWN/STALE separate, no anonymous or foreign-user lookup, no writes. Explanation is deterministic, not an external generative-AI integration. UI offers stored information / next action explanation.

Precision automatic import remains explicitly disabled for monthly scoped facts. The protected engine accepts age/year/KRW contracts; converting user months to ages or mapping available cash bands to total asset bands would change semantics. A versioned month-aware engine interface and provenance contract are required first. Current five canonical prefill fields remain supported independently. Do not report all financial bridging complete.

Local API180 tests + Web build and income-gap6 tests PASS. Actual new DB transaction member E2E, logout/relogin, mobile viewport and downloaded PDF remain release gates; prior SQL/CI or desktop partial-save evidence does not replace them. External mail/Kakao/GA4/payment and Legacy source-key verification require their own configured integrations. No main/production/Google source edits.
