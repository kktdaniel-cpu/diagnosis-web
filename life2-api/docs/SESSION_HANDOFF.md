# 월 단위 후속 확인 작업 묶음

퇴직·개인연금 / 자산 구간·큰 지출 / 퇴직 후 일 추가. 확인 총7항목. UNKNOWN은 null 유지, 계획 소득과 큰 지출 상세 미확인은 PARTIAL. 관련 값 변경 시 BRIDGE 재검토. 기존 운영과 legacy FACT 보호.

로컬 API173 tests, income-gap Web6 tests, build PASS. 개발 배포와 실제 회원/모바일/PDF 검증은 아직 완료되지 않음. 실제 Auth 완료를 메모리 테스트로 대체하지 않음. 개인연금 지급 종료/복수 연금 상세, 자산 정확액, 일 시작·종료 기간과 현금흐름 엔진은 후속.

# LIFE 2.0 공통 인수인계
검토일: 2026-10-12 KST
이 문서는 채팅방 간 승계용이다. 재개 시 GitHub 및 배포 현황을 다시 조회한다. 문서 기록을 실시간 상태로 간주하지 않는다.


## 최신 월 단위 확인 → FACT → 다음 행동 연결 (2026-10-13)
- 기준 dev6a573873bbfde569cada236f9694c08f288f0f60 (PR41). feat/life2-gap-confirm에서 구현.
- 저장한 초안의 RETIREMENT/NPS/BUDGET/BRIDGE 4항목 자기확인 화면 및 회원 confirm API 구현. 아직 전체 A3~A12 월 단위 연결이 아니다.
- 명시적 검토 확인 → 준비별 namespace FACT(USER_CONFIRMED/SELF_REPORTED; 기간은 RULE_DERIVED) → 전용 GAP_V1 Action DONE/PARTIAL → focused Top3 재계산. 기존 Awareness 완료/나이 FACT/Google DB 변경 없음.
- FACT key gap.v1.<preparation_id>.<field>로 버전/초안 간 혼합 방지. UNKNOWN/null·0·NOT_APPLICABLE 구분. 국민연금 없는 계획은 대기 기간을0으로 만들지 않음.
- 요청 UUID/hash 재호출 idempotency, 수정본에 같은 UUID 사용409, optimistic revision409, 다른 회원404. 선행값 변경 시 종속 FACT STALE/Action REVIEW_DUE.
- dev Supabase migration gap_review_facts(version20261013044608) 적용. RPC SECURITY INVOKER·internal header/secret guard 유지. 원격 이력과 생성 SQL 파일명 일치.
- 실제 dev SQL role RLS 테스트 PASS: 두 subject의 새 namespace FACT/Action/Activity 및 초안 격리, UNKNOWN/0, 직접 변경0행/권한 거부, 익명 및 invalid-secret confirm 차단. 모두 ROLLBACK, 준비/FACT/이력 마커 잔존0.
- SQL role simulation은 실제 Auth 로그인/완료 RPC 실행 증거가 아니다. 현금흐름/보험/연금 자격 계산 없음. 실제 전용 회원의 확인→FACT→새 연결/persistence E2E 미완료.
- Security Advisor 신규 DB finding 없음. 기존 Auth leaked-password WARN1 유지, 설정 변경 없음.
- 다음: A3/A6/A7 후속 정보의 월 단위 확인 연결, focused Finding 엔티티 연결(현재 부분 확인/재검토는 준비 확인 상태와 Action에 기록), 실제 전용 회원 E2E, 모바일/PDF, 월별 현금흐름.
- 로컬 최종 API164 tests / Web28 tests / build PASS. 이는 메모리/TestClient 및 mocked UI 검증이며 실제 회원의 RPC 완료를 대신하지 않는다. CI/Render 최종 상태는 현재 PR 및 최신 검증 기록을 확인.

