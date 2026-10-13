const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const {transformSync}=require('rolldown/experimental');
const context={exports:{}};
const serialize=transformSync('incomeGapInput.ts',fs.readFileSync(path.join(__dirname,'../src/incomeGapInput.ts'),'utf8')).code.replace(/export function (\w+)/g,'exports.$1=function $1');
vm.runInNewContext(serialize,context);
const payload=context.exports.incomeGapPayload;

test('empty answers are null/UNKNOWN; explicit zero and fractional manwon survive serialization',()=>{
 const d=payload({});assert.equal(d.budget_monthly_10k,null);assert.equal(d.nps_self.monthly_10k,null);
 const z=payload({budget_monthly_10k:'0','nps_self.state':'CONFIRMED','nps_self.monthly_10k':'150.5'});
 assert.equal(z.budget_monthly_10k,0);assert.equal(z.nps_self.monthly_10k,150.5);
 assert.throws(()=>payload({budget_monthly_10k:'NaN'}));assert.throws(()=>payload({budget_monthly_10k:'-1'}));
});
test('changing state or household removes stale hidden values from the payload',()=>{
 const d=payload({household:'single','nps_spouse.state':'CONFIRMED','nps_spouse.monthly_10k':'80','nps_self.state':'UNKNOWN','nps_self.monthly_10k':'150','post_work.state':'NONE','post_work.monthly_10k':'300'});
 assert.equal(d.nps_spouse.monthly_10k,null);assert.equal(d.nps_self.monthly_10k,null);assert.equal(d.post_work.monthly_10k,null);
});

const componentSource=transformSync('IncomeGap.tsx',fs.readFileSync(path.join(__dirname,'../src/IncomeGap.tsx'),'utf8'),{jsx:{runtime:'automatic'}}).code.replace(/import \{([^}]+)\} from ([^;]+);/g,(_,names,mod)=>`const {${names.replace(/ as /g,':')}}=require(${mod});`).replace('export function IncomeGap','exports.IncomeGap=function');
function fixture({fail=false}={}){
 let states=[],cursor=0,first=true,effects=[],tree,printCount=0,memberCount=0;
 const requests=[];
 const schema={total:12,questions:Array.from({length:12},(_,i)=>({id:`G${i+1}`,title:`확인 ${i+1}`,fields:i===0?[{key:'budget_monthly_10k',label:'월 생활비',type:'money',unit:'만원/월'}]:[]}))};
 const result={calendar:{first_salary_free_month:'2028-01',nps_self_start_month:'2031-01',nps_wait_months:36},missing:[],top3:[{code:'NPS',title:'연금 확인',reason:'확인 필요',target_date:'2026-10-20',steps:['조회하기'],completion:'시작 월 기록',support:'질문 정리표'}],notes:['저장하지 않습니다.']};
 const jsx=(type,props)=>({type,props});
 const react={useState:init=>{const n=cursor++;if(first)states[n]=typeof init==='function'?init():init;return [states[n],v=>states[n]=v]},useRef:init=>{const n=cursor++;if(first)states[n]={current:init};return states[n]},useEffect:f=>{if(first)effects.push(f)}};
 const sandbox={exports:{},require:n=>n==='react'?react:n==='./incomeGapInput'?context.exports:{jsx,jsxs:jsx},AbortController,window:{print:()=>printCount++},fetch:async(url,options)=>{requests.push({url,options});return {ok:!fail,json:async()=>({ok:!fail,data:url.endsWith('questions')?schema:result})}}};
 vm.runInNewContext(componentSource,sandbox);
 function render(){cursor=0;tree=sandbox.exports.IncomeGap({api:'https://api.test',onBack(){},onMember(){memberCount++}});first=false;return tree}
 function nodes(){const out=[];function walk(n){if(Array.isArray(n))n.forEach(walk);else if(n&&typeof n==='object'){out.push(n);walk(n.props?.children)}}walk(tree);return out}
 const text=n=>Array.isArray(n)?n.map(text).join(''):n&&typeof n==='object'?text(n.props?.children):n??'';
 const find=(type,label)=>nodes().find(n=>n.type===type&&text(n)===label);
 render();effects.forEach(f=>f());
 return {render,nodes,find,requests,print:()=>printCount,member:()=>memberCount,flush:()=>new Promise(r=>setImmediate(r))};
}
test('anonymous 12-question flow posts to preview without auth, displays server interval, edits and prints',async()=>{
 const f=fixture();await f.flush();f.render();
 f.nodes().find(n=>n.type==='input').props.onChange({target:{value:'300'}});f.render();
 for(let i=0;i<12;i++){f.nodes().find(n=>n.type==='form').props.onSubmit({preventDefault(){}});await f.flush();f.render();}
 assert.ok(f.find('strong','36개월'));
 assert.equal(f.requests.length,2);const request=f.requests[1];
 assert.equal(request.url,'https://api.test/v1/income-gap/preview');assert.equal(request.options.headers.Authorization,undefined);
 assert.equal(JSON.parse(request.options.body).budget_monthly_10k,300);
 f.find('button','달력·행동 계획 인쇄 / PDF 저장').props.onClick();assert.equal(f.print(),1);
 assert.equal(f.find('button','동의한 초안을 MY LIFE에 저장하기').props.disabled,true);
 f.nodes().find(n=>n.type==='input'&&n.props.type==='checkbox').props.onChange({target:{checked:true}});f.render();
 await f.find('button','동의한 초안을 MY LIFE에 저장하기').props.onClick();assert.equal(f.member(),1);
 f.find('button','입력 확인·수정하기').props.onClick();f.render();assert.equal(f.nodes().find(n=>n.type==='input').props.value,'300');
});
test('catalog error is visible with a retry button instead of an empty form',async()=>{
 const f=fixture({fail:true});await f.flush();f.render();assert.ok(f.find('button','다시 불러오기'));assert.ok(f.nodes().find(n=>n.props?.role==='alert'));assert.equal(f.requests.length,1);
});

test('saved draft fields preserve null and zero without browser calculation',()=>{
 const d=context.exports.incomeGapFields({household:'single',budget_monthly_10k:0,nps_self:{state:'UNKNOWN',start_month:null,monthly_10k:null}});
 assert.equal(d.budget_monthly_10k,'0');assert.equal(d['nps_self.monthly_10k'],'');
 assert.equal(payload(d).nps_self.monthly_10k,null);
});
