#!/usr/bin/env python3
"""Validate public litter routes, schema, registry projection and lifecycle rules."""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOBERMAN_ID = re.compile(r"^DI-(M|F)-\d{6}$")
LITTER_ID = re.compile(r"^DI-L-\d{6}$")
LITTER_STATES = {"planned", "born", "open", "closed", "archived"}
errors: list[str] = []


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


router = (ROOT / "profile.html").read_text(encoding="utf-8")
litter_page = (ROOT / "profiles" / "litter.html").read_text(encoding="utf-8")
builder_text = (ROOT / "scripts" / "build_registry.py").read_text(encoding="utf-8")
male_page = (ROOT / "profiles" / "male.html").read_text(encoding="utf-8")
female_page = (ROOT / "profiles" / "female.html").read_text(encoding="utf-8")
puppy_page = (ROOT / "profiles" / "puppy.html").read_text(encoding="utf-8")
kennel_page = (ROOT / "profiles" / "kennel-concept.html").read_text(encoding="utf-8")

for token in ('litter:"./profiles/litter.html"', 'window.DILifecycle.templateFor'):
    if token not in router:
        errors.append(f"profile router missing litter contract token: {token}")
for token in (
    '../assets/js/litter-profile.js',
    'window.DILitter.buildModel',
    'id="litterParents"',
    'id="litterPuppies"',
    'id="litterKennel"',
    'id="litterEmptyPuppies"',
):
    if token not in litter_page:
        errors.append(f"litter renderer missing token: {token}")
for token in ('"planned_date"', '"puppy_ids"', '"available_puppy_ids"', '"editorial_status"', '"media": {"cover"'):
    if token not in builder_text:
        errors.append(f"registry litter projection missing: {token}")
for page_name, page_text, tokens in (
    ("male", male_page, ("array(reproduction.litter_ids)", 'record.entity_type==="litter"')),
    ("female", female_page, ("array(reproduction.litter_ids)", 'record.entity_type==="litter"')),
    ("puppy", puppy_page, ('["Litter",parentage.litter_id', '../profile.html?id=${encodeURIComponent(linkedId)}')),
    ("kennel", kennel_page, ('chip.href=`../profile.html?id=${encodeURIComponent(item.record_id)}`',)),
):
    for token in tokens:
        if token not in page_text:
            errors.append(f"{page_name} profile missing reverse litter link: {token}")

schema = json.loads((ROOT / "schemas" / "registry.schema.json").read_text(encoding="utf-8"))
litter_schema = schema.get("$defs", {}).get("litter", {})
properties = litter_schema.get("properties", {})
for field in ("name", "kennel_id", "sire_id", "dam_id", "date_of_birth", "planned_date", "status", "puppy_ids", "available_puppy_ids", "media"):
    if field not in properties:
        errors.append(f"litter schema missing field: {field}")
if properties.get("puppy_ids", {}).get("items", {}).get("pattern") != "^DI-(M|F)-[0-9]{6}$":
    errors.append("litter puppy_ids must use permanent DI-M/DI-F IDs")
if properties.get("available_puppy_ids", {}).get("items", {}).get("pattern") != "^DI-(M|F)-[0-9]{6}$":
    errors.append("litter available_puppy_ids must use permanent DI-M/DI-F IDs")

for path in sorted((ROOT / "data" / "litters").glob("DI-L-*.json")):
    record = json.loads(path.read_text(encoding="utf-8-sig"))
    record_id = record.get("record_id")
    litter = record.get("litter") or {}
    if not isinstance(record_id, str) or not LITTER_ID.fullmatch(record_id) or path.stem != record_id or record.get("entity_type") != "litter":
        errors.append(f"canonical litter ID/file/entity mismatch: {path.relative_to(ROOT)}")
    puppy_ids = litter.get("puppy_ids")
    available_ids = litter.get("available_puppy_ids")
    if not isinstance(puppy_ids, list) or any(not isinstance(value, str) or not DOBERMAN_ID.fullmatch(value) for value in puppy_ids):
        errors.append(f"invalid permanent puppy_ids in {path.name}")
        puppy_ids = []
    if not isinstance(available_ids, list) or any(not isinstance(value, str) or not DOBERMAN_ID.fullmatch(value) for value in available_ids):
        errors.append(f"invalid available_puppy_ids in {path.name}")
        available_ids = []
    if len(puppy_ids) != len(set(puppy_ids)) or len(available_ids) != len(set(available_ids)):
        errors.append(f"duplicate puppy ID in {path.name}")
    if not set(available_ids).issubset(set(puppy_ids)):
        errors.append(f"available_puppy_ids must be a subset of puppy_ids in {path.name}")
    if litter.get("status") not in LITTER_STATES:
        errors.append(f"invalid editorial litter status in {path.name}")

