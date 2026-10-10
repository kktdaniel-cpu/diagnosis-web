from app.top3 import select_top3
from app.catalog import QUESTIONS

def all_state(state):
    return {q["id"]:state for q in QUESTIONS}

def test_all_confirmed_empty():
    assert select_top3(all_state("CONFIRMED")) == []

def test_unknown_selects_one_p0_and_foundations():
    result=select_top3(all_state("UNKNOWN_OR_NOT_PREPARED"))
    assert len(result)==3
    assert sum(1 for x in result if x["priority_class"]=="P0")==1
    assert result[0]["action_catalog_id"]=="ACT_DEFINE_CARE_PLAN"
    assert result[1]["action_catalog_id"]=="ACT_CONFIRM_RETIREMENT_AGE"
    assert result[2]["action_catalog_id"]=="ACT_CHECK_NPS_ESTIMATE"

def test_partial_mode_verify():
    a=all_state("CONFIRMED")
    a["AWR_Q02_NPS"]="PARTIAL"
    result=select_top3(a)
    assert result[0]["mode"]=="VERIFY"


def test_income_gap_hidden_until_a1_a2_a4_confirmed():
    a=all_state("CONFIRMED")
    a["AWR_Q05_INCOME_GAP"]="UNKNOWN_OR_NOT_PREPARED"
    a["AWR_Q01_RETIREMENT_AGE"]="UNKNOWN_OR_NOT_PREPARED"
    result=select_top3(a)
    assert all(x["action_catalog_id"]!="ACT_CALCULATE_INCOME_GAP" for x in result)


def test_income_gap_activates_after_a1_a2_a4_confirmed():
    a=all_state("CONFIRMED")
    a["AWR_Q05_INCOME_GAP"]="UNKNOWN_OR_NOT_PREPARED"
    result=select_top3(a)
    assert result
    assert result[0]["action_catalog_id"]=="ACT_CALCULATE_INCOME_GAP"


def test_top3_is_stable_even_if_answer_dict_order_changes():
    a=all_state("UNKNOWN_OR_NOT_PREPARED")
    forward=select_top3(a)
    reversed_answers=dict(reversed(list(a.items())))
    backward=select_top3(reversed_answers)
    assert [x["action_catalog_id"] for x in forward] == [x["action_catalog_id"] for x in backward]


def test_multiple_p0_candidates_still_emit_only_one_p0():
    a=all_state("CONFIRMED")
    for qid in ("AWR_Q10_CARE","AWR_Q11_DIGITAL_FAMILY_INFO","AWR_Q12_WELLDYING_CONVERSATION"):
        a[qid]="UNKNOWN_OR_NOT_PREPARED"
    result=select_top3(a)
    assert len(result)==3
    assert sum(1 for x in result if x["priority_class"]=="P0")==1
    assert result[0]["action_catalog_id"]=="ACT_DEFINE_CARE_PLAN"


def test_top3_has_no_duplicate_action_ids():
    result=select_top3(all_state("UNKNOWN_OR_NOT_PREPARED"))
    ids=[x["action_catalog_id"] for x in result]
    assert len(ids)==len(set(ids))


def test_eight_representative_personas_are_deterministic_and_bounded():
    personas=[]

    p1=all_state("UNKNOWN_OR_NOT_PREPARED")
    personas.append(p1)

    p2=all_state("CONFIRMED")
    personas.append(p2)

    p3=all_state("CONFIRMED")
    p3["AWR_Q02_NPS"]="PARTIAL"
    p3["AWR_Q03_RET_PRIVATE_PENSION"]="UNKNOWN_OR_NOT_PREPARED"
    personas.append(p3)

    p4=all_state("CONFIRMED")
    for qid in ("AWR_Q01_RETIREMENT_AGE","AWR_Q02_NPS","AWR_Q04_RETIREMENT_BUDGET","AWR_Q06_ASSETS_DEBT"):
        p4[qid]="UNKNOWN_OR_NOT_PREPARED"
    personas.append(p4)

    p5=all_state("CONFIRMED")
    p5["AWR_Q05_INCOME_GAP"]="UNKNOWN_OR_NOT_PREPARED"
    personas.append(p5)

    p6=all_state("CONFIRMED")
    p6["AWR_Q10_CARE"]="UNKNOWN_OR_NOT_PREPARED"
    p6["AWR_Q11_DIGITAL_FAMILY_INFO"]="UNKNOWN_OR_NOT_PREPARED"
    personas.append(p6)

    p7=all_state("CONFIRMED")
    p7["AWR_Q07_POST_RETIREMENT_WORK"]="PARTIAL"
    p7["AWR_Q08_HOUSING"]="UNKNOWN_OR_NOT_PREPARED"
    p7["AWR_Q09_HEALTH_COVERAGE"]="UNKNOWN_OR_NOT_PREPARED"
    personas.append(p7)

    p8=all_state("CONFIRMED")
    p8["AWR_Q12_WELLDYING_CONVERSATION"]="UNKNOWN_OR_NOT_PREPARED"
    personas.append(p8)

    for answers in personas:
        first=select_top3(answers)
        second=select_top3(dict(answers))
        assert first==second
        assert len(first)<=3
        ids=[x["action_catalog_id"] for x in first]
        assert len(ids)==len(set(ids))
        assert sum(1 for x in first if x["priority_class"]=="P0")<=1
