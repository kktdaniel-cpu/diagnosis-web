const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {transformSync}=require('rolldown/experimental');
const source=transformSync('App.tsx',fs.readFileSync(require('node:path').join(__dirname,'../src/App.tsx'),'utf8').replace('import.meta.env.VITE_API_BASE',"'https://api.example.test'"),{jsx:{runtime:'automatic'}}).code.replace(/import \{([^}]+)\} from ([^;]+);/g,(_,names,mod)=>`const {${names.replace(/ as /g,':')}}=require(${mod});`).replace('export default function App','exports.default=function App');
const familyContext={exports:{}};
vm.runInNewContext(transformSync('familyConversation.ts',fs.readFileSync(require('node:path').join(__dirname,'../src/familyConversation.ts'),'utf8')).code.replace('export function familyConversationBlockReason','exports.familyConversationBlockReason=function'),familyContext);
const inputContext={exports:{}};
vm.runInNewContext(transformSync('actionInput.ts',fs.readFileSync(require('node:path').join(__dirname,'../src/actionInput.ts'),'utf8')).code.replace(/export function /g,'exports.PLACEHOLDER=function ').replace(/exports.PLACEHOLDER=function (\w+)/g,'exports.$1=function $1'),inputContext);
function fixture(url,session=null,pending='',fetchResponse=null){
  let states=[],cursor=0,effects=[],first=true,listener,fetches=0,calls=[],tree;
  const children=[];const browserWindow={location:new URL(url),history:{replaceState(){}},open:()=>{const child={location:{},close(){this.closed=true;}};children.push(child);return child;}};
  const storage=new Map(pending?[['life2.pending_handoff',pending]]:[]);
  const auth={getSession:async()=>({data:{session}}),onAuthStateChange:f=>{listener=f;return {data:{listener:{subscription:{unsubscribe(){}}}}}},resetPasswordForEmail:async(...args)=>{calls.push(['request',...args]);return {error:null}},updateUser:async(...args)=>{calls.push(['update',...args]);return {error:null}},signOut:async()=>({error:null})};
  const react={useState:init=>{const i=cursor++;if(first)states[i]=typeof init==='function'?init():init;return [states[i],v=>states[i]=v]},useRef:init=>{const i=cursor++;if(first)states[i]={current:init};return states[i]},useEffect:f=>{if(first)effects.push(f)}};
  const jsx=(type,props)=>({type,props});
  const context={exports:{},require:n=>n==='react'?react:n==='./familyConversation'?familyContext.exports:n==='./actionInput'?inputContext.exports:n==='./precisionEntry'?{connectPrecision:(...args)=>calls.push(['precision',...args])}:n==='./supabase'?{supabase:{auth},isPasswordRecovery:new URL(url).searchParams.get('auth')==='recovery'||new URLSearchParams(new URL(url).hash.slice(1)).get('type')==='recovery'}:{jsx,jsxs:jsx},URL,URLSearchParams,window:browserWindow,localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},setTimeout,fetch:async(url,options)=>{fetches++;return {ok:true,json:async()=>fetchResponse?fetchResponse(url,options):({data:{dashboard:{},top3:[]}})}}};
  vm.runInNewContext(source,context);
  const render=()=>{cursor=0;tree=context.exports.default();first=false;return tree};
  const nodes=()=>{const out=[];function walk(n){if(Array.isArray(n))n.forEach(walk);else if(n&&typeof n==='object'){out.push(n);walk(n.props?.children)}}walk(tree);return out};
  const text=n=>Array.isArray(n)?n.map(text).join(''):n&&typeof n==='object'?text(n.props?.children):n||'';
  const find=(type,label)=>nodes().find(n=>n.type===type&&(label instanceof RegExp?label.test(text(n)):text(n)===label));
  render();effects.forEach(f=>f());
  return {render,find,nodes,calls,storage,children,browserWindow,fetches:()=>fetches,event:(e,s)=>listener(e,s),flush:()=>new Promise(r=>setImmediate(r))};
}
test('expired recovery link disables password change and does not claim pending results',async()=>{
 const f=fixture('https://web.test/?auth=recovery',null,'pending');await f.flush();f.render();assert.equal(f.find('button','비밀번호 변경').props.disabled,true);assert.equal(f.fetches(),0);assert.equal(f.storage.get('life2.pending_handoff'),'pending');
});
test('PASSWORD_RECOVERY takes priority over automatic claim',async()=>{
 const f=fixture('https://web.test/?auth=recovery',{access_token:'fake'},'pending');f.event('PASSWORD_RECOVERY',{access_token:'fake'});await f.flush();f.render();assert.ok(f.find('h2','새 비밀번호 설정'));assert.equal(f.fetches(),0);assert.equal(f.calls.length,0);
});
test('reset request needs only email and uses the exact recovery redirect',async()=>{
 const f=fixture('https://web.test/');await f.flush();f.render();f.find('button','MY LIFE 이어보기').props.onClick();await f.flush();f.render();f.find('button','아이디·비밀번호를 잊으셨나요?').props.onClick();f.render();f.nodes().find(n=>n.props?.id==='reset-email').props.onChange({target:{value:'someone@example.test'}});f.render();f.nodes().find(n=>n.type==='form').props.onSubmit({preventDefault(){}});await f.flush();f.render();assert.equal(f.calls[0][0],'request');assert.equal(f.calls[0][1],'someone@example.test');assert.equal(f.calls[0][2].redirectTo,'https://web.test/?auth=confirmed');assert.equal(f.calls.filter(c=>c[0]==='update').length,0);
});
test('mismatched passwords are blocked; successful update preserves pending diagnosis',async()=>{
 const f=fixture('https://web.test/?auth=recovery',{access_token:'fake'},'pending');await f.flush();f.render();f.nodes().find(n=>n.props?.id==='new-password').props.onChange({target:{value:'TestOnly123'}});f.nodes().find(n=>n.props?.id==='confirm-password').props.onChange({target:{value:'different'}});f.render();assert.equal(f.find('button','비밀번호 변경').props.disabled,true);f.nodes().find(n=>n.type==='form').props.onSubmit({preventDefault(){}});await f.flush();assert.equal(f.calls.length,0);f.render();f.nodes().find(n=>n.props?.id==='confirm-password').props.onChange({target:{value:'TestOnly123'}});f.render();f.nodes().find(n=>n.type==='form').props.onSubmit({preventDefault(){}});await f.flush();f.render();assert.equal(f.calls[0][0],'update');assert.ok(f.find('h2','계속 관리하려면 가입해 주세요'));assert.equal(f.fetches(),0);assert.equal(f.storage.get('life2.pending_handoff'),'pending');
});

