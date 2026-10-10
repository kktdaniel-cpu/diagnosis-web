import { useState } from 'react';

type Resp='CONFIRMED'|'PARTIAL'|'UNKNOWN_OR_NOT_PREPARED';
type Q={id:string;q:string;responses:Resp[]};
type Top={action_catalog_id:string;title:string;mode:string;priority_class:string};

const API=import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const labels:Record<Resp,string>={
  CONFIRMED:'확인했어요',
  PARTIAL:'일부만 알고 있어요',
  UNKNOWN_OR_NOT_PREPARED:'아직 잘 몰라요'
};

export default function App(){
  const [screen,setScreen]=useState<'landing'|'meta'|'quiz'|'result'>('landing');
  const [household,setHousehold]=useState<'single'|'couple'>('couple');
  const [qs,setQs]=useState<Q[]>([]);
  const [idx,setIdx]=useState(0);
  const [run,setRun]=useState('');
  const [top,setTop]=useState<Top[]>([]);
  const [busy,setBusy]=useState(false);

  async function start(){
    setBusy(true);
    const q=await fetch(`${API}/v1/awareness/questions?household_type=${household}`).then(r=>r.json());
    const rr=await fetch(`${API}/v1/awareness/runs`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({age_band:'50_55',household_type:household})
    }).then(r=>r.json());
    setQs(q.data.questions);
    setRun(rr.data.run_id);
    setIdx(0);
    setScreen('quiz');
    setBusy(false);
  }

  async function answer(resp:Resp){
    setBusy(true);
    await fetch(`${API}/v1/awareness/runs/${run}/answers/${qs[idx].id}`,{
      method:'PUT',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({response:resp})
    });
    if(idx+1<qs.length){
      setIdx(idx+1);
    }else{
      const d=await fetch(`${API}/v1/awareness/runs/${run}/complete`,{method:'POST'}).then(r=>r.json());
      setTop(d.data.top3);
      setScreen('result');
    }
    setBusy(false);
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
      <h2>가구 형태를 알려주세요</h2>
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
          <span>{x.mode==='VERIFY'?'일부 확인 · 이어서 확인':'새로 확인'} · {x.priority_class}</span>
        </div>
      )}
      <button>무료로 계속 관리하기</button>
      <p className="hint">회원가입 연결은 다음 Foundation slice에서 구현합니다.</p>
    </section>}
  </main>
}
