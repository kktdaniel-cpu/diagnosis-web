from datetime import date
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.income_gap import IncomeGapInput, build_preview
from app.store import store

client = TestClient(app)


def ready(**changes):
    data = dict(household="single", job_exit_month="2027-12", last_salary_month="2027-12",
                budget_monthly_10k=300, debt_monthly_10k=0, debt_in_budget="YES",
                nps_self={"state": "CONFIRMED", "start_month": "2031-01", "monthly_10k": 100},
                private_pension={"state": "NONE"}, post_work={"state": "NONE"},
                liquid_assets_band="1000_5000", large_cost_state="NONE", family_discussion="DONE")
    data.update(changes)
    return data


def test_catalog_and_anonymous_unknown_preview_do_not_touch_member_store():
    before = deepcopy(store.__dict__)
    catalog = client.get('/v1/income-gap/questions').json()['data']
    assert catalog['total'] == 12
    assert len({q['id'] for q in catalog['questions']}) == 12
    r = client.post('/v1/income-gap/preview', json={})
    assert r.status_code == 200
    assert r.headers['cache-control'] == 'no-store'
    result = r.json()['data']
    assert result['calendar']['nps_wait_months'] is None
    assert result['answers']['budget_monthly_10k'] is None
    assert result['monthly_shortfall_10k'] is None
    assert result['total_bridge_need_10k'] is None
    assert [a['code'] for a in result['top3']] == ['RETIREMENT', 'NPS', 'BUDGET']
    assert result['persistence'] == 'NONE' and result['fact_writes'] is False
    assert all(len(a['worksheet']) == 3 for a in result['top3'])
    assert store.__dict__ == before


def test_confirmed_calendar_month_boundary_and_only_remaining_action():
    data = build_preview(IncomeGapInput(**ready()), today=date(2026, 10, 13))
    assert data['calendar']['first_salary_free_month'] == '2028-01'
    assert data['calendar']['nps_wait_months'] == 36
    assert data['calendar']['status'] == 'RULE_DERIVED'
    assert data['calendar']['source_refs'] == ['last_salary_month', 'nps_self.start_month']
    assert [a['code'] for a in data['top3']] == ['BRIDGE']
    assert data['top3'][0]['target_date'] == '2026-11-12'
    assert data['monthly_shortfall_10k'] is None
    assert data['answers']['liquid_assets_band'] == '1000_5000'


@pytest.mark.parametrize('start,months', [('2027-12', 0), ('2028-01', 0), ('2028-02', 1), ('2031-01', 36)])
def test_calendar_never_goes_negative(start, months):
    data = client.post('/v1/income-gap/preview', json=ready(nps_self={"state": "CONFIRMED", "start_month": start, "monthly_10k": 100})).json()['data']
    assert data['calendar']['nps_wait_months'] == months
    assert bool(data['top3']) is (months > 0)


def test_zero_is_confirmed_and_fractional_manwon_is_preserved():
    d = client.post('/v1/income-gap/preview', json=ready(budget_monthly_10k=0, nps_self={"state": "CONFIRMED", "start_month": "2031-01", "monthly_10k": 0}, post_work={"state": "CONFIRMED", "monthly_10k": 150.5})).json()['data']
    assert d['answers']['nps_self']['monthly_10k'] == 0
    assert d['answers']['budget_monthly_10k'] == 0
    assert d['answers']['post_work']['monthly_10k'] == 150.5
    assert not any(m['key'] in ('budget_monthly_10k', 'nps_self.monthly_10k') for m in d['missing'])
    assert d['monthly_shortfall_10k'] is None


def test_couple_calendar_keeps_spouse_start_and_both_start_separate():
    d = client.post('/v1/income-gap/preview', json=ready(household='couple', nps_spouse={"state": "CONFIRMED", "start_month": "2034-01", "monthly_10k": 80})).json()['data']
    assert d['calendar']['nps_self_start_month'] == '2031-01'
    assert d['calendar']['nps_spouse_start_month'] == '2034-01'
    assert d['calendar']['both_nps_started_month'] == '2034-01'
    assert d['calendar']['nps_wait_months'] == 36


