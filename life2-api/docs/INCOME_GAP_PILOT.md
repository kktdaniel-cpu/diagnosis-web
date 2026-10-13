# 최신 연결 상태 — 2026-10-13 KST

PR39 후속: 저장 동의가 있는 준비 초안을 anonymous handoff로 만들고 로그인/가입 뒤 MY LIFE로 연결하는 코드와 개발 DB 저장 공간을 추가했다.
- POST /v1/income-gap/handoffs: answers + strict consent:true, 24시간 token. 서버 정규화·입력 검증. UNKNOWN→0 금지.
- POST /v1/me/income-gap/claim: 검증된 Auth subject 사용, row lock, 동일 회원 재호출 idempotent, 다른 회원409, 만료410.
- GET /v1/me/income-gap/preparation: 자기 최신 초안만 반환, 서버에서 달력/Top3 재계산. 이는 준비 안내이며 Action 완료 재계산과 다름.
- 저장된 초안은 FACT가 아니다. 기존 Awareness token은 보존하되 신규 gap claim에서 함께 자동 claim하지 않는다.
- 브라우저에는 opaque token만 보관. 새 확인 메일을 다른 브라우저에서 열었을 경우 원래 브라우저에서 로그인해야 pending token을 이어받을 수 있다. 이메일 URL에 재무값/token을 넣지 않는다.
- 만료된 미연결 초안은 재조회/claim 불가. 이후 새 handoff 생성 시 최대100개씩 opportunistic 삭제. 삭제 시각을 정확히24시간으로 약속하지 않는다.
- 회원 탈퇴 시 user_id FK cascade로 연결 초안 삭제. 준비 초안 별도 삭제 UI는 후속.
- 소득공백 입력에 월/만원 값은 보존하며 A1/A2의 기존 나이/원 FACT에 임의로 변환하지 않는다.
- 로컬 API149 tests / Web27 tests / build PASS, dev SQL rollback RLS PASS. 실제 로그인 기반 claim/persistence 및 모바일/PDF 실기 미완료.
- Security Advisor 기존 WARN: [유출 비밀번호 보호 설정](https://supabase.com/docs/guides/auth/password-security#password-strength-and-leaked-password-protection). 이번 변경에서 Auth 설정은 수정하지 않았다.

아래는 PR39 당시 범위 기록이다. 미리보기에는 여전히 persistence:NONE이 적용되며, 저장 동의 뒤에만 새 draft 저장 경로를 사용한다.

# 소득공백 중심 첫 제품 — 개발 범위와 승계

기준일: 2026-10-13 KST. 개발 기준 `mvp/life2-bootstrap`의 `80af0ce36155db32f3cdd24ee0674cb439e1ce4e`.
사용자 요청: 최근 정한 방향으로 개발을 계속하고, 추가 로그인 없이 가능한 작업을 묶어서 완료.

## 제품 약속

퇴직 전후 직장인이 월급 종료와 확인한 연금 시작 시점을 달력으로 보고, 이번 달 먼저 확인할 행동을 최대 3개 정한다.
결과물은 달력, 미확인 정보 목록, 행동별 목표일·단계·완료 기준·정리 항목이다.
기존 12영역 Awareness와 A1~A12는 유지한다. 신규 집중 문항은 기존 Awareness의 완료 수나 FACT로 변환하지 않는다.
기관 제안과 강의는 이 첫 제품을 활용한다. 여러 사업 영역을 같은 첫 화면에서 동시에 판매하지 않는다.

## 이번 코드

| 영역 | 구현 | 검증 범위 |
|---|---|---|
| 진입 | Web 첫 화면의 소득공백 준비 버튼, 기존 회원 MY LIFE에도 진입 버튼 | React 계약 테스트/빌드 |
| 문항 | 서버 카탈로그의 12문항, 월·금액(만원/월), 빈 값 허용, 이전/수정 | API 및 Web 테스트 |
| 달력 | 마지막 월급 다음 달 → 본인 국민연금 시작 월의 월수, 배우자 및 둘 다 시작 월 분리 | 서버 규칙 테스트 |
| 행동 | 선행 정보 먼저, 안정적인 순서, 7/14/30일 권장 목표일(KST 기준) | API 테스트 |
| 도움 | 각 행동의 확인 순서, 완료 기준, 질문·정리표 항목 | 결과 화면/인쇄 대상 |
| 인쇄 | 결과에서 브라우저 인쇄 호출, 인쇄 CSS | 호출 테스트. 실제 PDF 파일/잘림 검증은 남음 |
| 가입 안내 | session 없는 signUp 응답을 실제 메일 발송 증거로 표현하지 않음, 이메일 공백 제거 | mocked Auth 회귀 테스트 |

모든 금액·상태·기간 계산은 서버에서 수행한다. Web helper는 문자열을 요청 형식으로 직렬화만 한다.
달력은 USER_REPORTED 시점에서 계산한 준비용 미리보기이며 새 FACT를 만들지 않는다.
목표일은 추천 날짜이고 자동 알림이나 상담 예약이 아니다.

## 12문항

| 문항 | 확인할 내용 | 기존 Action 연결 개념 |
|---|---|---|
| G01 | 배우자와 함께 준비하는지 | 공통 가구 범위 |
| G02 | 퇴직 예상 월 | A1 (현재 저장 계약은 나이·출생연도 중심, 자동 변환 금지) |
| G03 | 마지막 급여 입금 월 | A1 후속 확인 |
| G04 | 목표 월 생활비 | A4 |
| G05 | 월 대출 상환액·생활비 포함 여부 | A4/A6 |
| G06 | 본인 국민연금 시작 월·월 예상액 | A2 |
| G07 | 배우자 국민연금 시작 월·월 예상액 | A2, 배우자 있을 때만 |
| G08 | 퇴직·개인연금 정보 | A3, 실제 지급 기간은 추가 확인 |
| G09 | 퇴직 후 일·소득: 미확인/없음/계획/확인 | A7 |
| G10 | 사용할 금융자산 구간 | A6, 정확금액으로 역산 금지 |
| G11 | 예정된 큰 지출 유무 | A6 후속 확인 |
| G12 | 준비 계획을 실제로 이야기했는지 | 신규 일반 대화. A12 웰다잉 완료와 다름 |

생년월일에서 나이·연금 수급권·시작 월을 추정하지 않는다. 공식 조회에서 확인한 월을 입력한다.
이미 조회한 연금은 같은 내용을 다시 조회하라고 우선 권하지 않으며, 부분 확인이면 빠진 정보를 권한다.

## 익명 API

- GET `/v1/income-gap/questions`: 버전 `INCOME_GAP_PREPARATION_V1`, 12문항과 필드 계약.
- POST `/v1/income-gap/preview`: 인증 없음, stateless, `Cache-Control: no-store`, `fact_writes:false`, `persistence:NONE`.
- 빈 JSON도 정상 미확인 결과를 반환한다. 미확인 금액은 null, 확인한 0은 0으로 보존한다.
- 개인정보/비밀번호/임의 user_id 등 등록되지 않은 필드는 422로 거부한다.
- UNKNOWN 또는 NONE 상태에 금액·시작 월을 붙인 모순된 연금 입력은 422. NONE은 UNKNOWN 또는 0원이 아니다.
- 1인 가구의 이전 배우자 입력은 결과에서 제거. planned 재취업 소득을 확인한 소득으로 합산하지 않는다.
- `nps_wait_months=max(0, 본인 연금 시작 월 - 마지막 급여 다음 월)`. 이것은 무소득 기간이 아니다.
- A5 대응 후속 행동은 퇴직/급여 종료·본인 연금 시작/월액·생활비가 준비됐을 때만 제안하며 기존 회원 Action을 활성화하거나 완료시키지 않는다.
- `monthly_shortfall_10k`, `total_bridge_need_10k`는 항상 null. 자산 소진 연령/총 필요자금/보험 점수/수익률 추정 없음.
- 요청 입력은 결과 처리에만 사용하며 회원 DB·브라우저 영구 저장소에 쓰지 않는다. 새로고침/화면 이탈 시 입력은 사라진다.

## 다음 개발 순서

| 순서 | 작업 | 로그인 필요 여부 / 완료 조건 |
|---|---|---|
| 다음 1 | 신규 달력의 월 단위 FACT 계약·출처·버전 정의 | 코드/메모리 테스트는 로그인 불필요. A1/A2의 나이 계약과 구분 |
| 다음 2 | 명시적 저장 동의 → 익명 handoff → 공통 user_id claim | 구현 테스트는 로그인 불필요. 실제 두 전용 테스트 회원 인증으로 저장/격리 검증 필요 |
| 다음 3 | 회원 Action에서 월·금액 확인 → FACT → focused Top3 재계산 | 기존 완료 loop 재사용. 이번 미리보기 값을 자동 확인 완료로 처리하지 않음 |
| 다음 4 | 월별 현금흐름 계약·기존 정밀 엔진 비교 | 지급 기간·시작 월·부채·큰 지출·부분 확인 처리 정의 후 서버 테스트. 임의 월 부족액 금지 |
| 다음 5 | 첫 제품 실사용·PDF | dev에서 새로고침·모바일·출력 페이지 확인. 계정 테스트는 별도 안전한 전용 인증 |
| 이후 | 강의 실습 자료와 기관 시범 운영 | 교육 자료 완성 후 실제 15~20명 규모 협의. 계약/성과/가격이 확정됐다고 표현하지 않음 |

현재 CTA는 기존 전체 Awareness → 가입/MY LIFE 경로로 이동한다. 신규 달력의 입력/결과를 자동 claim하지 않는다.
따라서 이번 버전은 첫 제품의 로그인 없는 준비 미리보기이며 전체 LIFE Management loop 완성이나 신규 회원 저장 통과로 보고하지 않는다.

## 검증 실행

```sh
cd life2-api
PYTHONPATH=. pytest -q
cd ../life2-web
node --test tests/*.test.cjs
npm run build
```

CI에 `test:income-gap`을 추가했다. 기존 legacy guard 허용 경로만 수정한다.
실제 배포 확인은 Render dev API/Web의 커밋과 live 상태를 조회하고, 합성 입력으로 anonymous catalog/preview를 검증한다.
main/운영 병합·배포, 기존 Google Sheets/GAS Master DB, diagnosis-api Ver32.42 변경은 이번 승인 범위에 포함되지 않는다.

## 다음 채팅에 붙일 문구

GitHub `kktdaniel-cpu/diagnosis-web`의 현재 dev 및 열린 `feat/life2-income-gap-pilot` PR을 확인하고 `life2-api/docs/INCOME_GAP_PILOT.md`와 `SESSION_HANDOFF.md` 맨 위부터 읽어 이어서 개발하세요.
최근 방향은 소득공백 준비 달력 → 이번 달 행동 최대 3개 → 확인/실행 지원입니다.
기존 A1~A12 Core를 새로 설계하지 말고 신규 월 단위 준비 정보를 안전하게 연결하세요. 이번 익명 미리보기는 FACT 저장/회원 claim이 없습니다.
로그인 없이 가능한 코드·테스트·개발 PR은 묶어서 진행하고, 실제 전용 회원 persistence E2E와 PDF 출력은 완료 범위를 분리하세요.
main/운영 변경은 별도 승인 전 금지합니다.

최종 로컬 검증: API141 tests passed, Web25 tests passed, production build 성공. Supabase 테스트 계정에 쓰거나 실제 PDF 파일을 생성한 결과는 아니다.
