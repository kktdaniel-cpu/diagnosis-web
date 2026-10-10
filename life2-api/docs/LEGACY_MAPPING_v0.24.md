# LIFE 2.0 Legacy Master DB → Master DB v2 Mapping v0.24

> Source reviewed: Google Sheet `2막1장_마스터DB`
> Review mode: metadata + header-only + non-PII aggregate inspection
> Source sheet edits: none.

## Core decision
- Supabase/PostgreSQL = LIFE 2.0 Master DB v2
- Existing Google Sheets/GAS = read-only Legacy Diagnosis Store
- One canonical `users.user_id` is shared across MY LIFE / diag / Career / Edu / Legacy
- Name, phone, email, participant code, diagnosis code, and Sheet row number are never canonical user PKs.

## Observed active tabs
- 대시보드_v3
- 빠른진단집계
- 웰다잉집계
- 진단결과
- 빠른진단DB
- 설문_통합
- 회원가입
- 상담신청
- 임시저장
- 진단지 및 설문 수정
- _오류로그
- sample450_rows

Archived/hidden tabs are excluded from migration by default.

## Identity-relevant legacy fields

### 회원가입
`제출일시 / 이름 / 연락처 / 출생연도 / 지역 / 이메일 / 관심분야 / 참여자코드 / 가입시각`

### 진단결과
`제출일시 / 참여자코드 / 이름 / 연락처 / 개인정보동의 / 출생연도 / 지역 / 이메일 / 가입시각 / 진단코드 / 진단버전 / 답변JSON`

### 임시저장
`제출일시 / 이름 / 연락처 / 진행파트 / 저장시각 / 답변JSON`

### 상담신청
`유형 / 이름 / 연락처 / 신청시각 / 희망시간 / 참여자코드`

### 설문_통합
`원본탭 / 원본행 / 제출일시 / 참여자코드 / 이름 / 연락처 / 연구활용동의_CONSENT_RESEARCH`

## Stable key decision
- `진단코드` field exists, but the inspected full-diagnosis data does not support declaring it the canonical stable key yet.
- Existing resume uses `name + phone`; this remains a lookup behavior only and MUST NOT become identity.
- `참여자코드` is a legacy linkage hint, not a LIFE 2.0 user ID.
- No fallback composite key is invented without explicit verification.

## Claim flow
```
LIFE 2.0 login
→ existing diagnosis lookup
→ candidate lookup via server-side bridge
→ identity verification
→ minimum candidate preview
→ explicit user approval
→ legacy_source_links = VERIFIED
→ read-only diagnosis access
```

## Migration rules
- no full Sheet-row JSON dumps into FACT
- no representative-choice values promoted to exact facts
- no historical result presented as current Ver32.42 without provenance
- no account creation from legacy contact data without consent
- no automatic account merge from name/phone
- no UNKNOWN→0 conversion
- no silent recalculation of historical diagnosis

Migrated provenance:
- `source_type = MIGRATED`
- `source_ref = DIAG_MASTER_GSHEET:<record_type>:<opaque-record-key>`

## Consent separation
`개인정보동의` and `연구활용동의_CONSENT_RESEARCH` remain separate consent purposes and MUST NOT collapse into one boolean.

## Public Beta
Legacy migration is not a Public Beta blocker.
New members use Master DB v2 immediately; existing diagnosis records stay in Legacy Store until verified bridge activation.

## Current Supabase state
- connected organization: `life20co`
- organization plan: free
- project count: 0
- project creation requires owner organization/cost confirmation before creation.
