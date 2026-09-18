#!/usr/bin/env python3
"""Validate the accepted post-v6.3 product copy, routing and movement rules."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

about = (ROOT / "about.html").read_text(encoding="utf-8")
for token in (
    "The Doberman world, connected through one living record.",
    'class="details-link"',
    ">Details<",
    ">Mission<",
    "A breed intelligence system for evidence, lineage and breeding decisions.",
    "03 / Decision",
    "Breeding Lens",
):
    if token not in about:
        errors.append(f"About accepted token missing: {token}")

index = (ROOT / "index.html").read_text(encoding="utf-8")
for token in (
    "Doberman <span class=\"accent\">Index.</span>",
    "What is Doberman Index?",
    "What am I actually buying?",
    "What is the Evidence Graph?",
    "Pedigree Intelligence",
    "Pairing Intelligence",
    "portal-search-results",
    "data/registry.json",
):
    if token not in index:
        errors.append(f"Portal product/search token missing: {token}")

submit = (ROOT / "submit.html").read_text(encoding="utf-8")
submit_js = (ROOT / "assets/js/submit-v3.js").read_text(encoding="utf-8")
schema = json.loads((ROOT / "schemas/registry.schema.json").read_text(encoding="utf-8"))
if "3–15 seconds" not in submit:
    errors.append("Submission movement copy must say 3–15 seconds")
if schema["$defs"]["doberman"]["properties"]["media"]["properties"]["movement_video_seconds"].get("minimum") != 3:
    errors.append("Schema movement-video minimum must be 3 seconds")
for token in ("MOVEMENT_VIDEO_MIN_SECONDS = 3", "MOVEMENT_VIDEO_MAX_SECONDS = 15", "validateMovementVideoDuration", "dataset.durationSeconds"):
    if token not in submit_js:
        errors.append(f"Movement duration enforcement missing: {token}")

puppy = json.loads((ROOT / "data/prototypes/puppy-card.json").read_text(encoding="utf-8"))
if not puppy["record_id"].startswith(("DI-F-", "DI-M-")):
    errors.append("Puppy prototype must demonstrate permanent sex-coded ID")
if "DI-P-" in (ROOT / "profiles/puppy.html").read_text(encoding="utf-8"):
    errors.append("Puppy profile must not imply a DI-P permanent ID prefix")

router = (ROOT / "profile.html").read_text(encoding="utf-8")
for token in (
    "window.DILifecycle.templateFor",
    'puppy:"./profiles/puppy.html"',
    'female:"./profiles/female/"',
    'male:"./profiles/male/"',
):
    if token not in router:
        errors.append(f"Lifecycle router missing: {token}")

for sex in ("male", "female"):
    page = (ROOT / "profiles" / sex / "index.html").read_text(encoding="utf-8")
    for token in ('const repoRoot=new URL("../../",document.baseURI);', 'assets/bloodline-network_v23.js', 'id="bloodlineRail"'):
        if token not in page:
            errors.append(f"{sex} V27 integration missing: {token}")

workflow = (ROOT / ".github/workflows/build-registry.yml").read_text(encoding="utf-8")
for token in ('cron: "17 3 * * *"', 'python scripts/apply_lifecycle_policy.py --write', 'profiles/male/**', 'profiles/female/**'):
    if token not in workflow:
        errors.append(f"Daily/product workflow missing: {token}")

if errors:
    print("Product integration contract FAIL", file=sys.stderr)
    for error in errors:
        print("-", error, file=sys.stderr)
    raise SystemExit(1)
print("Product integration contract PASS")
