import { useRef, useState } from 'react';
import { incomeGapFields, incomeGapPayload } from './incomeGapInput';

export type ReviewField={key:string;label:string;type:string;unit?:string;options?:{value:string;label:string}[];household_only?:string;show_when?:{key:string;value:string}};
export type Review={group:string;title:string;status:string;ready:boolean;fields:ReviewField[]};
export type ReviewSubmission={group:string;answers:ReturnType<typeof incomeGapPayload>;acknowledged:true;expected_revision:number;request_id:string};

export function GapReview({review,answers,revision,onConfirm,onCancel}: {review:Review;answers:Record<string,unknown>;revision:number;onConfirm:(payload:ReviewSubmission)=>Promise<void>;onCancel:()=>void}){
  const [fields,setFields]=useState(()=>incomeGapFields(answers));
  const [ack,setAck]=useState(false);
  const [busy,setBusy]=useState(false);
  const [message,setMessage]=useState('');
  const attempt=useRef<{signature:string;id:string}|null>(null);
  async function submit(){
    if(!ack || busy || !review.ready)return;
    setBusy(true);setMessage('');
    try{
      const value=incomeGapPayload(fields);
      const signature=JSON.stringify({value,group:review.group,revision});
      if(attempt.current?.signature!==signature)attempt.current={signature,id:crypto.randomUUID()};
      await onConfirm({group:review.group,answers:value,acknowledged:true,expected_revision:revision,request_id:attempt.current!.id});
    }catch(e){setMessage(e instanceof Error?e.message:'확인 내용을 저장하지 못했습니다.');}
    finally{setBusy(false);}
  }
  return <section className="coachBox gapNoPrint">
    <h3>{review.title}</h3>
    <p>확인한 값과 아직 모르는 항목을 검토하세요. 이 화면의 확인은 자기확인 기록이며, 기관의 검증을 받은 정보라는 뜻은 아닙니다.</p>
    <form onSubmit={e=>{e.preventDefault();submit();}}>
      {review.fields.map(f=>{
        if(f.household_only&&fields.household!==f.household_only)return null;
        if(f.show_when&&fields[f.show_when.key]!==f.show_when.value)return null;
        const id=`review-${f.key}`;
        return <div className="fieldBlock" key={f.key}>
          <label className="fieldLabel" htmlFor={id}>{f.label}{f.unit?` (${f.unit})`:''}</label>
          {f.type==='select'?<select id={id} className="select" value={fields[f.key] || f.options?.[0]?.value || ''} disabled={busy} onChange={e=>setFields({...fields,[f.key]:e.target.value})}>{f.options?.map(o=><option value={o.value} key={o.value}>{o.label}</option>)}</select>
          :f.type==='multi_select'?<div className="multiChoices">{f.options?.map(o=>{
            const selected=(fields[f.key] || '').split('|').filter(Boolean);
            return <label className="multiChoice" key={o.value}><input type="checkbox" disabled={busy} checked={selected.includes(o.value)} onChange={()=>setFields({...fields,[f.key]:selected.includes(o.value)?selected.filter(v=>v!==o.value).join('|'):[...selected,o.value].join('|')})}/>{o.label}</label>;
          })}</div>
          :<input id={id} className="textInput" type={f.type==='month'?'month':'number'} min={f.type==='month'?'2000-01':0} max={f.type==='month'?'2100-12':1000000} step={f.type==='month'?undefined:'0.0001'} value={fields[f.key] || ''} disabled={busy} onChange={e=>setFields({...fields,[f.key]:e.target.value})}/>}
        </div>;
      })}
      <label className="multiChoice"><input type="checkbox" checked={ack} disabled={busy} onChange={e=>setAck(e.target.checked)}/> 입력 내용과 아직 모르는 항목을 검토했습니다.</label>
      <button disabled={busy || !ack || !review.ready} type="submit">{busy?'확인 내용 저장 중…':'검토한 정보 저장·다음 할 일 확인'}</button>
    </form>
    <p className="hint">미확인 정보가 있으면 부분 확인으로 남습니다. 0은 실제로 없음을 확인했을 때만 입력합니다.</p>
    <button className="secondaryBtn" disabled={busy} onClick={onCancel}>취소하고 돌아가기</button>
    {message&&<p className="statusMsg" role="alert">{message}</p>}
  </section>;
}
