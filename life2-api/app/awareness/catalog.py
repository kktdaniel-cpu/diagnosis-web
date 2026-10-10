from typing import Final

AWARENESS_QUESTIONS: Final = [
    {
        "id": "AWR_Q01_RETIREMENT_AGE",
        "domain": "work",
        "title": "주된 직장을 그만둘 것으로 예상하는 나이를 정해두셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "정확히 정했어요"},
            {"value": "PARTIAL", "label": "대략 생각해뒀어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 정하지 않았어요"},
        ],
        "action_catalog_id": "ACT_CONFIRM_RETIREMENT_AGE",
    },
    {
        "id": "AWR_Q02_NPS",
        "domain": "cashflow_asset",
        "title_single": "본인의 국민연금을 언제부터 월 얼마 받을지 확인해두셨나요?",
        "title_couple": "본인과 배우자의 국민연금을 언제부터 월 얼마 받을지 확인해두셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "모두 확인했어요"},
            {"value": "PARTIAL", "label": "일부만 알고 있어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 잘 몰라요"},
        ],
        "action_catalog_id": "ACT_CHECK_NPS_ESTIMATE",
    },
    {
        "id": "AWR_Q03_RET_PRIVATE_PENSION",
        "domain": "cashflow_asset",
        "title": "퇴직연금·개인연금도 언제부터 월 얼마 받을지 확인해두셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "확인했어요"},
            {"value": "PARTIAL", "label": "일부만 확인했어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 확인 전이에요"},
        ],
        "action_catalog_id": "ACT_CHECK_RET_PRIVATE_PENSION",
    },
    {
        "id": "AWR_Q04_RETIREMENT_BUDGET",
        "domain": "cashflow_asset",
        "title": "65세 이후 우리 집이 매달 얼마를 써야 할지 계산해보셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "계산했어요"},
            {"value": "PARTIAL", "label": "대략만 생각했어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "계산하지 않았어요"},
        ],
        "action_catalog_id": "ACT_ESTIMATE_RETIREMENT_BUDGET",
    },
    {
        "id": "AWR_Q05_INCOME_GAP",
        "domain": "cashflow_asset",
        "title": "퇴직부터 연금이 충분히 들어오기 전까지 몇 년을 무엇으로 버틸지 계산해보셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "계산했어요"},
            {"value": "PARTIAL", "label": "일부만 생각했어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "계산하지 않았어요"},
        ],
        "action_catalog_id": "ACT_CALCULATE_INCOME_GAP",
    },
    {
        "id": "AWR_Q06_ASSETS_DEBT",
        "domain": "cashflow_asset",
        "title": "금융자산·퇴직자산·부채를 합쳐 우리 집 노후자산을 바로 적을 수 있나요?",
        "options": [
            {"value": "CONFIRMED", "label": "정리돼 있어요"},
            {"value": "PARTIAL", "label": "일부만 알아요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "바로 적기 어려워요"},
        ],
        "action_catalog_id": "ACT_SUMMARIZE_ASSETS_DEBT",
    },
    {
        "id": "AWR_Q07_POST_RETIREMENT_WORK",
        "domain": "work",
        "title": "퇴직 후에도 일한다면 몇 살까지, 월 얼마 정도 벌지 계획이 있나요?",
        "options": [
            {"value": "CONFIRMED", "label": "구체적인 계획이 있어요"},
            {"value": "PARTIAL", "label": "대략적인 계획은 있어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 계획이 없어요"},
        ],
        "action_catalog_id": "ACT_DEFINE_POST_RETIREMENT_WORK",
    },
    {
        "id": "AWR_Q08_HOUSING",
        "domain": "housing",
        "title": "은퇴 후 지금 집을 유지할지, 줄일지, 주택연금을 활용할지 방향을 정해두셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "방향을 정했어요"},
            {"value": "PARTIAL", "label": "고민 중이에요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 정하지 않았어요"},
        ],
        "action_catalog_id": "ACT_DEFINE_HOUSING_PLAN",
    },
    {
        "id": "AWR_Q09_HEALTH_COVERAGE",
        "domain": "health",
        "title": "큰 병이 생겼을 때 치료비와 소득중단을 버틸 준비가 되는지 점검해보셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "점검했어요"},
            {"value": "PARTIAL", "label": "일부만 점검했어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 점검하지 않았어요"},
        ],
        "action_catalog_id": "ACT_REVIEW_HEALTH_COVERAGE",
    },
    {
        "id": "AWR_Q10_CARE",
        "domain": "health",
        "title_single": "장기 돌봄이 필요할 때 누가, 어디서, 얼마로 돌볼지 생각해두셨나요?",
        "title_couple": "본인이나 배우자에게 장기 돌봄이 필요할 때 누가, 어디서, 얼마로 돌볼지 이야기해보셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "정리돼 있어요"},
            {"value": "PARTIAL", "label": "일부만 이야기했어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 준비가 없어요"},
        ],
        "action_catalog_id": "ACT_DEFINE_CARE_PLAN",
    },
    {
        "id": "AWR_Q11_DIGITAL_FAMILY_INFO",
        "domain": "welldying",
        "title": "내가 직접 처리할 수 없게 되면 가족이 보험·계좌·가상자산·간편결제·구독 등 중요한 자산과 계정을 찾을 수 있나요?",
        "options": [
            {"value": "CONFIRMED", "label": "찾을 수 있게 정리돼 있어요"},
            {"value": "PARTIAL", "label": "일부만 가능해요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "가족이 찾기 어려워요"},
        ],
        "action_catalog_id": "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
    },
    {
        "id": "AWR_Q12_WELLDYING_CONVERSATION",
        "domain": "welldying",
        "title": "내가 의사표현을 못 할 때 원하는 의료·돌봄·재산·삶의 마무리에 대해 가족과 이야기해두셨나요?",
        "options": [
            {"value": "CONFIRMED", "label": "구체적으로 이야기했어요"},
            {"value": "PARTIAL", "label": "일부 이야기했어요"},
            {"value": "UNKNOWN_OR_NOT_PREPARED", "label": "아직 이야기하지 않았어요"},
        ],
        "action_catalog_id": "ACT_START_FAMILY_WELLDYING_CONVERSATION",
    },
]


def public_questions() -> list[dict]:
    return AWARENESS_QUESTIONS
