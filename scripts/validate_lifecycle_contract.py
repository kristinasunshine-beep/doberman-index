#!/usr/bin/env python3
"""Validate lifecycle data, routing and the V27 profile presentation contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "registry.schema.json").read_text(encoding="utf-8"))
ROUTER = (ROOT / "profile.html").read_text(encoding="utf-8")
MALE = (ROOT / "profiles" / "male" / "index.html").read_text(encoding="utf-8")
FEMALE = (ROOT / "profiles" / "female" / "index.html").read_text(encoding="utf-8")
BUILD = (ROOT / "scripts" / "build_registry.py").read_text(encoding="utf-8")
MIGRATE = (ROOT / "scripts" / "migrate_lifecycle_v1_1.py").read_text(encoding="utf-8")
errors: list[str] = []

identity = SCHEMA["$defs"]["doberman"]["properties"]["identity"]
if SCHEMA["properties"]["schema_version"].get("const") != "1.1.0":
    errors.append("canonical schema_version must be 1.1.0")
if set(identity["properties"]["life_stage"].get("enum", [])) != {"puppy", "junior", "adult", "veteran", "unknown"}:
    errors.append("life_stage must contain age categories only")
if set(identity["properties"]["life_status"].get("enum", [])) != {"living", "deceased", "unknown"}:
    errors.append("life_status enum is incomplete")
for field in ("life_stage", "life_status"):
    if field not in identity.get("required", []):
        errors.append(f"identity.{field} must be required")

for token in (
    'legacy_deceased = source_stage == "deceased"',
    'identity["life_stage"] = "unknown" if legacy_deceased',
    '("deceased" if legacy_deceased else "unknown")',
):
    if token not in MIGRATE:
        errors.append(f"legacy submission migration missing: {token}")
for token in ('"life_status": life_status', 'if life_status == "deceased"', '"schema_version": "1.1.0"'):
    if token not in BUILD:
        errors.append(f"registry builder lifecycle logic missing: {token}")

for token in (
    'window.DILifecycle.templateFor',
    'male:"./profiles/male/"',
    'female:"./profiles/female/"',
    'puppy:"./profiles/puppy.html"',
    'litter:"./profiles/litter.html"',
):
    if token not in ROUTER:
        errors.append(f"profile router lifecycle behavior missing: {token}")
if 'if(/^DI-M-' in ROUTER:
    errors.append("profile router must not shortcut DI-M IDs around lifecycle routing")

for name, page in (("male", MALE), ("female", FEMALE)):
    for token in (
        'id="lifeStatusBadge"',
        'lifeStatus:"Life status"',
        'lifeSpan:"Life span"',
        'const isDeceased=lifecycleState==="deceased"',
        'lifecycleState==="living"?""',
        'async function loadProfile()',
    ):
        if token not in page:
            errors.append(f"{name} V27 profile lifecycle display missing: {token}")

if errors:
    print("Lifecycle contract FAIL", file=sys.stderr)
    for error in errors:
        print(f" - {error}", file=sys.stderr)
    raise SystemExit(1)
print("Lifecycle contract PASS (schema, router and V27 profile templates)")
