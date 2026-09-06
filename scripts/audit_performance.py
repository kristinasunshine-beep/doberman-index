#!/usr/bin/env python3
"""Audit performance-sensitive markup and public media without altering approved assets."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
errors=[];notes=[]
registry=json.loads((ROOT/"data/registry.json").read_text(encoding="utf-8"))

if (ROOT/"index.html").stat().st_size>500_000:errors.append("index.html exceeds the 500 KB compatibility budget")
if (ROOT/"assets/css/seo-record.css").stat().st_size>24_000:errors.append("canonical record CSS exceeds 24 KB")
if (ROOT/"assets/js/seo-runtime.js").stat().st_size>12_000:errors.append("SEO runtime exceeds 12 KB")

for page in (ROOT/"index.html",ROOT/"about.html",ROOT/"profiles/male.html",ROOT/"profiles/female.html",ROOT/"profiles/puppy.html"):
    text=page.read_text(encoding="utf-8")
    if "fonts.googleapis.com" in text and "display=swap" not in text:errors.append(f"font loading lacks display=swap: {page.name}")

for record in registry.get("records",[]):
    if record.get("status")!="published":continue
    page=ROOT/"records"/record["record_id"]/"index.html"
    text=page.read_text(encoding="utf-8")
    hero=re.search(r'<img[^>]+fetchpriority="high"[^>]*>',text)
    if record.get("hero"):
        if not hero:errors.append(f"canonical hero lacks fetchpriority: {record['record_id']}")
        elif not re.search(r'\bwidth="\d+"',hero.group(0)) or not re.search(r'\bheight="\d+"',hero.group(0)):errors.append(f"canonical hero lacks dimensions: {record['record_id']}")
        if '<link rel="preload" as="image"' not in text:errors.append(f"canonical hero is not preloaded: {record['record_id']}")

for page in ("profiles/male.html","profiles/female.html","profiles/puppy.html"):
    text=(ROOT/page).read_text(encoding="utf-8")
    if 'preload="metadata"' not in text:errors.append(f"movement video must use metadata preload: {page}")
    if 'loading="${index?"lazy":"eager"}"' not in text:errors.append(f"gallery loading policy missing: {page}")

large=[]
for path in (ROOT/"media").rglob("*"):
    if path.is_file() and path.stat().st_size>4_000_000:large.append(f"{path.relative_to(ROOT).as_posix()} ({path.stat().st_size/1_000_000:.1f} MB)")
if large:notes.append("Approved large media retained and lazy/metadata loaded: "+", ".join(large))
inline=(ROOT/"index.html").read_text(encoding="utf-8").count("data:image/")
if inline:notes.append(f"Homepage retains {inline} accepted inline brand image; total HTML remains inside the compatibility budget.")

if errors:
    print("Performance audit FAIL",file=sys.stderr)
    for error in errors:print(f" - {error}",file=sys.stderr)
    raise SystemExit(1)
print("Performance audit PASS")
for note in notes:print(f" - NOTE: {note}")
