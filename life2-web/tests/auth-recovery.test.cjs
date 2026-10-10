const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {transformSync}=require('rolldown/experimental');
const source=transformSync('App.tsx',fs.readFileSync(require('node:path').join(__dirname,'../src/App.tsx'),'utf8').replace('import.meta.env.VITE_API_BASE',"'https://api.example.test'"),{jsx:{runtime:'automatic'}}).code.replace(/import \{([^}]+)\} from ([^;]+);/g,(_,names,mod)=>`const {${names.replace(/ as /g,':')}}=require(${mod});`).replace('export default function App','exports.default=function App');
const familyContext={exports:{}};
vm.runInNewContext(transformSync('familyConversation.ts',fs.readFileSync(require('node:path').join(__dirname,'../src/familyConversation.ts'),'utf8')).code.replace('export function familyConversationBlockReason','exports.familyConversationBlockReason=function'),familyContext);
function fixture(url,session=null,pending='',fetchResponse=null){
  let states=[],cursor=0,effects=[],first=true,listener,fetches=0,calls=[],tree;
  const storage=new Map(pending?[['life2.pending_handoff',pending]]:[]);
  const auth={getSession:async()=>({data:{session}}),onAuthStateChange:f=>{listener=f;return {data:{listener:{subscription:{unsubscribe(){}}}}}},resetPasswordForEmail:async(...args)=>{calls.push(['request',...args]);return {error:null}},updateUser:async(...args)=>{calls.push(['update',...args]);return {error:null}},signOut:async()=>({error:null})};
  const react={useState:init=>{const i=cursor++;if(first)states[i]=typeof init==='function'?init():init;return [states[i],v=>states[i]=v]},useRef:init=>{const i=cursor++;if(first)states[i]={current:init};return states[i]},useEffect:f=>{if(first)effects.push(f)}};
  const jsx=(type,props)=>({type,props});
  const context={exports:{},require:n=>n==='react'?react:n==='./familyConversation'?familyContext.exports:n==='./supabase'?{supabase:{auth},isPasswordRecovery:new URL(url).searchParams.get('auth')==='recovery'||new URLSearchParams(new URL(url).hash.slice(1)).get('type')==='recovery'}:{jsx,jsxs:jsx},URL,URLSearchParams,window:{location:new URL(url),history:{replaceState(){}}},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},setTimeout,fetch:async(url,options)=>{fetches++;return {ok:true,json:async()=>fetchResponse?fetchResponse(url,options):({data:{dashboard:{},top3:[]}})}}};
  vm.runInNewContext(source,context);
  const render=()=>{cursor=0;tree=context.exports.default();first=false;return tree};
  const nodes=()=>{const out=[];function walk(n){if(Array.isArray(n))n.forEach(walk);else if(n&&typeof n==='object'){out.push(n);walk(n.props?.children)}}walk(tree);return out};
  const text=n=>Array.isArray(n)?n.map(text).join(''):n&&typeof n==='object'?text(n.props?.children):n||'';
  const find=(type,label)=>nodes().find(n=>n.type===type&&(label instanceof RegExp?label.test(text(n)):text(n)===label));
  render();effects.forEach(f=>f());
  return {render,find,nodes,calls,storage,fetches:()=>fetches,event:(e,s)=>listener(e,s),flush:()=>new Promise(r=>setImmediate(r))};
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
