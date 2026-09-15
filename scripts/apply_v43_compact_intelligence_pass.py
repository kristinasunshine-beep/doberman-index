#!/usr/bin/env python3
from pathlib import Path
import json, re

ROOT=Path(__file__).resolve().parents[1]
MALE=ROOT/'profiles'/'male.html'
DANTE=ROOT/'data'/'dobermans'/'DI-M-000001.json'

s=MALE.read_text(encoding='utf-8')

css=r'''

    /* v4.3b — compact genealogy + intelligence hierarchy */
    @media(min-width:981px){
      #bloodlineRail{overflow:visible}
      .bloodline-breadcrumb{margin-bottom:14px}
      .bloodline-tree{display:grid;grid-template-columns:1.05fr repeat(4,minmax(0,1fr));gap:10px;align-items:start;overflow:visible;scroll-snap-type:none;padding:0}
      .bloodline-column{min-width:0;width:auto;display:flex;flex-direction:column;gap:8px}
      .bloodline-column:not(:first-child)::before{left:-10px;width:10px}
      .bloodline-subject,.ancestor.v43-ancestor,.bloodline-placeholder{width:100%;min-height:0;aspect-ratio:1/1;display:grid;grid-template-rows:48% 52%;overflow:hidden}
      .bloodline-subject .ancestor-info,.ancestor.v43-ancestor .ancestor-info{padding:10px 11px 11px;gap:4px}
      .bloodline-subject .ancestor-info h4,.ancestor.v43-ancestor .ancestor-info h4{font-size:clamp(11px,1.02vw,15px);line-height:1.02}
      .bloodline-subject .ancestor-info small,.ancestor.v43-ancestor .ancestor-info small{font-size:7px}
      .bloodline-subject .ancestor-info p,.ancestor.v43-ancestor .ancestor-info p{font-size:7px;line-height:1.3}
      .ancestor-open{margin-top:auto;font-size:7px}
      .ancestor-gen{left:7px;top:7px;padding:4px 5px;font-size:7px}
      .ancestor-monogram{font-size:clamp(30px,3vw,44px)}
      .bloodline-placeholder{place-items:center;border:1px dashed #c9c9c3;background:rgba(255,255,255,.38);color:#83837d;text-align:center;padding:18px;grid-template-rows:1fr}
      .bloodline-placeholder span{max-width:16ch;font-size:9px;font-weight:650;line-height:1.45}
    }

    .pedigree-intelligence-layout{display:grid;grid-template-columns:minmax(280px,.9fr) minmax(0,1.35fr);gap:14px;align-items:stretch}
    .pi-primary-panel{min-height:340px;padding:26px;display:flex;flex-direction:column;background:var(--acid);color:var(--ink)}
    .pi-primary-kicker{font-size:10px;font-weight:800;letter-spacing:.09em;text-transform:uppercase}
    .pi-primary-value{margin:auto 0 24px;display:flex;align-items:flex-end;gap:8px}
    .pi-primary-value strong{font-size:clamp(78px,8.5vw,134px);font-weight:730;line-height:.75;letter-spacing:-.09em;white-space:nowrap}
    .pi-primary-value span{padding-bottom:7px;font-size:12px;font-weight:750}
    .pi-primary-panel h3{margin:0;font-size:22px;line-height:1;letter-spacing:-.045em}
    .pi-primary-panel p{max-width:42ch;margin:10px 0 0;font-size:11px;line-height:1.5}
    .pi-register{border-top:1px solid var(--ink)}
    .pi-row{display:grid;grid-template-columns:76px minmax(0,1fr) auto;gap:16px;align-items:center;min-height:67px;padding:12px 2px;border-bottom:1px solid #bdbdb7}
    .pi-row-code{font-size:9px;font-weight:800;letter-spacing:.1em;color:var(--muted)}
    .pi-row-copy strong{display:block;font-size:15px;line-height:1.05;letter-spacing:-.025em}
    .pi-row-copy small{display:block;margin-top:5px;color:var(--muted);font-size:9px;line-height:1.35}
    .pi-row-value{font-size:clamp(24px,2.5vw,36px);font-weight:720;line-height:1;letter-spacing:-.055em;white-space:nowrap}

    #breeding-lens.performance-showcase{background:#ebece8}
    .lens-brief{display:grid;grid-template-columns:minmax(280px,.95fr) minmax(0,1.35fr);gap:14px}
    .lens-priority{min-height:420px;padding:28px;display:flex;flex-direction:column;background:var(--white);border:1px solid #d0d0ca}
    .lens-priority .lens-kicker,.lens-row .lens-kicker{font-size:9px;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:var(--muted)}
    .lens-priority h3{margin:auto 0 18px;font-size:clamp(34px,4.2vw,62px);font-weight:670;line-height:.92;letter-spacing:-.06em}
    .lens-priority p{max-width:42ch;margin:0;font-size:13px;line-height:1.58;color:#393935}
    .lens-stack{border-top:1px solid var(--ink)}
    .lens-row{display:grid;grid-template-columns:110px minmax(0,1fr);gap:20px;padding:20px 2px 22px;border-bottom:1px solid #bdbdb7}
    .lens-row h4{margin:0 0 8px;font-size:18px;line-height:1;letter-spacing:-.035em}
    .lens-row p{margin:0;max-width:64ch;color:#3c3c38;font-size:12px;line-height:1.58}
    .lens-readiness{grid-column:1/-1;margin-top:2px;padding:16px 18px;background:var(--ink);color:var(--white);display:grid;grid-template-columns:140px minmax(0,1fr);gap:18px;align-items:center}
    .lens-readiness strong{font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--acid)}
    .lens-readiness span{font-size:12px;line-height:1.5}

    @media(max-width:980px){
      .pedigree-intelligence-layout,.lens-brief{grid-template-columns:1fr}
      .pi-primary-panel{min-height:300px}
      .lens-priority{min-height:330px}
    }
    @media(max-width:680px){
      .bloodline-tree{display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory}
      .bloodline-column{flex:0 0 82vw;max-width:320px;scroll-snap-align:start}
      .bloodline-subject,.ancestor.v43-ancestor,.bloodline-placeholder{aspect-ratio:1/1;min-height:0;grid-template-rows:46% 54%}
      .bloodline-placeholder{display:grid;place-items:center;border:1px dashed #c9c9c3;background:rgba(255,255,255,.5);padding:24px;text-align:center}
      .bloodline-placeholder span{font-size:11px;line-height:1.45;color:var(--muted)}
      .pi-primary-panel{min-height:240px;padding:20px}
      .pi-primary-value strong{font-size:clamp(72px,24vw,98px)}
      .pi-row{grid-template-columns:58px minmax(0,1fr) auto;gap:10px;min-height:63px}
      .pi-row-copy strong{font-size:13px}.pi-row-value{font-size:25px}
      .lens-priority{min-height:0;padding:22px}.lens-priority h3{margin:44px 0 16px;font-size:38px}
      .lens-row{grid-template-columns:1fr;gap:9px;padding:18px 2px}
      .lens-readiness{grid-template-columns:1fr;gap:7px;padding:16px}
    }
'''
if '/* v4.3b — compact genealogy + intelligence hierarchy */' not in s:
    s=s.replace('</style>',css+'\n  </style>',1)