def test_single_household_ignores_stale_spouse_information():
    d = client.post('/v1/income-gap/preview', json=ready(nps_spouse={"state": "CONFIRMED", "start_month": "2034-01", "monthly_10k": 80})).json()['data']
    assert d['answers']['nps_spouse']['state'] == 'UNKNOWN'
    assert d['answers']['nps_spouse']['monthly_10k'] is None
    assert d['calendar']['nps_spouse_start_month'] is None
    assert d['calendar']['both_nps_started_month'] is None


def test_explicit_no_pension_is_distinct_from_unknown_and_does_not_become_zero():
    d = client.post('/v1/income-gap/preview', json=ready(nps_self={'state': 'NONE'})).json()['data']
    assert d['calendar']['nps_self_state'] == 'NONE'
    assert d['calendar']['nps_wait_months'] is None
    assert d['answers']['nps_self']['monthly_10k'] is None
    assert not any(a['code'] == 'NPS' for a in d['top3'])
    assert any(a['code'] == 'ALTERNATIVE_INCOME' for a in d['top3'])


def test_partially_confirmed_pension_still_requires_amount_and_no_shortfall_estimate():
    d = client.post('/v1/income-gap/preview', json=ready(nps_self={'state': 'CONFIRMED', 'start_month': '2031-01'})).json()['data']
    assert d['calendar']['nps_wait_months'] == 36
    assert d['top3'][0]['code'] == 'NPS'
    assert {'key': 'nps_self.monthly_10k', 'label': '본인 국민연금 월 예상액'} in d['missing']
    assert d['monthly_shortfall_10k'] is None


def test_unincluded_debt_and_planned_income_remain_followups():
    d = client.post('/v1/income-gap/preview', json=ready(debt_monthly_10k=70, debt_in_budget='NO', post_work={'state': 'PLAN_ONLY', 'monthly_10k': 250})).json()['data']
    assert [a['code'] for a in d['top3']] == ['BUDGET', 'WORK', 'BRIDGE']
    assert d['monthly_shortfall_10k'] is None


@pytest.mark.parametrize('change', [{'household': 'UNKNOWN'}, {'job_exit_month': None}, {'budget_monthly_10k': None}, {'nps_self': {'state': 'CONFIRMED', 'start_month': '2031-01'}}])
def test_bridge_action_waits_for_retirement_pension_and_budget_information(change):
    d = client.post('/v1/income-gap/preview', json=ready(**change)).json()['data']
    assert not any(a['code'] == 'BRIDGE' for a in d['top3'])


@pytest.mark.parametrize('bad', [
    {'last_salary_month': '2030-13'}, {'last_salary_month': '2030-1'}, {'last_salary_month': '2030-01-01'},
    {'budget_monthly_10k': -1}, {'budget_monthly_10k': True}, {'budget_monthly_10k': '300'},
    {'nps_self': {'state': 'UNKNOWN', 'monthly_10k': 100}},
    {'nps_self': {'state': 'NONE', 'start_month': '2030-01'}},
    {'password': 'synthetic-secret'}, {'user_id': 'cannot-claim'}, {'household': 'INVALID'},
])
def test_invalid_or_secret_or_identity_fields_rejected(bad):
    assert client.post('/v1/income-gap/preview', json=bad).status_code == 422


def test_repeating_preview_never_creates_facts_and_has_stable_priority():
    before = deepcopy(store.__dict__)
    first = client.post('/v1/income-gap/preview', json=ready()).json()['data']
    second = client.post('/v1/income-gap/preview', json=ready()).json()['data']
    assert first == second
    assert store.__dict__ == before
    assert not any(a['action_catalog_id'] == 'ACT_START_FAMILY_WELLDYING_CONVERSATION' for a in first['top3'])
