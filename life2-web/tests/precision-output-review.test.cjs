const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const exported={exports:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../review/precision-output/proposal.js'),'utf8'),{module:exported});
const review=exported.exports;

function fixture(){
 const nodes=new Map(); let prints=0;
 function element(){
  const el={style:{},hidden:false,children:[],textContent:'',listeners:{},
   appendChild(child){child.parentNode=this;this.children.push(child);},
   insertBefore(child){if(child.parentNode)child.parentNode.children=child.parentNode.children.filter(x=>x!==child);child.parentNode=this;this.children.unshift(child);},
   addEventListener(name,fn){this.listeners[name]=fn;}};
  Object.defineProperty(el,'id',{get(){return this._id;},set(id){this._id=id;nodes.set(id,this);}});
  Object.defineProperty(el,'firstChild',{get(){return this.children[0]||null;}});
  return el;
 }
 const report=element();report.id='fullReportWrap';report.style.display='block';
 const win={document:{getElementById:id=>nodes.get(id)||null,createElement:element},localStorage:{getItem:()=> '1'},_svDone:true,printReport:()=>prints++};
 return {win,report,nodes,element,prints:()=>prints};
}

test('locked, short-survey and unavailable-storage states cannot print',()=>{
 const {win,report}=fixture();
 win._svDone=false;assert.equal(review.canPrint(win,report),false);
 win._svDone=true;win.localStorage.getItem=()=> '0';assert.equal(review.canPrint(win,report),false);
 win.localStorage.getItem=()=>{throw Error('denied')};assert.equal(review.canPrint(win,report),false);
});
test('unlocked report keeps one working print entry across repeated redraw syncs',()=>{
 const f=fixture();review.sync(f.win);review.sync(f.win);
 assert.equal(f.report.children.length,1);
 const actions=f.nodes.get('l2p-report-print-actions');
 assert.equal(actions.firstChild.textContent,'PDF 저장 / 인쇄');
 actions.firstChild.listeners.click();assert.equal(f.prints(),1);
 f.win._svDone=false;actions.firstChild.listeners.click();review.sync(f.win);
 assert.equal(f.prints(),1);assert.equal(actions.hidden,true);
});
test('entry follows replacement report and language without changing facts or scores',()=>{
 const f=fixture();f.win.FACT={value:null};review.sync(f.win);
 const replacement=f.element();replacement.id='fullReportWrap';replacement.style.display='block';
 f.win.L2P_LANG='en';review.sync(f.win);
 assert.equal(replacement.children.length,1);
 assert.equal(replacement.firstChild.firstChild.textContent,'Save PDF / Print');
 assert.deepEqual(f.win.FACT,{value:null});
});
test('hidden or missing report never exposes the action',()=>{
 const f=fixture();f.report.style.display='none';review.sync(f.win);
 assert.equal(f.report.children.length,0);assert.equal(review.canPrint(f.win,null),false);
});
test('cost explanation describes unchanged target input and makes no no-change claim',()=>{
 assert.match(review.costScenarioExplanation,/현재 생활비/);
 assert.match(review.costScenarioExplanation,/목표 생활비는 그대로/);
 assert.doesNotMatch(review.costScenarioExplanation,/소진 시점이 달라지지|부족액.*줄어/);
});
