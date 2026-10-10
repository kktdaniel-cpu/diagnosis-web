import { useState } from 'react';
import { supabase } from './supabase';

type Resp='CONFIRMED'|'PARTIAL'|'UNKNOWN_OR_NOT_PREPARED';
type Q={id:string;q:string;responses:Resp[]};
type Top={action_catalog_id:string;title:string;mode:string;priority_class:string};
type Dashboard={
  confirmed_awareness_count:number;
  awareness_total:number;
  top3:Top[];
  in_progress:unknown[];
  recent_changes:unknown[];
};

const API=import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const labels:Record<Resp,string>={
  CONFIRMED:'확인했어요',
  PARTIAL:'일부만 알고 있어요',
  UNKNOWN_OR_NOT_PREPARED:'아직 잘 몰라요'
};

export default function App(){
  const [screen,setScreen]=useState<'landing'|'meta'|'quiz'|'result'|'auth'|'dashboard'>('landing');
  const [household,setHousehold]=useState<'single'|'couple'>('couple');
  const [ageBand,setAgeBand]=useState('50_55');
  const [qs,setQs]=useState<Q[]>([]);
  const [idx,setIdx]=useState(0);
  const [run,setRun]=useState('');
  const [runToken,setRunToken]=useState('');
  const [handoffToken,setHandoffToken]=useState('');
  const [top,setTop]=useState<Top[]>([]);
  const [dashboard,setDashboard]=useState<Dashboard|null>(null);
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [authMsg,setAuthMsg]=useState('');
  const [busy,setBusy]=useState(false);

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
        setScreen('result');
      }
    } finally {
      setBusy(false);
    }
  }

  async function claimWithToken(accessToken:string){
    const r=await fetch(`${API}/v1/me/awareness/claim`,{
      method:'POST',
      headers:{
        'Content-Type':'application/json',
        'Authorization':`Bearer ${accessToken}`
      },
      body:JSON.stringify({handoff_token:handoffToken})
    });
    const body=await r.json();
    if(!r.ok) throw new Error(body?.detail?.code || 'CLAIM_FAILED');
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
      await claimWithToken(data.session.access_token);
      return;
    }
    setScreen('auth');
  }

  async function signUp(){
    if(!supabase) return;
    setBusy(true);
    setAuthMsg('');
    try{
      const {data,error}=await supabase.auth.signUp({email,password});
      if(error) throw error;
      if(data.session){
        await claimWithToken(data.session.access_token);
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
      await claimWithToken(data.session.access_token);
    }catch(e){
      setAuthMsg(e instanceof Error ? e.message : '로그인 중 오류가 발생했습니다.');
    }finally{
      setBusy(false);
    }
  }

  async function signOut(){
    if(supabase) await supabase.auth.signOut();
    setDashboard(null);
    setScreen('landing');
  }

  return <main className="app">
    {screen==='landing'&&<section className="hero">
      <span className="badge">LIFE 2.0</span>
      <h1>내 노후,<br/>얼마나 준비되어 있을까요?</h1>
      <p>연금·소득·건강·일자리·주거·가족 준비까지 12가지 질문으로 먼저 확인해 보세요.</p>
      <button onClick={()=>setScreen('meta')}>3분 노후준비 체크하기</button>
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
      <h2>계속 관리하려면 가입해 주세요</h2>
      <p>지금 확인한 3가지와 진행상태를 저장합니다.</p>
      <label className="fieldLabel">이메일</label>
      <input className="textInput" type="email" value={email} onChange={e=>setEmail(e.target.value)} autoComplete="email"/>
      <label className="fieldLabel">비밀번호</label>
      <input className="textInput" type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/>
      <button disabled={busy || !email || password.length<6} onClick={signUp}>무료 회원가입</button>
      <button className="secondaryBtn" disabled={busy || !email || !password} onClick={signIn}>기존 회원 로그인</button>
      {authMsg&&<p className="statusMsg">{authMsg}</p>}
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
      {dashboard.top3.map((x,i)=>
        <div className="action" key={x.action_catalog_id}>
          <b>{i+1}. {x.title}</b>
          <span>{x.mode==='VERIFY'?'확인 이어가기':'새로 준비하기'}</span>
        </div>
      )}
      <p className="hint">다음 구현 단계에서 Action 상세·FACT 저장이 연결됩니다.</p>
    </section>}
  </main>
}
