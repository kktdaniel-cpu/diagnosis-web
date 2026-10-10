from fastapi.testclient import TestClient

from app.actions import nps_normal_start_age
from app.auth import get_current_subject
from app.catalog import QUESTIONS
from app.main import app
from app.store import store

client=TestClient(app)

def make_member(subject="action-user"):
    created=client.post("/v1/awareness/runs",json={"age_band":"50_55","household_type":"couple"}).json()["data"]
    headers={"X-Awareness-Token":created["run_token"]}
    for q in QUESTIONS:
        r=client.put(
            f"/v1/awareness/runs/{created['run_id']}/answers/{q['id']}",
            json={"response":"UNKNOWN_OR_NOT_PREPARED"},
            headers=headers,
        )
        assert r.status_code==200
    done=client.post(f"/v1/awareness/runs/{created['run_id']}/complete",headers=headers).json()["data"]
    app.dependency_overrides[get_current_subject]=lambda:subject
    claim=client.post("/v1/me/awareness/claim",json={"handoff_token":done["handoff_token"]})
    assert claim.status_code==200
    return subject

def test_nps_start_age_rule():
    assert nps_normal_start_age(1968)==64
    assert nps_normal_start_age(1970)==65

def test_a1_complete_updates_fact_and_top3():
    subject=make_member("a1-user")
    try:
        start=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start")
        assert start.status_code==200
        aid=start.json()["data"]["action_instance_id"]

        saved=client.post(f"/v1/me/actions/{aid}/submit",json={"fields":{"retirement_age":60}})
        assert saved.status_code==200

        done=client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{aid}/complete",
            json={"fields":{"retirement_age":60}},
        )
        assert done.status_code==200
        data=done.json()["data"]
        assert data["action"]["status"]=="SELF_REPORTED_DONE"
        assert "work.primary_job_exit_age" in data["changes"]["fact_keys"]
        assert data["dashboard"]["confirmed_awareness_count"]==1
        assert all(x["action_catalog_id"]!="ACT_CONFIRM_RETIREMENT_AGE" for x in data["dashboard"]["top3"])
        assert store.facts[subject]["work.primary_job_exit_age"]["value"]==60
    finally:
        app.dependency_overrides.clear()

def test_a2_couple_complete_derives_start_age():
    subject=make_member("a2-user")
    try:
        start=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start")
        assert start.status_code==200
        aid=start.json()["data"]["action_instance_id"]
        fields={
            "birth_year_self":1968,
            "nps_monthly_self":1200000,
            "birth_year_spouse":1970,
            "nps_monthly_spouse":900000,
        }
        done=client.post(
            f"/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/{aid}/complete",
            json={"fields":fields},
        )
        assert done.status_code==200
        data=done.json()["data"]
        assert data["normalized"]["nps_start_age_self"]==64
        assert data["normalized"]["nps_start_age_spouse"]==65
        assert store.facts[subject]["pension.nps.start_age_self"]["source_type"]=="RULE_DERIVED"
        assert data["dashboard"]["confirmed_awareness_count"]==1
        assert all(x["action_catalog_id"]!="ACT_CHECK_NPS_ESTIMATE" for x in data["dashboard"]["top3"])
    finally:
        app.dependency_overrides.clear()

def test_a2_requires_spouse_fields_for_couple():
    make_member("a2-invalid")
    try:
        start=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start").json()["data"]
        bad=client.post(
            f"/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/{start['action_instance_id']}/complete",
            json={"fields":{"birth_year_self":1968,"nps_monthly_self":1000000}},
        )
        assert bad.status_code==422
        assert bad.json()["detail"]["field"]=="birth_year_spouse"
    finally:
        app.dependency_overrides.clear()


