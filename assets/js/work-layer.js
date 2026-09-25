(function(){
  "use strict";

  const scriptUrl = document.currentScript?.src ? new URL(document.currentScript.src, location.href) : null;
  const siteRoot = scriptUrl ? new URL("../../", scriptUrl) : new URL("/", location.href);
  const list = value => Array.isArray(value) ? value.filter(Boolean) : [];
  const text = value => value === null || value === undefined ? "" : String(value).trim();
  const escapeSelectorValue = value => String(value).replace(/["\\]/g, "\\$&");
  const siteUrl = path => {
    const raw = text(path);
    if (!raw) return "";
    if (/^https?:\/\//i.test(raw)) return raw;
    return new URL(raw.replace(/^(\.\.\/)+/,"").replace(/^\/+/, ""), siteRoot).href;
  };
  const fetchJson = async path => {
    const response = await fetch(siteUrl(path), {cache:"no-store"});
    if (!response.ok) throw new Error("Unable to load "+path);
    return response.json();
  };
  const mediaPath = item => text(typeof item === "string" ? item : item?.path);
  const mediaCaption = (item, fallback) => text(typeof item === "object" ? item?.caption : "") || fallback;
  const videoUrl = item => text(typeof item === "string" ? item : item?.url);
  const videoLabel = (item, index) => text(typeof item === "object" ? item?.label : "") || `Work video ${String(index+1).padStart(2,"0")}`;
  const isWorkingDog = record => {
    const dog = record?.doberman || {};
    const perf = dog.performance || {};
    const media = dog.media || {};
    return list(perf.working_exams).length || list(perf.sports).length || list(media.work_gallery).length || list(media.work_videos).length;
  };

  function stat(label,value){
    const card=document.createElement("div"); card.className="di-work-stat";
    const key=document.createElement("span"); key.textContent=label;
    const strong=document.createElement("strong"); strong.textContent=value || "—";
    card.append(key,strong); return card;
  }

  function renderDogWork(section, record){
    const dog=record?.doberman || {};
    const perf=dog.performance || {};
    const media=dog.media || {};
    const exams=list(perf.working_exams);
    const sports=list(perf.sports);
    const photos=list(media.work_gallery).slice(0,20);
    const videos=list(media.work_videos).slice(0,10);
    if(!exams.length && !sports.length && !photos.length && !videos.length) return;

    const summary=section.querySelector("[data-work-summary]");
    summary.replaceChildren(
      stat("Working exams", exams.length ? exams.join(" · ") : "Not submitted"),
      stat("Sports", sports.length ? sports.join(" · ") : "Not submitted"),
      stat("Work gallery", photos.length ? `${photos.length} photos` : "No media"),
      stat("Work videos", videos.length ? `${videos.length} links` : "No media")
    );

    const rail=section.querySelector("[data-work-media]");
    rail.replaceChildren();
    photos.forEach((item,index)=>{
      const src=siteUrl(mediaPath(item)); if(!src) return;
      const figure=document.createElement("figure"); figure.className="di-work-media-card";
      const img=document.createElement("img"); img.src=src; img.loading=index ? "lazy" : "eager"; img.alt=`${text(dog.identity?.registered_name)||"Doberman"} — work photo ${index+1}`;
      const caption=document.createElement("figcaption"); caption.textContent=mediaCaption(item,`Work ${String(index+1).padStart(2,"0")}`);
      const count=document.createElement("small"); count.textContent=`${String(index+1).padStart(2,"0")} / ${String(photos.length).padStart(2,"0")}`;
      figure.append(img,caption,count); rail.append(figure);
    });
    videos.forEach((item,index)=>{
      const url=videoUrl(item); if(!/^https?:\/\//i.test(url)) return;
      const link=document.createElement("a"); link.className="di-work-video-card"; link.href=url; link.target="_blank"; link.rel="noopener noreferrer";
      const small=document.createElement("small"); small.textContent=`WORK VIDEO · ${String(index+1).padStart(2,"0")}`;
      const strong=document.createElement("strong"); strong.textContent=videoLabel(item,index);
      const span=document.createElement("span"); span.textContent="Open video ↗";
      link.append(small,strong,span); rail.append(link);
    });
    if(!rail.children.length){
      const empty=document.createElement("p"); empty.className="di-work-empty-media"; empty.textContent="Working qualifications are recorded. Work media has not been added to this profile.";
      rail.append(empty);
    }

    section.hidden=false;
    section.querySelectorAll(".reveal").forEach(node=>node.classList.add("is-visible"));
    document.querySelectorAll("[data-work-nav]").forEach(link=>link.hidden=false);
  }

  async function initDog(){
    const section=document.querySelector('[data-di-work-layer="dog"]');
    if(!section) return;
    const id=(new URLSearchParams(location.search).get("id") || document.getElementById("heroProfileId")?.textContent || "").trim().toUpperCase();
    if(!/^DI-[MF]-\d{6}$/.test(id)) return;
    try{ renderDogWork(section, await fetchJson(`data/dobermans/${id}.json`)); }catch(error){ console.warn("Doberman Index work layer unavailable",error); }
  }

  function workDogCard(record){
    const dog=record.doberman || {};
    const identity=dog.identity || {};
    const perf=dog.performance || {};
    const media=dog.media || {};
    const exams=list(perf.working_exams), sports=list(perf.sports), photos=list(media.work_gallery), videos=list(media.work_videos);
    const sex=identity.sex === "female" ? "female" : "male";
    const link=document.createElement("a"); link.className="di-work-dog-card"; link.href=siteUrl(`profiles/${sex}/?id=${record.record_id}#work`);
    const top=document.createElement("div"); top.className="top";
    const id=document.createElement("span"); id.textContent=record.record_id;
    const rule=document.createElement("i");
    const badge=document.createElement("b"); badge.className="di-work-badge"; badge.textContent="WORK";
    top.append(id,rule,badge);
    const body=document.createElement("div"); body.className="body";
    const name=document.createElement("strong"); name.textContent=text(identity.registered_name)||record.record_id;
    const meta=document.createElement("span");
    const details=[];
    if(exams.length) details.push(exams.join(" · "));
    if(sports.length) details.push(sports.join(" · "));
    if(photos.length) details.push(`${photos.length} work photos`);
    if(videos.length) details.push(`${videos.length} work videos`);
    meta.textContent=details.join(" · ") || "Working record";
    body.append(name,meta); link.append(top,body); return link;
  }

  function ledgerRow(label,value){
    const row=document.createElement("div");
    const span=document.createElement("span"); span.textContent=label;
    const strong=document.createElement("strong"); strong.textContent=String(value);
    row.append(span,strong); return row;
  }

  async function initKennel(){
    const section=document.querySelector('[data-di-work-layer="kennel"]');
    if(!section) return;
    const queryId=(new URLSearchParams(location.search).get("id")||"").trim().toUpperCase();
    const fallback=(document.querySelector("[data-record-id]")?.textContent||"DI-K-000001").trim().toUpperCase();
    const kennelId=/^DI-K-\d{6}$/.test(queryId)?queryId:fallback;
    if(!/^DI-K-\d{6}$/.test(kennelId)) return;
    try{
      const [kennelRecord,registry]=await Promise.all([fetchJson(`data/kennels/${kennelId}.json`),fetchJson("data/registry.json")]);
      const kennel=kennelRecord.kennel || {};
      const ids=new Set(list(kennel.dog_ids));
      list(registry.records).filter(item=>item?.entity_type==="doberman"&&item?.kennel_id===kennelId).forEach(item=>ids.add(item.record_id));
      const records=(await Promise.all([...ids].filter(id=>/^DI-[MF]-\d{6}$/.test(id)).map(id=>fetchJson(`data/dobermans/${id}.json`).catch(()=>null)))).filter(Boolean);
      const working=records.filter(isWorkingDog);
      const workingResults=working.reduce((sum,item)=>sum+list(item.doberman?.performance?.working_exams).length+list(item.doberman?.performance?.sports).length,0);
      const photoCount=working.reduce((sum,item)=>sum+list(item.doberman?.media?.work_gallery).length,0);
      const videoCount=working.reduce((sum,item)=>sum+list(item.doberman?.media?.work_videos).length,0);
      document.querySelectorAll('[data-system-metric="working_dobermans"]').forEach(node=>node.textContent=String(working.length));
      document.querySelectorAll('[data-system-metric="working_results"]').forEach(node=>node.textContent=String(workingResults));
      if(!working.length) return;

      section.hidden=false;
      section.querySelectorAll(".reveal").forEach(node=>node.classList.add("is-visible"));
      const summary=section.querySelector("[data-work-summary]");
      summary.replaceChildren(
        stat("Working Dobermans", String(working.length)),
        stat("Documented results", String(workingResults)),
        stat("Work gallery", photoCount ? `${photoCount} photos` : "No media"),
        stat("Work videos", videoCount ? `${videoCount} links` : "No media")
      );
      const rail=section.querySelector("[data-kennel-work-dogs]");
      rail.replaceChildren(...working.map(workDogCard));

      const tab=document.getElementById("kennelWorkTab"); if(tab) tab.hidden=false;
      const ledger=document.getElementById("kennelDeskWork");
      if(ledger) ledger.replaceChildren(
        ledgerRow("Working Dobermans",working.length),
        ledgerRow("Working exams + sports",workingResults),
        ledgerRow("Work photos",photoCount),
        ledgerRow("Work video links",videoCount)
      );

      working.forEach(record=>{
        const card=[...document.querySelectorAll("#kennelDobermanRail a")].find(link=>link.href.includes(record.record_id));
        const top=card?.querySelector(".related-card-top");
        if(top && !top.querySelector(".di-work-badge")){ const badge=document.createElement("b"); badge.className="di-work-badge"; badge.textContent="WORK"; top.append(badge); }
      });
    }catch(error){ console.warn("Doberman Index kennel work layer unavailable",error); }
  }

  function start(){ initDog(); initKennel(); }
  if(document.readyState==="loading") document.addEventListener("DOMContentLoaded",start,{once:true}); else start();
})();