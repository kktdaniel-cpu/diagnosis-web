from __future__ import annotations

RESPONSES = ["CONFIRMED", "PARTIAL", "UNKNOWN_OR_NOT_PREPARED"]

QUESTIONS = [
    {"id":"AWR_Q01_RETIREMENT_AGE","domain":"work","q":"주된 직장을 그만둘 것으로 예상하는 나이를 정해두셨나요?","responses":RESPONSES,"action":"ACT_CONFIRM_RETIREMENT_AGE"},
    {"id":"AWR_Q02_NPS","domain":"cashflow_asset","q_single":"본인의 국민연금을 언제부터 월 얼마 받을지 확인해두셨나요?","q_couple":"본인과 배우자의 국민연금을 언제부터 월 얼마 받을지 확인해두셨나요?","responses":RESPONSES,"action":"ACT_CHECK_NPS_ESTIMATE"},
    {"id":"AWR_Q03_RET_PRIVATE_PENSION","domain":"cashflow_asset","q":"퇴직연금·개인연금도 언제부터 월 얼마 받을지 확인해두셨나요?","responses":RESPONSES,"action":"ACT_CHECK_RET_PRIVATE_PENSION"},
    {"id":"AWR_Q04_RETIREMENT_BUDGET","domain":"cashflow_asset","q":"65세 이후 우리 집이 매달 얼마를 써야 할지 계산해보셨나요?","responses":RESPONSES,"action":"ACT_ESTIMATE_RETIREMENT_BUDGET"},
    {"id":"AWR_Q05_INCOME_GAP","domain":"cashflow_asset","q":"퇴직부터 연금이 충분히 들어오기 전까지 몇 년을 무엇으로 버틸지 계산해보셨나요?","responses":RESPONSES,"action":"ACT_CALCULATE_INCOME_GAP"},
    {"id":"AWR_Q06_ASSETS_DEBT","domain":"cashflow_asset","q":"금융자산·퇴직자산·부채를 합쳐 우리 집 노후자산을 바로 적을 수 있나요?","responses":RESPONSES,"action":"ACT_SUMMARIZE_ASSETS_DEBT"},
    {"id":"AWR_Q07_POST_RETIREMENT_WORK","domain":"work","q":"퇴직 후에도 일한다면 몇 살까지, 월 얼마 정도 벌지 계획이 있나요?","responses":RESPONSES,"action":"ACT_DEFINE_POST_RETIREMENT_WORK"},
    {"id":"AWR_Q08_HOUSING","domain":"housing","q":"은퇴 후 지금 집을 유지할지, 줄일지, 주택연금을 활용할지 방향을 정해두셨나요?","responses":RESPONSES,"action":"ACT_DEFINE_HOUSING_PLAN"},
    {"id":"AWR_Q09_HEALTH_COVERAGE","domain":"health","q":"큰 병이 생겼을 때 치료비와 소득중단을 버틸 준비가 되는지 점검해보셨나요?","responses":RESPONSES,"action":"ACT_REVIEW_HEALTH_COVERAGE"},
    {"id":"AWR_Q10_CARE","domain":"health","q_single":"장기 돌봄이 필요할 때 누가, 어디서, 얼마로 돌볼지 생각해두셨나요?","q_couple":"본인이나 배우자에게 장기 돌봄이 필요할 때 누가, 어디서, 얼마로 돌볼지 이야기해보셨나요?","responses":RESPONSES,"action":"ACT_DEFINE_CARE_PLAN"},
    {"id":"AWR_Q11_DIGITAL_FAMILY_INFO","domain":"welldying","q":"내가 직접 처리할 수 없게 되면 가족이 보험·계좌·가상자산·간편결제·구독 등 중요한 자산과 계정을 찾을 수 있나요?","responses":RESPONSES,"action":"ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST"},
    {"id":"AWR_Q12_WELLDYING_CONVERSATION","domain":"welldying","q":"내가 의사표현을 못 할 때 원하는 의료·돌봄·재산·삶의 마무리에 대해 가족과 이야기해두셨나요?","responses":RESPONSES,"action":"ACT_START_FAMILY_WELLDYING_CONVERSATION"},
]

QUESTION_BY_ID = {q["id"]: q for q in QUESTIONS}

ACTION_META = {
    "ACT_CONFIRM_RETIREMENT_AGE": ("퇴직 예상시점 정하기", "P1", 10),
    "ACT_CHECK_NPS_ESTIMATE": ("국민연금 예상액 확인하기", "P1", 20),
    "ACT_CHECK_RET_PRIVATE_PENSION": ("퇴직·개인연금 확인하기", "P2", 30),
    "ACT_ESTIMATE_RETIREMENT_BUDGET": ("은퇴 생활비 계산하기", "P1", 40),
    "ACT_CALCULATE_INCOME_GAP": ("내 소득공백 계산하기", "P2", 50),
    "ACT_SUMMARIZE_ASSETS_DEBT": ("자산·부채 한눈에 정리하기", "P1", 60),
    "ACT_DEFINE_POST_RETIREMENT_WORK": ("퇴직 후 일자리 계획 만들기", "P3", 70),
    "ACT_DEFINE_HOUSING_PLAN": ("은퇴 후 주거 전략 정리하기", "P3", 80),
    "ACT_REVIEW_HEALTH_COVERAGE": ("보험·보장 점검하기", "P3", 90),
    "ACT_DEFINE_CARE_PLAN": ("돌봄 비용·방법 체크하기", "P3", 100),
    "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST": ("가족 비상·디지털 자산 목록 만들기", "P4", 110),
    "ACT_START_FAMILY_WELLDYING_CONVERSATION": ("가족 대화 시작하기", "P4", 120),
}
