#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MALE = ROOT / 'profiles' / 'male.html'
SUBMIT = ROOT / 'submit.html'
SUBMIT_JS = ROOT / 'assets' / 'js' / 'submit-v3.js'
DANTE = ROOT / 'data' / 'dobermans' / 'DI-M-000001.json'


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f'v4.3 migration could not find {label}')
    return text.replace(old, new, 1)


def patch_male() -> None:
    s = MALE.read_text(encoding='utf-8')
    s = must_replace(s,
        '<p class="section-note"><b>Three-generation view</b>Move through the pedigree as a connected line. Indexed ancestors can open as individual profiles.</p>',
        '<p class="section-note"><b id="bloodlineDepthLabel">Mapped pedigree</b>Explore the full mapped ancestry as a visual lineage network. Open each generation, inspect repeated ancestors and follow indexed records.</p>',
        'bloodline description')
    s = must_replace(s,
        '<div class="section-content slider reveal" id="bloodlineRail"></div>',
        '<div class="section-content bloodline-network reveal" id="bloodlineRail"></div>',
        'bloodline rail')
    s = must_replace(s,
        '<div class="metric-grid" id="pedigreeIntelligenceRail"></div>',
        '<div class="metric-grid pedigree-intelligence-grid" id="pedigreeIntelligenceRail"></div><div class="pedigree-repeats" id="pedigreeRepeatedRail"></div>',
        'pedigree intelligence rail')
    s = must_replace(s,
        '<p class="section-note"><b>No competitive counters</b>Notable progeny may be shown by name. Descendant counts are derived only from records actually connected inside Doberman Index.</p>',
        '<p class="section-note"><b>Lineage in motion</b>Named progeny, connected litters and indexed descendants extend one Doberman record into a growing lineage history.</p>',
        'lineage-forward note')
    s = must_replace(s,
        '<p class="impact-intro-copy">The record follows meaningful lineage connections without asking owners to estimate litter totals, offspring totals or export reach.</p>',
        '<p class="impact-intro-copy">Each connected descendant adds another verified relationship to the living lineage map and reveals how this bloodline continues through indexed generations.</p>',
        'lineage-forward intro')
    s = must_replace(s,
        '<p class="section-note"><b>Living network</b>Parents, littermates and directly connected indexed Dobermans stay one tap away.</p>',
        '<p class="section-note"><b>Beyond ancestry</b>Littermates, half-siblings, offspring and linked litters extend the record sideways and forward. Ancestors remain inside Bloodline Network.</p>',
        'related note')

    css = r'''

    /* v4.3 — Record Intelligence */
    #bloodlineRail{display:grid;grid-template-columns:repeat(4,minmax(230px,1fr));gap:14px;overflow-x:auto;padding-bottom:6px;scroll-snap-type:x proximity}
    .bloodline-generation{min-width:230px;display:flex;flex-direction:column;gap:10px;scroll-snap-align:start}
    .bloodline-generation-head{display:flex;align-items:center;justify-content:space-between;padding:0 2px 9px;border-bottom:1px solid #c9c9c3;color:var(--muted);font-size:9px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
    .ancestor.v43-ancestor{min-width:0;min-height:238px;padding:0;display:grid;grid-template-rows:112px 1fr;border:1px solid #d4d4ce;background:#f6f6f2;color:var(--ink);overflow:hidden;text-decoration:none;transition:transform .3s var(--ease),background .3s var(--ease),border-color .3s var(--ease)}
    .ancestor.v43-ancestor:hover{transform:translateY(-3px);background:var(--white);border-color:#a9a9a3}
    .ancestor-visual{position:relative;overflow:hidden;background:#151515;color:var(--white)}
    .ancestor-visual img{width:100%;height:100%;object-fit:cover;display:block;filter:grayscale(1);transition:filter .35s var(--ease),transform .5s var(--ease)}
    .ancestor.v43-ancestor:hover .ancestor-visual img{filter:grayscale(0);transform:scale(1.025)}
    .ancestor-monogram{height:100%;display:flex;align-items:center;justify-content:center;font-size:54px;font-weight:800;letter-spacing:-.08em}
    .ancestor-gen{position:absolute;left:10px;top:10px;padding:5px 7px;background:var(--acid);color:var(--ink);font-size:8px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
    .ancestor-info{padding:13px 14px 15px;display:flex;flex-direction:column;gap:6px}
    .ancestor-info small{color:var(--muted);font-size:8px;font-weight:700;letter-spacing:.07em;text-transform:uppercase}
    .ancestor-info h4{margin:0;font-size:17px;line-height:.98;letter-spacing:-.045em}
    .ancestor-info p{margin:auto 0 0;color:var(--muted);font-size:9px;line-height:1.45}
    .ancestor-media-source{font-size:8px!important;color:#85857f!important}
    .pedigree-intelligence-grid{grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
    .pedigree-intelligence-grid .metric{min-height:270px;padding:22px 18px;border:1px solid #292929;border-top:1px solid #292929;background:#111;color:#fff}
    .pedigree-intelligence-grid .metric strong{font-size:clamp(56px,6.2vw,94px);line-height:.86;overflow-wrap:anywhere}
    .pedigree-intelligence-grid .metric em{font-size:12px;line-height:1.1}
    .pedigree-intelligence-grid .metric::after{font-size:9px;line-height:1.35;color:#9a9a95}
    .pedigree-intelligence-grid .metric.highlight{background:var(--acid);color:var(--ink);border-color:var(--acid)}
    .pedigree-intelligence-grid .metric.highlight::after{color:#3a3a34}
    .pedigree-repeats{margin-top:16px;display:flex;flex-wrap:wrap;gap:8px}
    .pedigree-repeat-chip{padding:8px 11px;border:1px solid #c8c8c2;background:#f6f6f2;font-size:9px;font-weight:650}
    #breedingLensRail{grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
    #breedingLensRail .metric{min-height:280px;padding:22px;background:#111;color:#fff;border:1px solid #2b2b2b}
    #breedingLensRail .metric strong{position:static;margin:0 0 18px;font-size:clamp(28px,3vw,44px);line-height:.95;letter-spacing:-.05em}
    #breedingLensRail .metric em{order:-1;margin:0 0 auto;color:#aaa;font-size:10px;text-transform:uppercase;letter-spacing:.08em}
    #breedingLensRail .metric::after{margin-top:16px}
    #performanceRail .metric[role="button"]{cursor:none}
    #performanceRail .metric[aria-expanded="true"]{outline:2px solid var(--acid);outline-offset:3px}
    .performance-detail-note{margin:0;padding:18px 0;color:var(--muted);font-size:12px;line-height:1.55}
    @media(max-width:1100px){.pedigree-intelligence-grid{grid-template-columns:repeat(2,minmax(0,1fr))}#bloodlineRail{grid-template-columns:repeat(4,minmax(210px,72vw))}}
    @media(max-width:700px){.pedigree-intelligence-grid,#breedingLensRail{grid-template-columns:1fr}.pedigree-intelligence-grid .metric{min-height:220px}.pedigree-intelligence-grid .metric strong{font-size:clamp(58px,20vw,86px)}#bloodlineRail{grid-template-columns:repeat(4,minmax(82vw,1fr))}}
'''
    if '/* v4.3 — Record Intelligence */' not in s:
        s = s.replace('</style>', css + '\n  </style>', 1)

    # Add canonical bloodline builder before canonicalToProfile.
    anchor = '    function canonicalToProfile(record,recordId,parentIdentities=new Map()){'
    if anchor not in s:
        raise SystemExit('v4.3 migration could not find canonicalToProfile')
    helper = r'''
    function buildCanonicalBloodline(recordId,graph,depth=4){
      const nodes=graph?.nodes||{};
      if(!nodes[recordId])return [];
      const out=[];
      let frontier=[{id:recordId,path:""}];
      for(let gen=1;gen<=depth;gen++){
        const next=[];
        frontier.forEach(item=>{
          const node=nodes[item.id];
          if(!node)return;
          [[node.sire_id,"S"],[node.dam_id,"D"]].forEach(([id,side])=>{
            if(!id||!nodes[id])return;
            const ancestor=nodes[id];
            const path=item.path+side;
            const role=gen===1?(side==="S"?"Sire":"Dam"):(path[0]==="S"?"Paternal line":"Maternal line");
            const image=ancestor.approved_image&&ancestor.image_rights_status==="approved"?mediaUrl(ancestor.approved_image):"";
            out.push({gen,role,name:displayRegisteredName(ancestor.registered_name||id),registration:array(ancestor.registration_numbers)[0]||"",country:ancestor.country||"",sex:ancestor.sex||"",url:ancestor.source_record_id?profileUrl(ancestor.source_record_id):"#bloodline",image,imageSource:ancestor.image_source_label||"",imageSourceUrl:ancestor.image_source_url||"",canonicalId:id,path});
            next.push({id,path});
          });
        });
        frontier=next;
      }
      return out;
    }

    function repeatedAncestorView(record,graph){
      const intelligence=record?.doberman?.pedigree_intelligence||{};
      return array(intelligence.repeated_ancestors).map(item=>({name:item.name||graph?.nodes?.[item.record_id]?.registered_name||item.record_id,occurrences:item.occurrences||0}));
    }

'''
    s = s.replace(anchor, helper + '    function canonicalToProfile(record,recordId,parentIdentities=new Map(),graph=null){', 1)

    old_pi = '        pedigreeIntelligence:{"Pedigree COI": pedigreeIntelligence.coi_percent != null ? `${Number(pedigreeIntelligence.coi_percent).toFixed(2)}%` : "Pending mapping","Completeness": pedigreeIntelligence.completeness_percent != null ? `${Number(pedigreeIntelligence.completeness_percent).toFixed(0)}%` : "Pending mapping","Repeated ancestors": pedigreeIntelligence.repeated_ancestors_count ?? "—","Unique ancestors": pedigreeIntelligence.unique_ancestors_count ?? "—"},'
    new_pi = '        pedigreeIntelligence:{"Coefficient of inbreeding (COI)": pedigreeIntelligence.coi_percent != null ? `${Number(pedigreeIntelligence.coi_percent).toFixed(2)}%` : "Pending mapping","Ancestor loss (AVK)": pedigreeIntelligence.avk_percent != null ? `${Number(pedigreeIntelligence.avk_percent).toFixed(2)}%` : "Pending mapping","Pedigree completeness": pedigreeIntelligence.completeness_percent != null ? `${Number(pedigreeIntelligence.completeness_percent).toFixed(0)}%` : "Pending mapping","Repeated ancestors": pedigreeIntelligence.repeated_ancestors_count ?? "—","Unique ancestors": pedigreeIntelligence.unique_ancestors_count ?? "—","Analysed depth": pedigreeIntelligence.generation_depth ? `${pedigreeIntelligence.generation_depth} generations` : "—"},'
    s = must_replace(s, old_pi, new_pi, 'pedigree metrics object')
    s = must_replace(s,
        '        performanceDetails:{Titles:array(performance.titles)},',
        '        performanceDetails:{Shows:array(performance.show_results),Titles:array(performance.titles),"Working exams":array(performance.working_exams),Sports:array(performance.sports)},',
        'performance details')
    s = must_replace(s,
        '        bloodline:buildBloodline(parentage,parentIdentities),gallery:buildGallery(media),related:buildRelated(recordId,parentage,reproduction),',
        '        bloodline:buildCanonicalBloodline(recordId,graph,Number(pedigreeIntelligence.generation_depth)||4),pedigreeDepth:Number(pedigreeIntelligence.generation_depth)||4,repeatedAncestors:repeatedAncestorView(record,graph),gallery:buildGallery(media),related:buildRelated(recordId,parentage,reproduction).filter(item=>!["Sire","Dam"].includes(item.type)),',
        'canonical bloodline binding')

    # Load graph alongside profile.
    old_load = '      const parentIdentities=await loadPedigreeIdentities(record.doberman?.parentage||{});\n      return canonicalToProfile(record,recordId,parentIdentities);'
    new_load = '      const parentIdentities=await loadPedigreeIdentities(record.doberman?.parentage||{});\n      const graph=await fetch(new URL("data/pedigree-graph.json",repoRoot),{cache:"no-store"}).then(response=>{if(!response.ok)throw new Error("Pedigree graph unavailable");return response.json()});\n      return canonicalToProfile(record,recordId,parentIdentities,graph);'
    s = must_replace(s, old_load, new_load, 'graph load')

    # Replace captions and make all performance tiles expandable.
    old_captions = '      const captions={Shows:"submitted entries",Titles:"championship record","Working exams":"submitted exams",Sports:"active disciplines","Notable progeny":"owner-named highlight","Connected descendants":"index-derived","Connected litters":"index-derived","Record basis":"source model","Pedigree COI":"known ancestry","Completeness":"known pedigree slots","Repeated ancestors":"within analysed depth","Unique ancestors":"within analysed depth",Preserve:"record context",Complement:"record context",Watch:"record context",Unknown:"explicit uncertainty"};'
    new_captions = '      const captions={Shows:"show entries with event-level details",Titles:"championship and official titles","Working exams":"exam, level and result",Sports:"sporting disciplines and competition results","Notable progeny":"named lineage highlights","Connected descendants":"index-derived","Connected litters":"index-derived","Record basis":"source model","Coefficient of inbreeding (COI)":"pedigree-based inbreeding coefficient","Ancestor loss (AVK)":"unique ancestors / maximum ancestor positions","Pedigree completeness":"known pedigree positions","Repeated ancestors":"within analysed depth","Unique ancestors":"within analysed depth","Analysed depth":"canonical pedigree depth",Preserve:"record synthesis",Complement:"mate-selection context",Watch:"health and lineage considerations",Unknown:"what would deepen the analysis"};'
    s = must_replace(s, old_captions, new_captions, 'metric captions')
    s = must_replace(s,
        '        const expandable=id==="performanceRail"&&k==="Titles";',
        '        const expandable=id==="performanceRail";',
        'performance expandability')

    # Replace title-only dropdown renderer with generic performance renderer.
    start = s.find('    function toggleTitleListing(card){')
    end = s.find('\n\n    function bloodline(', start)
    if start < 0 or end < 0:
        raise SystemExit('v4.3 migration could not find title dropdown function')
    generic = r'''    function togglePerformanceListing(card){
      const panel=byId("performanceDetails");
      const key=card.dataset.metricKey;
      const entries=array(profileData.performanceDetails?.[key]).filter(Boolean);
      const opening=panel.hidden||panel.dataset.activeKey!==key;
      document.querySelectorAll('#performanceRail [aria-expanded="true"]').forEach(item=>item.setAttribute("aria-expanded","false"));
      if(!opening){panel.hidden=true;panel.dataset.activeKey="";return}
      card.setAttribute("aria-expanded","true");
      panel.dataset.activeKey=key;
      const explanations={Shows:"Each line is one submitted show or show result. Future records capture event name and result rather than a count alone.",Titles:"Official championship and recognized titles submitted for this record.","Working exams":"Formal working qualifications with level/result where supplied.",Sports:"Competitive or organized sporting disciplines outside the formal working-exam list; leave this empty when the Doberman has no separate sport record."};
      const legacyCount=key==="Shows"?Number(profileData.performance?.Shows||0):0;
      const body=entries.length?`<ol class="performance-title-list">${entries.map((entry,index)=>`<li><span>${String(index+1).padStart(2,"0")}</span>${escapeHTML(typeof entry==="string"?entry:(entry.label||entry.name||JSON.stringify(entry)))}</li>`).join("")}</ol>`:(legacyCount?`<p class="performance-detail-note">${legacyCount} show entries were recorded in the original profile, but event-level names were not captured by the earlier intake. v4.3 records the show and result line by line.</p>`:`<p class="performance-detail-note">${escapeHTML(explanations[key]||"No detailed entries submitted for this category.")}</p>`);
      panel.innerHTML=`<div class="performance-detail-head"><h3>${escapeHTML(key)}.</h3><small>${String(entries.length||legacyCount).padStart(2,"0")} recorded</small></div>${body}<p class="performance-detail-note">${escapeHTML(explanations[key]||"")}</p>`;
      panel.hidden=false;
    }'''
    s = s[:start] + generic + s[end:]

    # Replace bloodline renderer with grouped four-generation visual cards.
    start = s.find('    function bloodline(depth=3){')
    end = s.find('\n\n    function heroMetadata()', start)
    if start < 0 or end < 0:
        raise SystemExit('v4.3 migration could not find bloodline renderer')
    bloodline = r'''    function bloodline(depth=4){
      const entries=profileData.bloodline.filter(x=>x.gen<=depth);
      byId("bloodlineDepthLabel").textContent=`${depth}-generation canonical view`;
      const groups=[];
      for(let gen=1;gen<=depth;gen++){
        const group=entries.filter(item=>item.gen===gen);
        if(!group.length)continue;
        groups.push(`<div class="bloodline-generation"><div class="bloodline-generation-head"><span>Generation ${gen}</span><span>${group.length} ancestor${group.length===1?"":"s"}</span></div>${group.map(x=>{
          const metadata=[x.registration,x.country].map(value=>present(value,"")).filter(Boolean);
          const visual=x.image?`<img src="${escapeHTML(x.image)}" alt="${escapeHTML(x.name)}" loading="lazy">`:`<div class="ancestor-monogram">${escapeHTML(x.name.charAt(0)||"D")}</div>`;
          const source=x.imageSource?`<p class="ancestor-media-source">Image: ${escapeHTML(x.imageSource)}</p>`:"";
          return `<a href="${escapeHTML(x.url||"#bloodline")}" class="ancestor v43-ancestor"><div class="ancestor-visual">${visual}<span class="ancestor-gen">G${gen}</span></div><div class="ancestor-info"><small>${escapeHTML(x.role)} · ${escapeHTML(x.sex||"ancestor")}</small><h4>${escapeHTML(x.name)}</h4><p>${metadata.map(escapeHTML).join(" · ")||"Canonical pedigree node"}</p>${source}</div></a>`;
        }).join("")}</div>`);
      }
      byId("bloodlineRail").innerHTML=groups.length?groups.join(""):'<div class="ancestor"><div class="ancestor-body"><h4>Pedigree mapping pending</h4><p>The lineage network appears as soon as canonical pedigree nodes are mapped.</p></div></div>';
    }

    function pedigreeRepeats(){
      const rail=byId("pedigreeRepeatedRail");
      const items=array(profileData.repeatedAncestors);
      rail.innerHTML=items.length?items.map(item=>`<span class="pedigree-repeat-chip">↻ ${escapeHTML(item.name)} · ${escapeHTML(item.occurrences)} occurrences</span>`).join(""):'<span class="pedigree-repeat-chip">No repeated ancestor inside the analysed depth</span>';
    }'''
    s = s[:start] + bloodline + s[end:]

    old_init = '      core();gallery();anchorMovement();bloodline(3);metrics("pedigreeIntelligenceRail",profileData.pedigreeIntelligence,1);health();surfaces("structureRail",profileData.structure);surfaces("temperamentRail",profileData.temperament);metrics("performanceRail",profileData.performance,1);metrics("reproductionRail",profileData.reproduction,1);related();metrics("breedingLensRail",profileData.breedingLens,1);'
    new_init = '      core();gallery();anchorMovement();bloodline(profileData.pedigreeDepth||4);metrics("pedigreeIntelligenceRail",profileData.pedigreeIntelligence,0);pedigreeRepeats();health();surfaces("structureRail",profileData.structure);surfaces("temperamentRail",profileData.temperament);metrics("performanceRail",profileData.performance,1);metrics("reproductionRail",profileData.reproduction,1);related();metrics("breedingLensRail",profileData.breedingLens,-1);'
    s = must_replace(s, old_init, new_init, 'initialize profile')

    old_events = '''    byId("performanceRail").addEventListener("click",event=>{
      const card=event.target.closest('[data-metric-key="Titles"]');
      if(card)toggleTitleListing(card);
    });
    byId("performanceRail").addEventListener("keydown",event=>{
      if(event.key!=="Enter"&&event.key!==" ")return;
      const card=event.target.closest('[data-metric-key="Titles"]');
      if(!card)return;
      event.preventDefault();
      toggleTitleListing(card);
    });'''
    new_events = '''    byId("performanceRail").addEventListener("click",event=>{
      const card=event.target.closest('[data-metric-key]');
      if(card)togglePerformanceListing(card);
    });
    byId("performanceRail").addEventListener("keydown",event=>{
      if(event.key!=="Enter"&&event.key!==" ")return;
      const card=event.target.closest('[data-metric-key]');
      if(!card)return;
      event.preventDefault();
      togglePerformanceListing(card);
    });'''
    s = must_replace(s, old_events, new_events, 'performance events')

    MALE.write_text(s, encoding='utf-8')