## 최신 소득공백 준비 초안 연결 — 2026-10-13 KST
- 기준: PR39 merged dev 6a08eba7159076ee81d3fc280015f0723675eb73. feat/life2-gap-save에서 후속 구현.
- 명시적 동의 → 익명 초안 저장 → 24시간 opaque token → 검증된 Auth subject로 claim → MY LIFE 재조회 구현. 브라우저에는 토큰만 보관, DB에는 SHA256 digest만 저장.
- 초안은 새 income_gap_preparations 테이블에 공통 user_id로 연결. 기존 Awareness/FACT/Action을 덮어쓰거나 완료하지 않는다. 월 입력을 나이로 변환하지 않음.
- Supabase dev migration income_gap_preparation 적용. CLI 생성 SQL을 원격 적용 이력 version20261013033910과 대조해 파일명을 일치시켰다. CLI db push 전 전체 기존 원격 이력을 pull/대조해야 한다. 신규 테이블 RLS, 3 RPC 모두 SECURITY INVOKER, 서버 내부 secret/header guard 사용. 기존 DB schema/운영 및 Google Master DB 변경 없음.
- 실제 dev SQL rollback 검증: 두 subject 자기 행만 조회, 0/null 유지, 직접 수정/익명 INSERT/조회/유효하지 않은 secret RPC 차단 PASS. 실제 Auth 로그인/claim RPC E2E와 다름.
- 로컬 API149 / Web27 / build PASS. 실제 신규 전용 회원 claim·새 로그인 persistence E2E 및 PDF는 미완료. 현재 PR/CI/Render는 재조회.
- Advisor 신규 DB 항목 없음. 기존 leaked password protection WARN1 유지; 설정 변경하지 않음.
- 다음: 준비 초안을 Action 확인 과정으로 연결하는 월 단위 FACT 계약, 확인 완료 뒤 focused Top3, 서버 월별 현금흐름. 일반 가족 대화를 A12 완료로 처리하지 않음.

## 최신 제품 방향과 개발 — 2026-10-13 KST
- 사용자 요청: 소득공백 중심 첫 제품으로 개발 계속, 추가 로그인 없이 가능한 작업을 일괄 진행.
- 기준 dev head를 GitHub에서 재확인: 80af0ce36155db32f3cdd24ee0674cb439e1ce4e (PR38). 기존 작업 파일은 보호하고 별도 feat/life2-income-gap-pilot에서 구현.
- 신규 stateless anonymous 12문항 / 준비 달력 / 최대 Top3 / 권장 목표일 / 단계·완료 기준·정리 항목 / 인쇄 호출 구현. 서버가 달력/행동 순서를 계산하며 UNKNOWN은 null 유지.
- 첫 화면을 소득공백 준비로 집중, 기존 Awareness/MY LIFE/A1~A12 유지. 기존 회원에게도 새 진입 버튼 제공.
- signup에서 session 없음만으로 메일 발송을 단정하던 문구 수정. 실제 메일 발송/수신 검증을 새로 통과한 것은 아님.
- 새 결과는 미리보기로 FACT를 만들거나 회원 Action 완료를 처리하지 않음. 월 부족액/총 필요자금/자산 소진 연령은 계산하지 않음.
- 신규 월 단위 결과를 회원에 자동 저장하는 handoff는 아직 없음. 기존 CTA는 전체 Awareness 체크 → 회원 저장 흐름이며 구분 안내를 표시.
- 로컬 최종 검증: API141 passed / Web25 passed / npm build 성공. mocked Auth와 메모리 저장소 테스트이며 회원 live 저장 증거가 아님.
- 상세 제품 범위·API·검증·다음 작업은 INCOME_GAP_PILOT.md. 현재 PR/CI/Render 상태는 재조회해야 함.
- 운영 main/diag.lpp20.com/diagnosis-api 및 Google Master DB 변경 승인 없음. dev 코드/검증만 진행.

## 최신 DB 검증 — 2026-10-12
- 개발 기준: PR37 merged, 33e620d8a072194ae317a9813aa3f012af0f9a07.
- 실제 dev Supabase(bikvcuchdlreqkqypwcr)에서 tests/db/verify_dev_rls_rollback.sql 단일 트랜잭션 실행 PASS. 스키마·정책·자격증명 변경 없음.
- 두 합성 SQL subject로 10개 회원 테이블의 자기 행만 보이는지 검증. 익명 사용자는 11개 테이블에서 행을 읽을 수 없고, 내부 idempotency 정보도 차단됨.
- UNKNOWN/JSON null 유지, 직접 FACT INSERT 차단, 상대 FACT UPDATE/Action DELETE 차단 확인. 모든 합성 데이터 ROLLBACK. 추가 조회에서 테스트 FACT/Finding/Activity/Legacy link/idempotency 잔존 모두0.
- SQL 수준 JWT subject 모의 검증이며 실제 Supabase Auth 로그인·API 완료 RPC·다른 연결의 영구 저장 통과 증거는 아니다. 완료 범위를 부풀리지 않는다.
- 사용자 선호: 구현/검증/커밋을 한 묶음으로, CI는 마지막 확인. 브라우저는 최종 Release Gate에만. 모드/모델/과금 전환은 자동 수행했다고 말하지 않는다.
- 남음: 전용 테스트 회원 안전한 인증을 연결한 API start→draft→complete→FACT→Top3→새 연결 persistence/다른 회원 격리 E2E, 브라우저 Action 흐름, 실제 PDF 저장/잘림. 생성형 AI 연결 미완료(현재 deterministic fallback).

