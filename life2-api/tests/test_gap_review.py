from copy import deepcopy
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_subject
from app.store import MemoryStore, StoreError
from app.gap_review import GapReviewRequest, prepare
import app.main as api

client=TestClient(app)

def ready():
    return dict(household='single',job_exit_month='2027-12',last_salary_month='2027-12',budget_monthly_10k=300,
                debt_monthly_10k=0,debt_in_budget='YES',nps_self={'state':'CONFIRMED','start_month':'2031-01','monthly_10k':150.5})

@pytest.fixture
def context(monkeypatch):
    memory=MemoryStore();monkeypatch.setattr(api,'store',memory)
    subject=str(uuid4());app.dependency_overrides[get_current_subject]=lambda:subject
    token=client.post('/v1/income-gap/handoffs',json={'answers':ready(),'consent':True}).json()['data']['handoff_token']
    pid=client.post('/v1/me/income-gap/claim',json={'handoff_token':token}).json()['data']['preparation_id']
    yield memory,subject,pid
    app.dependency_overrides.clear()

def confirm(pid, group, answers=None, revision=0, request_id=None):
    payload={'group':group,'answers':answers or ready(),'acknowledged':True,'expected_revision':revision,'request_id':request_id or str(uuid4())}
    response=client.post(f'/v1/me/income-gap/preparations/{pid}/confirm',json=payload)
    return response,payload

def test_draft_does_not_auto_confirm_and_bridge_waits_for_review(context):
    mem,subject,pid=context
    initial=client.get('/v1/me/income-gap/preparation').json()['data']
    assert initial['reviewed_groups']==0 and mem.member_facts(subject)=={}
    assert [a['code'] for a in initial['top3']]==['RETIREMENT','NPS','BUDGET']
    assert next(x for x in initial['reviews'] if x['group']=='BRIDGE')['ready'] is False
    assert confirm(pid,'BRIDGE',dict(ready(),bridge_methods=['LIQUID_ASSETS']))[0].status_code==409
    assert mem.member_facts(subject)=={}

def test_review_fact_action_and_focused_top3_loop(context):
    mem,subject,pid=context
    mem.facts[subject]={'legacy.example':{'status':'KNOWN','value':123}}
    for revision,group in enumerate(('RETIREMENT','NPS','BUDGET')):
        r,_=confirm(pid,group,revision=revision);assert r.status_code==200
        assert r.json()['data']['status']=='DONE'
        assert r.json()['data']['preparation']['reviewed_groups']==revision+1
    assert client.get('/v1/me/income-gap/preparation').json()['data']['top3'][0]['code']=='BRIDGE'
    r,_=confirm(pid,'BRIDGE',dict(ready(),bridge_methods=['LIQUID_ASSETS','WORK']),revision=3)
    assert r.status_code==200 and r.json()['data']['status']=='DONE'
    assert all(a['code'] not in ('RETIREMENT','NPS','BUDGET','BRIDGE') for a in r.json()['data']['preparation']['top3'])
    facts=mem.member_facts(subject)
    assert facts['legacy.example']['value']==123
    assert facts[f'gap.v1.{pid}.nps_wait_months']['value']==36
    assert facts[f'gap.v1.{pid}.nps_wait_months']['source_type']=='RULE_DERIVED'
    assert facts[f'gap.v1.{pid}.debt_monthly_10k']['value']==0
    assert facts[f'gap.v1.{pid}.nps_self.monthly_10k']['value']==150.5
    assert facts[f'gap.v1.{pid}.nps_spouse.monthly_10k']['status']=='NOT_APPLICABLE'
    assert len(mem.action_instances)==4 and len(mem.recent[subject])==4
    assert mem.member_run=={}  # Focused review does not manufacture Awareness completion.
    assert TestClient(app).get('/v1/me/income-gap/preparation').json()['data']['reviewed_groups']==4

