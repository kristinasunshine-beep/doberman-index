#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MALE = ROOT / "profiles" / "male.html"

s = MALE.read_text(encoding="utf-8")

# 1) Core ticker: identity values must never be ellipsized.
s = s.replace(
    '.core-chip{position:relative;width:220px;min-height:82px;padding:15px 34px 14px 20px;display:flex;flex-direction:column;justify-content:center;text-align:left;background:var(--white);transition:background .3s var(--ease)}',
    '.core-chip{position:relative;width:max-content;min-width:220px;min-height:82px;padding:15px 34px 14px 20px;display:flex;flex-direction:column;justify-content:center;text-align:left;background:var(--white);transition:background .3s var(--ease)}'
)
s = s.replace(
    '.core-chip strong{display:block;color:var(--ink);font-size:16.5px;font-weight:700;line-height:1.04;letter-spacing:-.045em;font-variant-numeric:tabular-nums;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:transform .3s var(--ease),letter-spacing .3s var(--ease)}',
    '.core-chip strong{display:block;color:var(--ink);font-size:16.5px;font-weight:700;line-height:1.04;letter-spacing:-.045em;font-variant-numeric:tabular-nums;white-space:nowrap;overflow:visible;text-overflow:clip;transition:transform .3s var(--ease),letter-spacing .3s var(--ease)}'
)

# 2) Clarify bloodline copy around interaction.
s = s.replace(
    '<p class="section-note"><b id="bloodlineDepthLabel">Mapped pedigree</b>Explore the full mapped ancestry as a visual lineage network. Open each generation, inspect repeated ancestors and follow indexed records.</p>',
    '<p class="section-note"><b id="bloodlineDepthLabel">Mapped pedigree</b>Start with the parents, then open either branch generation by generation. Every tap keeps the chosen line in view while revealing the next pair of ancestors.</p>'
)

# 3) Replace existing v4.3 CSS block with interaction/mobile-first refinement.
css_start = s.find('    /* v4.3 — Record Intelligence */')
css_end = s.find('\n\n  </style>', css_start)
if css_start < 0 or css_end < 0:
    raise SystemExit('v4.3 CSS block not found')