## 최신 확인 — 2026-10-12 후속 검증
- 아래 과거 head/deploy/test 수치는 역사 기록이다. 재개 시 이 최신 절과 GitHub 실제 상태를 우선 대조한다.
- 개발 기준 head: 1da01a6f2dd78ef63f0f932fc9e2a8b31406e0c6 (PR33 dev 병합).
- 운영 main: db9fa2a2eb06ac7ab4685535cfe5f288396510f3 (PR36). 사용자가 승인한 PDF 버튼/생활비 설명 두 UI 수정만 병합. GitHub Pages run38190157889 success. Render LIFE2 운영/API 및 Google Master DB 변경 없음.
- 실제 운영 PDF 버튼 1개 표시, 클릭 후 기존 인쇄 엔진 #printDoc .rp-page 3개 생성 및 본문 있음 확인. 실제 PDF 파일 저장/출력 잘림은 미완료.
- 후속 개발 검증: API113 passed / Web20 passed. AI 안내 API에 29개 계약 테스트 추가: 12Action × Explain/Help, 다른 회원 FACT 참조 금지, 호출 전후 FACT/Top3/Activity 동일, 인증 없는 3경로401, 미등록 Action404. 로컬 메모리 저장소 증거이며 live Supabase 증거가 아니다.
- Explain/Help는 deterministic_fallback; 외부 생성 AI 모델을 연결한 것으로 보고하지 않는다.
- live 검증 스크립트 실행은 인증/전용 테스트 회원 opt-in 부재로 BLOCKED(exit2), 요청0건. 기존 사용자 FACT를 테스트값으로 덮어쓰지 않았다.
- 남음: 새 전용 회원의 안전한 인증으로 Supabase 실제 저장/회원격리 E2E; 브라우저 Action 전체경로; 실제 PDF 파일 저장/레이아웃. main/운영 추가변경 승인 없음.
- 감사 상세: PR34, 원 수정 제안: PR35(운영 병합 대상 아님), 승인된 실제 운영 수정/검증: PR36. 이 후속 PR은 테스트·승계문서만 변경한다.

## 목표와 승인 경계
Awareness → Top3 → 회원가입 → MY LIFE → Action → FACT 저장 → 완료 → Top3 재계산.
2026-10-12 사용자 지시: 구현·검증 진행. main merge 및 운영 deploy는 별도 명시 승인 전 금지.
기존 diag.lpp20.com / diagnosis-api Ver32.42와 Google Sheets/GAS Master DB 보호.
Supabase PostgreSQL Master DB v2, 공통 user_id. UNKNOWN은 0으로 변환하지 않는다.
브라우저 business logic 계산, AI 임의 FACT 생성 금지.
Digital Legacy 비밀번호/PIN/private key/seed/recovery phrase 저장 금지.
A10 정확한 비용 대신 비용 구간. A12 실제 가족 대화 1회 이상 + 선호사항 1개 이상.

## 확인한 현재 상태
repo: kktdaniel-cpu/diagnosis-web
dev branch: mvp/life2-bootstrap
조회한 head: cbf5aadaf1d9c098e88fc2835ffb4304dbf58b88
PR #18: closed. 과거 본문은 RC MERGE HOLD이며 최신 완료상태의 증거로 사용하지 않는다.
PR #31: 개발용 정밀진단 출처 허용. main merged a0fa5d19611cc630127455e3868b3bc9a5f1fc06.
PR #32: 기존 dev 회원 저장소를 유지하며 검증된 LIFE 2.0 코드만 dev에 동기화. merged cbf5aadaf1d9c098e88fc2835ffb4304dbf58b88.
이 과거 이력은 앞으로의 main 병합/운영 배포 승인이 아니다.
dev API: https://life2-api-dev.onrender.com
dev Web: https://life2-web-dev.onrender.com
dev API Render srv-db4rrbh42hec73ep0180 deploy dep-db5reqqvcj2c73ev1dhg live.
dev Web Render srv-db4s46p42hec73epusk0 deploy dep-db5reqqvcj2c73ev1dn0 live.
workspace tea-da0ii0s9v7es739euic0.
dev Auth host bikvcuchdlreqkqypwcr.supabase.co.
prod Auth host zqnxnaxgmfhzxqtflppw.supabase.co.
두 저장소는 별도다. 개발용 계정으로 운영용 로그인을 반복하거나 재가입을 요구하지 않는다.
회원 ID/비밀번호·token·개인 FACT는 문서에 기록하지 않는다.

