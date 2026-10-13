# 월 단위 후속 확인 작업 묶음

퇴직·개인연금 / 자산 구간·큰 지출 / 퇴직 후 일 추가. 확인 총7항목. UNKNOWN은 null 유지, 계획 소득과 큰 지출 상세 미확인은 PARTIAL. 관련 값 변경 시 BRIDGE 재검토. 기존 운영과 legacy FACT 보호.

로컬 API173 tests, income-gap Web6 tests, build PASS. 개발 배포와 실제 회원/모바일/PDF 검증은 아직 완료되지 않음. 실제 Auth 완료를 메모리 테스트로 대체하지 않음. 개인연금 지급 종료/복수 연금 상세, 자산 정확액, 일 시작·종료 기간과 현금흐름 엔진은 후속.

# LIFE 2.0 검증 범위

2026-10-12 KST. API 113 passed, Web 20 passed, Web build 성공.
로컬 TestClient 검증과 live Supabase 검증은 구분한다.

| Action | 핵심 검증 | 로컬 통합 경로 |
|---|---|---|
| A1 퇴직 시점 | 사용자 확인 나이 저장, Top3 변경 | 1인/부부 통과 |
| A2 국민연금 | 출생연도 규칙, 원 단위 API, 1인 배우자 FACT 없음 | 1인/부부 통과 |
| A3 퇴직·개인연금 | 존재/월액/시작/기간, 종료 나이 RULE_DERIVED | 1인/부부 통과 |
| A4 생활비 | 만원 단위 목표 FACT | 1인/부부 통과 |
| A5 소득공백 | A1/A2/A4 선행, 4년 RULE_DERIVED, 월 부족액 미생성 | 1인/부부 통과 |
| A6 자산·부채 | Q23/Q30 구간, 정확금액 임의 생성 금지 | 1인/부부 통과 |
| A7 퇴직 후 일 | 명시적 NO_WORK의 확인된 0, UNKNOWN과 구분 | 1인/부부 통과 |
| A8 주거 | UNKNOWN=null, NO_PLAN과 분리, PARTIAL 유지 | 1인/부부 통과 |
| A9 건강·보장 | 미확인 보장 구간 UNKNOWN, 보장점수 생성 없음 | 1인/부부 통과 |
| A10 Care Lite | 비용 구간, 정확금액 생성 없음 | 1인/부부 통과 |
| A11 Digital Legacy | 위치 유형/접근 준비/가족 인지, 비밀 필드 거부 | 1인/부부 통과 |
| A12 가족 대화 | 실제 대화 + 선호 주제 필요 | 1인/부부 통과 |

모든 Action: draft → complete → 동일 요청 replay → FACT/대시보드 무변경을 검증한다.
Explain/Help는 deterministic fallback이며 저장 FACT key만 참조한다. 외부 생성 AI 검증은 포함하지 않는다.
두 회원 로컬 API: 상대 FACT/이력/설명 참조 없음, 상대 Action 수정·완료·이력 조회 차단, handoff 재사용 차단, 원래 회원 상태 유지.

## 실제 개발 서버 실행

API URL은 https://life2-api-dev.onrender.com 으로 고정된다. 운영 엔드포인트로 변경하지 않는다.
신규 전용 테스트 회원만 사용한다. 기존 FACT/Top3/진행/이력이 있으면 쓰기 전 중단한다.
토큰은 안전한 실행 환경에 제공하고 채팅, 명령 인자, GitHub, 로그에 넣지 않는다.

- LIFE2_E2E_ACCESS_TOKEN: 신규 테스트 회원의 유효한 dev 인증
- LIFE2_E2E_DISPOSABLE_ACCOUNT=1: 테스트 계정 데이터 생성 허용
- LIFE2_E2E_ISOLATION_ACCESS_TOKEN: 선택적인 별도 신규 테스트 회원 인증. 같은 user_id면 중단

life2-api 디렉터리에서 실행:

```bash
python scripts/verify_dev_member_loop.py
```

httpx 설치 필요. 인증/opt-in이 없으면 종료 코드 2, 요청 0건.
통과는 종료 코드 0. 실패는 종료 코드 1. 생성된 테스트 기록은 자동 삭제하지 않는다.
두 번째 인증이 없으면 회원 간 live 격리를 검증하지 않는다.
새 HTTP 연결은 로그인 재인증 또는 브라우저 세션 갱신의 증거가 아니다.

## 아직 완료하지 않은 검증