test('confirmation callback with recovery fragment still opens reset form before claiming',async()=>{
 const f=fixture('https://web.test/?auth=confirmed#type=recovery',{access_token:'fake'},'pending');await f.flush();f.render();assert.ok(f.find('h2','새 비밀번호 설정'));assert.equal(f.fetches(),0);
});

test('failed email callback offers login and reset instead of silently showing landing',async()=>{
 const f=fixture('https://web.test/?auth=confirmed');await f.flush();f.render();assert.ok(f.find('h2','MY LIFE에 로그인'));assert.ok(f.find('button','아이디·비밀번호를 잊으셨나요?'));assert.equal(f.fetches(),0);
});

test('unfinished family conversation saves as a draft and returns to MY LIFE without completion',async()=>{
 const action='ACT_START_FAMILY_WELLDYING_CONVERSATION';
 const requests=[];
 const dashboard={confirmed_awareness_count:0,awareness_total:12,top3:[{action_catalog_id:action,title:'가족 대화 시작하기',mode:'CREATE',priority_class:'P1',status:'IN_PROGRESS'}],in_progress:[],recent_changes:[]};
 const form={action_catalog_id:action,title:'가족 대화 시작하기',description:'',fields:[{key:'conversation_done',label:'대화 여부',type:'select',options:[{value:'NO',label:'아직 못했습니다'},{value:'YES',label:'대화했습니다'}]},{key:'preference_topics',label:'선호사항',type:'multi_select',options:[{value:'CARE',label:'돌봄 방식'}]}]};
 const f=fixture('https://web.test/?auth=confirmed',{access_token:'fake'},'',(url,options)=>{
   requests.push({url,options});
   return {data:url.endsWith('/dashboard')?dashboard:url.endsWith('/start')?{action_instance_id:'test-instance',draft:{}}:url.endsWith('/submit')?{}:form};
 });
 await f.flush();f.render();
 await f.find('button',/가족 대화 시작하기/).props.onClick();f.render();
 f.nodes().find(n=>n.type==='select').props.onChange({target:{value:'NO'}});f.render();
 f.nodes().find(n=>n.type==='input'&&n.props.type==='checkbox').props.onChange();f.render();
 assert.equal(f.find('button','대화 후 확인 완료').props.disabled,true);
 await f.find('button','대화 후 확인 완료').props.onClick();
 assert.equal(requests.filter(r=>r.url.endsWith('/complete')).length,0);
 await f.find('button','저장하고 나중에').props.onClick();f.render();
 assert.ok(f.find('h2','지금 먼저 할 일'));
 const draft=requests.find(r=>r.url.endsWith('/submit'));
 assert.equal(JSON.parse(draft.options.body).fields.conversation_done,'NO');
 assert.deepEqual(JSON.parse(draft.options.body).fields.preference_topics,['CARE']);
});