def test_unknown_remains_partial_and_none_never_becomes_zero(context):
    mem,subject,pid=context
    unknown=dict(ready(),nps_self={'state':'UNKNOWN'})
    r,_=confirm(pid,'NPS',unknown);assert r.status_code==200
    assert r.json()['data']['status']=='PARTIAL'
    assert mem.member_facts(subject)[f'gap.v1.{pid}.nps_self.monthly_10k']=={
        'fact_key':f'gap.v1.{pid}.nps_self.monthly_10k','status':'UNKNOWN','value':None,'source_type':'USER_CONFIRMED',
        'source_ref':f'GAP_REVIEW:{pid}:NPS','verification_level':'SELF_REPORTED','unit':'만원/월'}
    assert next(x for x in r.json()['data']['preparation']['reviews'] if x['group']=='NPS')['status']=='PARTIAL'
    r,_=confirm(pid,'NPS',dict(ready(),nps_self={'state':'NONE'}),revision=1)
    assert r.json()['data']['status']=='DONE'
    assert mem.member_facts(subject)[f'gap.v1.{pid}.nps_self.monthly_10k']['value'] is None

def test_replay_and_payload_conflict_do_not_duplicate_or_mutate(context):
    mem,subject,pid=context
    r,payload=confirm(pid,'RETIREMENT');assert r.status_code==200
    snapshot=deepcopy(mem.__dict__)
    again=client.post(f'/v1/me/income-gap/preparations/{pid}/confirm',json=payload)
    assert again.status_code==200 and again.json()['data']['idempotent'] is True
    assert mem.__dict__==snapshot
    payload['answers']['job_exit_month']='2028-01'
    assert client.post(f'/v1/me/income-gap/preparations/{pid}/confirm',json=payload).status_code==409
    assert mem.__dict__==snapshot
    assert confirm(pid,'NPS',revision=0)[0].status_code==409
    assert mem.__dict__==snapshot

def test_upstream_change_invalidates_bridge_facts_and_action(context):
    mem,subject,pid=context
    for revision,group in enumerate(('RETIREMENT','NPS','BUDGET')):confirm(pid,group,revision=revision)
    bridge=dict(ready(),bridge_methods=['WORK']);r,original=confirm(pid,'BRIDGE',bridge,revision=3)
    action=r.json()['data']['action_instance_id']
    changed=dict(ready(),job_exit_month='2028-12',last_salary_month='2028-12')
    r,_=confirm(pid,'RETIREMENT',changed,revision=4)
    assert next(x for x in r.json()['data']['preparation']['reviews'] if x['group']=='BRIDGE')['status']=='REVIEW_DUE'
    assert mem.member_facts(subject)[f'gap.v1.{pid}.nps_wait_months']['status']=='STALE'
    assert mem.action_instances[action]['status']=='REVIEW_DUE'
    assert client.post(f'/v1/me/income-gap/preparations/{pid}/confirm',json=original).json()['data']['idempotent'] is True

def test_household_change_invalidates_nps_and_budget(context):
    mem,subject,pid=context
    for revision,group in enumerate(('RETIREMENT','NPS','BUDGET')):confirm(pid,group,revision=revision)
    r,_=confirm(pid,'RETIREMENT',dict(ready(),household='couple'),revision=3)
    reviews={x['group']:x for x in r.json()['data']['preparation']['reviews']}
    assert reviews['NPS']['status']=='REVIEW_DUE' and reviews['BUDGET']['status']=='REVIEW_DUE'
    assert reviews['BRIDGE']['ready'] is False
    assert mem.member_facts(subject)[f'gap.v1.{pid}.nps_household_scope']['status']=='STALE'

def test_group_patch_cannot_confirm_other_groups_or_another_member(context):
    mem,subject,pid=context
    r,_=confirm(pid,'RETIREMENT',dict(ready(),budget_monthly_10k=999))
    assert r.json()['data']['preparation']['answers']['budget_monthly_10k']==300
    assert not any(k.endswith('budget_monthly_10k') for k in mem.member_facts(subject))
    before=deepcopy(mem.__dict__)
    app.dependency_overrides[get_current_subject]=lambda:str(uuid4())
    assert confirm(pid,'NPS')[0].status_code==404
    assert mem.__dict__==before

def test_no_nps_end_is_not_applicable_not_zero(context):
    mem,subject,pid=context
    answers=dict(ready(),nps_self={'state':'NONE'},bridge_methods=['WORK'])
    for revision,group in enumerate(('RETIREMENT','NPS','BUDGET','BRIDGE')):
        r,_=confirm(pid,group,answers,revision=revision)
        assert r.status_code==200 and r.json()['data']['status']=='DONE'
    fact=mem.member_facts(subject)[f'gap.v1.{pid}.nps_wait_months']
    assert fact['status']=='NOT_APPLICABLE' and fact['value'] is None

