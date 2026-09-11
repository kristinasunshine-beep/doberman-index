#!/usr/bin/env python3
"""Validate deterministic, non-publishing relationship opportunity output."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from build_relationship_opportunities import build

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "relationship-opportunities.json"
errors = []

if not PATH.is_file():
    errors.append("relationship-opportunities.json missing")
else:
    actual = json.loads(PATH.read_text(encoding="utf-8"))
    expected = build(ROOT)
    if actual != expected:
        errors.append("relationship opportunities are stale or non-deterministic")
    if actual.get("publications_created") != 0:
        errors.append("relationship planning artifact must never auto-publish records")
    serialized = PATH.read_text(encoding="utf-8").lower()
    for forbidden in ("submitter_email", "submitter_name", "redacted@example.invalid"):
        if forbidden in serialized:
            errors.append(f"private submission field leaked: {forbidden}")

if errors:
    print("Relationship opportunities validation FAIL", file=sys.stderr)
    for error in errors:
        print(" -", error, file=sys.stderr)
    raise SystemExit(1)
print("Relationship opportunities validation PASS")
