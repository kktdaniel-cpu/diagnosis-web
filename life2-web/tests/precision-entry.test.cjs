const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {transformSync}=require('rolldown/experimental');
const sender=transformSync('precisionEntry.ts',fs.readFileSync(path.join(__dirname,'../src/precisionEntry.ts'),'utf8')).code.replace('export function connectPrecision','exports.connectPrecision=function');
const receiver=fs.readFileSync(path.join(__dirname,'../../life2-precision.js'),'utf8');

test('sender checks origin and exact child window before sharing; waits for acknowledgement',()=>{
 let receive,timeout,removed=0,done=[];
 const posts=[],child={location:{},postMessage:(...a)=>posts.push(a)};
 const context={exports:{},URL,window:{addEventListener:(n,f)=>receive=f,removeEventListener:()=>removed++,setTimeout:f=>{timeout=f;return 1;},clearTimeout(){}}};
 vm.runInNewContext(sender,context);
 context.exports.connectPrecision(child,'https://diag.lpp20.com/life2-precision.html',{nps_monthly_self:1505001},ok=>done.push(ok));
 const msg={protocol:'LIFE2_PREFILL_V1',type:'READY'};
 receive({origin:'https://attacker.test',source:child,data:msg});
 receive({origin:'https://diag.lpp20.com',source:{},data:msg});
 assert.equal(posts.length,0);
 receive({origin:'https://diag.lpp20.com',source:child,data:msg});
 receive({origin:'https://diag.lpp20.com',source:child,data:msg});
 assert.equal(posts.length,1);assert.equal(posts[0][1],'https://diag.lpp20.com');
 assert.equal(child.location.href,'https://diag.lpp20.com/life2-precision.html');
 receive({origin:'https://diag.lpp20.com',source:child,data:{...msg,type:'APPLIED'}});
 assert.deepEqual(done,[true]);assert.equal(removed,1);
 assert.throws(()=>context.exports.connectPrecision(child,'https://attacker.test/',{},()=>{}),/TARGET_INVALID/);
});

function fixture(initial={}){
 let listener,notice,started=0;
 const posts=[],parent={postMessage:(...a)=>posts.push(a)};
 const container={prepend:node=>notice=node};
 const context={answers:{...initial},Q:[{id:'Q48',opts:[{t:'배우자 없이 자녀와 함께',couple:0},{t:'배우자와 함께',couple:1},{t:'혼자 삽니다 (1인 가구)',couple:0}],inputs:[{qid:'Q7A',kind:'year'}]},{id:'Q3',inputs:[{qid:'Q3B',kind:'age',unit:'세'}]},{id:'Q27',inputs:[{qid:'Q28A',unit:'만원'},{qid:'Q28B',unit:'만원'}]}],L2P_DIU:{},uiQuestionHTML:q=>q.id,loadCatalog:()=>Promise.resolve(),goFullIntro:()=>started++,document:{getElementById:id=>id==='life2-prefill-info'?notice:container,createElement:()=>({setAttribute(){},style:{}}),body:container},window:{opener:parent,addEventListener:(n,f)=>listener=f,removeEventListener(){}},setInterval:()=>1,setTimeout:()=>2,clearInterval(){},clearTimeout(){}};
 vm.runInNewContext(receiver,context);
 return {context,parent,posts,notice:()=>notice,send:(payload,origin='https://life2-web-prod.onrender.com',source=parent)=>listener({origin,source,data:{protocol:'LIFE2_PREFILL_V1',type:'PREFILL',prefill:payload}}),flush:()=>new Promise(r=>setImmediate(r))};
}
test('receiver uses engine options and units; preserves fractional manwon, zero, and existing answers',async()=>{
 const f=fixture({Q3B:'61'});
 const p={household_type:'couple',birth_year_self:1975,birth_year_spouse:1973,nps_monthly_self:1505001,nps_monthly_spouse:0,primary_job_exit_age:60,password:'never-copy'};
 f.send(p,'https://attacker.test');f.send(p,undefined,{});await f.flush();assert.equal(f.context.answers.Q28A,undefined);
 f.send(p);await f.flush();
 assert.equal(f.context.answers.Q48.idx,1);assert.equal(f.context.answers.Q7A,'1973');
 assert.equal(f.context.answers.Q28A,'150.5001');assert.equal(f.context.answers.Q28B,'0');assert.equal(f.context.answers.Q3B,'61');
 assert.equal(f.context.answers.Q2A,undefined);assert.equal(f.context.answers.password,undefined);
 assert.equal(f.context.window.opener,null);assert.equal(f.posts.at(-1)[0].type,'APPLIED');
 assert.match(f.notice().textContent,/1975.*만 나이/);
 assert.match(f.context.uiQuestionHTML(f.context.Q[2]),/불러온 값/);
});
test('single household does not import spouse; wrong engine units and invalid values are omitted',async()=>{
 const f=fixture();f.context.Q[2].inputs[0].unit='원';
 f.send({household_type:'single',birth_year_spouse:1973,nps_monthly_self:1500000,nps_monthly_spouse:700000,primary_job_exit_age:-1});await f.flush();
 assert.equal(f.context.answers.Q48.idx,2);assert.equal(f.context.answers.Q7A,undefined);assert.equal(f.context.answers.Q28A,undefined);assert.equal(f.context.answers.Q28B,undefined);assert.equal(f.context.answers.Q3B,undefined);
});
