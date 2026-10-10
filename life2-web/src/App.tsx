import { useEffect, useRef, useState } from 'react';
import { supabase, isPasswordRecovery } from './supabase';

type Resp='CONFIRMED'|'PARTIAL'|'UNKNOWN_OR_NOT_PREPARED';
type Q={id:string;q:string;responses:Resp[]};
type Top={action_catalog_id:string;title:string;mode:string;priority_class:string;status?:string};
type Dashboard={
  confirmed_awareness_count:number;
  awareness_total:number;
  top3:Top[];
  in_progress:unknown[];
  recent_changes:unknown[];
  domains?:Record<string,{confirmed:number;partial:number;unknown_or_not_prepared:number;total:number}>;
};
type ActionField={
  key:string;
  label:string;
  type:'integer'|'select'|'multi_select';
  unit?:string;
  min?:number;
  max?:number;
  required?:boolean;
  options?:{value:string;label:string}[];
  show_when?:{key:string;value:string};
  show_when_not?:{key:string;value:string};
  show_when_owner?:boolean;
};
type ActionForm={
  action_catalog_id:string;
  question_id:string;
  title:string;
  description:string;
  fields:ActionField[];
  preview?:{
    ready:boolean;
    missing_actions?:string[];
    retirement_age?:number;
    nps_start_age_self?:number;
    income_gap_years?:number;
    retirement_budget_10k?:number;
    note?:string;
  };
};

const API=import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const PENDING_HANDOFF_KEY='life2.pending_handoff';
const labels:Record<Resp,string>={
  CONFIRMED:'확인했어요',
  PARTIAL:'일부만 알고 있어요',
  UNKNOWN_OR_NOT_PREPARED:'아직 잘 몰라요'
};
const supported=new Set([
  'ACT_CONFIRM_RETIREMENT_AGE',
  'ACT_CHECK_NPS_ESTIMATE',
  'ACT_CHECK_RET_PRIVATE_PENSION',
  'ACT_ESTIMATE_RETIREMENT_BUDGET',
  'ACT_CALCULATE_INCOME_GAP',
  'ACT_SUMMARIZE_ASSETS_DEBT',
  'ACT_DEFINE_POST_RETIREMENT_WORK',
  'ACT_DEFINE_HOUSING_PLAN',
  'ACT_REVIEW_HEALTH_COVERAGE',
  'ACT_DEFINE_CARE_PLAN',
  'ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST',
  'ACT_START_FAMILY_WELLDYING_CONVERSATION'
]);

