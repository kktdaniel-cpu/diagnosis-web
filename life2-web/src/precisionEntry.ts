// Financial facts travel in a source-checked message, never in a URL or token.
export function connectPrecision(child: Window, url: string, prefill: Record<string, unknown>, done: (ok: boolean)=>void){
  const target=new URL(url);
  if(target.origin!=='https://diag.lpp20.com' || target.pathname!=='/life2-precision.html') throw new Error('PRECISION_TARGET_INVALID');
  let sent=false;
  const cleanup=(ok:boolean)=>{window.removeEventListener('message',receive);window.clearTimeout(timer);done(ok);};
  const receive=(event:MessageEvent)=>{
    if(event.origin!==target.origin || event.source!==child || event.data?.protocol!=='LIFE2_PREFILL_V1') return;
    if(event.data.type==='READY' && !sent){sent=true;child.postMessage({protocol:'LIFE2_PREFILL_V1',type:'PREFILL',prefill},target.origin);}
    else if(event.data.type==='APPLIED' && sent) cleanup(true);
  };
  window.addEventListener('message',receive);
  const timer=window.setTimeout(()=>cleanup(false),30000);
  child.location.href=target.href;
  return ()=>cleanup(false);
}
