#!/usr/bin/env python3
"""Synchronize age-derived lifecycle fields and litter availability.

Public classification policy is configured in data/lifecycle-policy.json.
Individual records may opt out with doberman.publication.lifecycle_mode="manual".
"""
from __future__ import annotations
import argparse, calendar, json, sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]

def load(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value,dict): raise ValueError(f"JSON object required: {path}")
    return value

def add_months(value:date,months:int)->date:
    raw=value.month-1+months
    year=value.year+raw//12
    month=raw%12+1
    day=min(value.day,calendar.monthrange(year,month)[1])
    return date(year,month,day)

def derived_stage(dob:date,today:date,policy:dict[str,Any])->str:
    puppy=int(policy.get("puppy_until_months",9))
    junior=int(policy.get("junior_until_months",18))
    veteran=int(policy.get("veteran_from_years",8))*12
    if today < add_months(dob,puppy): return "puppy"
    if today < add_months(dob,junior): return "junior"
    if today < add_months(dob,veteran): return "adult"
    return "veteran"

def update_doberman(path:Path,policy:dict[str,Any],today:date,write:bool)->tuple[bool,str|None]:
    record=load(path)
    if record.get("entity_type")!="doberman": return False,None
    dog=record.get("doberman") or {}; identity=dog.get("identity") or {}; publication=dog.setdefault("publication",{})
    if publication.get("lifecycle_mode","automatic")=="manual": return False,None
    if str(identity.get("life_status") or "").lower()!="living": return False,None
    raw=identity.get("date_of_birth")
    try: dob=date.fromisoformat(str(raw))
    except (TypeError,ValueError): return False,None
    stage=derived_stage(dob,today,policy)
    sex=str(identity.get("sex") or "").lower()
    template="puppy" if stage=="puppy" else (sex if sex in {"male","female"} else publication.get("profile_template"))
    changed=False
    if identity.get("life_stage")!=stage: identity["life_stage"]=stage; changed=True
    if publication.get("profile_template")!=template: publication["profile_template"]=template; changed=True
    publication.setdefault("lifecycle_mode","automatic")
    if changed:
        record["updated_at"]=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
        if write: path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return changed, stage

def prune_litters(root:Path,puppy_ids:set[str],write:bool)->list[Path]:
    changed=[]
    for path in sorted((root/"data"/"litters").glob("DI-L-*.json")):
        data=load(path); litter=data.get("litter") or {}; values=litter.get("available_puppy_ids"); historical=set(litter.get("puppy_ids") or [])
        if not isinstance(values,list): continue
        fresh=[]
        for item in values:
            if item in puppy_ids and item in historical and item not in fresh: fresh.append(item)
        if fresh!=values:
            litter["available_puppy_ids"]=fresh
            data["updated_at"]=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
            if write: path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            changed.append(path)
    return changed

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--root",type=Path,default=ROOT); parser.add_argument("--write",action="store_true"); parser.add_argument("--today",help="YYYY-MM-DD test override")
    args=parser.parse_args(); root=args.root.resolve(); policy=load(root/"data"/"lifecycle-policy.json"); today=date.fromisoformat(args.today) if args.today else date.today()
    touched=[]; current_puppies=set()
    for path in sorted((root/"data"/"dobermans").glob("DI-[MF]-*.json")):
        changed,stage=update_doberman(path,policy,today,args.write)
        data=load(path) if args.write and changed else load(path)
        identity=(data.get("doberman") or {}).get("identity") or {}
        publication=(data.get("doberman") or {}).get("publication") or {}
        if publication.get("lifecycle_mode","automatic")!="manual" and str(identity.get("life_status") or "").lower()=="living":
            try: effective=derived_stage(date.fromisoformat(str(identity.get("date_of_birth"))),today,policy)
            except (TypeError,ValueError): effective=str(identity.get("life_stage") or "unknown").lower()
        else: effective=str(identity.get("life_stage") or "unknown").lower()
        puppy_status=str(((data.get("doberman") or {}).get("puppy_lifecycle") or {}).get("current_status") or "").lower()
        if data.get("status")=="published" and effective=="puppy" and puppy_status=="available": current_puppies.add(str(data.get("record_id") or ""))
        if changed: touched.append(path)
    touched.extend(prune_litters(root,current_puppies,args.write))
    if touched and not args.write:
        print("Lifecycle sync required:")
        for path in touched: print(path.relative_to(root))
        return 1
    print(f"Lifecycle sync {'updated' if args.write else 'clean'} · {today.isoformat()} · {len(touched)} file(s) changed")
    return 0
if __name__=="__main__": raise SystemExit(main())