- 신규 인증으로 실제 Supabase 저장 및 회원 격리: 인증 미연결
- 브라우저 회원가입/로그인/Action UI 전체 흐름
- 상세리포트 및 설문 후 PDF 실제 페이지·잘림·빈 페이지
- 기존 정밀진단 나이 반영, 생활비 시나리오 설명 불일치 조사

운영 엔진·Google Master DB 보호. main merge/운영 deploy는 별도 승인 전 금지.
승계 기록은 Draft PR #33의 docs/life2-session-handoff-20261012 브랜치에 있다.

## 2026-10-12 후속 AI API 계약 검증
12Action × Explain/Help 24경로에서 다른 회원 FACT를 읽지 않고, FACT/대시보드(Top3·진행·최근변경)를 호출 전후 보존한다. 인증 없는 Explain/Help/change-summary401 및 미등록 Action404를 확인했다. API113 tests passed, Web20 passed. 저장소는 로컬 메모리이며 Supabase live 통과로 바꾸어 쓰지 않는다.

운영 UI 두 수정은 PR36 사용자 승인으로 main 병합·GitHub Pages 배포 완료. 실제 PDF 버튼 및 인쇄용 본문3페이지 생성 확인. PDF 파일 저장/페이지 잘림은 미완료. 새 dev 인증 없이는 live 스크립트가 쓰기 전 BLOCKED(요청0)로 중단한다.

## 실제 개발 DB RLS 검증 — 2026-10-12

`tests/db/verify_dev_rls_rollback.sql`을 dev Supabase에서 단일 트랜잭션으로 실행해 PASS. 두 SQL subject가 10개 회원 테이블에서 자신의 행만 조회하며, 다른 회원의 수정/삭제와 직접 FACT INSERT가 차단되고, 익명 및 내부 idempotency 조회가 차단됨. UNKNOWN/null 유지. 테스트 전체 ROLLBACK 후 FACT/Finding/Activity/Legacy link/idempotency 마커 잔존0.

SQL JWT subject 모의 검증이므로 실제 Auth 로그인/API/RPC 완료 및 연결 간 영구저장 E2E와 구분한다. 운영·DB 스키마·정책 변경 없음. 다음 실행은 별도 테스트 회원 안전한 인증으로 `scripts/verify_dev_member_loop.py`를 실행해야 한다.


## 소득공백 준비 미리보기 — 2026-10-13

신규 익명 `/v1/income-gap/questions` 및 `/preview`는 DB와 회원 저장소를 호출하지 않는다.
12문항, UNKNOWN/null·확인한0·소수 만원, 달력 월 경계·음수 방지, 부부 시작 월 분리, stale 배우자 입력 제거, NONE/UNKNOWN 분리, A1/A2/A4 정보 전 후속 행동 보류, 중복 요청 무변경, 미등록/secret/identity 필드422를 테스트한다.
Web은 12문항 흐름·서버 결과 표시·수정·인쇄 호출·실패 후 재시도·가입 안내 회귀를 검증한다. 기존 Auth 회복/회원 복귀/가족/정밀진단 entry 테스트도 실행한다.
새 익명 입력의 회원 handoff/FACT persistence, 실제 브라우저 인쇄 PDF 저장·페이지 잘림은 미완료. 테스트 통과를 live 완료로 바꾸어 쓰지 않는다.

최종 로컬 결과: API141 passed / Web25 passed / npm build 성공. 실제 API/Web dev 배포 커밋과 smoke 결과는 현재 PR/Render 상태로 확인한다.


## 월 단위 자기확인 FACT loop (2026-10-13)

RETIREMENT/NPS/BUDGET/BRIDGE 4항목: 검토 checkbox → scoped FACT → Action DONE/PARTIAL → focused Top3. 메모리 API와 mock UI에서 확인. 요청 재사용 무변경/본문변경409/오래된 revision409/두 동시 요청1승자/회원간404/타항목 patch 무시/기존 FACT·Awareness 보존/선행 수정 종속 FACT STALE 및 Action REVIEW_DUE를 검증. UNKNOWN/null, 0, NONE/NOT_APPLICABLE, 소수 만원 유지.

로컬 API164/Web28/build PASS. 실제 dev SQL rollback: 새 namespace FACT/Action/Activity·준비 데이터의 두 subject RLS 격리, 직접 UPDATE0행 또는 권한 차단, 익명0행·invalid-secret RPC차단 PASS. 준비/FACT/이력 마커 잔존0. 실제 confirm RPC와 Auth 로그인/재로그인 persistence E2E는 미완료. 기존 Auth WARN1 외 신규 advisor finding 없음.
