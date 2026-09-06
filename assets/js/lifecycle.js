(function(global){
  "use strict";
  const DEFAULT_POLICY=Object.freeze({puppy_until_months:9,junior_until_months:18,veteran_from_years:8});
  const clampPolicy=value=>({
    puppy_until_months:Number.isFinite(Number(value?.puppy_until_months))?Number(value.puppy_until_months):DEFAULT_POLICY.puppy_until_months,
    junior_until_months:Number.isFinite(Number(value?.junior_until_months))?Number(value.junior_until_months):DEFAULT_POLICY.junior_until_months,
    veteran_from_years:Number.isFinite(Number(value?.veteran_from_years))?Number(value.veteran_from_years):DEFAULT_POLICY.veteran_from_years
  });
  const parseDate=value=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(String(value||"")))return null;const [y,m,d]=String(value).split("-").map(Number);const date=new Date(Date.UTC(y,m-1,d));return Number.isNaN(date.getTime())?null:date};
  const daysInMonth=(year,month)=>new Date(Date.UTC(year,month+1,0)).getUTCDate();
  const addMonths=(date,months)=>{const baseMonth=date.getUTCMonth()+months;const year=date.getUTCFullYear()+Math.floor(baseMonth/12);const month=((baseMonth%12)+12)%12;const day=Math.min(date.getUTCDate(),daysInMonth(year,month));return new Date(Date.UTC(year,month,day))};
  const startOfToday=()=>{const now=new Date();return new Date(Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate()))};
  function stageFor(record,policy=DEFAULT_POLICY,today=startOfToday()){
    if(!record||record.entity_type!=="doberman")return record?.life_stage||"";
    if(String(record.lifecycle_mode||"automatic").toLowerCase()==="manual")return String(record.life_stage||"unknown").toLowerCase();
    if(String(record.life_status||"").toLowerCase()!=="living")return String(record.life_stage||"unknown").toLowerCase();
    const dob=parseDate(record.date_of_birth); if(!dob)return String(record.life_stage||"unknown").toLowerCase();
    const p=clampPolicy(policy);
    if(today<addMonths(dob,p.puppy_until_months))return "puppy";
    if(today<addMonths(dob,p.junior_until_months))return "junior";
    if(today<addMonths(dob,p.veteran_from_years*12))return "adult";
    return "veteran";
  }
  function templateFor(record,policy=DEFAULT_POLICY,today=startOfToday()){
    if(!record)return "";
    if(record.entity_type==="kennel")return "kennel";
    if(record.entity_type==="litter")return "litter";
    if(record.entity_type!=="doberman")return record.template||"";
    if(String(record.lifecycle_mode||"automatic").toLowerCase()==="manual" && record.template)return record.template;
    const stage=stageFor(record,policy,today);
    if(stage==="puppy")return "puppy";
    const sex=String(record.sex||"").toLowerCase();
    return sex==="female"?"female":sex==="male"?"male":record.template||"";
  }
  async function loadPolicy(base=document.baseURI){
    try{const response=await fetch(new URL("data/lifecycle-policy.json",base),{cache:"no-store"});if(!response.ok)throw new Error("policy unavailable");return clampPolicy(await response.json())}
    catch(_){return clampPolicy(DEFAULT_POLICY)}
  }
  global.DILifecycle={DEFAULT_POLICY,clampPolicy,stageFor,templateFor,loadPolicy};
})(window);