export default function App(){
  const [screen,setScreen]=useState<'landing'|'meta'|'quiz'|'result'|'auth'|'dashboard'|'action'|'forgot'|'reset'>(isPasswordRecovery?'reset':'landing');
  const [household,setHousehold]=useState<'single'|'couple'>('couple');
  const [ageBand,setAgeBand]=useState('50_55');
  const [qs,setQs]=useState<Q[]>([]);
  const [idx,setIdx]=useState(0);
  const [run,setRun]=useState('');
  const [runToken,setRunToken]=useState('');
  const [handoffToken,setHandoffToken]=useState(()=>localStorage.getItem(PENDING_HANDOFF_KEY) || '');
  const [top,setTop]=useState<Top[]>([]);
  const [dashboard,setDashboard]=useState<Dashboard|null>(null);
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [authMsg,setAuthMsg]=useState('');
  const [newPassword,setNewPassword]=useState('');
  const [confirmPassword,setConfirmPassword]=useState('');
  const [recoveryReady,setRecoveryReady]=useState(false);
  const recovering=useRef(isPasswordRecovery);
  const [busy,setBusy]=useState(false);
  const [actionForm,setActionForm]=useState<ActionForm|null>(null);
  const [actionInstanceId,setActionInstanceId]=useState('');
  const [actionFields,setActionFields]=useState<Record<string,string|number|string[]>>({});
  const [actionMsg,setActionMsg]=useState('');
  const [coachMsg,setCoachMsg]=useState('');
  const [coachSteps,setCoachSteps]=useState<string[]>([]);
  const [changeSummary,setChangeSummary]=useState('');


  useEffect(()=>{
    if(!supabase) return;
    const client=supabase;
    let active=true;

    const finishAuth=async()=>{
      const {data}=await client.auth.getSession();
      if(!active) return;
      if(recovering.current){
        setScreen('reset');
        setRecoveryReady(Boolean(data.session));
        if(!data.session) setAuthMsg('재설정 링크가 만료되었거나 유효하지 않습니다. 재설정 메일을 다시 요청해 주세요.');
        return;
      }
      if(!data.session){
        if(new URL(window.location.href).searchParams.get('auth')==='confirmed'){
          setScreen('auth');
          setAuthMsg('이메일 링크가 만료되었거나 확인되지 않았습니다. 비밀번호 재설정 메일을 다시 요청하거나 로그인해 주세요.');
        }
        return;
      }
      const pending=localStorage.getItem(PENDING_HANDOFF_KEY) || '';
      try{
        if(pending) await claimWithToken(data.session.access_token,pending);
        else if(new URL(window.location.href).searchParams.get('auth')==='confirmed'){
          await loadDashboard(data.session.access_token);
        }
      }catch(e){
        if(active) setAuthMsg(e instanceof Error ? e.message : '회원 연결 중 오류가 발생했습니다.');
      }
    };

    finishAuth();
    const {data:listener}=client.auth.onAuthStateChange((event,session)=>{
      if(!active) return;
      if(event==='PASSWORD_RECOVERY' || recovering.current){
        recovering.current=true;
        setScreen('reset');
        setRecoveryReady(Boolean(session));
        return;
      }
      if(!session) return;
      const pending=localStorage.getItem(PENDING_HANDOFF_KEY) || '';
      if(pending){
        setTimeout(()=>claimWithToken(session.access_token,pending).catch(e=>{
          if(active) setAuthMsg(e instanceof Error ? e.message : '회원 연결 중 오류가 발생했습니다.');
        }),0);
      }
    });
    return ()=>{
      active=false;
      listener.subscription.unsubscribe();
    };
  },[]);

  async function accessToken(){
    if(!supabase) throw new Error('회원 시스템 연결 설정이 없습니다.');
    const {data}=await supabase.auth.getSession();
    if(!data.session) throw new Error('로그인이 필요합니다.');
    return data.session.access_token;
  }

  async function start(){
    setBusy(true);
    try{
      const q=await fetch(`${API}/v1/awareness/questions?household_type=${household}`).then(r=>r.json());
      const rr=await fetch(`${API}/v1/awareness/runs`,{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({age_band:ageBand,household_type:household})
      }).then(r=>r.json());
      setQs(q.data.questions);
      setRun(rr.data.run_id);
      setRunToken(rr.data.run_token);
      setIdx(0);
      setScreen('quiz');
    } finally {
      setBusy(false);
    }
  }

  async function answer(resp:Resp){
    setBusy(true);
    try{
      await fetch(`${API}/v1/awareness/runs/${run}/answers/${qs[idx].id}`,{
        method:'PUT',
        headers:{
          'Content-Type':'application/json',
          'X-Awareness-Token':runToken
        },
        body:JSON.stringify({response:resp})
      });
      if(idx+1<qs.length){
        setIdx(idx+1);
      }else{
        const d=await fetch(
          `${API}/v1/awareness/runs/${run}/complete`,
          {method:'POST',headers:{'X-Awareness-Token':runToken}}
        ).then(r=>r.json());
        setTop(d.data.top3);
        setHandoffToken(d.data.handoff_token);
        localStorage.setItem(PENDING_HANDOFF_KEY,d.data.handoff_token);
        setScreen('result');
      }
    } finally {
      setBusy(false);
    }
  }

  async function loadDashboard(token:string){
    const r=await fetch(`${API}/v1/me/dashboard`,{
      headers:{'Authorization':`Bearer ${token}`}
    });
    const body=await r.json();
    if(!r.ok) throw new Error(body?.detail?.code || 'DASHBOARD_FAILED');
    setDashboard(body.data);
    setScreen('dashboard');
  }

  async function claimWithToken(token:string,pendingToken?:string){
    const claimToken=pendingToken || handoffToken || localStorage.getItem(PENDING_HANDOFF_KEY) || '';
    if(!claimToken){
      await loadDashboard(token);
      return;
    }
    const r=await fetch(`${API}/v1/me/awareness/claim`,{
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'Authorization':`Bearer ${token}`
      },
      body:JSON.stringify({handoff_token:claimToken})
    });
    const body=await r.json();
    if(!r.ok) throw new Error(body?.detail?.code || 'CLAIM_FAILED');
    localStorage.removeItem(PENDING_HANDOFF_KEY);
    setHandoffToken('');
    setDashboard(body.data.dashboard);
    setScreen('dashboard');
  }

  async function continueToMember(){
    if(!supabase){
      setAuthMsg('회원 시스템 연결 설정이 아직 완료되지 않았습니다.');
      setScreen('auth');
      return;
    }
    const {data}=await supabase.auth.getSession();
    if(data.session){
      if(handoffToken) await claimWithToken(data.session.access_token);
      else await loadDashboard(data.session.access_token);
      return;
    }
    setScreen('auth');
  }

  async function signUp(){
    if(!supabase) return;
    setBusy(true);
    setAuthMsg('');
    try{
      if(handoffToken) localStorage.setItem(PENDING_HANDOFF_KEY,handoffToken);
      const {data,error}=await supabase.auth.signUp({
        email,
        password,
        options:{emailRedirectTo:`${window.location.origin}/?auth=confirmed`}
      });
      if(error) throw error;
      if(data.session){
        if(handoffToken) await claimWithToken(data.session.access_token);
        else await loadDashboard(data.session.access_token);
      }else{
        setAuthMsg('가입 확인 메일을 보냈습니다. 이메일 확인 후 로그인해 주세요.');
      }
    }catch(e){
      setAuthMsg(e instanceof Error ? e.message : '가입 중 오류가 발생했습니다.');
    }finally{
      setBusy(false);
    }
  }

  async function signIn(){
    if(!supabase) return;
    setBusy(true);
    setAuthMsg('');
    try{
      const {data,error}=await supabase.auth.signInWithPassword({email,password});
      if(error) throw error;
      if(handoffToken) await claimWithToken(data.session.access_token);
      else await loadDashboard(data.session.access_token);
    }catch(e){
      const message=e instanceof Error ? e.message : '';
      setAuthMsg(message==='Invalid login credentials'?'이메일 또는 비밀번호가 맞지 않습니다. 가입 이메일을 확인하거나 비밀번호를 재설정해 주세요.':message==='Email not confirmed'?'가입 확인 메일에서 이메일 인증을 완료해 주세요.':'로그인하지 못했습니다. 잠시 후 다시 시도해 주세요.');
    }finally{
      setBusy(false);
    }
  }

  function openForgot(){
    setPassword('');
    setAuthMsg('');
    setScreen('forgot');
  }

  async function requestPasswordReset(){
    if(!supabase) return;
    setBusy(true);
    setAuthMsg('');
    try{
      const {error}=await supabase.auth.resetPasswordForEmail(email.trim(),{
        redirectTo:`${window.location.origin}/?auth=confirmed`
      });
      if(error) throw error;
      setAuthMsg('입력한 이메일로 가입된 계정이 있다면 재설정 메일이 발송됩니다. 메일함과 스팸함을 확인해 주세요.');
    }catch{
      setAuthMsg('재설정 메일을 요청하지 못했습니다. 잠시 후 다시 시도해 주세요.');
    }finally{
      setBusy(false);
    }
  }

  async function saveNewPassword(){
    if(!supabase || !recoveryReady || busy) return;
    if(newPassword.length<8){setAuthMsg('새 비밀번호는 8자 이상으로 입력해 주세요.');return;}
    if(newPassword!==confirmPassword){setAuthMsg('두 비밀번호가 일치하지 않습니다.');return;}
    setBusy(true);
    setAuthMsg('');
    try{
      const {error}=await supabase.auth.updateUser({password:newPassword});
      if(error) throw error;
      // Recovery never claims a pending diagnosis before the user finishes this form.
      await supabase.auth.signOut({scope:'local'});
      recovering.current=false;
      setRecoveryReady(false);
      setNewPassword('');
      setConfirmPassword('');
      setPassword('');
      window.history.replaceState(null,'',window.location.pathname);
      setScreen('auth');
      setAuthMsg('비밀번호를 변경했습니다. 가입 이메일과 새 비밀번호로 로그인해 주세요.');
    }catch{
      setAuthMsg('비밀번호를 변경하지 못했습니다. 다른 비밀번호를 사용하거나 재설정 메일을 다시 요청해 주세요.');
    }finally{
      setBusy(false);
    }
  }

  async function signOut(){
    if(supabase) await supabase.auth.signOut();
    setDashboard(null);
    setActionForm(null);
    setChangeSummary('');
    setScreen('landing');
  }


  async function openPrecision(){
    setBusy(true);
    setActionMsg('');
    try{
      const token=await accessToken();
      const r=await fetch(`${API}/v1/me/precision/entry`,{
        headers:{'Authorization':`Bearer ${token}`}
      });
      const body=await r.json();
      if(!r.ok) throw new Error(body?.detail?.code || 'PRECISION_ENTRY_FAILED');
      window.open(body.data.url,'_blank','noopener,noreferrer');
    }catch(e){
      setActionMsg(e instanceof Error ? e.message : '정밀진단을 열지 못했습니다.');
    }finally{
      setBusy(false);
    }
  }

  async function openAction(item:Top){
    setActionMsg('');
    setCoachMsg('');
    setCoachSteps([]);
    if(!supported.has(item.action_catalog_id)){
      setActionMsg(item.action_catalog_id==='ACT_CALCULATE_INCOME_GAP'
        ? '소득공백 계산은 선행 FACT가 준비된 뒤 정밀 계산 엔진과 연결하는 다음 단계입니다.'
        : '이 Action은 다음 구현 순서입니다.');
      return;
    }
    setBusy(true);
    try{
      const token=await accessToken();
      const headers={Authorization:`Bearer ${token}`};
      const [formRes,startRes]=await Promise.all([
        fetch(`${API}/v1/me/actions/${item.action_catalog_id}`,{headers}),
        fetch(`${API}/v1/me/actions/${item.action_catalog_id}/start`,{method:'POST',headers}),
      ]);
      const formBody=await formRes.json();
      const startBody=await startRes.json();
      if(!formRes.ok) throw new Error(formBody?.detail?.code || 'ACTION_FORM_FAILED');
      if(!startRes.ok) throw new Error(startBody?.detail?.code || 'ACTION_START_FAILED');
      setActionForm(formBody.data);
      setActionInstanceId(startBody.data.action_instance_id);
      setActionFields(startBody.data.draft || {});
      setScreen('action');
    }catch(e){
      setActionMsg(e instanceof Error ? e.message : 'Action을 열지 못했습니다.');
    }finally{
      setBusy(false);
    }
  }

  async function saveActionDraft(){
    if(!actionInstanceId) return;
    setBusy(true);
    setActionMsg('');
    try{
      const token=await accessToken();
      const r=await fetch(`${API}/v1/me/actions/${actionInstanceId}/submit`,{
        method:'POST',
        headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
        body:JSON.stringify({fields:actionFields})
      });
      const body=await r.json();
      if(!r.ok) throw new Error(body?.detail?.code || 'ACTION_SAVE_FAILED');
      setActionMsg('저장했습니다. 나중에 이어서 할 수 있어요.');
    }catch(e){
      setActionMsg(e instanceof Error ? e.message : '저장하지 못했습니다.');
    }finally{
      setBusy(false);
    }
  }


  async function waitAction(){
    if(!actionInstanceId) return;
    setBusy(true);
    setActionMsg('');
    try{
      const token=await accessToken();
      const saveRes=await fetch(`${API}/v1/me/actions/${actionInstanceId}/submit`,{
        method:'POST',
        headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
        body:JSON.stringify({fields:actionFields})
      });
      const saveBody=await saveRes.json();
      if(!saveRes.ok) throw new Error(saveBody?.detail?.code || 'ACTION_SAVE_FAILED');

      const r=await fetch(`${API}/v1/me/actions/${actionInstanceId}/wait`,{
        method:'POST',
        headers:{'Authorization':`Bearer ${token}`}
      });
      const body=await r.json();
      if(!r.ok) throw new Error(body?.detail?.code || 'ACTION_WAIT_FAILED');

      const dashboardRes=await fetch(`${API}/v1/me/dashboard`,{
        headers:{'Authorization':`Bearer ${token}`}
      });
      const dashboardBody=await dashboardRes.json();
      if(!dashboardRes.ok) throw new Error(dashboardBody?.detail?.code || 'DASHBOARD_FAILED');
      setDashboard(dashboardBody.data);
      setActionForm(null);
      setActionInstanceId('');
      setActionFields({});
      setActionMsg('외부 확인 후 이어서 할 수 있도록 저장했습니다.');
      setScreen('dashboard');
    }catch(e){
      setActionMsg(e instanceof Error ? e.message : '대기 상태로 저장하지 못했습니다.');
    }finally{
      setBusy(false);
    }
  }

  function fieldVisible(f:ActionField){
    if(f.show_when_owner){
      const tenure=String(actionFields['housing_tenure'] ?? '');
      if(!['OWNER_APARTMENT','OWNER_OTHER'].includes(tenure)) return false;
    }
    if(f.show_when){
      return String(actionFields[f.show_when.key] ?? '')===f.show_when.value;
    }
    if(f.show_when_not){
      return String(actionFields[f.show_when_not.key] ?? '')!==f.show_when_not.value;
    }
    return true;
  }


  async function loadCoach(kind:'explain'|'help'){
    if(!actionForm) return;
    setBusy(true);
    setCoachMsg('');
    setCoachSteps([]);
    try{
      const token=await accessToken();
      const path=kind==='explain'?'/v1/me/ai/action-explain':'/v1/me/ai/action-help';
      const payload=kind==='explain'
        ?{action_catalog_id:actionForm.action_catalog_id}
        :{action_catalog_id:actionForm.action_catalog_id,question:'이 Action을 어디서 어떻게 확인하면 되나요?'};
      const r=await fetch(`${API}${path}`,{
        method:'POST',
        headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
        body:JSON.stringify(payload)
      });
      const body=await r.json();
      if(!r.ok) throw new Error(body?.detail?.code || 'COACH_FAILED');
      if(kind==='explain'){
        setCoachMsg(`${body.data.why_now} ${body.data.why_important}`);
        setCoachSteps(body.data.missing_prerequisites?.length
          ?['먼저 필요한 Action: '+body.data.missing_prerequisites.join(', ')]
          :[]);
      }else{
        setCoachMsg(body.data.answer || '확인 순서를 안내합니다.');
        setCoachSteps(body.data.steps || []);
        if(body.data.secret_warning) setCoachSteps([...(body.data.steps||[]),body.data.secret_warning]);
      }
    }catch(e){
      setCoachMsg(e instanceof Error ? e.message : '도움말을 불러오지 못했습니다.');
    }finally{
      setBusy(false);
    }
  }

  async function completeAction(){
    if(!actionForm || !actionInstanceId) return;
    setBusy(true);
    setActionMsg('');
    try{
      const token=await accessToken();
      const r=await fetch(
        `${API}/v1/me/actions/${actionForm.action_catalog_id}/${actionInstanceId}/complete`,
        {
          method:'POST',
          headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
          body:JSON.stringify({fields:actionFields})
        }
      );
      const body=await r.json();
      if(!r.ok){
        const field=body?.detail?.field;
        const label=actionForm.fields.find(item=>item.key===field)?.label;
        throw new Error(label ? `‘${label}’ 항목을 확인해 주세요.` : '입력 내용을 확인한 뒤 다시 완료해 주세요.');
      }
      setDashboard(body.data.dashboard);
      if(!body.data.idempotent){
        try{
          const summaryRes=await fetch(`${API}/v1/me/ai/change-summary`,{
            method:'POST',
            headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},
            body:JSON.stringify({action_instance_id:actionInstanceId})
          });
          const summaryBody=await summaryRes.json();
          setChangeSummary(summaryRes.ok ? summaryBody.data.message : '');
        }catch{
          setChangeSummary('');
        }
      }
      setActionForm(null);
      setActionInstanceId('');
      setActionFields({});
      setActionMsg(body.data.awareness_response==='PARTIAL'
        ? '점검 내용을 저장했습니다. 아직 모르는 항목은 확인 이어가기에 남겨 두었습니다.'
        : '확인 완료. 다음 할 일을 다시 계산했습니다.');
      setScreen('dashboard');
    }catch(e){
      setActionMsg(e instanceof Error ? e.message : '완료하지 못했습니다.');
    }finally{
      setBusy(false);
    }
  }

  return <main className="app">
    {screen==='landing'&&<section className="hero">
      <span className="badge">LIFE 2.0</span>
      <h1>내 노후,<br/>얼마나 준비되어 있을까요?</h1>
      <p>연금·소득·건강·일자리·주거·가족 준비까지 12가지 질문으로 먼저 확인해 보세요.</p>
      <button onClick={()=>setScreen('meta')}>3분 노후준비 체크하기</button>
      <button className="secondaryBtn" onClick={()=>{setHandoffToken('');setScreen('auth')}}>MY LIFE 이어보기</button>
      <small>회원가입 없이 시작 · 가장 먼저 할 3가지를 알려드려요</small>
    </section>}

    {screen==='meta'&&<section className="card">
      <div className="progress">시작 전</div>
      <h2>기본정보를 알려주세요</h2>
      <label className="fieldLabel">연령대</label>
      <select className="select" value={ageBand} onChange={e=>setAgeBand(e.target.value)}>
        <option value="45_49">45~49세</option>
        <option value="50_55">50~55세</option>
        <option value="56_59">56~59세</option>
        <option value="60_64">60~64세</option>
        <option value="65_PLUS">65세 이상</option>
      </select>
      <label className="fieldLabel">가구 형태</label>
      <label className="choice"><input type="radio" checked={household==='couple'} onChange={()=>setHousehold('couple')}/> 배우자와 함께 삽니다</label>
      <label className="choice"><input type="radio" checked={household==='single'} onChange={()=>setHousehold('single')}/> 혼자 삽니다</label>
      <button disabled={busy} onClick={start}>12문항 시작하기</button>
    </section>}

    {screen==='quiz'&&qs[idx]&&<section className="card">
      <div className="progress">{idx+1} / 12</div>
      <h2>{qs[idx].q}</h2>
      {qs[idx].responses.map((r:Resp)=>
        <button className="choiceBtn" disabled={busy} key={r} onClick={()=>answer(r)}>{labels[r]}</button>
      )}
      <p className="hint">잘 모르는 것은 실패가 아닙니다. 확인할 Action으로 바뀝니다.</p>
    </section>}

    {screen==='result'&&<section className="card">
      <div className="progress">첫 결과</div>
      <h2>지금 먼저 확인할 것은 3가지입니다.</h2>
      {top.map((x:Top,i:number)=>
        <div className="action" key={x.action_catalog_id}>
          <b>{i+1}. {x.title}</b>
          <span>{x.mode==='VERIFY'?'일부 확인 · 이어서 확인':'새로 확인'}</span>
        </div>
      )}
      <button disabled={busy} onClick={continueToMember}>무료로 계속 관리하기</button>
      <p className="hint">가입 후 이 결과를 다시 입력하지 않고 MY LIFE에 이어서 저장합니다.</p>
    </section>}

    {screen==='auth'&&<section className="card">
      <div className="progress">MY LIFE 2.0</div>
      <h2>{handoffToken?'계속 관리하려면 가입해 주세요':'MY LIFE에 로그인'}</h2>
      <p>{handoffToken?'지금 확인한 3가지와 진행상태를 저장합니다.':'저장한 준비상태와 Action을 이어서 확인합니다.'}</p>
      <p className="hint">로그인 아이디는 가입할 때 입력한 이메일 주소입니다.</p>
      <label className="fieldLabel" htmlFor="login-email">이메일 (로그인 아이디)</label>
      <input id="login-email" className="textInput" type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email"/>
      <label className="fieldLabel" htmlFor="login-password">비밀번호</label>
      <input id="login-password" className="textInput" type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/>
      {handoffToken&&<button disabled={busy || !email || password.length<6} onClick={signUp}>무료 회원가입</button>}
      <button className={handoffToken?'secondaryBtn':''} disabled={busy || !email || !password} onClick={signIn}>로그인</button>
      <button className="linkBtn" disabled={busy} onClick={openForgot}>아이디·비밀번호를 잊으셨나요?</button>
      {authMsg&&<p className="statusMsg" role="status">{authMsg}</p>}
    </section>}

    {screen==='forgot'&&<section className="card">
      <div className="progress">MY LIFE 2.0</div>
      <h2>아이디 확인 · 비밀번호 재설정</h2>
      <p>아이디는 가입 이메일입니다. 받은 메일함에서 LIFE 2.0 가입 확인 메일을 찾아보세요.</p>
      <p>가입 이메일을 입력하면 새 비밀번호를 설정할 수 있는 링크를 보내드립니다.</p>
      <form onSubmit={e=>{e.preventDefault();requestPasswordReset();}}>
        <label className="fieldLabel" htmlFor="reset-email">가입 이메일</label>
        <input id="reset-email" className="textInput" type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email" required/>
        <button type="submit" disabled={busy || !supabase || !email.trim()}>비밀번호 재설정 메일 보내기</button>
      </form>
      <button className="secondaryBtn" disabled={busy} onClick={()=>{setAuthMsg('');setScreen('auth');}}>로그인으로 돌아가기</button>
      {authMsg&&<p className="statusMsg" role="status">{authMsg}</p>}
    </section>}

    {screen==='reset'&&<section className="card">
      <div className="progress">MY LIFE 2.0</div>
      <h2>새 비밀번호 설정</h2>
      <p>8자 이상의 새 비밀번호를 입력해 주세요.</p>
      <form onSubmit={e=>{e.preventDefault();saveNewPassword();}}>
        <label className="fieldLabel" htmlFor="new-password">새 비밀번호</label>
        <input id="new-password" className="textInput" type="password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} autoComplete="new-password" minLength={8} required disabled={!recoveryReady}/>
        <label className="fieldLabel" htmlFor="confirm-password">새 비밀번호 확인</label>
        <input id="confirm-password" className="textInput" type="password" value={confirmPassword} onChange={e=>setConfirmPassword(e.target.value)} autoComplete="new-password" minLength={8} required disabled={!recoveryReady}/>
        <button type="submit" disabled={busy || !recoveryReady || newPassword.length<8 || newPassword!==confirmPassword}>비밀번호 변경</button>
      </form>
      <button className="secondaryBtn" disabled={busy} onClick={openForgot}>재설정 메일 다시 요청하기</button>
      {authMsg&&<p className="statusMsg" role="status">{authMsg}</p>}
    </section>}

    {screen==='dashboard'&&dashboard&&<section className="card">
      <div className="dashboardHead">
        <div>
          <div className="progress">MY LIFE 2.0</div>
          <h2>지금 먼저 할 일</h2>
        </div>
        <button className="linkBtn" onClick={signOut}>로그아웃</button>
      </div>
      <div className="confirmCount">확인 완료 <b>{dashboard.confirmed_awareness_count}/{dashboard.awareness_total}</b></div>
      {changeSummary&&<div className="changeSummary"><b>이번에 달라진 점</b><p>{changeSummary}</p></div>}
      {dashboard.domains&&<div className="domainGrid">
        {[
          ['cashflow_asset','돈·연금'],
          ['work','일'],
          ['health','건강·돌봄'],
          ['housing','주거'],
          ['welldying','가족·웰다잉']
        ].map(([key,label])=>{
          const d=dashboard.domains?.[key];
          return <div className="domainCard" key={key}>
            <span>{label}</span>
            <b>{d?.confirmed ?? 0}/{d?.total ?? 0}</b>
            <small>확인 완료</small>
          </div>
        })}
      </div>}
      {dashboard.top3.map((x,i)=>
        <button className="action actionButton" key={x.action_catalog_id} onClick={()=>openAction(x)} disabled={busy}>
          <b>{i+1}. {x.title}</b>
          <span>{x.status==='WAITING_EXTERNAL'?'외부 확인 중 · 이어하기':x.status==='IN_PROGRESS'?'진행 중 · 이어하기':x.mode==='VERIFY'?'확인 이어가기':'새로 준비하기'}</span>
        </button>
      )}
      <div className="precisionEntry">
        <b>더 정확한 계산이 필요하다면</b>
        <p>기존 정밀진단에서 연금·현금흐름·자산 시나리오를 확인할 수 있습니다.</p>
        <button className="secondaryBtn" disabled={busy} onClick={openPrecision}>정밀진단 열기</button>
      </div>
      {actionMsg&&<p className="statusMsg">{actionMsg}</p>}
      <p className="hint">점수가 아니라, 지금 확인하고 바꿀 일을 하나씩 완료합니다.</p>
    </section>}

    {screen==='action'&&actionForm&&<section className="card">
      <button className="backBtn" onClick={()=>setScreen('dashboard')}>← MY LIFE</button>
      <div className="progress">ACTION</div>
      <h2>{actionForm.title}</h2>
      <p>{actionForm.description}</p>
      <div className="coachActions">
        <button className="coachBtn" disabled={busy} onClick={()=>loadCoach('explain')}>왜 지금 해야 하나요?</button>
        <button className="coachBtn" disabled={busy} onClick={()=>loadCoach('help')}>어디서 확인하나요?</button>
      </div>
      {coachMsg&&<div className="coachBox">
        <b>AI Action Coach</b>
        <p>{coachMsg}</p>
        {coachSteps.length>0&&<ul>{coachSteps.map((x,i)=><li key={i}>{x}</li>)}</ul>}
        <small>현재는 검증된 FACT·Rule만 사용하는 안전한 기본 안내 모드입니다.</small>
      </div>}
      {actionForm.action_catalog_id==='ACT_CALCULATE_INCOME_GAP'&&actionForm.preview?.ready&&
        <div className="previewBox">
          <b>퇴직 → 본인 국민연금 개시 공백</b>
          <strong>{actionForm.preview.income_gap_years}년</strong>
          <span>{actionForm.preview.retirement_age}세 → {actionForm.preview.nps_start_age_self}세</span>
          <small>{actionForm.preview.note}</small>
        </div>
      }
      {actionForm.action_catalog_id==='ACT_CALCULATE_INCOME_GAP'&&!actionForm.preview?.ready&&
        <p className="statusMsg">먼저 퇴직시점·국민연금·은퇴생활비를 확인해 주세요.</p>
      }
      {actionForm.fields.filter(fieldVisible).map(f=>
        <div key={f.key} className="fieldBlock">
          <label className="fieldLabel">{f.label}{f.required?' *':''}</label>
          {f.type==='select'?
            <select
              className="select"
              value={String(actionFields[f.key] ?? '')}
              onChange={e=>setActionFields({...actionFields,[f.key]:e.target.value})}
            >
              <option value="">선택해 주세요</option>
              {(f.options||[]).map(o=><option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          :f.type==='multi_select'?
            <div className="multiChoices">
              {(f.options||[]).map(o=>{
                const values=Array.isArray(actionFields[f.key]) ? actionFields[f.key] as string[] : [];
                const checked=values.includes(o.value);
                return <label className="multiChoice" key={o.value}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={()=>{
                      const nextValues=checked?values.filter(v=>v!==o.value):[...values,o.value];
                      setActionFields({...actionFields,[f.key]:nextValues});
                    }}
                  />
                  <span>{o.label}</span>
                </label>
              })}
            </div>
          :
            <div className="inputWithUnit">
              <input
                className="textInput"
                type="number"
                min={f.min}
                max={f.max}
                value={actionFields[f.key] ?? ''}
                onChange={e=>setActionFields({...actionFields,[f.key]:e.target.value})}
              />
              {f.unit&&<span>{f.unit}</span>}
            </div>
          }
        </div>
      )}
      {actionForm.action_catalog_id==='ACT_CHECK_NPS_ESTIMATE'&&
        <p className="ruleNote">수령 시작 나이는 출생연도 기준으로 계산합니다. 1968년생은 만 64세, 1969년 이후 출생자는 만 65세입니다.</p>
      }
      {actionForm.action_catalog_id==='ACT_CHECK_RET_PRIVATE_PENSION'&&
        <p className="ruleNote">수령 개시 나이는 만 55세 이상만 입력할 수 있습니다. 수령 종료 나이는 개시 나이 + 수령 기간으로 계산합니다.</p>
      }
      {actionForm.action_catalog_id==='ACT_DEFINE_HOUSING_PLAN'&&
        <p className="ruleNote">주택연금 월지급액이나 주택가액은 여기서 임의 계산하지 않습니다. 현재 방향만 정리합니다.</p>
      }
      {actionForm.action_catalog_id==='ACT_REVIEW_HEALTH_COVERAGE'&&
        <p className="ruleNote">이 화면은 보유 상태 확인용입니다. 보험상품 추천이나 보장 적정성 점수는 만들지 않습니다.</p>
      }
      {actionForm.action_catalog_id==='ACT_DEFINE_CARE_PLAN'&&
        <p className="ruleNote">MVP에서는 정확한 간병비가 아니라 월 비용 구간까지만 정리합니다.</p>
      }
      {actionForm.action_catalog_id==='ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST'&&
        <p className="ruleNote">비밀번호·PIN·개인키·복구문구는 LIFE 2.0에 입력하거나 저장하지 않습니다. 존재 여부와 찾는 방법만 정리합니다.</p>
      }
      {actionForm.action_catalog_id==='ACT_START_FAMILY_WELLDYING_CONVERSATION'&&
        <p className="ruleNote">완료 기준은 가족과 실제 대화 1회 이상 + 선호사항 1개 이상 기록입니다.</p>
      }
      <button disabled={busy} onClick={completeAction}>확인 완료</button>
      <button className="secondaryBtn" disabled={busy} onClick={saveActionDraft}>저장하고 나중에</button>
      <button className="secondaryBtn" disabled={busy} onClick={waitAction}>자료 확인 후 이어하기</button>
      {actionMsg&&<p className="statusMsg">{actionMsg}</p>}
    </section>}
  </main>
}