new_css = r'''    /* v4.3 — Interaction pass / mobile-first record intelligence */
    #bloodlineRail{display:block;max-width:100%;overflow:hidden}
    .bloodline-breadcrumb{display:flex;align-items:center;gap:7px;min-height:32px;margin:0 0 16px;color:var(--muted);font-size:9px;font-weight:700;letter-spacing:.065em;text-transform:uppercase;overflow-x:auto;scrollbar-width:none}
    .bloodline-breadcrumb::-webkit-scrollbar{display:none}
    .bloodline-breadcrumb span{white-space:nowrap}
    .bloodline-breadcrumb i{width:14px;height:1px;background:#a8a8a2;flex:none}
    .bloodline-tree{display:flex;align-items:stretch;gap:18px;max-width:100%;padding:4px 0 16px;overflow-x:auto;overscroll-behavior-inline:contain;scroll-snap-type:x mandatory;scrollbar-width:none}
    .bloodline-tree::-webkit-scrollbar{display:none}
    .bloodline-column{position:relative;flex:0 0 clamp(240px,23vw,310px);min-width:0;display:flex;flex-direction:column;gap:10px;scroll-snap-align:start}
    .bloodline-column:not(:first-child)::before{content:"";position:absolute;left:-18px;top:50%;width:18px;height:1px;background:#b8b8b2}
    .bloodline-generation-head{display:flex;align-items:center;justify-content:space-between;min-height:28px;padding:0 2px 8px;border-bottom:1px solid #c9c9c3;color:var(--muted);font-size:9px;font-weight:750;letter-spacing:.08em;text-transform:uppercase}
    .bloodline-subject,.ancestor.v43-ancestor{position:relative;width:100%;min-height:220px;padding:0;display:grid;grid-template-rows:104px 1fr;border:1px solid #d4d4ce;background:#f6f6f2;color:var(--ink);overflow:hidden;text-align:left;text-decoration:none;transition:transform .28s var(--ease),background .28s var(--ease),border-color .28s var(--ease),box-shadow .28s var(--ease)}
    button.ancestor.v43-ancestor{font:inherit;cursor:pointer}
    .bloodline-subject{background:var(--white);border-color:var(--ink)}
    .ancestor.v43-ancestor:hover,.ancestor.v43-ancestor:focus-visible,.ancestor.v43-ancestor.is-selected{transform:translateY(-2px);background:var(--white);border-color:var(--ink);box-shadow:0 10px 24px rgba(18,18,18,.07)}
    .ancestor.v43-ancestor.is-selected{box-shadow:inset 5px 0 0 var(--acid),0 10px 24px rgba(18,18,18,.07)}
    .ancestor-visual{position:relative;overflow:hidden;background:#151515;color:var(--white)}
    .ancestor-visual img{width:100%;height:100%;object-fit:cover;display:block;filter:grayscale(1);transition:filter .35s var(--ease),transform .5s var(--ease)}
    .ancestor.v43-ancestor:hover .ancestor-visual img,.ancestor.v43-ancestor.is-selected .ancestor-visual img{filter:grayscale(0);transform:scale(1.02)}
    .ancestor-monogram{height:100%;display:flex;align-items:center;justify-content:center;font-size:54px;font-weight:800;letter-spacing:-.08em}
    .ancestor-gen{position:absolute;left:10px;top:10px;padding:5px 7px;background:var(--acid);color:var(--ink);font-size:8px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
    .ancestor-info{padding:13px 14px 15px;display:flex;flex-direction:column;gap:6px}
    .ancestor-info small{color:var(--muted);font-size:8px;font-weight:750;letter-spacing:.07em;text-transform:uppercase}
    .ancestor-info h4{margin:0;font-size:17px;line-height:1;letter-spacing:-.045em}
    .ancestor-info p{margin:auto 0 0;color:var(--muted);font-size:9px;line-height:1.42}
    .ancestor-open{display:block;margin-top:7px;color:var(--ink);font-size:8px;font-weight:800;letter-spacing:.07em;text-transform:uppercase}
    .ancestor-media-source{font-size:8px!important;color:#85857f!important}

    /* Pedigree intelligence: short labels, one-line values, no forced word breaking. */
    .pedigree-intelligence-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
    .pi-card{position:relative;min-width:0;min-height:210px;padding:20px 18px 18px;display:flex;flex-direction:column;border:1px solid #d0d0ca;background:var(--white);overflow:hidden}
    .pi-card.is-primary{background:var(--acid);border-color:var(--acid)}
    .pi-code{display:block;margin-bottom:auto;color:var(--muted);font-size:10px;font-weight:800;letter-spacing:.09em;text-transform:uppercase}
    .pi-card.is-primary .pi-code{color:#32322d}
    .pi-value{display:flex;align-items:baseline;gap:6px;margin:26px 0 14px;white-space:nowrap}
    .pi-value strong{font-size:clamp(44px,4.7vw,72px);font-weight:720;line-height:.88;letter-spacing:-.075em;white-space:nowrap}
    .pi-value span{font-size:11px;font-weight:700;color:var(--muted);white-space:nowrap}
    .pi-card h3{margin:0;font-size:15px;font-weight:720;line-height:1.1;letter-spacing:-.025em}
    .pi-card p{margin:7px 0 0;color:var(--muted);font-size:10px;line-height:1.42}
    .pedigree-repeats{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
    .pedigree-repeat-chip{padding:8px 11px;border:1px solid #c8c8c2;background:#f6f6f2;font-size:9px;font-weight:650}

    /* Breeding Lens: quiet editorial decision layer rather than poster cards. */
    #breeding-lens.performance-showcase{min-height:auto;background:var(--paper);color:var(--ink)}
    #breeding-lens.performance-showcase .section-head{margin-bottom:clamp(48px,6vw,76px)}
    #breeding-lens.performance-showcase .section-title{font-size:clamp(54px,7.2vw,102px)}
    #breedingLensRail{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
    .lens-card{position:relative;min-width:0;min-height:250px;padding:24px 24px 26px;border:1px solid #d0d0ca;background:var(--white);display:flex;flex-direction:column}
    .lens-card::before{content:"";position:absolute;left:-1px;top:-1px;bottom:-1px;width:5px;background:var(--acid)}
    .lens-meta{display:flex;align-items:center;justify-content:space-between;margin-bottom:42px;color:var(--muted);font-size:9px;font-weight:750;letter-spacing:.08em;text-transform:uppercase}
    .lens-card h3{margin:0 0 15px;font-size:clamp(24px,2.4vw,34px);line-height:.95;letter-spacing:-.045em}
    .lens-card p{max-width:46ch;margin:0;color:#3c3c38;font-size:14px;line-height:1.58}

    #performanceRail .metric[role="button"]{cursor:pointer}
    #performanceRail .metric[aria-expanded="true"]{outline:2px solid var(--acid);outline-offset:3px}
    .performance-detail-note{margin:0;padding:18px 0;color:var(--muted);font-size:12px;line-height:1.55}

    @media(max-width:900px){
      .pedigree-intelligence-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
      #breedingLensRail{grid-template-columns:1fr 1fr}
      .bloodline-column{flex-basis:min(78vw,300px)}
    }
    @media(max-width:680px){
      #bloodline .section-head{margin-bottom:36px}
      .bloodline-breadcrumb{margin-bottom:12px;font-size:8px}
      .bloodline-tree{gap:12px;margin-right:calc(var(--pad) * -1);padding-right:var(--pad);scroll-padding-left:0}
      .bloodline-column{flex-basis:84vw;max-width:330px}
      .bloodline-column:not(:first-child)::before{left:-12px;width:12px}
      .bloodline-subject,.ancestor.v43-ancestor{min-height:204px;grid-template-rows:96px 1fr}
      .pedigree-intelligence-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
      .pi-card{min-height:176px;padding:15px 13px}
      .pi-value{margin:21px 0 12px;gap:4px}
      .pi-value strong{font-size:clamp(35px,11vw,48px)}
      .pi-value span{font-size:9px}
      .pi-card h3{font-size:12px}
      .pi-card p{font-size:9px;line-height:1.35}
      #breeding-lens.performance-showcase{padding-top:88px;padding-bottom:88px}
      #breeding-lens.performance-showcase .section-title{font-size:clamp(48px,14vw,66px)}
      #breedingLensRail{grid-template-columns:1fr;gap:10px}
      .lens-card{min-height:0;padding:21px 20px 23px}
      .lens-meta{margin-bottom:28px}
      .lens-card h3{font-size:27px}
      .lens-card p{font-size:13px;line-height:1.55}
    }
'''
s = s[:css_start] + new_css + s[css_end:]

