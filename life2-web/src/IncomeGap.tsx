import { useEffect, useRef, useState } from 'react';
import { incomeGapPayload, incomeGapFields } from './incomeGapInput';

type Field={key:string;label:string;type:'select'|'month'|'money';unit?:string;options?:{value:string;label:string}[];show_when?:{key:string;value:string};show_when_any?:{key:string;values:string[]}};
type Question={id:string;title:string;hint?:string;fields:Field[];show_when?:{key:string;value:string}};
type Action={code:string;title:string;reason:string;target_date:string;steps:string[];completion:string;support:string;worksheet?:string[]};
export type GapResult={answers?:Record<string,unknown>;persistence?:string;saved_at?:string;calendar:{last_salary_month:string|null;first_salary_free_month:string|null;nps_self_state?:string;nps_spouse_state?:string;nps_self_start_month:string|null;nps_spouse_start_month:string|null;both_nps_started_month:string|null;nps_wait_months:number|null};missing:{key:string;label:string}[];top3:Action[];notes:string[]};

export function IncomeGap({api,onBack,onMember,initial}: {api:string;onBack:()=>void;onMember:(payload:ReturnType<typeof incomeGapPayload>)=>Promise<void>|void;initial?:GapResult|null}){
  const [questions,setQuestions]=useState<Question[]>([]);
  const [index,setIndex]=useState(0);
  const [fields,setFields]=useState<Record<string,string>>(()=>initial?.answers?incomeGapFields(initial.answers):{});
  const [result,setResult]=useState<GapResult|null>(initial || null);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const [agreed,setAgreed]=useState(false);
  const [loading,setLoading]=useState(true);
  const [reload,setReload]=useState(0);
  const heading=useRef<HTMLHeadingElement>(null);

  useEffect(()=>{
    const controller=new AbortController();
    setLoading(true);setMessage('');
    fetch(`${api}/v1/income-gap/questions`,{signal:controller.signal}).then(async r=>{
      const body=await r.json();
      if(!r.ok || !body.ok || body.data?.total!==12 || !Array.isArray(body.data.questions)) throw new Error('CATALOG_FAILED');
      setQuestions(body.data.questions);
    }).catch(e=>{
      if(e.name!=='AbortError') setMessage('질문을 불러오지 못했습니다. 연결을 확인한 뒤 다시 시도해 주세요.');
    }).finally(()=>{if(!controller.signal.aborted) setLoading(false);});
    return ()=>controller.abort();
  },[api,reload]);
  useEffect(()=>{heading.current?.focus();},[index,result]);

  async function complete(){
    if(busy) return;
    setBusy(true);setMessage('');
    try{
      const r=await fetch(`${api}/v1/income-gap/preview`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(incomeGapPayload(fields))});
      const body=await r.json();
      if(!r.ok || !body.ok) throw new Error('입력한 월·금액을 확인해 주세요. 잘 모르는 값은 비워둘 수 있습니다.');
      setResult(body.data);
    }catch(e){setMessage(e instanceof Error?e.message:'결과를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.');}
    finally{setBusy(false);}
  }

  const question=questions[index];
  const applicable=!question?.show_when || fields[question.show_when.key]===question.show_when.value;
  const display=(value:string|null)=>value ?? '아직 확인하지 않음';
  return <section className="card incomeGap">
    <button className="backBtn gapNoPrint" disabled={busy} onClick={onBack}>‹ 홈으로</button>
    <span className="badge">{initial?'MY LIFE 소득공백 준비 초안':'소득공백 준비 · 로그인 없이 시작'}</span>
    {loading&&<p role="status">질문을 불러오고 있습니다.</p>}
    {!loading&&!question&&<button onClick={()=>setReload(reload+1)}>다시 불러오기</button>}
    {!loading&&question&&!result&&<>
      <div className="progress">{index+1} / {questions.length}</div>
      <h2 tabIndex={-1} ref={heading}>{question.title}</h2>
      <p className="hint">모르는 값은 비워두세요. 0은 실제로 없음을 확인했을 때만 입력합니다.</p>
      {question.hint&&<p className="ruleNote">{question.hint}</p>}
      <form onSubmit={e=>{e.preventDefault();setMessage('');if(index+1<questions.length)setIndex(index+1);else complete();}}>
        {!applicable&&<p>배우자와 함께 준비하는 경우에만 확인하는 항목입니다. 다음으로 넘어가세요.</p>}
        {applicable&&question.fields.map(f=>{
          if(f.show_when&&fields[f.show_when.key]!==f.show_when.value) return null;
          if(f.show_when_any&&!f.show_when_any.values.includes(fields[f.show_when_any.key])) return null;
          return <div className="fieldBlock" key={f.key}>
            <label className="fieldLabel" htmlFor={`gap-${f.key}`}>{f.label}{f.unit?` (${f.unit})`:''}</label>
            {f.type==='select'?<select id={`gap-${f.key}`} className="select" value={fields[f.key] || f.options?.[0]?.value || ''} disabled={busy} onChange={e=>setFields({...fields,[f.key]:e.target.value})}>
              {f.options?.map(o=><option value={o.value} key={o.value}>{o.label}</option>)}
            </select>:<input id={`gap-${f.key}`} className="textInput" type={f.type==='month'?'month':'number'} min={f.type==='month'?'2000-01':0} max={f.type==='month'?'2100-12':1000000} step={f.type==='money'?'0.0001':undefined} value={fields[f.key] || ''} disabled={busy} onChange={e=>setFields({...fields,[f.key]:e.target.value})}/>}
          </div>;
        })}
        <button type="submit" disabled={busy}>{busy?'결과 확인 중…':index+1===questions.length?'달력과 이번 달 행동 보기':'다음 ›'}</button>
      </form>
      {index>0&&<button className="secondaryBtn" disabled={busy} onClick={()=>{setMessage('');setIndex(index-1)}}>‹ 이전</button>}
      <p className="hint">결과 확인 시 입력한 정보를 서버로 보내 계산하고 저장하지 않습니다. 새로고침·이탈하면 사라집니다. 금융 로그인 정보는 입력하지 않습니다.</p>
    </>}
    {result&&<>
      <h2 tabIndex={-1} ref={heading}>월급이 끝난 뒤,<br/>이번 달 준비할 것</h2>
      <div className="previewBox">
        <b>월급이 없는 첫 달 → 본인 국민연금 시작</b>
        <span>{display(result.calendar.first_salary_free_month)} → {result.calendar.nps_self_state==='NONE'?'현재 수급 계획 없음':display(result.calendar.nps_self_start_month)}</span>
        <strong>{result.calendar.nps_wait_months===null?'기간 확인 필요':`${result.calendar.nps_wait_months}개월`}</strong>
        <small>본인 국민연금을 기다리는 기간입니다. 다른 수입까지 없다는 뜻은 아닙니다.</small>
      </div>
      {(result.calendar.nps_spouse_start_month || fields.household==='couple')&&<p>배우자 연금 시작: {result.calendar.nps_spouse_state==='NONE'?'현재 수급 계획 없음':display(result.calendar.nps_spouse_start_month)}<br/>두 사람 모두 연금 시작: {result.calendar.nps_self_state==='NONE'||result.calendar.nps_spouse_state==='NONE'?'현재 해당하지 않음':display(result.calendar.both_nps_started_month)}</p>}
      <h3>이번 달 먼저 할 행동</h3>
      {result.top3.length===0&&<p>추가 확인 행동이 없습니다. 계획이 바뀌면 입력을 다시 확인해 주세요.</p>}
      {result.top3.map((action,i)=><article className="action" key={action.code}>
        <b>{i+1}. {action.title}</b><p>{action.reason}</p>
        <span>권장 목표일: {action.target_date}</span>
        <ul>{action.steps.map(step=><li key={step}>{step}</li>)}</ul>
        <p><strong>완료 기준</strong><br/>{action.completion}</p>
        <p><strong>도움을 받을 내용</strong><br/>{action.support}</p>
        {action.worksheet&&<div className="gapWorksheet"><strong>지금 정리할 항목</strong><ul>{action.worksheet.map(row=><li key={row}>{row}</li>)}</ul></div>}
      </article>)}
      {result.missing.length>0&&<details><summary>아직 확인할 정보 {result.missing.length}개</summary><ul>{result.missing.map(m=><li key={m.key}>{m.label}</li>)}</ul></details>}
      <div className="ruleNote">{result.notes.map(note=><p key={note}>{note}</p>)}</div>
      <div className="gapNoPrint">
        <button onClick={()=>window.print()}>달력·행동 계획 인쇄 / PDF 저장</button>
        <button className="secondaryBtn" onClick={()=>{setResult(null);setIndex(0);setMessage('')}}>입력 확인·수정하기</button>
        <label className="multiChoice"><input type="checkbox" checked={agreed} onChange={e=>setAgreed(e.target.checked)} disabled={busy}/> 입력한 정보를 준비 초안으로 저장하는 데 동의합니다.</label>
        <p className="hint">동의하면 초안을 서버에 보관하고, 24시간 안에 로그인·가입해 MY LIFE로 연결할 수 있습니다. 연결하지 않은 초안은 만료됩니다. 확정 FACT나 Action 확인 완료로 처리하지 않습니다.</p>
        <button className="secondaryBtn" disabled={busy || !agreed} onClick={async()=>{if(!agreed || busy)return;setBusy(true);setMessage('');try{await onMember(incomeGapPayload(fields));}catch{setMessage('초안을 연결하지 못했습니다. 입력은 유지됩니다. 잠시 후 다시 시도해 주세요.');}finally{setBusy(false)}}}>동의한 초안을 MY LIFE에 저장하기</button>
        <p className="hint">자동 알림·상담 예약은 신청되지 않습니다.</p>
      </div>
    </>}
    {message&&<p className="statusMsg" role="alert">{message}</p>}
  </section>;
}
