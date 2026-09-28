#!/usr/bin/env python3
from __future__ import annotations
import io, json, os, sys, time
from pathlib import Path
from urllib.parse import urlparse
import urllib.request, urllib.error

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"data/bloodline-images.json"
REPORT=ROOT/"data/bloodline-r2-migration-report.json"
WORKER=os.environ.get("DI_MEDIA_ADMIN_BASE","https://doberman-index-media-admin.dobermanindex-records.workers.dev").rstrip("/")
TOKEN=os.environ.get("MEDIA_ADMIN_KEY","").strip()
PUBLIC_PREFIX=WORKER+"/ancestors/"
ALLOWED_INTERNAL=("doberman-index.com","doberman-index-media-admin.dobermanindex-records.workers.dev","media.doberman-index.com")

try:
    from PIL import Image
except Exception as exc:
    raise SystemExit("Pillow is required: "+str(exc))

def is_external(url:str)->bool:
    if not url.startswith(("http://","https://")):
        return False
    host=(urlparse(url).hostname or "").lower()
    return not any(host==h or host.endswith("."+h) for h in ALLOWED_INTERNAL)

def fetch(url:str)->bytes:
    headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136 Safari/537.36",
        "Accept":"image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer":f"{urlparse(url).scheme}://{urlparse(url).netloc}/",
    }
    last=None
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req,timeout=30) as r:
                data=r.read()
                ctype=(r.headers.get("content-type") or "").lower()
            if len(data)<500:
                raise ValueError(f"response too small ({len(data)} bytes)")
            if "text/html" in ctype:
                raise ValueError("received HTML instead of image")
            return data
        except Exception as exc:
            last=exc
            time.sleep(1.5*(attempt+1))
    raise last

def normalize_jpeg(data:bytes)->bytes:
    with Image.open(io.BytesIO(data)) as im:
        im=im.convert("RGB")
        max_side=1800
        if max(im.size)>max_side:
            ratio=max_side/max(im.size)
            im=im.resize((round(im.width*ratio),round(im.height*ratio)),Image.Resampling.LANCZOS)
        out=io.BytesIO()
        im.save(out,"JPEG",quality=90,optimize=True,progressive=True)
        return out.getvalue()

def upload(key:str,data:bytes,name:str,source_url:str)->None:
    if not TOKEN:
        raise RuntimeError("MEDIA_ADMIN_KEY is not configured")
    endpoint=f"{WORKER}/v1/admin/media/{key}"
    headers={
        "Authorization":f"Bearer {TOKEN}",
        "Content-Type":"image/jpeg",
        "X-DI-Registered-Name":name,
        "X-DI-Role":"bloodline_ancestor",
        "X-DI-Source-Url":source_url,
        "User-Agent":"Doberman-Index-R2-Migrator/1.0",
    }
    req=urllib.request.Request(endpoint,data=data,headers=headers,method="PUT")
    with urllib.request.urlopen(req,timeout=45) as r:
        body=r.read()
        if r.status<200 or r.status>=300:
            raise RuntimeError(f"upload HTTP {r.status}: {body[:200]!r}")

def main():
    doc=json.loads(MANIFEST.read_text(encoding="utf-8"))
    # One canonical source per ancestor id; mirror result to every root that references it.
    by_id={}
    for root,record in (doc.get("records") or {}).items():
        for aid,item in (record.get("ancestors") or {}).items():
            sel=item.get("selected") if isinstance(item,dict) else None
            url=(sel or {}).get("image_url","")
            if item.get("status")=="selected" and is_external(url):
                by_id.setdefault(aid,{"source":sel,"roots":[]})
                by_id[aid]["roots"].append(root)

    graph=json.loads((ROOT/"data/pedigree-graph.json").read_text(encoding="utf-8"))
    report={"attempted":len(by_id),"migrated":[],"missing_after_failure":[],"skipped":[]}

    for aid,payload in sorted(by_id.items()):
        source=payload["source"]
        url=source["image_url"]
        name=(graph.get("nodes",{}).get(aid,{}) or {}).get("registered_name",aid)
        print(f"[{aid}] {name}")
        try:
            raw=fetch(url)
            jpg=normalize_jpeg(raw)
            key=f"ancestors/{aid}/main.jpg"
            upload(key,jpg,name,source.get("source_url") or url)
            internal_url=f"{PUBLIC_PREFIX}{aid}/main.jpg"
            for root in payload["roots"]:
                item=doc["records"][root]["ancestors"][aid]
                item["status"]="selected"
                item["selected"]["image_url"]=internal_url
                item["selected"]["migrated_from"]=url
            report["migrated"].append({"record_id":aid,"name":name,"from":url,"to":internal_url,"bytes":len(jpg)})
            print("  -> migrated")
        except Exception as exc:
            message=str(exc)
            for root in payload["roots"]:
                old=doc["records"][root]["ancestors"][aid]
                doc["records"][root]["ancestors"][aid]={
                    "status":"missing",
                    "note":f"External Bloodline image removed during R2 migration because it could not be fetched reliably: {message[:180]}",
                    "previous_source_url":(old.get("selected") or {}).get("source_url")
                }
            report["missing_after_failure"].append({"record_id":aid,"name":name,"from":url,"error":message})
            print("  -> fetch/upload failed; marked missing:",message)

    # Assert there is no selected external image left.
    leftovers=[]
    for root,record in (doc.get("records") or {}).items():
        for aid,item in (record.get("ancestors") or {}).items():
            sel=item.get("selected") if isinstance(item,dict) else None
            url=(sel or {}).get("image_url","")
            if item.get("status")=="selected" and is_external(url):
                leftovers.append({"root":root,"record_id":aid,"url":url})
    if leftovers:
        raise SystemExit("External Bloodline images remain: "+json.dumps(leftovers))

    MANIFEST.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:len(v) if isinstance(v,list) else v for k,v in report.items()},indent=2))

if __name__=="__main__":
    main()