# Replace bloodline renderer with 5-column desktop / progressive mobile tree.
start=s.index('    let bloodlineFocusPath="";')
end=s.index('\n\n    function pedigreeIntelligence(){',start)
new_blood=r'''    let bloodlineFocusPath="";

    function bloodline(depth=4,focusPath=bloodlineFocusPath,scrollForward=false){
      const entries=profileData.bloodline.filter(x=>x.gen<=depth);
      const byPath=new Map(entries.map(item=>[item.path,item]));
      if(focusPath&&!byPath.has(focusPath))focusPath="";
      bloodlineFocusPath=focusPath;
      byId("bloodlineDepthLabel").textContent=`Dante + ${depth} mapped generations`;

      const crumb=[profileData.name];
      for(let i=1;i<=focusPath.length;i++){
        const item=byPath.get(focusPath.slice(0,i));
        if(item)crumb.push(item.name);
      }
      const breadcrumb=`<div class="bloodline-breadcrumb">${crumb.map((name,index)=>`${index?'<i></i>':''}<span>${escapeHTML(name)}</span>`).join("")}</div>`;

      const subject=`<div class="bloodline-column bloodline-root"><div class="bloodline-generation-head"><span>Dante</span><span>Subject</span></div><article class="bloodline-subject"><div class="ancestor-visual"><img src="${escapeHTML(profileData.heroImage)}" alt="${escapeHTML(profileData.name)}" style="object-position:${escapeHTML(profileData.heroPosition||'50% 50%')}"><span class="ancestor-gen">DI</span></div><div class="ancestor-info"><small>Indexed Doberman</small><h4>${escapeHTML(profileData.name)}</h4><p>${escapeHTML(profileData.core.registrationNumber||profileData.core.profileId)}</p><span class="ancestor-open">Start with sire or dam →</span></div></article></div>`;

      const columns=[subject];
      for(let gen=1;gen<=depth;gen++){
        const unlocked=gen===1||focusPath.length>=gen-1;
        const parentPath=gen===1?"":focusPath.slice(0,gen-1);
        const candidates=unlocked?[parentPath+"S",parentPath+"D"].map(path=>byPath.get(path)).filter(Boolean):[];
        const selectedPath=focusPath.slice(0,gen);
        let cards='';
        if(candidates.length){
          cards=candidates.map(x=>{
            const metadata=[x.registration,x.country].map(value=>present(value,"")).filter(Boolean);
            const visual=x.image?`<img src="${escapeHTML(x.image)}" alt="${escapeHTML(x.name)}" loading="lazy">`:`<div class="ancestor-monogram">${escapeHTML(x.name.charAt(0)||"D")}</div>`;
            const hasParents=gen<depth&&(byPath.has(x.path+"S")||byPath.has(x.path+"D"));
            const selected=x.path===selectedPath;
            return `<button class="ancestor v43-ancestor${selected?' is-selected':''}" type="button" data-bloodline-path="${escapeHTML(x.path)}" aria-pressed="${selected?'true':'false'}" aria-label="Open parents of ${escapeHTML(x.name)}"><div class="ancestor-visual">${visual}<span class="ancestor-gen">G${gen}</span></div><div class="ancestor-info"><small>${escapeHTML(x.role)} · ${escapeHTML(x.sex||"ancestor")}</small><h4>${escapeHTML(x.name)}</h4><p>${metadata.map(escapeHTML).join(" · ")||"Canonical pedigree node"}</p><span class="ancestor-open">${hasParents?'Open parents →':'Mapped boundary'}</span></div></button>`;
          }).join('');
        }else{
          cards=`<div class="bloodline-placeholder"><span>${gen===1?'Pedigree branch unavailable':`Select a Generation ${gen-1} ancestor to reveal Generation ${gen}.`}</span></div>`;
        }
        columns.push(`<div class="bloodline-column" data-bloodline-generation="${gen}"><div class="bloodline-generation-head"><span>Generation ${gen}</span><span>${unlocked&&candidates.length?'Sire + dam':'Next branch'}</span></div>${cards}</div>`);
      }
      const rail=byId("bloodlineRail");
      rail.innerHTML=breadcrumb+`<div class="bloodline-tree">${columns.join("")}</div>`;
      rail.querySelectorAll('[data-bloodline-path]').forEach(button=>button.addEventListener('click',()=>{
        const path=button.dataset.bloodlinePath||"";
        bloodline(depth,path,true);
      }));
      if(scrollForward&&matchMedia('(max-width:980px)').matches){
        requestAnimationFrame(()=>{
          const tree=rail.querySelector('.bloodline-tree');
          const target=tree?.children[Math.min(depth,focusPath.length+1)];
          if(tree&&target)tree.scrollTo({left:Math.max(0,target.offsetLeft-12),behavior:'smooth'});
        });
      }
    }
'''
s=s[:start]+new_blood+s[end:]

