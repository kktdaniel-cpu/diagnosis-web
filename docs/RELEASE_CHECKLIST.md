# LIFE 2.0 Release Checklist

## 목적
merge가 곧 운영 노출로 이어질 수 있는 현재 구조에서, 배포 순서와 되돌리기 절차를 고정한다.

## 0. 전제
- CI PASS = LEVEL A 통과일 뿐, LEVEL B 타당성 승인이 아니다.
- 대표의 명시적 merge 승인 전에는 merge하지 않는다.
- 스테이징/preview가 없는 변경은 운영 노출 전 위험을 별도로 보고한다.

## 1. 변경 전
- [ ] 연결 Issue와 승인 범위 확인
- [ ] 변경 파일이 committed allowlist 안인지 확인
- [ ] 새 공식/임계값/가정/중요 문구가 있으면 별도 승인
- [ ] 자동화 정책 파일과 제품 파일이 같은 PR에 섞이지 않았는지 확인
- [ ] private engine/test 자산이 공개 diagnosis-web에 추가되지 않았는지 확인

## 2. LEVEL A 검증
- [ ] diagnosis-verify PASS
- [ ] static negative contract PASS
- [ ] 운영 HTML 존재/기본 무결성 PASS
- [ ] private verification이 필요한 변경이면 해당 비공개 게이트 PASS
- [ ] 결과 요약에 "LEVEL A only" 명시

## 3. 배포 순서
backend 변경이 포함된 릴리스는 반드시:
1. engine/backend 먼저
2. backend /health 확인
3. 필요한 schema/contract 확인
4. frontend merge/deploy
5. 운영 smoke

frontend-only 변경은 backend 무수정/호환 상태를 확인하고 진행한다.

## 4. merge 직전
- [ ] 대표 merge 승인
- [ ] base/head 최신 여부 확인
- [ ] required checks PASS
- [ ] 즉시 revert 대상 commit SHA 기록
- [ ] 운영 점검 시나리오 준비

## 5. 운영 배포 직후
- [ ] GitHub Pages/배포 상태 Success
- [ ] 운영 URL 200
- [ ] 핵심 화면 smoke
- [ ] 사용자 노출 null/undefined/NaN 등 확인
- [ ] 인쇄/PDF 변경이면 실제 PDF 생성 확인
- [ ] 발견 이슈는 silent fix하지 않고 새 Issue로 분리

## 6. 즉시 revert 조건
다음 중 하나면 HOLD + revert 검토:
- 운영 페이지 진입 실패
- 진단/결과 렌더 중단
- 사용자 데이터/계산 의미 회귀
- 빈 PDF/인쇄 불가
- 승인 범위 밖 변경 확인
- backend/frontend contract 불일치

## 7. 자동화 2단계 전제
- private verification 저장소/runner 위치 확정
- 공개/비공개 자산 경계 문서화
- backend → health → frontend release gate 설계
- agent retry 상한 및 diff 상한 확정
