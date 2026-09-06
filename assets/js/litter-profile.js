(function(global){
  "use strict";

  const DOBERMAN_ID=/^DI-[MF]-\d{6}$/;
  const KENNEL_ID=/^DI-K-\d{6}$/;
  const LITTER_ID=/^DI-L-\d{6}$/;
  const STATUS_LABELS=Object.freeze({
    planned:"Planned litter",
    born:"Born",
    open:"Open",
    closed:"Closed",
    archived:"Archived"
  });

  const list=value=>Array.isArray(value)?value:[];
  const text=value=>value===null||value===undefined?"":String(value).trim();
  const unique=value=>[...new Set(list(value).map(text).filter(Boolean))];
  const profileHref=id=>`../profile.html?id=${encodeURIComponent(id)}`;
  const statusLabel=value=>STATUS_LABELS[text(value).toLowerCase()]||"Status not published";
  const formatDate=value=>{
    const raw=text(value);
    if(!/^\d{4}-\d{2}-\d{2}$/.test(raw))return "Date not published";
    const date=new Date(`${raw}T00:00:00Z`);
    return Number.isNaN(date.getTime())?"Date not published":new Intl.DateTimeFormat("en-GB",{day:"2-digit",month:"short",year:"numeric",timeZone:"UTC"}).format(date);
  };
  const recordName=(record,names={})=>{
    if(!record)return "";
    if(record.entity_type==="doberman")return names.doberman?names.doberman(record.registered_name||record.record_id):text(record.registered_name)||record.record_id;
    if(record.entity_type==="kennel")return names.kennel?names.kennel(record.name||record.record_id):text(record.name)||record.record_id;
    return text(record.name)||record.record_id;
  };

  function buildModel(record,registry,names={}){
    if(!record||record.entity_type!=="litter"||!LITTER_ID.test(text(record.record_id))||!record.litter)throw new Error("Invalid litter record");
    const litter=record.litter;
    const records=list(registry?.records||registry).filter(item=>item&&item.status==="published");
    const byId=new Map(records.map(item=>[item.record_id,item]));
    const relationship=(id,type,pattern)=>{
      const normalized=text(id).toUpperCase();
      const valid=pattern.test(normalized);
      const linked=valid?byId.get(normalized):null;
      return {
        id:valid?normalized:"",
        type,
        name:linked?recordName(linked,names):(valid?normalized:"Not linked"),
        linked:Boolean(linked),
        href:linked?profileHref(normalized):"",
        image:linked?.hero||""
      };
    };
    const puppyIds=unique(litter.puppy_ids).filter(id=>DOBERMAN_ID.test(id));
    const puppyIdSet=new Set(puppyIds);
    const availableIds=new Set(unique(litter.available_puppy_ids).filter(id=>puppyIdSet.has(id)));
    const puppies=puppyIds.map(id=>{
      const linked=byId.get(id);
      return {
        id,
        name:linked?recordName(linked,names):id,
        linked:Boolean(linked),
        href:linked?profileHref(id):"",
        image:linked?.hero||"",
        life_stage:text(linked?.life_stage)||"unpublished",
        available:availableIds.has(id)&&Boolean(linked)
      };
    });
    const date=litter.date_of_birth
      ?{label:"Date of birth",value:formatDate(litter.date_of_birth),raw:litter.date_of_birth,kind:"born"}
      :litter.planned_date
        ?{label:"Planned date",value:formatDate(litter.planned_date),raw:litter.planned_date,kind:"planned"}
        :{label:"Date",value:"Date not published",raw:"",kind:"unknown"};
    const media=litter.media&&typeof litter.media==="object"?litter.media:{};
    return {
      record_id:record.record_id,
      name:text(litter.name)||`Litter ${record.record_id}`,
      editorial_status:text(record.status)||"unknown",
      litter_status:text(litter.status)||"unknown",
      litter_status_label:statusLabel(litter.status),
      date,
      notes:text(litter.notes),
      kennel:relationship(litter.kennel_id,"Kennel",KENNEL_ID),
      sire:relationship(litter.sire_id,"Sire",DOBERMAN_ID),
      dam:relationship(litter.dam_id,"Dam",DOBERMAN_ID),
      puppies,
      puppy_count:puppies.length,
      available_count:puppies.filter(item=>item.available).length,
      cover:text(media.cover),
      gallery:list(media.gallery),
      updated_at:text(record.updated_at)
    };
  }

  const api={DOBERMAN_ID,KENNEL_ID,LITTER_ID,statusLabel,formatDate,profileHref,buildModel};
  global.DILitter=api;
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
})(typeof window!=="undefined"?window:globalThis);