# 4) Replace generic pedigree/breeding rendering calls with dedicated renderers.
s = s.replace(
    'core();gallery();anchorMovement();bloodline(profileData.pedigreeDepth||4);metrics("pedigreeIntelligenceRail",profileData.pedigreeIntelligence,0);pedigreeRepeats();health();surfaces("structureRail",profileData.structure);surfaces("temperamentRail",profileData.temperament);metrics("performanceRail",profileData.performance,1);metrics("reproductionRail",profileData.reproduction,1);related();metrics("breedingLensRail",profileData.breedingLens,-1);',
    'core();gallery();anchorMovement();bloodline(profileData.pedigreeDepth||4);pedigreeIntelligence();pedigreeRepeats();health();surfaces("structureRail",profileData.structure);surfaces("temperamentRail",profileData.temperament);metrics("performanceRail",profileData.performance,1);metrics("reproductionRail",profileData.reproduction,1);related();breedingLens();'
)

# 5) Replace bloodline renderer with an interactive genealogical branch explorer.
start = s.find('    function bloodline(depth=4){')
end = s.find('\n\n    function pedigreeRepeats()', start)
if start < 0 or end < 0:
    raise SystemExit('bloodline function not found')
new_bloodline = r'''    let bloodlineFocusPath="";

    function bloodline(depth=4,focusPath=bloodlineFocusPath,scrollForward=false){
      const entries=profileData.bloodline.filter(x=>x.gen<=depth);
      const byPath=new Map(entries.map(item=>[item.path,item]));
      if(focusPath&&!byPath.has(focusPath))focusPath="";
      bloodlineFocusPath=focusPath;
      byId("bloodlineDepthLabel").textContent=`${depth}-generation interactive pedigree`;

      const crumb=[profileData.name];
      for(let i=1;i<=focusPath.length;i++){
        const item=byPath.get(focusPath.slice(0,i));
        if(item)crumb.push(item.name);
      }
      const breadcrumb=`<div class="bloodline-breadcrumb">${crumb.map((name,index)=>`${index?'<i></i>':''}<span>${escapeHTML(name)}</span>`).join("")}</div>`;

      const subject=`<div class="bloodline-column bloodline-root"><div class="bloodline-generation-head"><span>Subject</span><span>DI record</span></div><article class="bloodline-subject"><div class="ancestor-visual"><img src="${escapeHTML(profileData.heroImage)}" alt="${escapeHTML(profileData.name)}" style="object-position:${escapeHTML(profileData.heroPosition||'50% 50%')}"><span class="ancestor-gen">DI</span></div><div class="ancestor-info"><small>Indexed Doberman</small><h4>${escapeHTML(profileData.name)}</h4><p>${escapeHTML(profileData.core.registrationNumber||profileData.core.profileId)} · ${escapeHTML(profileData.country||'')}</p><span class="ancestor-open">Choose sire or dam →</span></div></article></div>`;

      const columns=[subject];
      const visibleGenerations=Math.min(depth,focusPath.length+1);
      for(let gen=1;gen<=visibleGenerations;gen++){
        const parentPath=gen===1?"":focusPath.slice(0,gen-1);
        const candidates=[parentPath+"S",parentPath+"D"].map(path=>byPath.get(path)).filter(Boolean);
        if(!candidates.length)break;
        const selectedPath=focusPath.slice(0,gen);
        const cards=candidates.map(x=>{
          const metadata=[x.registration,x.country].map(value=>present(value,"")).filter(Boolean);
          const visual=x.image?`<img src="${escapeHTML(x.image)}" alt="${escapeHTML(x.name)}" loading="lazy">`:`<div class="ancestor-monogram">${escapeHTML(x.name.charAt(0)||"D")}</div>`;
          const source=x.imageSource?`<p class="ancestor-media-source">Image: ${escapeHTML(x.imageSource)}</p>`:"";
          const hasParents=gen<depth&&(byPath.has(x.path+"S")||byPath.has(x.path+"D"));
          const selected=x.path===selectedPath;
          return `<button class="ancestor v43-ancestor${selected?' is-selected':''}" type="button" data-bloodline-path="${escapeHTML(x.path)}" aria-pressed="${selected?'true':'false'}" aria-label="Open parents of ${escapeHTML(x.name)}"><div class="ancestor-visual">${visual}<span class="ancestor-gen">G${gen}</span></div><div class="ancestor-info"><small>${escapeHTML(x.role)} · ${escapeHTML(x.sex||"ancestor")}</small><h4>${escapeHTML(x.name)}</h4><p>${metadata.map(escapeHTML).join(" · ")||"Canonical pedigree node"}</p>${source}<span class="ancestor-open">${hasParents?'Open parents →':'Mapped boundary'}</span></div></button>`;
        }).join("");
        columns.push(`<div class="bloodline-column" data-bloodline-generation="${gen}"><div class="bloodline-generation-head"><span>Generation ${gen}</span><span>${candidates.length===2?'Sire + dam':'Mapped branch'}</span></div>${cards}</div>`);
      }
      const rail=byId("bloodlineRail");
      rail.innerHTML=breadcrumb+`<div class="bloodline-tree">${columns.join("")}</div>`;
      rail.querySelectorAll('[data-bloodline-path]').forEach(button=>button.addEventListener('click',()=>{
        const path=button.dataset.bloodlinePath||"";
        const hasNext=byPath.has(path+"S")||byPath.has(path+"D");
        bloodline(depth,hasNext?path:path,true);
      }));
      if(scrollForward){
        requestAnimationFrame(()=>{
          const tree=rail.querySelector('.bloodline-tree');
          const last=tree?.lastElementChild;
          if(tree&&last)tree.scrollTo({left:Math.max(0,last.offsetLeft-tree.clientWidth*.08),behavior:'smooth'});
        });
      }
    }
'''
s = s[:start] + new_bloodline + s[end:]

