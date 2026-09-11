#!/usr/bin/env python3
"""Validate generated Owner Link Kit assets for every published canonical record."""
from __future__ import annotations
import html
import json
import sys
from pathlib import Path
from build_seo import ID_RE, owner_link_kit, origin_for

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
registry = json.loads((ROOT / "data" / "registry.json").read_text(encoding="utf-8"))
records = [item for item in registry.get("records", []) if isinstance(item, dict) and item.get("status") == "published" and ID_RE.fullmatch(str(item.get("record_id", "")))]
origin = origin_for(ROOT)

if not (ROOT / "assets" / "js" / "owner-link-kit.js").is_file():
    errors.append("assets/js/owner-link-kit.js is missing")

for record in records:
    record_id = record["record_id"]
    record_dir = ROOT / "records" / record_id
    page_path = record_dir / "index.html"
    json_path = record_dir / "owner-link-kit.json"
    qr_path = record_dir / "owner-link-qr.svg"
    badge_path = record_dir / "indexed-badge.svg"
    expected = owner_link_kit(origin, record)
    for path in (page_path, json_path, qr_path, badge_path):
        if not path.is_file(): errors.append(f"{record_id}: missing generated Owner Link Kit asset {path.name}")
    if not json_path.is_file(): continue
    try: actual = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{record_id}: invalid owner-link-kit.json: {exc}"); continue
    if actual != expected: errors.append(f"{record_id}: owner-link-kit.json does not match current canonical record data")
    if len(actual.get("anchors", [])) != 3: errors.append(f"{record_id}: exactly three anchor variants are required")
    canonical = expected["canonical_url"]
    if qr_path.is_file():
        qr = qr_path.read_text(encoding="utf-8")
        if canonical not in qr or '<svg' not in qr or 'viewBox="0 0 45 45"' not in qr: errors.append(f"{record_id}: QR SVG metadata/matrix contract failed")
    if badge_path.is_file():
        badge = badge_path.read_text(encoding="utf-8")
        if "INDEXED ON DOBERMAN INDEX" not in badge or record_id not in badge: errors.append(f"{record_id}: badge SVG identity contract failed")
    if page_path.is_file():
        page = page_path.read_text(encoding="utf-8")
        tokens = ['id="owner-link-kit"', "owner-link-kit.json", "owner-link-qr.svg", "indexed-badge.svg", "../../assets/js/owner-link-kit.js", canonical, *[html.escape(item["text"]) for item in expected["anchors"]]]
        for token in tokens:
            if token not in page: errors.append(f"{record_id}: canonical page missing Owner Link Kit token: {token}")

if errors:
    print("Owner Link Kit validation FAIL", file=sys.stderr)
    for error in errors: print(f" - {error}", file=sys.stderr)
    raise SystemExit(1)
print(f"Owner Link Kit validation PASS ({len(records)} published record kit(s))")