# Replace pedigree intelligence renderer.
start=s.index('    function pedigreeIntelligence(){')
end=s.index('\n\n    function breedingLens(){',start)
new_pi=r'''    function pedigreeIntelligence(){
      const d=profileData.pedigreeIntelligence||{};
      const coi=present(d["Coefficient of inbreeding (COI)"],"—");
      const depth=present(d["Analysed depth"],"—");
      const rows=[
        ["AVK","Ancestor loss coefficient",d["Ancestor loss (AVK)"],"Unique ancestors relative to all mapped ancestor positions."],
        ["MAP","Pedigree completeness",d["Pedigree completeness"],"Known pedigree positions inside the analysed depth."],
        ["REP","Repeated ancestors",d["Repeated ancestors"],"Distinct mapped ancestors that occur more than once."],
        ["UNQ","Unique ancestors",d["Unique ancestors"],"Distinct ancestors represented inside the mapped pedigree."],
        ["GEN","Analysed depth",depth,"How far the canonical calculation currently extends."]
      ];
      byId("pedigreeIntelligenceRail").innerHTML=`<div class="pedigree-intelligence-layout"><article class="pi-primary-panel"><span class="pi-primary-kicker">Primary pedigree metric</span><div class="pi-primary-value"><strong>${escapeHTML(coi)}</strong></div><h3>Coefficient of inbreeding</h3><p>Pedigree COI calculated from the canonical ancestry currently mapped for this record. Current analysed depth: ${escapeHTML(depth)}.</p></article><div class="pi-register">${rows.map(([code,label,value,copy])=>`<div class="pi-row"><span class="pi-row-code">${escapeHTML(code)}</span><div class="pi-row-copy"><strong>${escapeHTML(label)}</strong><small>${escapeHTML(copy)}</small></div><span class="pi-row-value">${escapeHTML(present(value,"—"))}</span></div>`).join('')}</div></div>`;
    }
'''
s=s[:start]+new_pi+s[end:]