test('digital list cannot complete until family knows the location and procedure',()=>{
 const reason=inputContext.exports.digitalListBlockReason;
 const fields={digital_categories:['EMAIL_SOCIAL'],inventory_location_type:'DIGITAL_SECURE_FILE',family_can_locate:'NO',access_procedure_prepared:'NO'};
 assert.match(reason('ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST',fields),/저장하고 나중에/);
 fields.family_can_locate='YES';assert.match(reason('ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST',fields),/절차/);
 fields.access_procedure_prepared='YES';assert.equal(reason('ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST',fields),null);
});
test('pension draft round trip keeps original won precision and converts only NPS amounts',()=>{
 const convert=inputContext.exports.pensionFields;
 const original={birth_year_self:1975,nps_monthly_self:1500001,nps_monthly_spouse:0};
 const display=convert('ACT_CHECK_NPS_ESTIMATE',original,false);
 assert.equal(display.nps_monthly_self,150.0001);assert.equal(display.nps_monthly_spouse,0);
 const stored=convert('ACT_CHECK_NPS_ESTIMATE',display,true);
 assert.equal(stored.nps_monthly_self,1500001);assert.equal(stored.birth_year_self,1975);
 assert.equal(convert('ACT_CHECK_NPS_ESTIMATE',{nps_monthly_self:'150.5',nps_monthly_spouse:''},true).nps_monthly_self,1505000);
 assert.equal(convert('ACT_CHECK_NPS_ESTIMATE',{nps_monthly_spouse:''},true).nps_monthly_spouse,'');
 assert.equal(convert('OTHER',original,true),original);
});
test('digital list draft returns to dashboard without marking incomplete preparation done',async()=>{
 const action='ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST',requests=[];
 const fields={digital_categories:['EMAIL_SOCIAL'],inventory_location_type:'DIGITAL_SECURE_FILE',family_can_locate:'NO',access_procedure_prepared:'NO'};
 const dashboard={confirmed_awareness_count:0,awareness_total:12,top3:[{action_catalog_id:action,title:'디지털 목록',mode:'CREATE',status:'IN_PROGRESS'}],in_progress:[],recent_changes:[]};
 const f=fixture('https://web.test/?auth=confirmed',{access_token:'fake'},'',(url,options)=>{
  requests.push({url,options});return {data:url.endsWith('/dashboard')?dashboard:url.endsWith('/start')?{action_instance_id:'digital-test',draft:fields}:url.endsWith('/submit')?{}:{action_catalog_id:action,title:'디지털 목록',description:'',fields:[]}};
 });
 await f.flush();f.render();await f.find('button',/디지털 목록/).props.onClick();f.render();
 assert.equal(f.find('button','확인 완료').props.disabled,true);
 await f.find('button','확인 완료').props.onClick();assert.equal(requests.filter(r=>r.url.endsWith('/complete')).length,0);
 await f.find('button','저장하고 나중에').props.onClick();f.render();assert.ok(f.find('h2','지금 먼저 할 일'));
 assert.deepEqual(JSON.parse(requests.find(r=>r.url.endsWith('/submit')).options.body).fields,fields);
});


test('precision entry opens a tab during the click and connects only the authorized prefill response',async()=>{
 const payload={household_type:'couple',nps_monthly_self:1500000};
 const f=fixture('https://web.test/?auth=confirmed',{access_token:'fake'},'',url=>({data:url.endsWith('/precision/entry')?{url:'https://diag.lpp20.com/life2-precision.html',handoff:'LIFE2_PREFILL_V1',prefill:payload}:{confirmed_awareness_count:12,awareness_total:12,top3:[],in_progress:[],recent_changes:[]}}));
 await f.flush();f.render();const pending=f.find('button','정밀진단 열기').props.onClick();
 assert.equal(f.children.length,1);await pending;
 const connected=f.calls.find(c=>c[0]==='precision');assert.equal(connected[1],f.children[0]);assert.equal(connected[2],'https://diag.lpp20.com/life2-precision.html');assert.deepEqual(connected[3],payload);
});
test('a blocked precision popup shows recovery guidance without requesting financial facts',async()=>{
 const f=fixture('https://web.test/?auth=confirmed',{access_token:'fake'},'',()=>({data:{confirmed_awareness_count:12,awareness_total:12,top3:[],in_progress:[],recent_changes:[]}}));
 await f.flush();f.render();const before=f.fetches();f.browserWindow.open=()=>null;await f.find('button','정밀진단 열기').props.onClick();f.render();assert.equal(f.fetches(),before);assert.ok(f.nodes().some(n=>typeof n.props?.children==='string'&&n.props.children.includes('팝업을 허용')));
});
