from __future__ import annotations

from typing import Any

from .actions import ACTION_FORMS, income_gap_preview
from .catalog import ACTION_META

ACTION_FACT_KEYS: dict[str, tuple[str, ...]] = {
    "ACT_CONFIRM_RETIREMENT_AGE": (
        "work.primary_job_exit_age",
    ),
    "ACT_CHECK_NPS_ESTIMATE": (
        "profile.birth_year_self",
        "profile.birth_year_spouse",
        "pension.nps.monthly_self",
        "pension.nps.monthly_spouse",
        "pension.nps.start_age_self",
        "pension.nps.start_age_spouse",
    ),
    "ACT_CHECK_RET_PRIVATE_PENSION": (
        "pension.ret_private.exists",
        "pension.ret_private.monthly_household",
        "pension.ret_private.start_age",
        "pension.ret_private.duration_years",
        "pension.ret_private.end_age",
    ),
    "ACT_ESTIMATE_RETIREMENT_BUDGET": (
        "cashflow.retirement_monthly_budget_target",
    ),
    "ACT_CALCULATE_INCOME_GAP": (
        "work.primary_job_exit_age",
        "pension.nps.start_age_self",
        "cashflow.retirement_monthly_budget_target",
        "pension.ret_private.exists",
        "pension.ret_private.start_age",
        "work.post_retirement.monthly_income",
        "work.income_end_age",
        "cashflow.income_gap_years_to_nps_self",
        "cashflow.income_gap_bridge_sources",
    ),
    "ACT_SUMMARIZE_ASSETS_DEBT": (
        "asset.financial_liquid_band_q23",
        "debt.total_band_q30",
    ),
    "ACT_DEFINE_POST_RETIREMENT_WORK": (
        "work.primary_job_exit_age",
        "work.post_retirement.plan_type",
        "work.post_retirement.monthly_income",
        "work.income_end_age",
        "work.post_retirement.health_insurance_type",
    ),
    "ACT_DEFINE_HOUSING_PLAN": (
        "housing.tenure_q16",
        "housing.move_plan_q21",
        "housing.reverse_mortgage_plan_q19",
        "housing.reverse_mortgage_start_age",
    ),
    "ACT_REVIEW_HEALTH_COVERAGE": (
        "health.critical_illness_benefit_band_q12",
        "health.indemnity_coverage_q13",
        "health.major_history_q11",
        "health.income_stop_plan_checked",
    ),
    "ACT_DEFINE_CARE_PLAN": (
        "care.primary_provider_plan",
        "care.primary_place_plan",
        "care.monthly_cost_band",
        "care.coverage_status_q14",
    ),
    "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST": (
        "digital_legacy.inventory_categories",
        "digital_legacy.inventory_location_type",
        "digital_legacy.family_can_locate",
        "digital_legacy.access_procedure_prepared",
    ),
    "ACT_START_FAMILY_WELLDYING_CONVERSATION": (
        "welldying.family_conversation_done",
        "welldying.preference_topics_recorded",
    ),
}