# Replace breeding lens renderer.
start=s.index('    function breedingLens(){')
end=s.index('\n\n    function pedigreeRepeats(){',start)
new_lens=r'''    function breedingLens(){
      const d=profileData.breedingLens||{};
      byId("breedingLensRail").innerHTML=`<div class="lens-brief"><article class="lens-priority"><span class="lens-kicker">Priority mate profile</span><h3>${escapeHTML(present(d.priority,"Pairing profile pending"))}</h3><p>${escapeHTML(present(d.summary,"The Breeding Lens becomes specific when the structured record is complete."))}</p></article><div class="lens-stack"><article class="lens-row"><span class="lens-kicker">01 · Cardiac + genetic</span><div><h4>Manage known risk signals.</h4><p>${escapeHTML(present(d.cardiac,"—"))}</p></div></article><article class="lens-row"><span class="lens-kicker">02 · Lineage control</span><div><h4>Protect diversity while reading the repeats.</h4><p>${escapeHTML(present(d.lineage,"—"))}</p></div></article><article class="lens-row"><span class="lens-kicker">03 · Type + mind</span><div><h4>Preserve strengths; use the mate as the deliberate lever.</h4><p>${escapeHTML(present(d.phenotype,"—"))}</p></div></article></div><div class="lens-readiness"><strong>Decision boundary</strong><span>${escapeHTML(present(d.readiness,"A concrete female record is required before projected COI, shared ancestry and pair-specific health/phenotype context can be calculated."))}</span></div></div>`;
    }
'''
s=s[:start]+new_lens+s[end:]

# Replace canonical profile mapping for breeding lens with structured fields.
old='        breedingLens:{Preserve:present(breedingLens.preserve,"Generated after pedigree mapping"),Complement:present(breedingLens.complement,"Generated after record review"),Watch:present(breedingLens.watch,"Generated after record review"),Unknown:present(breedingLens.unknown,"Missing data remain explicit")},'
new='        breedingLens:{summary:present(breedingLens.summary,breedingLens.preserve||"Generated from the structured record"),priority:present(breedingLens.priority,breedingLens.complement||"Pairing profile pending"),cardiac:present(breedingLens.cardiac,breedingLens.watch||"Health context pending"),lineage:present(breedingLens.lineage,"Lineage synthesis pending"),phenotype:present(breedingLens.phenotype,"Phenotype and temperament synthesis pending"),readiness:present(breedingLens.readiness,breedingLens.unknown||"Pair-specific analysis requires a selected mate")},'
if old not in s: raise SystemExit('breeding lens mapping anchor missing')
s=s.replace(old,new,1)

MALE.write_text(s,encoding='utf-8')

payload=json.loads(DANTE.read_text(encoding='utf-8'))
bl=payload['doberman'].setdefault('breeding_lens',{})
bl.clear(); bl.update({
  'status':'generated_v2',
  'summary':'Dante’s record supports partner preselection now: the strongest case is to preserve his balanced, elegant type, strong topline, free elastic movement and stable high drive while using the female record to strengthen confidence/social stability and manage cardiac and lineage risk deliberately.',
  'priority':'A low-related female with current cardiac screening, a cardiac-genetic profile that does not stack Dante’s known DCM1 signal, high confidence, stable social behaviour and structurally compatible movement/topline.',
  'cardiac':'Dante is recorded DCM1 Carrier, DCM2–5 Clear and clinically without signs of DCM on Holter + Echo. DCM1 is a risk marker rather than a diagnosis, so mate selection should combine the female’s current cardiac screening, DCM1/DCM2 status and available family cardiac/longevity context rather than treating one marker as a verdict.',
  'lineage':'The mapped four-generation pedigree currently shows COI 0.78%, AVK 96.67% and one repeated ancestor. The pairing target is to keep projected COI low and avoid increasing concentration through the existing repeat unless that linebreeding is deliberate and justified by the complete female record.',
  'phenotype':'Recorded strengths are balanced/elegant type, strong topline, harmonious structure and free elastic movement, backed by Champion of Serbia, BH-VT and IGP 1. Temperament is recorded Stable with High drive, Neutral social behaviour and Moderate confidence; the female’s confidence/social profile is therefore a useful deliberate selection lever rather than a generic “more is better” score.',
  'readiness':'This record is sufficient to shortlist females. A final pairing recommendation begins only after a specific female is selected, because projected COI, shared ancestors, variant combinations and structural/temperament complementarity are pair-specific calculations.'
})
DANTE.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('v4.3b compact intelligence pass applied')
