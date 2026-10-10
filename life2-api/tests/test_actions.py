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