def test_duplicate_a1_completion_is_idempotent():
    subject=make_member("a1-idempotent")
    try:
        start=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start").json()["data"]
        aid=start["action_instance_id"]
        first=client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{aid}/complete",
            json={"fields":{"retirement_age":60}},
        )
        assert first.status_code==200
        second=client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{aid}/complete",
            json={"fields":{"retirement_age":65}},
        )
        assert second.status_code==200
        data=second.json()["data"]
        assert data["idempotent"] is True
        assert data["normalized"] is None
        assert data["changes"]["fact_keys"]==[]
        assert store.facts[subject]["work.primary_job_exit_age"]["value"]==60
    finally:
        app.dependency_overrides.clear()


def test_a4_budget_complete_stores_exact_target_in_10k_krw():
    subject=make_member("a4-user")
    try:
        start=client.post("/v1/me/actions/ACT_ESTIMATE_RETIREMENT_BUDGET/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_ESTIMATE_RETIREMENT_BUDGET/{start['action_instance_id']}/complete",
            json={"fields":{"retirement_budget_10k":320}},
        )
        assert done.status_code==200
        data=done.json()["data"]
        assert data["normalized"]["retirement_budget_10k"]==320
        fact=store.facts[subject]["cashflow.retirement_monthly_budget_target"]
        assert fact["value"]==320
        assert fact["unit"]=="10k_KRW_per_month"
    finally:
        app.dependency_overrides.clear()


def test_a6_uses_q23_q30_bands_not_exact_amounts():
    subject=make_member("a6-user")
    try:
        start=client.post("/v1/me/actions/ACT_SUMMARIZE_ASSETS_DEBT/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_SUMMARIZE_ASSETS_DEBT/{start['action_instance_id']}/complete",
            json={"fields":{
                "financial_asset_band":"100M_200M",
                "debt_band":"LT_100M"
            }},
        )
        assert done.status_code==200
        data=done.json()["data"]
        assert data["normalized"]=={
            "financial_asset_band":"100M_200M",
            "debt_band":"LT_100M"
        }
        facts=store.facts[subject]
        assert facts["asset.financial_liquid_band_q23"]["value"]=="100M_200M"
        assert facts["debt.total_band_q30"]["value"]=="LT_100M"
        assert "financial_asset_amount" not in facts
        assert "debt_amount" not in facts
    finally:
        app.dependency_overrides.clear()


def test_a3_ret_private_pension_yes_records_direct_facts_and_derived_end_age():
    subject=make_member("a3-user")
    try:
        start=client.post("/v1/me/actions/ACT_CHECK_RET_PRIVATE_PENSION/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_CHECK_RET_PRIVATE_PENSION/{start['action_instance_id']}/complete",
            json={"fields":{
                "has_ret_private_pension":"YES",
                "ret_private_monthly_10k":120,
                "ret_private_start_age":60,
                "ret_private_years":20
            }},
        )
        assert done.status_code==200
        data=done.json()["data"]
        assert data["normalized"]["ret_private_end_age"]==80
        facts=store.facts[subject]
        assert facts["pension.ret_private.monthly_household"]["value"]==120
        assert facts["pension.ret_private.start_age"]["value"]==60
        assert facts["pension.ret_private.duration_years"]["value"]==20
        assert facts["pension.ret_private.end_age"]["value"]==80
        assert facts["pension.ret_private.end_age"]["source_type"]=="RULE_DERIVED"
    finally:
        app.dependency_overrides.clear()


