from fastapi.testclient import TestClient

from app.auth import get_current_subject
from app.catalog import QUESTIONS
from app.main import app

client=TestClient(app)


def _claim_all_unknown(subject: str):
    created=client.post(
        "/v1/awareness/runs",
        json={"age_band":"50_55","household_type":"couple"},
    ).json()["data"]
    headers={"X-Awareness-Token":created["run_token"]}
    for q in QUESTIONS:
        r=client.put(
            f"/v1/awareness/runs/{created['run_id']}/answers/{q['id']}",
            json={"response":"UNKNOWN_OR_NOT_PREPARED"},
            headers=headers,
        )
        assert r.status_code==200
    done=client.post(
        f"/v1/awareness/runs/{created['run_id']}/complete",
        headers=headers,
    ).json()["data"]
    app.dependency_overrides[get_current_subject]=lambda:subject
    claim=client.post(
        "/v1/me/awareness/claim",
        json={"handoff_token":done["handoff_token"]},
    )
    assert claim.status_code==200


def _complete(action_id: str, fields: dict):
    start=client.post(f"/v1/me/actions/{action_id}/start")
    assert start.status_code==200
    aid=start.json()["data"]["action_instance_id"]
    done=client.post(
        f"/v1/me/actions/{action_id}/{aid}/complete",
        json={"fields":fields},
    )
    assert done.status_code==200
    return done.json()["data"]


def test_release_gate_golden_path_awareness_to_a5_recompute_and_delete():
    subject="release-golden-user"
    _claim_all_unknown(subject)
    try:
        _complete("ACT_CONFIRM_RETIREMENT_AGE",{"retirement_age":60})
        _complete("ACT_CHECK_NPS_ESTIMATE",{
            "birth_year_self":1968,
            "nps_monthly_self":1200000,
            "birth_year_spouse":1970,
            "nps_monthly_spouse":900000,
        })
        _complete("ACT_ESTIMATE_RETIREMENT_BUDGET",{"retirement_budget_10k":320})

        # A5 becomes dependency-eligible after A1/A2/A4.
        preview=client.get("/v1/me/actions/ACT_CALCULATE_INCOME_GAP")
        assert preview.status_code==200
        assert preview.json()["data"]["preview"]["ready"] is True
        assert preview.json()["data"]["preview"]["income_gap_years"]==4

        # A6 is a higher-priority foundational Action, so complete it before
        # asserting that A5 is surfaced in the visible Top 3.
        a6=_complete("ACT_SUMMARIZE_ASSETS_DEBT",{
            "financial_asset_band":"100M_200M",
            "debt_band":"LT_100M",
        })
        assert a6["changes"]["top3_changed"] is True

        dash=client.get("/v1/me/dashboard")
        assert dash.status_code==200
        top_ids=[x["action_catalog_id"] for x in dash.json()["data"]["top3"]]
        assert "ACT_CALCULATE_INCOME_GAP" in top_ids

        a5=_complete("ACT_CALCULATE_INCOME_GAP",{
            "bridge_sources":["POST_RETIREMENT_WORK","FINANCIAL_ASSETS"]
        })
        assert a5["normalized"]["income_gap_years"]==4

        facts=client.get("/v1/me/facts")
        assert facts.status_code==200
        fact_map=facts.json()["data"]
        assert fact_map["work.primary_job_exit_age"]["status"]=="KNOWN"
        assert fact_map["pension.nps.start_age_self"]["value"]==64
        assert fact_map["cashflow.income_gap_years_to_nps_self"]["source_type"]=="RULE_DERIVED"

        final_dash=client.get("/v1/me/dashboard").json()["data"]
        assert final_dash["confirmed_awareness_count"]==5
        assert final_dash["domains"]["work"]["confirmed"]>=1
        assert final_dash["domains"]["cashflow_asset"]["confirmed"]>=4

        deleted=client.delete("/v1/me")
        assert deleted.status_code==200
        assert deleted.json()["data"]["deleted"] is True
    finally:
        app.dependency_overrides.clear()
