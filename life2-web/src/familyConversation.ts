type Fields=Record<string,string|number|string[]>;
const topics=new Set(['MEDICAL_DECISION','CARE','ASSET_INHERITANCE','FUNERAL_MEMORIAL','DIGITAL_INFO']);

export function familyConversationBlockReason(fields:Fields):string|null{
  if(fields.conversation_done==='NO'){
    return '아직 대화하지 않았다면 ‘저장하고 나중에’를 눌러 주세요. 가족과 실제로 대화한 뒤 완료할 수 있습니다.';
  }
  if(fields.conversation_done!=='YES') return '가족과 실제로 대화했는지 선택해 주세요.';
  const selected=fields.preference_topics;
  if(!Array.isArray(selected) || selected.length===0 || selected.some(topic=>!topics.has(topic))){
    return '가족과 나눈 대화에서 기록한 선호사항을 한 가지 이상 선택해 주세요.';
  }
  return null;
}