@pytest.mark.parametrize('changes',[{'acknowledged':False},{'acknowledged':'true'},{'group':'UNKNOWN'},{'expected_revision':True},{'fact_rows':[]},{'user_id':'fake'}])
def test_closed_review_contract(context,changes):
    mem,subject,pid=context
    payload=dict(group='RETIREMENT',answers=ready(),acknowledged=True,expected_revision=0,request_id=str(uuid4()));payload.update(changes)
    assert client.post(f'/v1/me/income-gap/preparations/{pid}/confirm',json=payload).status_code==422
    assert mem.member_facts(subject)=={}

def test_concurrent_requests_have_one_winner(context):
    mem,subject,pid=context;record=mem.gap_review_record(subject,pid)
    def submit(group):
        payload=GapReviewRequest(group=group,answers=ready(),acknowledged=True,expected_revision=0,request_id=uuid4())
        try:
            mem.confirm_gap_review(subject,pid,group,0,str(payload.request_id),prepare(record,payload));return 'saved'
        except StoreError as e:return e.code
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(submit,['RETIREMENT','BUDGET']))
    assert sorted(results)==['GAP_REVISION_CONFLICT','saved']
    assert mem.gap_review_record(subject,pid)['revision']==1
    assert len(mem.recent[subject])==1 and len(mem.action_instances)==1

@pytest.mark.parametrize('group,patch,status',[
 ('PRIVATE_PENSION',{'private_pension':{'state':'NONE'}},'DONE'),
 ('PRIVATE_PENSION',{'private_pension':{'state':'CONFIRMED','start_month':'2028-01','monthly_10k':0}},'DONE'),
 ('PRIVATE_PENSION',{'private_pension':{'state':'UNKNOWN'}},'PARTIAL'),
 ('ASSETS',{'liquid_assets_band':'1000_5000','large_cost_state':'NONE'},'DONE'),
 ('ASSETS',{'liquid_assets_band':'1000_5000','large_cost_state':'PLANNED'},'PARTIAL'),
 ('WORK',{'post_work':{'state':'PLAN_ONLY','monthly_10k':250}},'PARTIAL'),
 ('WORK',{'post_work':{'state':'CONFIRMED','monthly_10k':0}},'DONE'),
 ('WORK',{'post_work':{'state':'NONE'}},'DONE'),
])
def test_followup_review_semantics(context,group,patch,status):
    mem,subject,pid=context
    r,_=confirm(pid,group,dict(ready(),**patch))
    assert r.status_code==200 and r.json()['data']['status']==status
    assert r.json()['data']['preparation']['review_total']==7
    facts=mem.member_facts(subject)
    assert all(k.startswith(f'gap.v1.{pid}.') for k in facts)
    assert not any('exact' in k or 'shortfall' in k for k in facts)
    if group=='ASSETS':assert facts[f'gap.v1.{pid}.liquid_assets_band']['value']=='1000_5000'
    if group=='WORK' and patch['post_work']['state']=='NONE':
        assert facts[f'gap.v1.{pid}.post_work.monthly_10k']['status']=='NOT_APPLICABLE'
        assert facts[f'gap.v1.{pid}.post_work.monthly_10k']['value'] is None
    replay=TestClient(app).get('/v1/me/income-gap/preparation').json()['data']
    assert next(x for x in replay['reviews'] if x['group']==group)['status']==status

def test_followup_change_invalidates_bridge(context):
    mem,subject,pid=context
    for rev,group in enumerate(('RETIREMENT','NPS','BUDGET')):assert confirm(pid,group,revision=rev)[0].status_code==200
    assert confirm(pid,'BRIDGE',dict(ready(),bridge_methods=['WORK']),revision=3)[0].status_code==200
    r,_=confirm(pid,'WORK',dict(ready(),post_work={'state':'CONFIRMED','monthly_10k':250}),revision=4)
    assert r.status_code==200
    assert next(x for x in r.json()['data']['preparation']['reviews'] if x['group']=='BRIDGE')['status']=='REVIEW_DUE'
    assert mem.member_facts(subject)[f'gap.v1.{pid}.bridge_methods']['status']=='STALE'
