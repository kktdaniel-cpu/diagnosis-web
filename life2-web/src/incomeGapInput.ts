// Serialization only. Calendar and priority rules belong to the API.
export function incomeGapPayload(fields: Record<string,string>){
  const month=(key:string)=>fields[key] || null;
  const money=(key:string)=>{
    const value=fields[key];
    if(value===undefined || value==='') return null;
    const number=Number(value);
    if(!Number.isFinite(number) || number<0) throw new Error('금액을 0 이상의 숫자로 입력해 주세요.');
    return number;
  };
  const pension=(key:string)=>{
    const state=fields[`${key}.state`] || 'UNKNOWN';
    return {state,start_month:state==='CONFIRMED'?month(`${key}.start_month`):null,monthly_10k:state==='CONFIRMED'?money(`${key}.monthly_10k`):null};
  };
  const workState=fields['post_work.state'] || 'UNKNOWN';
  return {
    household:fields.household || 'UNKNOWN',job_exit_month:month('job_exit_month'),last_salary_month:month('last_salary_month'),
    budget_monthly_10k:money('budget_monthly_10k'),debt_monthly_10k:money('debt_monthly_10k'),debt_in_budget:fields.debt_in_budget || 'UNKNOWN',
    nps_self:pension('nps_self'),nps_spouse:fields.household==='couple'?pension('nps_spouse'):{state:'UNKNOWN',start_month:null,monthly_10k:null},
    private_pension:pension('private_pension'),post_work:{state:workState,monthly_10k:['CONFIRMED','PLAN_ONLY'].includes(workState)?money('post_work.monthly_10k'):null},
    liquid_assets_band:fields.liquid_assets_band || 'UNKNOWN',large_cost_state:fields.large_cost_state || 'UNKNOWN',family_discussion:fields.family_discussion || 'UNKNOWN'
  };
}
