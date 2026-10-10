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
