/* Companion entry for MY LIFE. The legacy engine and scoring stay authoritative. */
(function(){
  'use strict';
  var origin='https://life2-web-prod.onrender.com', parent=window.opener;
  var accepted=false, transferred={}, protocol='LIFE2_PREFILL_V1';
  function notice(text){
    var node=document.getElementById('life2-prefill-info');
    if(!node){node=document.createElement('aside');node.id='life2-prefill-info';node.setAttribute('role','status');node.style.cssText='padding:16px;margin:12px 16px;border-radius:12px;background:#e7f3eb;color:#164e36;line-height:1.7;';(document.getElementById('s-intro')||document.body).prepend(node);}
    node.textContent=text;
  }
  function blank(key){return answers[key]===undefined || answers[key]===null || answers[key]==='';}
  function integer(value,lo,hi){return typeof value==='number' && Number.isSafeInteger(value) && value>=lo && value<=hi;}
  function inputFor(key){
    var found;
    Q.some(function(q){found=(q.inputs||[]).find(function(i){return i.qid===key;});return !!found;});
    return found;
  }
  function apply(payload){
    var household=payload.household_type, count=0;
    var q=Q.find(function(q){return q.id==='Q48';});
    if(blank('Q48') && q && Array.isArray(q.opts)){
      var matches=q.opts.map(function(o,i){return {o:o,i:i};}).filter(function(x){
        return household==='couple'?(x.o.couple===1||x.o.couple===true):household==='single' && (x.o.couple===0||x.o.couple===false) && /혼자|1인 가구/.test(x.o.t);
      });
      if(matches.length===1){answers.Q48={idx:matches[0].i,opt:matches[0].o};transferred.Q48=true;count++;}
    }
    var couple=answers.Q48 && answers.Q48.opt && (answers.Q48.opt.couple===1||answers.Q48.opt.couple===true);
    [
      ['primary_job_exit_age','Q3B',45,80,'세',false],
      ['birth_year_spouse','Q7A',1940,2010,null,true],
      ['nps_monthly_self','Q28A',0,20000000,'만원',false],
      ['nps_monthly_spouse','Q28B',0,20000000,'만원',true]
    ].forEach(function(row){
      var value=payload[row[0]], input=inputFor(row[1]);
      if(row[5] && !couple || !input || !blank(row[1]) || !integer(value,row[2],row[3]))return;
      if(row[4] && input.unit!==row[4])return;
      if(row[1]==='Q7A' && input.kind!=='year')return;
      answers[row[1]]=String(row[4]==='만원'?value/10000:value);
      if(typeof L2P_DIU!=='undefined')L2P_DIU[row[1]]=false;
      transferred[row[1]]=true;count++;
    });
    var text=count?'MY LIFE에서 확인한 정보 '+count+'개를 불러왔습니다. 각 질문에서 확인하거나 수정할 수 있습니다.':'이미 입력한 답변을 유지했습니다. 새로운 질문부터 이어서 확인해 주세요.';
    if(integer(payload.birth_year_self,1940,2010))text+=' 본인 출생연도는 '+payload.birth_year_self+'년입니다. 나이 질문에서 현재 만 나이를 확인해 주세요.';
    notice(text);
    // Annotate the corresponding cards, without skipping any new questions.
    var original=uiQuestionHTML;
    uiQuestionHTML=function(q){
      var carried=transferred[q.id] || (q.inputs||[]).some(function(i){return transferred[i.qid];});
      return (carried?'<p style="padding:10px;background:#e7f3eb;border-radius:8px;color:#164e36">MY LIFE에서 불러온 값입니다. 확인하거나 수정해 주세요.</p>':'')+original(q);
    };
    goFullIntro();
  }
  function stop(){clearInterval(ping);clearTimeout(timeout);window.removeEventListener('message',receive);window.opener=null;}
  function receive(event){
    if(accepted || event.origin!==origin || event.source!==parent || !event.data || event.data.protocol!==protocol || event.data.type!=='PREFILL')return;
    var payload=event.data.prefill;
    if(!payload || typeof payload!=='object' || Array.isArray(payload))return;
    accepted=true;
    loadCatalog().then(function(){
      apply(payload);
      parent.postMessage({protocol:protocol,type:'APPLIED'},origin);
      stop();
    }).catch(function(){notice('정보 불러오기를 완료하지 못했습니다. 정밀진단에서 직접 입력할 수 있습니다.');stop();});
  }
  goFullIntro();
  if(!parent){notice('정밀진단을 시작해 주세요. MY LIFE에서 열면 확인한 정보를 불러올 수 있습니다.');return;}
  window.addEventListener('message',receive);
  function ready(){parent.postMessage({protocol:protocol,type:'READY'},origin);}
  var ping=setInterval(ready,500);
  var timeout=setTimeout(function(){notice('자동 불러오기가 연결되지 않았습니다. 정밀진단을 직접 진행할 수 있습니다.');stop();},25000);
  ready();
})();