def patch_submit() -> None:
    s = SUBMIT.read_text(encoding='utf-8')
    old = '''<div class="field-grid">
<label class="field"><span>Shows</span><input min="0" name="shows_count" type="number"/></label>
<label class="field"><span>Titles</span><textarea name="titles" placeholder="One title abbreviation per line · put the two hero titles first." rows="3"></textarea></label>
<label class="field"><span>Working exams</span><textarea name="working_exams" placeholder="Exact exam + level." rows="3"></textarea></label>
<label class="field"><span>Sports</span><textarea name="sports" placeholder="One discipline or result per line." rows="3"></textarea></label>
</div>'''
    new = '''<div class="field-grid">
<label class="field"><span>Shows &amp; show results</span><textarea name="show_results" placeholder="One event/result per line · e.g. IDS Belgrade — CAC, CACIB, BOB" rows="3"></textarea><small>List the event and result when you know it. The Index derives the count from these entries.</small></label>
<label class="field"><span>Titles</span><textarea name="titles" placeholder="One official title per line · e.g. Champion of Serbia in Beauty" rows="3"></textarea><small>Use the complete title rather than only a number.</small></label>
<label class="field"><span>Working exams</span><textarea name="working_exams" placeholder="One qualification per line · e.g. BH-VT · IGP 1" rows="3"></textarea><small>Formal working qualifications and levels belong here.</small></label>
<label class="field"><span>Sports</span><textarea name="sports" placeholder="One discipline or competition result per line" rows="3"></textarea><small>For organized sporting disciplines or competition results outside the formal working-exam list. Leave blank when none apply.</small></label>
</div>'''
    s = must_replace(s, old, new, 'performance intake')
    SUBMIT.write_text(s, encoding='utf-8')


