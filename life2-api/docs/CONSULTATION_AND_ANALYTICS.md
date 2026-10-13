# 상담 신청·이용 분석 진행 상태

회원 소득공백 초안에서 명시적 동의 후 CALENDAR 상담 요청을 저장하는 화면/API 계약을 구현했습니다. 요청 UUID 재사용은 중복 저장하지 않으며 수정 본문 충돌409, 다른 회원 초안404, 동의 없음422입니다. 신청은 RECEIVED이며 일정 확정이나 발송 완료가 아닙니다. 이메일/카카오 발송은 NOT_CONFIGURED입니다.

SQL 019_consultation_requests.sql은 내부 secret/header, ACTIVE 회원 및 초안 소유권을 확인하고 기존 activity_log에 기록합니다. 사용자별 동시 요청 잠금과 최대20건 제한. 새로운 FACT·알림·결제는 생성하지 않습니다. 아직 실제 DB 적용/운영 배포/실제 회원 신청 검증 전입니다.

로컬 API178 tests, Web build 및 income-gap6 tests PASS. 외부 메일/카카오 발송에는 발송 계정·템플릿·발송 동의와 검증이 필요합니다. GA4 측정ID는 아직 확인하지 않았습니다. 분석 이벤트 후보: diagnosis_started, preview_viewed, preparation_saved, review_saved, consultation_requested. 금액·이메일·회원ID·초안ID를 GA4에 전송하지 않습니다. 실제 이벤트 연결/수집은 후속이며 현재GA4완료가 아닙니다.

남은 통합 점검: 로그아웃 재로그인, 모바일, 실제PDF. main·기존운영·GoogleMasterDB 유지.
