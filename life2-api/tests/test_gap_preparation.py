from copy import deepcopy
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_subject
from app.store import store

client=TestClient(app)

def create():
    r=client.post('/v1/income-gap/handoffs',json={'answers':{'household':'single','last_salary_month':'2027-12','budget_monthly_10k':0},'consent':True})
    assert r.status_code==200
    assert r.headers['cache-control']=='no-store'
    return r.json()['data']['handoff_token']

def auth(subject):
    app.dependency_overrides[get_current_subject]=lambda:subject

@pytest.fixture(autouse=True)
def clear_auth():
    yield
    app.dependency_overrides.clear()

@pytest.mark.parametrize('payload',[{'answers':{}},{'answers':{},'consent':False},{'answers':{},'consent':'true'},{'answers':{'password':'reject'},'consent':True}])
def test_requires_explicit_consent_and_closed_input(payload):
    before=deepcopy(store.gap_preparations)
    assert client.post('/v1/income-gap/handoffs',json=payload).status_code==422
    assert store.gap_preparations==before

def test_claim_reload_is_idempotent_isolated_and_never_writes_facts_or_awareness():
    before={k:deepcopy(getattr(store,k)) for k in ('facts','member_run','action_instances','recent')}
    token=create()
    assert token not in store.gap_preparations
    assert sha256(token.encode()).hexdigest() in store.gap_preparations
    auth('gap-owner')
    first=client.post('/v1/me/income-gap/claim',json={'handoff_token':token})
    assert first.status_code==200 and first.json()['data']['idempotent'] is False
    second=client.post('/v1/me/income-gap/claim',json={'handoff_token':token})
    assert second.json()['data']['idempotent'] is True
    loaded=TestClient(app).get('/v1/me/income-gap/preparation').json()['data']
    assert loaded['answers']['budget_monthly_10k']==0
    assert loaded['answers']['nps_self']['monthly_10k'] is None
    assert loaded['persistence']=='MEMBER_PREPARATION' and loaded['fact_writes'] is False
    auth('gap-other')
    assert client.get('/v1/me/income-gap/preparation').json()['data'] is None
    assert client.post('/v1/me/income-gap/claim',json={'handoff_token':token}).status_code==409
    assert all(getattr(store,k)==v for k,v in before.items())

def test_expired_unclaimed_token_fails_but_claimed_replay_is_safe():
    token=create();store.gap_preparations[sha256(token.encode()).hexdigest()]['expires_at']=datetime.now(timezone.utc)-timedelta(seconds=1)
    auth('expiry-user');assert client.post('/v1/me/income-gap/claim',json={'handoff_token':token}).status_code==410

def test_claim_and_read_require_authentication(monkeypatch):
    from app import config
    monkeypatch.setattr(config,"SUPABASE_URL","https://example.supabase.co")
    monkeypatch.setattr(config,"SUPABASE_ANON_KEY","anon")
    assert client.get('/v1/me/income-gap/preparation').status_code==401
    assert client.post('/v1/me/income-gap/claim',json={'handoff_token':'x'*32}).status_code==401

def test_delete_account_removes_owned_preparation_only():
    first=create();second=create()
    store.claim_gap_preparation(first,'delete-gap-owner');store.claim_gap_preparation(second,'keep-gap-owner')
    store.delete_account('delete-gap-owner')
    assert store.member_gap_preparation('delete-gap-owner') is None
    assert store.member_gap_preparation('keep-gap-owner') is not None