def test_a3_no_pension_records_explicit_absence_not_fake_money():
    subject=make_member("a3-none")
    try:
        start=client.post("/v1/me/actions/ACT_CHECK_RET_PRIVATE_PENSION/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_CHECK_RET_PRIVATE_PENSION/{start['action_instance_id']}/complete",
            json={"fields":{"has_ret_private_pension":"NO"}},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["pension.ret_private.exists"]["value"] is False
        assert "pension.ret_private.monthly_household" not in facts
    finally:
        app.dependency_overrides.clear()


def test_a7_no_work_creates_explicit_zero_income_fact():
    subject=make_member("a7-no-work")
    try:
        start=client.post("/v1/me/actions/ACT_DEFINE_POST_RETIREMENT_WORK/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_DEFINE_POST_RETIREMENT_WORK/{start['action_instance_id']}/complete",
            json={"fields":{"work_plan_type":"NO_WORK"}},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["work.post_retirement.plan_type"]["value"]=="NO_WORK"
        assert facts["work.post_retirement.monthly_income"]["value"]==0
        assert facts["work.post_retirement.monthly_income"]["source_ref"].endswith(":NO_WORK")
    finally:
        app.dependency_overrides.clear()


def test_a7_working_requires_income_end_age_and_health_insurance_type():
    make_member("a7-working")
    try:
        start=client.post("/v1/me/actions/ACT_DEFINE_POST_RETIREMENT_WORK/start").json()["data"]
        bad=client.post(
            f"/v1/me/actions/ACT_DEFINE_POST_RETIREMENT_WORK/{start['action_instance_id']}/complete",
            json={"fields":{"work_plan_type":"PART_TIME_GIG","post_retirement_income_10k":180}},
        )
        assert bad.status_code==422
        assert bad.json()["detail"]["field"]=="work_end_age"
    finally:
        app.dependency_overrides.clear()


def test_a10_care_lite_uses_cost_band_not_exact_amount():
    subject=make_member("a10-user")
    try:
        start=client.post("/v1/me/actions/ACT_DEFINE_CARE_PLAN/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_DEFINE_CARE_PLAN/{start['action_instance_id']}/complete",
            json={"fields":{
                "care_provider":"MIXED",
                "care_place":"HOME",
                "care_cost_band":"1M_2M",
                "care_coverage_status":"RESEARCHING"
            }},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["care.monthly_cost_band"]["value"]=="1M_2M"
        assert "care.monthly_cost_exact" not in facts
    finally:
        app.dependency_overrides.clear()


def test_a11_digital_lite_completes_without_secret_values():
    subject=make_member("a11-user")
    try:
        start=client.post("/v1/me/actions/ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST/{start['action_instance_id']}/complete",
            json={"fields":{
                "digital_categories":["INSURANCE","BANK_SECURITIES","CRYPTO"],
                "inventory_location_type":"DIGITAL_SECURE_FILE",
                "family_can_locate":"YES",
                "access_procedure_prepared":"YES"
            }},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["digital_legacy.inventory_categories"]["value"]==["INSURANCE","BANK_SECURITIES","CRYPTO"]
        assert facts["digital_legacy.family_can_locate"]["value"] is True
        assert facts["digital_legacy.access_procedure_prepared"]["value"] is True
        assert all("password" not in k.lower() for k in facts)
    finally:
        app.dependency_overrides.clear()


def test_a11_rejects_password_pin_private_key_seed_phrase_fields_even_on_draft():
    make_member("a11-secret")
    try:
        start=client.post("/v1/me/actions/ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST/start").json()["data"]
        for bad_key in ("password","pin","private_key","seed_phrase","recovery_phrase"):
            bad=client.post(
                f"/v1/me/actions/{start['action_instance_id']}/submit",
                json={"fields":{bad_key:"DO_NOT_STORE"}},
            )
            assert bad.status_code==422
            assert bad.json()["detail"]["code"]=="SECRET_NOT_ALLOWED"
    finally:
        app.dependency_overrides.clear()


def test_a11_requires_family_location_and_access_procedure_for_done():
    make_member("a11-incomplete")
    try:
        start=client.post("/v1/me/actions/ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST/start").json()["data"]
        bad=client.post(
            f"/v1/me/actions/ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST/{start['action_instance_id']}/complete",
            json={"fields":{
                "digital_categories":["INSURANCE"],
                "inventory_location_type":"PHYSICAL_SECURE_FILE",
                "family_can_locate":"NO",
                "access_procedure_prepared":"YES"
            }},
        )
        assert bad.status_code==422
        assert bad.json()["detail"]["field"]=="family_can_locate"
    finally:
        app.dependency_overrides.clear()


def test_a12_done_requires_conversation_and_at_least_one_preference_topic():
    subject=make_member("a12-user")
    try:
        start=client.post("/v1/me/actions/ACT_START_FAMILY_WELLDYING_CONVERSATION/start").json()["data"]
        bad=client.post(
            f"/v1/me/actions/ACT_START_FAMILY_WELLDYING_CONVERSATION/{start['action_instance_id']}/complete",
            json={"fields":{"conversation_done":"NO","preference_topics":["CARE"]}},
        )
        assert bad.status_code==422
        assert bad.json()["detail"]["field"]=="conversation_done"

        done=client.post(
            f"/v1/me/actions/ACT_START_FAMILY_WELLDYING_CONVERSATION/{start['action_instance_id']}/complete",
            json={"fields":{
                "conversation_done":"YES",
                "preference_topics":["CARE","MEDICAL_DECISION"]
            }},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["welldying.family_conversation_done"]["value"] is True
        assert facts["welldying.preference_topics_recorded"]["value"]==["CARE","MEDICAL_DECISION"]
    finally:
        app.dependency_overrides.clear()


def _complete_basic_prereqs_for_gap(subject: str):
    a1=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start").json()["data"]
    assert client.post(
        f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{a1['action_instance_id']}/complete",
        json={"fields":{"retirement_age":60}},
    ).status_code==200

    a2=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start").json()["data"]
    assert client.post(
        f"/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/{a2['action_instance_id']}/complete",
        json={"fields":{
            "birth_year_self":1968,
            "nps_monthly_self":1200000,
            "birth_year_spouse":1970,
            "nps_monthly_spouse":900000,
        }},
    ).status_code==200

    a4=client.post("/v1/me/actions/ACT_ESTIMATE_RETIREMENT_BUDGET/start").json()["data"]
    assert client.post(
        f"/v1/me/actions/ACT_ESTIMATE_RETIREMENT_BUDGET/{a4['action_instance_id']}/complete",
        json={"fields":{"retirement_budget_10k":320}},
    ).status_code==200


def test_a5_income_gap_is_rule_derived_from_confirmed_facts_only():
    subject=make_member("a5-user")
    try:
        _complete_basic_prereqs_for_gap(subject)

        form=client.get("/v1/me/actions/ACT_CALCULATE_INCOME_GAP")
        assert form.status_code==200
        preview=form.json()["data"]["preview"]
        assert preview["ready"] is True
        assert preview["retirement_age"]==60
        assert preview["nps_start_age_self"]==64
        assert preview["income_gap_years"]==4

        start=client.post("/v1/me/actions/ACT_CALCULATE_INCOME_GAP/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_CALCULATE_INCOME_GAP/{start['action_instance_id']}/complete",
            json={"fields":{"bridge_sources":["POST_RETIREMENT_WORK","FINANCIAL_ASSETS"]}},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["cashflow.income_gap_years_to_nps_self"]["value"]==4
        assert facts["cashflow.income_gap_years_to_nps_self"]["source_type"]=="RULE_DERIVED"
        assert facts["cashflow.income_gap_bridge_sources"]["value"]==["POST_RETIREMENT_WORK","FINANCIAL_ASSETS"]
        assert "monthly_shortfall" not in " ".join(facts.keys())
    finally:
        app.dependency_overrides.clear()


def test_a5_not_ready_without_prerequisite_facts():
    make_member("a5-blocked")
    try:
        form=client.get("/v1/me/actions/ACT_CALCULATE_INCOME_GAP")
        assert form.status_code==200
        preview=form.json()["data"]["preview"]
        assert preview["ready"] is False
        assert "ACT_CONFIRM_RETIREMENT_AGE" in preview["missing_actions"]

        start=client.post("/v1/me/actions/ACT_CALCULATE_INCOME_GAP/start").json()["data"]
        bad=client.post(
            f"/v1/me/actions/ACT_CALCULATE_INCOME_GAP/{start['action_instance_id']}/complete",
            json={"fields":{"bridge_sources":["FINANCIAL_ASSETS"]}},
        )
        assert bad.status_code==422
        assert bad.json()["detail"]["code"]=="PRECONDITION_REQUIRED"
    finally:
        app.dependency_overrides.clear()


def test_a8_renter_housing_plan_does_not_invent_reverse_mortgage_fact():
    subject=make_member("a8-renter")
    try:
        start=client.post("/v1/me/actions/ACT_DEFINE_HOUSING_PLAN/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_DEFINE_HOUSING_PLAN/{start['action_instance_id']}/complete",
            json={"fields":{
                "housing_tenure":"RENT",
                "housing_move_plan":"MOVE_LOWER_COST"
            }},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["housing.tenure_q16"]["value"]=="RENT"
        assert facts["housing.move_plan_q21"]["value"]=="MOVE_LOWER_COST"
        assert "housing.reverse_mortgage_plan_q19" not in facts
        assert "housing.reverse_mortgage_start_age" not in facts
    finally:
        app.dependency_overrides.clear()


def test_a8_owner_reverse_mortgage_plan_requires_start_age_when_planned():
    subject=make_member("a8-owner")
    try:
        start=client.post("/v1/me/actions/ACT_DEFINE_HOUSING_PLAN/start").json()["data"]
        bad=client.post(
            f"/v1/me/actions/ACT_DEFINE_HOUSING_PLAN/{start['action_instance_id']}/complete",
            json={"fields":{
                "housing_tenure":"OWNER_APARTMENT",
                "housing_move_plan":"KEEP",
                "reverse_mortgage_plan":"PLAN_USE"
            }},
        )
        assert bad.status_code==422
        assert bad.json()["detail"]["field"]=="reverse_mortgage_start_age"

        done=client.post(
            f"/v1/me/actions/ACT_DEFINE_HOUSING_PLAN/{start['action_instance_id']}/complete",
            json={"fields":{
                "housing_tenure":"OWNER_APARTMENT",
                "housing_move_plan":"KEEP",
                "reverse_mortgage_plan":"PLAN_USE",
                "reverse_mortgage_start_age":65
            }},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["housing.reverse_mortgage_start_age"]["value"]==65
    finally:
        app.dependency_overrides.clear()


def test_a9_health_review_preserves_unknown_band_without_money_guess():
    subject=make_member("a9-user")
    try:
        start=client.post("/v1/me/actions/ACT_REVIEW_HEALTH_COVERAGE/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_REVIEW_HEALTH_COVERAGE/{start['action_instance_id']}/complete",
            json={"fields":{
                "critical_illness_benefit_band":"NONE_UNKNOWN",
                "indemnity_coverage":"INDEMNITY_ONLY",
                "major_history":"CANCER",
                "income_stop_plan_checked":"NO"
            }},
        )
        assert done.status_code==200
        facts=store.facts[subject]
        assert facts["health.critical_illness_benefit_band_q12"]["status"]=="UNKNOWN"
        assert facts["health.critical_illness_benefit_band_q12"]["value"]=="NONE_UNKNOWN"
        assert facts["health.income_stop_plan_checked"]["value"] is False
        assert "health.coverage_score" not in facts
    finally:
        app.dependency_overrides.clear()


def test_member_facts_endpoint_returns_canonical_fact_map():
    subject=make_member("facts-read")
    try:
        start=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start").json()["data"]
        assert client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{start['action_instance_id']}/complete",
            json={"fields":{"retirement_age":61}},
        ).status_code==200
        got=client.get("/v1/me/facts")
        assert got.status_code==200
        facts=got.json()["data"]
        assert facts["work.primary_job_exit_age"]["value"]==61
        assert facts["work.primary_job_exit_age"]["status"]=="KNOWN"
    finally:
        app.dependency_overrides.clear()


def test_a1_a2_a4_prereqs_make_a5_eligible_for_top3():
    subject=make_member("a5-top3")
    try:
        _complete_basic_prereqs_for_gap(subject)

        a3=client.post("/v1/me/actions/ACT_CHECK_RET_PRIVATE_PENSION/start").json()["data"]
        assert client.post(
            f"/v1/me/actions/ACT_CHECK_RET_PRIVATE_PENSION/{a3['action_instance_id']}/complete",
            json={"fields":{"has_ret_private_pension":"NO"}},
        ).status_code==200

        a6=client.post("/v1/me/actions/ACT_SUMMARIZE_ASSETS_DEBT/start").json()["data"]
        done=client.post(
            f"/v1/me/actions/ACT_SUMMARIZE_ASSETS_DEBT/{a6['action_instance_id']}/complete",
            json={"fields":{
                "financial_asset_band":"30M_100M",
                "debt_band":"NONE"
            }},
        )
        assert done.status_code==200
        ids=[x["action_catalog_id"] for x in done.json()["data"]["dashboard"]["top3"]]
        assert "ACT_CALCULATE_INCOME_GAP" in ids
    finally:
        app.dependency_overrides.clear()


def test_action_can_wait_for_external_confirmation_and_resume():
    make_member("waiting-user")
    try:
        start=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start").json()["data"]
        aid=start["action_instance_id"]
        waiting=client.post(f"/v1/me/actions/{aid}/wait")
        assert waiting.status_code==200
        assert waiting.json()["data"]["status"]=="WAITING_EXTERNAL"

        dashboard=client.get("/v1/me/dashboard").json()["data"]
        top=next(x for x in dashboard["top3"] if x["action_catalog_id"]=="ACT_CHECK_NPS_ESTIMATE")
        assert top["status"]=="WAITING_EXTERNAL"

        resumed=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start")
        assert resumed.status_code==200
        assert resumed.json()["data"]["action_instance_id"]==aid
        assert resumed.json()["data"]["status"]=="IN_PROGRESS"
    finally:
        app.dependency_overrides.clear()


def test_dashboard_reports_five_domain_confirmed_counts_not_scores():
    make_member("domain-user")
    try:
        dash=client.get("/v1/me/dashboard")
        assert dash.status_code==200
        domains=dash.json()["data"]["domains"]
        assert set(domains)=={"cashflow_asset","work","health","housing","welldying"}
        assert sum(x["total"] for x in domains.values())==12
        assert all(x["confirmed"]==0 for x in domains.values())

        a1=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start").json()["data"]
        assert client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{a1['action_instance_id']}/complete",
            json={"fields":{"retirement_age":60}},
        ).status_code==200
        domains2=client.get("/v1/me/dashboard").json()["data"]["domains"]
        assert domains2["work"]["confirmed"]==1
    finally:
        app.dependency_overrides.clear()


def test_authenticated_member_without_awareness_gets_empty_dashboard_not_error():
    app.dependency_overrides[get_current_subject]=lambda:"no-awareness-user"
    try:
        dash=client.get("/v1/me/dashboard")
        assert dash.status_code==200
        data=dash.json()["data"]
        assert data["confirmed_awareness_count"]==0
        assert data["awareness_total"]==12
        assert data["top3"]==[]
    finally:
        app.dependency_overrides.clear()


def test_cross_user_cannot_access_foreign_action_instance():
    make_member("isolation-a")
    try:
        a=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start").json()["data"]
        foreign_action_id=a["action_instance_id"]
    finally:
        app.dependency_overrides.clear()

    make_member("isolation-b")
    try:
        submit=client.post(
            f"/v1/me/actions/{foreign_action_id}/submit",
            json={"fields":{"retirement_age":60}},
        )
        assert submit.status_code==404

        waiting=client.post(f"/v1/me/actions/{foreign_action_id}/wait")
        assert waiting.status_code==404

        complete=client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{foreign_action_id}/complete",
            json={"fields":{"retirement_age":60}},
        )
        assert complete.status_code==404

        summary=client.post(
            "/v1/me/ai/change-summary",
            json={"action_instance_id":foreign_action_id},
        )
        assert summary.status_code==404
    finally:
        app.dependency_overrides.clear()


def test_invalid_action_completion_rolls_back_without_fact_or_state_change():
    subject=make_member("rollback-user")
    try:
        start=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start").json()["data"]
        aid=start["action_instance_id"]
        before=client.get("/v1/me/dashboard").json()["data"]

        bad=client.post(
            f"/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/{aid}/complete",
            json={"fields":{
                "birth_year_self":1968,
                "nps_monthly_self":1200000
            }},
        )
        assert bad.status_code==422

        assert "pension.nps.monthly_self" not in store.facts.get(subject,{})
        item=store.action_instances[aid]
        assert item["status"]=="IN_PROGRESS"
        awareness=store.member_awareness(subject)
        assert awareness["answers"]["AWR_Q02_NPS"]=="UNKNOWN_OR_NOT_PREPARED"
        after=client.get("/v1/me/dashboard").json()["data"]
        assert before["confirmed_awareness_count"]==after["confirmed_awareness_count"]
    finally:
        app.dependency_overrides.clear()


def test_all_twelve_actions_expose_form_and_can_start():
    make_member("all-actions")
    try:
        action_ids=[
            "ACT_CONFIRM_RETIREMENT_AGE",
            "ACT_CHECK_NPS_ESTIMATE",
            "ACT_CHECK_RET_PRIVATE_PENSION",
            "ACT_ESTIMATE_RETIREMENT_BUDGET",
            "ACT_CALCULATE_INCOME_GAP",
            "ACT_SUMMARIZE_ASSETS_DEBT",
            "ACT_DEFINE_POST_RETIREMENT_WORK",
            "ACT_DEFINE_HOUSING_PLAN",
            "ACT_REVIEW_HEALTH_COVERAGE",
            "ACT_DEFINE_CARE_PLAN",
            "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
            "ACT_START_FAMILY_WELLDYING_CONVERSATION",
        ]
        for action_id in action_ids:
            form=client.get(f"/v1/me/actions/{action_id}")
            assert form.status_code==200, action_id
            assert form.json()["data"]["action_catalog_id"]==action_id
            start=client.post(f"/v1/me/actions/{action_id}/start")
            assert start.status_code==200, action_id
            assert start.json()["data"]["action_catalog_id"]==action_id
            assert start.json()["data"]["status"]=="IN_PROGRESS"
    finally:
        app.dependency_overrides.clear()


def test_partial_awareness_action_starts_in_verify_mode():
    created=client.post(
        "/v1/awareness/runs",
        json={"age_band":"50_55","household_type":"single"},
    ).json()["data"]
    headers={"X-Awareness-Token":created["run_token"]}
    for q in QUESTIONS:
        response="PARTIAL" if q["id"]=="AWR_Q02_NPS" else "CONFIRMED"
        saved=client.put(
            f"/v1/awareness/runs/{created['run_id']}/answers/{q['id']}",
            json={"response":response},
            headers=headers,
        )
        assert saved.status_code==200

    completed=client.post(
        f"/v1/awareness/runs/{created['run_id']}/complete",
        headers=headers,
    ).json()["data"]

    app.dependency_overrides[get_current_subject]=lambda:"verify-user"
    try:
        claim=client.post(
            "/v1/me/awareness/claim",
            json={"handoff_token":completed["handoff_token"]},
        )
        assert claim.status_code==200
        start=client.post("/v1/me/actions/ACT_CHECK_NPS_ESTIMATE/start")
        assert start.status_code==200
        assert start.json()["data"]["mode"]=="VERIFY"
    finally:
        app.dependency_overrides.clear()