def patch_submit_js() -> None:
    s = SUBMIT_JS.read_text(encoding='utf-8')
    s = s.replace('shows_count: numberValue("shows_count"),', 'show_results: listValue("show_results"),\n          shows_count: listValue("show_results").length,', 1)
    # If a review summary references the old numeric input, derive from detailed lines.
    s = s.replace('numberValue("shows_count")', 'listValue("show_results").length')
    SUBMIT_JS.write_text(s, encoding='utf-8')


def patch_dante() -> None:
    payload = json.loads(DANTE.read_text(encoding='utf-8'))
    dog = payload['doberman']
    perf = dog.setdefault('performance', {})
    perf.setdefault('show_results', [])
    dog['breeding_lens'] = {
        'status': 'generated',
        'preserve': 'Balanced, elegant type · strong topline · free, elastic movement · stable high drive · proven IGP 1 working qualification.',
        'complement': 'Prioritize high confidence, stable social behaviour and structural compatibility while protecting overall balance and movement.',
        'watch': 'DCM1 carrier status remains a pairing consideration together with the current Holter + Echo status and the selected female’s cardiac and genetic profile.',
        'unknown': 'The mapped four-generation pedigree is complete at the analysed depth. Deeper ancestry and event-level show history can extend the analysis further.'
    }
    DANTE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    patch_male()
    patch_submit()
    patch_submit_js()
    patch_dante()
    print('v4.3 record-intelligence migration applied')


if __name__ == '__main__':
    main()