# 6) Insert dedicated renderers before pedigreeRepeats.
marker = '    function pedigreeRepeats(){'
if marker not in s:
    raise SystemExit('pedigreeRepeats marker not found')
renderers = r'''    function pedigreeIntelligence(){
      const d=profileData.pedigreeIntelligence||{};
      const defs=[
        ["COI","Coefficient of inbreeding (COI)",d["Coefficient of inbreeding (COI)"],"Pedigree-based coefficient",true],
        ["AVK","Ancestor loss (AVK)",d["Ancestor loss (AVK)"],"Unique ancestors across mapped positions",false],
        ["MAP","Pedigree completeness",d["Pedigree completeness"],"Known positions at analysed depth",false],
        ["REPEAT","Repeated ancestors",d["Repeated ancestors"],"Distinct ancestors appearing more than once",false],
        ["UNIQUE","Unique ancestors",d["Unique ancestors"],"Distinct mapped ancestors",false],
        ["DEPTH","Analysed depth",d["Analysed depth"],"Canonical pedigree depth",false]
      ];
      byId("pedigreeIntelligenceRail").innerHTML=defs.map(([code,label,raw,sub,primary])=>{
        let value=present(raw,"—"),unit="";
        if(code==="DEPTH"){
          const match=String(value).match(/^(\d+)/); value=match?match[1]:value; unit="generations";
        }
        return `<article class="pi-card${primary?' is-primary':''}"><span class="pi-code">${escapeHTML(code)}</span><div class="pi-value"><strong>${escapeHTML(value)}</strong>${unit?`<span>${escapeHTML(unit)}</span>`:''}</div><h3>${escapeHTML(label)}</h3><p>${escapeHTML(sub)}</p></article>`;
      }).join("");
    }

    function breedingLens(){
      const labels={Preserve:["01","Preserve","What the current record suggests protecting in future combinations."],Complement:["02","Complement","What a selected mate can add or strengthen."],Watch:["03","Watch","Health, lineage or phenotype points that deserve deliberate attention."],Unknown:["04","Extend","Information that would deepen the decision context as the living record grows."]};
      byId("breedingLensRail").innerHTML=Object.entries(profileData.breedingLens||{}).map(([key,value])=>{
        const meta=labels[key]||["—",key,"Record context"];
        return `<article class="lens-card"><div class="lens-meta"><span>${meta[0]}</span><span>Breeding lens</span></div><h3>${escapeHTML(meta[1])}</h3><p>${escapeHTML(value)}</p></article>`;
      }).join("");
    }

'''
s = s.replace(marker, renderers + marker, 1)

MALE.write_text(s, encoding="utf-8")
print("v4.3 interaction pass applied")
