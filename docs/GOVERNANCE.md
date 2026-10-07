# LIFE 2.0 진단프로그램 변경 거버넌스

## 목적
운영 변경을 `요청 → 분석 → 승인 → 패치 → 자동검증 → 대표 승인 → merge → 배포 → 운영검증` 순서로 고정한다.

## 승인 게이트
- 분석과 테스트 실행은 자동화할 수 있다.
- 기능 코드 수정은 승인된 Issue 범위 안에서만 한다.
- `main` 직접 수정은 금지하고 작업 브랜치와 PR을 사용한다.
- merge와 운영 배포는 대표의 명시적 승인 전에는 수행하지 않는다.

## 반드시 별도 승인할 변경
- 계산식, 가중치, 임계값, 단위
- 질문/응답의 의미 또는 U(unknown) 처리 규칙
- 진단 등급/점수 의미
- backend/API schema
- DIAGNOSIS_SPEC 및 잠금 스냅샷
- APP_VERSION
- 사용자에게 보이는 중요한 신규 문구

## 자동 수행 가능
- 읽기 전용 원인 분석
- 테스트/회귀 테스트 실행
- 변경 파일 범위 검사
- hash/배포 상태 확인
- null/undefined/NaN 등 사용자 노출 회귀 검사(전용 렌더 테스트가 있는 경우)
- PDF 빈 페이지/overflow 등 전용 UI 테스트(테스트가 구현된 경우)

## 작업 상태
`NEW → PREFLIGHT → APPROVED_FOR_PATCH → PATCHED → CI_PASS → OWNER_APPROVED → MERGED → DEPLOYED → VERIFIED → CLOSED`

범위를 벗어난 문제를 발견하면 수정하지 않고 `[NEW ISSUE FOUND]`로 보고하고 STOP한다.

## 보호 대상
다음 항목은 해당 저장소에 존재하거나 향후 추가될 경우 별도 승인 없이 변경하지 않는다.
- `api/main.py`
- `DIAGNOSIS_SPEC.md`
- `DIAGNOSIS_SPEC_v1.5_LOCK.md`
- `APP_VERSION` 또는 버전 선언

## 현재 자동화 1단계의 한계
`diagnosis-web` 운영 저장소에는 현재 전체 Python/JS 계약 테스트 소스가 포함되어 있지 않다. 따라서 1단계 CI는 변경 범위와 운영 파일의 기본 무결성을 우선 검증한다. p0/p1/p2/p4, 계약 테스트, Playwright/PDF 회귀를 자동 실행하려면 해당 테스트가 실행 가능한 저장소/경로를 CI에 연결한 뒤 2단계로 승격한다.
