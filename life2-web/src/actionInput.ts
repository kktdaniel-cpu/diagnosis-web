type Fields=Record<string,string|number|string[]>;
const pensionKeys=new Set(['nps_monthly_self','nps_monthly_spouse']);
export function isPensionAmount(action:string,key:string){
  return action==='ACT_CHECK_NPS_ESTIMATE' && pensionKeys.has(key);
}
export function pensionFields(action:string,fields:Fields,toApi:boolean):Fields{
  if(action!=='ACT_CHECK_NPS_ESTIMATE') return fields;
  const result={...fields};
  for(const key of pensionKeys){
    const value=fields[key];
    if(value===undefined || value==='') continue;
    if((typeof value==='string'||typeof value==='number') && Number.isFinite(Number(value))){
      result[key]=toApi?Math.round(Number(value)*10000):Number(value)/10000;
    }
  }
  return result;
}
export function digitalListBlockReason(action:string,fields:Fields):string|null{
  if(action!=='ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST') return null;
  if(fields.family_can_locate!=='YES') return '가족에게 목록 보관 위치를 알려야 완료할 수 있습니다. 아직이라면 ‘저장하고 나중에’를 눌러 주세요.';
  if(fields.access_procedure_prepared!=='YES') return '필요할 때 목록을 확인할 절차를 정해야 완료할 수 있습니다. 아직이라면 ‘저장하고 나중에’를 눌러 주세요.';
  if(!Array.isArray(fields.digital_categories)||fields.digital_categories.length===0) return '목록에 포함한 항목을 한 가지 이상 선택해 주세요.';
  if(!fields.inventory_location_type) return '목록 보관 위치 유형을 선택해 주세요.';
  return null;
}