ACTION_GUIDE: dict[str, dict[str, Any]] = {
    "ACT_CONFIRM_RETIREMENT_AGE": {
        "why":"소득공백과 이후 연금·일 계획의 시작점을 정하려면 퇴직 예상시점이 먼저 필요합니다.",
        "help":["회사 정년·희망퇴직 가능성을 확인합니다.","현재 계획 기준의 주된 직장 종료 나이를 적습니다.","계획이 바뀌면 나중에 다시 갱신합니다."],
        "effort":"짧음",
    },
    "ACT_CHECK_NPS_ESTIMATE": {
        "why":"국민연금 개시 나이와 월 예상액은 퇴직 뒤 현금흐름의 기준 FACT입니다.",
        "help":["국민연금 예상연금액 조회 결과를 준비합니다.","본인과 배우자가 있으면 각각 월 예상액을 확인합니다.","출생연도는 개시연령 규칙 확인에만 사용합니다."],
        "effort":"보통",
    },
    "ACT_CHECK_RET_PRIVATE_PENSION": {
        "why":"국민연금 외 연금이 언제, 얼마 동안 들어오는지 알아야 소득공백을 연결할 수 있습니다.",
        "help":["퇴직연금·IRP·연금저축의 예상 수령정보를 확인합니다.","월 수령액·개시 나이·수령 기간을 적습니다.","해당 연금이 없다면 없음을 명확히 기록합니다."],
        "effort":"보통",
    },
    "ACT_ESTIMATE_RETIREMENT_BUDGET": {
        "why":"필요 생활비가 확인되어야 이후 현금흐름 부족 여부를 계산할 수 있습니다.",
        "help":["65세 이후 예상 월 생활비를 생각합니다.","현재 생활비가 아니라 은퇴 후 목표 생활비를 적습니다.","정확하지 않아도 현재 계획 기준으로 기록하고 나중에 갱신합니다."],
        "effort":"짧음",
    },
    "ACT_CALCULATE_INCOME_GAP": {
        "why":"퇴직과 국민연금 개시 사이 기간을 먼저 알아야 그 기간을 어떤 자금으로 연결할지 결정할 수 있습니다.",
        "help":["퇴직 예상시점·국민연금·은퇴 생활비가 먼저 확인되어야 합니다.","시스템이 퇴직→본인 국민연금 개시 기간을 계산합니다.","그 기간을 연결할 실제 수단을 선택합니다."],
        "effort":"짧음",
    },
    "ACT_SUMMARIZE_ASSETS_DEBT": {
        "why":"노후에 실제로 쓸 수 있는 금융자산과 갚아야 할 부채를 같은 화면에서 봐야 다음 계획을 세울 수 있습니다.",
        "help":["연금계좌를 제외한 금융자산 구간을 선택합니다.","주택·사업·신용대출 등 남은 대출 총액 구간을 선택합니다.","MVP에서는 구간만 저장하고 임의의 정확한 금액을 만들지 않습니다."],
        "effort":"짧음",
    },
    "ACT_DEFINE_POST_RETIREMENT_WORK": {
        "why":"퇴직 후 근로소득은 연금 개시 전 소득공백을 줄일 수 있는 핵심 선택지입니다.",
        "help":["퇴직 후 일할 형태를 정합니다.","일할 계획이면 예상 월소득과 소득활동 종료 나이를 적습니다.","일하지 않을 계획이면 그 선택 자체를 FACT로 기록합니다."],
        "effort":"보통",
    },
    "ACT_DEFINE_HOUSING_PLAN": {
        "why":"주거 유지·이동·주택연금 방향은 은퇴 이후 현금흐름과 생활방식을 함께 바꿀 수 있습니다.",
        "help":["현재 거주형태를 확인합니다.","유지·다운사이징·이동 등 방향을 선택합니다.","자가라면 주택연금 활용 여부만 먼저 정리합니다."],
        "effort":"짧음",
    },
    "ACT_REVIEW_HEALTH_COVERAGE": {
        "why":"큰 병은 치료비뿐 아니라 일시적인 소득중단도 만들 수 있어 보유 보장을 먼저 확인할 필요가 있습니다.",
        "help":["3대 진단비 보장 구간을 확인합니다.","실손·수술·입원 보장 상태를 확인합니다.","치료로 일을 쉬게 될 때 생활비 마련 방법을 확인했는지 기록합니다."],
        "effort":"보통",
    },
    "ACT_DEFINE_CARE_PLAN": {
        "why":"장기 돌봄은 누가·어디서·어느 비용범위로 돌볼지를 미리 정해야 가족의 즉흥 결정을 줄일 수 있습니다.",
        "help":["주된 돌봄 담당을 정합니다.","주된 돌봄 장소를 정합니다.","MVP에서는 정확한 금액 대신 비용 구간까지만 기록합니다."],
        "effort":"보통",
    },
    "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST": {
        "why":"가족이 중요한 계정과 자산의 존재 자체를 모르면 긴급 상황에서 찾는 것부터 막힐 수 있습니다.",
        "help":["보험·계좌·가상자산·구독 등 존재하는 항목 종류를 정리합니다.","목록이 보관된 안전한 위치 유형을 기록합니다.","비밀번호·PIN·개인키·복구문구는 LIFE 2.0에 입력하지 않습니다."],
        "effort":"보통",
    },
    "ACT_START_FAMILY_WELLDYING_CONVERSATION": {
        "why":"의사표현이 어려운 상황에서는 가족이 본인의 선호를 알고 있는지가 실제 의사결정에 중요합니다.",
        "help":["가족과 실제로 한 번 대화합니다.","의료·돌봄·재산·장례·디지털 중 최소 한 가지 선호를 기록합니다.","법적 효력이 필요한 문서는 별도 전문가 절차를 확인합니다."],
        "effort":"보통",
    },
}

