# LIFE 2.0 공통 인수인계
검토일: 2026-10-12 KST
이 문서는 채팅방 간 승계용이다. 재개 시 GitHub 및 배포 현황을 다시 조회한다. 문서 기록을 실시간 상태로 간주하지 않는다.

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
'GitHub mvp/life2-bootstrap의 life2-api/docs/SESSION_HANDOFF.md를 읽고 최신 branch/CI/Render와 대조해 이어서 진행하세요. 기존 운영과 Google Master DB를 보호하고 main merge/운영 deploy는 별도 승인 전 금지합니다.'

## 업데이트 규칙
새 PR/커밋/배포/검증/보류가 생길 때 이 문서 갱신.
완료는 코드 존재/테스트 통과/live 배포/실기 E2E로 구분.
채팅방 용량을 자동 예측한다고 약속하지 않는다. 항상 최신 승계 문서를 유지한다.
Claude가 GitHub에 반영한 코드·기록을 조회할 수 있으나 Claude 채팅 내용을 자동 공유받거나 자동 협업했다고 말하지 않는다.
