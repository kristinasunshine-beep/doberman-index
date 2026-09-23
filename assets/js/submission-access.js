(function(global){
  "use strict";
  const API="https://doberman-index-commerce.dobermanindex-records.workers.dev";
  const form=document.getElementById("submission-form");
  if(!form)return;

  const service=document.body.dataset.accessService||"";
  const params=new URLSearchParams(location.search);
  const paymentId=params.get("payment_id")||"";
  const orderReference=params.get("order_reference")||params.get("order")||"";
  const invite=params.get("invite")||"";
  const controls=[...form.querySelectorAll("input,select,textarea,button")];
  controls.forEach(el=>{el.disabled=true});

  const gate=document.createElement("div");
  gate.style.cssText="margin:0 0 18px;padding:14px 16px;border:1px solid #c8c8c2;background:#fff;font:700 13px/1.45 system-ui,sans-serif";
  gate.textContent="Verifying your order or private invitation…";
  form.parentNode.insertBefore(gate,form);

  let context=null;

  async function verify(){
    const q=new URLSearchParams({service});
    if(invite)q.set("invite",invite);
    else if(paymentId)q.set("payment_id",paymentId);
    else if(orderReference)q.set("order_reference",orderReference);
    else throw new Error("Open this questionnaire from a confirmed purchase or private invitation.");

    const response=await fetch(API+"/v1/commerce/access?"+q.toString(),{cache:"no-store"});
    const body=await response.json().catch(()=>({}));
    if(!response.ok||!body.valid)throw new Error(body.error||"Access could not be verified.");
    context=body;
    controls.forEach(el=>{el.disabled=false});
    gate.textContent=body.source_type==="invitation_waiver"
      ?"Private invitation verified · service fee waived."
      :"Payment verified · questionnaire unlocked.";

    const email=form.elements.namedItem("contact_email");
    if(email&&!email.value&&body.customer_email)email.value=body.customer_email;
    return body;
  }

  async function consume(submissionReference){
    if(!context)return;
    if(context.source_type==="invitation_waiver"){
      await fetch(API+"/v1/invitations/redeem",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({token:invite,service_key:service,submission_reference:submissionReference||null})
      });
    }else{
      await fetch(API+"/v1/commerce/consume",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({payment_id:paymentId||null,order_reference:orderReference||null,service_key:service,submission_reference:submissionReference||null})
      });
    }
  }

  global.DIAccess={
    ready:verify().catch(error=>{
      gate.textContent=error.message;
      gate.style.borderColor="#b00020";
      throw error;
    }),
    context:()=>context?{
      source_type:context.source_type,
      source_reference:context.source_reference,
      service_key:context.service_key,
      invitation_id:context.invitation_id||null
    }:null,
    consume
  };
})(window);