## 구현과 검증을 구분
A1~A12 contract, 화면 wiring은 존재한다. A5 preview 화면도 dev remote App.tsx에서 확인했다.
A3/A7/A10/A11/A12: contract 테스트 존재. A10 band, A11 secret 거부 및 가족 접근조건, A12 대화조건.
A5: prerequisite A1/A2/A4, RULE_DERIVED gap. 정밀엔진 없이 월 부족액 생성 금지.
A8: Q16/Q19/Q21 개념. 잘 모름은 UNKNOWN.
A9: Q11/Q12/Q13 개념. 새 보장 점수/보험 추천 계산 금지.
API 로컬 재실행: 70 passed (2026-10-12).
Web 연결/회복/가족 테스트: 19 passed (이 방).
GitHub CI run 38155022047: success (PR #32 최종 head 2122bb46bb2b06c923b213131e90e670243dfcaf).
실제 Supabase 회원 FACT 전체 E2E와 Action 완료 후 Top3 변경은 새로 완료한 것으로 보고하지 않는다.
AI Context / Explain / Help / 기본 Change Summary 코드 존재. 외부 생성 AI 통합 완료로 간주하지 않는다.

## 사용자 실기 확인
기존 dev MY LIFE 12/12 → 정밀진단 entry life2-precision.html?go=diag.
사용자 사진: MY LIFE 확인 정보 3개 불러옴. 실제 전달 성공 증거.
사용자 진단 결과 화면: 71점, 현재 나이 51세, 은퇴 65세, 월 현금흐름 -180만원, 자산 소진 70.8세, 90세 3개 중 0개 통과.
위 숫자는 화면 관찰이며 계산 정확성 검증 PASS가 아니다.
entry의 출생연도 1968과 결과 51세 불일치. 입력 경로를 확인해야 한다. 출생연도만으로 정확한 만 나이를 생성하지 않는다.
생활비 시나리오 고정 설명 '소진 시점이 달라지지 않습니다'와 +2.8년 표시 충돌.
이미 연금 FACT가 있는데 연금 조회부터 권하는 일반 추천도 점검 대상.
사용자 설명: 설문 후 상세리포트/PDF 인쇄 가능. 설문 전 잠금을 오류로 분류하지 않는다.
PDF 실제 생성·페이지 누락/잘림/빈 페이지 검증은 미완료.
기존 정밀진단 결과 오류는 별도 조사로 기록하며 보호된 엔진을 임의 수정하지 않는다.

## 다음 작업 시나리오
1. dev 최신 head/CI/Render 다시 조회. 작업 중 다른 방/Claude 변경 확인.
2. A5 prerequisite 미충족/충족, 월 부족액 미생성 검증.
3. A8 UNKNOWN/NO 분리, A9 응답→FACT 대응 검증.
4. 별도 테스트 회원으로 Supabase live: start→draft→complete→FACT read→새 세션 persistence→Finding/Top3 변화.
5. 같은 completion 요청 반복 시 중복 FACT/Activity 없는지, 다른 회원 격리 확인.
6. A3~A12 전체 catalog coverage 및 UNKNOWN follow-up 확인.
7. AI Context/Explain/Help는 확정 FACT와 rule 출처만 사용. 외부 모델 연결은 별도 설계·검증.
8. 정밀리포트 표시 오류 조사와 실제 PDF 출력 검증.

## 다음 채팅 시작 문구
GitHub kktdaniel-cpu/diagnosis-web의 mvp/life2-bootstrap 최신 브랜치에서 life2-api/docs/SESSION_HANDOFF.md를 읽고 이어서 진행하세요. 맨 위 최신 절과 현재 GitHub 상태를 우선 확인하세요. 아직 병합 전인 verify/life2-db-rollback PR이 있으면 그 문서도 확인하세요. 구현·테스트·커밋을 한 묶음으로 진행하고, 브라우저는 최종 Release Gate에만 사용하세요. main/운영 추가변경은 별도 승인 전 금지합니다.

## 업데이트 규칙
새 PR/커밋/배포/검증/보류가 생길 때 이 문서 갱신.
완료는 코드 존재/테스트 통과/live 배포/실기 E2E로 구분.
채팅방 용량을 자동 예측한다고 약속하지 않는다. 항상 최신 승계 문서를 유지한다.
Claude가 GitHub에 반영한 코드·기록을 조회할 수 있으나 Claude 채팅 내용을 자동 공유받거나 자동 협업했다고 말하지 않는다.

## 2026-10-12 02:05 이후 점검
- Supabase dev live 읽기: action start/submit/complete, member facts/awareness 함수 존재, SECURITY INVOKER 유지.
- 완료 함수: idempotency 분기, PARTIAL 분기, 행 잠금 확인.
- 개인값 없이 aggregate로 A5 cashflow gap/bridge, A8 housing, A9 health FACT 저장 존재 확인. 이번 실행의 새 계정 API E2E 통과 증거는 아니다.
- Security Advisor 현재 WARN 1건: auth_leaked_password_protection. 설정 변경하지 않음. 과거 0건을 현재 결과로 보고하지 않는다.
- A8 UNKNOWN/NO_PLAN 구분 회귀 테스트 추가. API 71 passed.
- 새 회원 로그인 기반 start/draft/complete/reconnect/Top3 및 격리 E2E는 미완료. DB 관리자 접근으로 Auth 경로를 대신했다고 보고하지 않는다.

## 개발용 검증 실행기 추가
- scripts/verify_dev_member_loop.py: dev API URL 고정, Supabase backend 확인, 신규 전용 테스트 회원만 허용.
- LIFE2_E2E_ACCESS_TOKEN은 안전한 환경으로 제공하며, LIFE2_E2E_DISPOSABLE_ACCOUNT=1 명시 없으면 요청하지 않음. 기존 FACT/Top3/진행/이력 있는 회원은 쓰기 전에 중단.
- Awareness 12 → claim → A1/A2/A4 → A5/A8/A9 draft/complete → FACT 읽기 → 새 HTTP 연결 → Top3 변경/유지 확인. 중복 completion의 FACT/dashboard 변화 없음 확인.
- 로컬 TestClient로 실행 절차 점검 완료. 이 결과는 live Supabase 또는 브라우저 로그인 E2E가 아님.
- 안전장치 회귀 테스트 7개 추가. API 전체 78 passed.
- 실제 dev 실행은 인증 정보 부재로 BLOCKED, 요청 0건. 사용자 데이터/운영 배포 변경 없음.
- 남은 작업: 전용 테스트 인증을 안전하게 연결한 live 실행, 두 회원 격리, 브라우저 UI 흐름, 상세리포트/PDF 검증.
- 실행: life2-api에서 python scripts/verify_dev_member_loop.py. httpx 설치 필요. 비밀번호/token을 채팅·인자·로그·문서에 기록하지 않는다.

## 일괄 검증 확대 (2026-10-12)
- 사용자 요청: 한 번에 가능한 항목들을 묶어 진행. main/운영 승인 경계 유지.
- 검증 실행기를 A1~A12 전체 draft/complete/replay/FACT read로 확대. 로컬 1인·부부 가구 경로 통과.
- 12 Action Explain/Help API 호출 확인: deterministic_fallback, fact_refs가 실제 저장 키의 부분집합. 외부 AI 연결 완료 아님.
- 두 회원 API 격리: FACT/Activity/Explain/Help에 상대 데이터 없음. foreign draft/wait/complete/change-summary 404, claim handoff 재사용 409, 원래 회원 FACT/dashboard 무변경. 모두 memory TestClient 검증이며 live RLS 검증 아님.
- 실제 실행기에는 선택적인 두 번째 인증 LIFE2_E2E_ISOLATION_ACCESS_TOKEN을 지원. 서로 다른 auth_subject와 두 계정의 빈 상태를 쓰기 전에 확인.
- 최종 API 84 passed, 웹 테스트 19 passed, npm build 성공.
- VERIFICATION_MATRIX.md에 Action별 검증·실행 방법·미완료 범위 기록.
- 실서버 인증 정보는 아직 없음. 실제 Supabase 저장/회원 격리와 브라우저 UI·PDF는 여전히 미완료.

## 실제 로그인 및 재접속 조사 (2026-10-12)
- browserAuth 안전한 입력을 통한 dev 로그인 성공. 실제 MY LIFE 12/12 표시를 확인. 사용자 인증값은 읽거나 저장하지 않음.
- 기존 완료 회원이므로 합성 FACT를 생성하지 않음. 신규 두 테스트 계정 live 쓰기 검증은 여전히 미완료.
- 일반 reload 후 landing → 이어보기에서 로그인 화면 표시. 세션 자체의 잔존 여부는 인증 보호 범위에서 읽지 않았으므로 미확정.
- 코드 확인: 기존 session이 있어도 pending handoff 또는 auth=confirmed일 때만 dashboard를 로드함. 일반 기존 session에도 dashboard를 로드하도록 수정, 회복 흐름의 우선순위 유지.
- 웹 20 tests 및 build 통과. 아직 배포 전이며 실제 새로고침 복귀 PASS 아님.
