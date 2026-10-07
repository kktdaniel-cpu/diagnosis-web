# LIFE 2.0 진단프로그램 변경 거버넌스

## 목적
운영 변경을 `요청 → 분석 → 승인 → 패치 → 자동검증 → 대표 승인 → merge → 배포 → 운영검증` 순서로 고정한다.

## 핵심 원칙
- 기계 검증이 LEVEL A 통과/실패를 판정한다.
- ChatGPT/코딩 에이전트는 결과를 설명하고 수정안을 제시할 수 있지만, 기계 게이트를 대체하지 않는다.
- CI PASS는 LEVEL B(진단 타당성) 승인을 의미하지 않는다.
- `main` 직접 수정은 금지하고 작업 브랜치와 PR을 사용한다.
- merge와 운영 배포는 대표의 명시적 승인 전에는 수행하지 않는다.
- 범위를 벗어난 문제는 수정하지 않고 `[NEW ISSUE FOUND]` 로 보고 후 STOP한다.

## 저장소 경계
### diagnosis-web (공개)
- 운영 프론트와 공개 가능한 정적 검증만 둔다.
- 비공개 엔진 소스, 450 fixture, 엔진 의존 테스트 자산을 넣지 않는다.
- 1단계 CI는 secrets 0으로 운영한다.

### private verification (2단계 예정)
- p0/p1/p2/p4, p2timing, 엔진 계약, JS 렌더, PDF/Playwright 등 엔진 의존 검증은 비공개 검증 환경에서만 실행한다.
- 권고 구조: 별도 private `diagnosis-verify` 저장소 또는 동등한 private runner 환경.
- 위치 확정 전에는 비공개 검증 자산을 공개 저장소로 복사하지 않는다.

## 반드시 별도 대표 승인할 변경
- 계산식, 가중치, 임계값, 단위
- 질문/응답 의미 또는 U(unknown) 처리 규칙
- 진단 등급/점수 의미
- backend/API schema
- APP_VERSION
- DIAGNOSIS_SPEC 및 잠금 스냅샷
- 사용자에게 보이는 중요한 신규 문구
- 자동화 정책/워크플로 자체 변경
- merge / deploy

## 1단계 자동 수행 가능
- 읽기 전용 원인 분석
- 변경 파일 범위 검사
- 운영 HTML 기본 무결성 검사
- 공개 소스에서 가능한 negative contract / stale reference 정적 검사
- hash / 배포 상태 확인
- CI 결과 요약

## 작업 상태
`NEW → PREFLIGHT → APPROVED_FOR_PATCH → PATCHED → CI_PASS → OWNER_APPROVED → MERGED → DEPLOYED → VERIFIED → CLOSED`

## 승인 범위의 출처
Issue 본문은 참고 자료다. Issue 작성자 임의로 허용 범위를 넓힐 수 없다.
실제 자동화 범위는 커밋된 정책 + 대표 승인 상태를 기준으로 한다.

## 자동화 인프라 자기보호
- 일반 제품 PR에서 `.github/**`, `scripts/verify_*`, `docs/GOVERNANCE.md`, `docs/RELEASE_CHECKLIST.md` 변경은 별도 자동화 유지보수 승인 없이는 허용하지 않는다.
- base branch의 `pull_request_target` 정책 가드가 PR 자체의 workflow 수정으로 검사 약화를 시도하는 것을 차단해야 한다.
- 자동화 유지보수는 별도 `automation-maintenance` 승인 절차를 사용한다.
- branch protection / required checks / 관리자 우회 금지 설정은 저장소 설정 작업이므로 별도 대표 승인 전에는 변경하지 않는다.

## 에이전트 재시도 상한
향후 자동 패치 에이전트를 붙일 때:
- 자동 재시도 최대 2회
- 승인된 파일 범위 밖 변경 1건이라도 발생하면 STOP
- 파일 수 또는 diff 상한 초과 시 HOLD
- 재시도 중 새 이슈 발견 시 수정하지 않고 보고

## 배포
현재 web은 main merge가 운영 GitHub Pages 배포로 이어질 수 있으므로 merge 후 smoke만으로 안전하다고 간주하지 않는다.
배포 전 체크, 즉시 revert 절차, backend → /health → frontend 순서 보장은 RELEASE_CHECKLIST를 따른다.

## 현재 1단계의 한계
이 저장소에는 전체 Python/JS 계약 테스트 및 비공개 엔진 자산이 없다.
따라서 현재 CI는 LEVEL A 중 공개 저장소에서 실행 가능한 정적/범위 검증만 담당한다.