_SECRET_MARKERS=("password","passwd","passcode","pin","private_key","seed_phrase","recovery_phrase","mnemonic")

def _safe_fact_item(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    key=str(item.get("fact_key") or "")
    low=key.lower()
    if any(x in low for x in _SECRET_MARKERS):
        return None
    status=str(item.get("status") or "UNKNOWN")
    return {
        "fact_key":key,
        "status":status,
        "value":None if status=="UNKNOWN" else item.get("value"),
        "unit":item.get("unit"),
        "source_type":item.get("source_type"),
        "source_ref":item.get("source_ref"),
        "verification_level":item.get("verification_level"),
    }

def build_action_context(
    action_catalog_id: str,
    facts: dict[str, Any],
    awareness: dict[str, Any],
    dashboard: dict[str, Any],
) -> dict[str, Any]:
    if action_catalog_id not in ACTION_FORMS:
        raise KeyError(action_catalog_id)

    relevant=[]
    for key in ACTION_FACT_KEYS.get(action_catalog_id,()):
        safe=_safe_fact_item(facts.get(key))
        if safe:
            relevant.append(safe)

    question_id=ACTION_FORMS[action_catalog_id]["question_id"]
    awareness_state=(awareness.get("answers") or {}).get(question_id,"UNKNOWN_OR_NOT_PREPARED")
    top=next(
        (x for x in dashboard.get("top3",[]) if x.get("action_catalog_id")==action_catalog_id),
        None,
    )

    context={
        "action_catalog_id":action_catalog_id,
        "question_id":question_id,
        "awareness_state":awareness_state,
        "relevant_facts":relevant,
        "rule_reason_code":(top or {}).get("reason_code"),
        "priority_class":(top or {}).get("priority_class"),
        "source_policy":{
            "facts_are_authoritative":True,
            "unknown_must_remain_unknown":True,
            "ai_may_not_create_fact":True,
            "secret_values_forbidden":True,
        },
    }
    if action_catalog_id=="ACT_CALCULATE_INCOME_GAP":
        context["derived_preview"]=income_gap_preview(facts)
    return context

def explain_action(action_catalog_id: str, context: dict[str, Any]) -> dict[str, Any]:
    guide=ACTION_GUIDE[action_catalog_id]
    state=context["awareness_state"]
    if state=="PARTIAL":
        why_now="일부는 확인됐지만 아직 필요한 정보가 완성되지 않았습니다."
    elif state=="CONFIRMED":
        why_now="이미 확인된 항목입니다. 필요하면 최신 정보로 다시 점검할 수 있습니다."
    else:
        why_now="아직 확인되지 않은 항목이라 현재 Action 후보가 되었습니다."

    missing=[]
    preview=context.get("derived_preview")
    if isinstance(preview,dict) and not preview.get("ready",True):
        missing=list(preview.get("missing_actions") or [])

    return {
        "mode":"deterministic_fallback",
        "source_type":"RULE_DERIVED",
        "action_catalog_id":action_catalog_id,
        "why_now":why_now,
        "why_important":guide["why"],
        "completion_effect":"완료하면 관련 FACT와 Awareness 상태가 갱신되고 Top 3가 다시 계산됩니다.",
        "estimated_effort":guide["effort"],
        "missing_prerequisites":missing,
        "fact_refs":[x["fact_key"] for x in context["relevant_facts"]],
    }

def help_action(action_catalog_id: str, question: str, context: dict[str, Any]) -> dict[str, Any]:
    guide=ACTION_GUIDE[action_catalog_id]
    return {
        "mode":"deterministic_fallback",
        "source_type":"RULE_DERIVED",
        "action_catalog_id":action_catalog_id,
        "answer":"현재 단계에서는 아래 순서로 확인하면 됩니다.",
        "steps":guide["help"],
        "completion_note":"모르는 값을 임의로 추정하지 말고, 확인되지 않은 값은 확인 후 입력하세요.",
        "secret_warning":(
            "비밀번호·PIN·개인키·복구문구는 입력하지 마세요."
            if action_catalog_id=="ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST"
            else None
        ),
        "fact_refs":[x["fact_key"] for x in context["relevant_facts"]],
    }