builder = load_module("build_registry_litter_test", ROOT / "scripts" / "build_registry.py")
with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(temp_dir)
    path = temp / "data" / "litters" / "DI-L-000777.json"
    path.parent.mkdir(parents=True)
    data = {
        "record_id": "DI-L-000777",
        "status": "published",
        "litter": {
            "name": "Registry fixture",
            "kennel_id": None,
            "sire_id": None,
            "dam_id": None,
            "date_of_birth": None,
            "planned_date": "2027-01-01",
            "status": "planned",
            "puppy_ids": [],
            "available_puppy_ids": [],
            "media": {"cover": None, "gallery": []},
        },
    }
    entry = builder.litter_entry(path, data, temp)
    for field in ("record_id", "name", "kennel_id", "sire_id", "dam_id", "date_of_birth", "planned_date", "editorial_status", "litter_status", "puppy_ids", "available_puppy_ids", "media", "hero"):
        if field not in entry:
            errors.append(f"generated litter registry entry missing: {field}")

with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(temp_dir)
    (temp / "data" / "dobermans").mkdir(parents=True)
    (temp / "data" / "litters").mkdir(parents=True)
    (temp / "data" / "lifecycle-policy.json").write_text(json.dumps({"puppy_until_months": 9, "junior_until_months": 18, "veteran_from_years": 8}), encoding="utf-8")
    for record_id, current_status in (("DI-M-000801", "available"), ("DI-F-000802", "reserved")):
        dog = {
            "record_id": record_id,
            "entity_type": "doberman",
            "status": "published",
            "doberman": {
                "identity": {"sex": "male" if "-M-" in record_id else "female", "life_status": "living", "life_stage": "puppy", "date_of_birth": "2026-01-01"},
                "publication": {"profile_template": "puppy", "lifecycle_mode": "automatic"},
                "puppy_lifecycle": {"current_status": current_status},
            },
        }
        (temp / "data" / "dobermans" / f"{record_id}.json").write_text(json.dumps(dog), encoding="utf-8")
    litter_path = temp / "data" / "litters" / "DI-L-000803.json"
    litter_path.write_text(json.dumps({
        "record_id": "DI-L-000803",
        "entity_type": "litter",
        "status": "published",
        "litter": {"status": "open", "puppy_ids": ["DI-M-000801", "DI-F-000802"], "available_puppy_ids": ["DI-M-000801", "DI-F-000802"]},
    }), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "apply_lifecycle_policy.py"), "--root", str(temp), "--write", "--today", "2026-05-01"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        errors.append("lifecycle litter fixture failed: " + (result.stderr.strip() or result.stdout.strip()))
    updated = json.loads(litter_path.read_text(encoding="utf-8"))["litter"]
    if updated.get("available_puppy_ids") != ["DI-M-000801"]:
        errors.append("lifecycle must retain only published, under-9-month puppies marked available")
    if updated.get("puppy_ids") != ["DI-M-000801", "DI-F-000802"]:
        errors.append("lifecycle must preserve historical puppy_ids")
    if updated.get("status") != "open":
        errors.append("lifecycle must never close or change litter status automatically")

if errors:
    print("Litter system contract FAIL", file=sys.stderr)
    for error in errors:
        print(f" - {error}", file=sys.stderr)
    raise SystemExit(1)

print("Litter system contract PASS (routes, schema, registry, lifecycle and permanent IDs)")
