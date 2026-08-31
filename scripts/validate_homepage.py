#!/usr/bin/env python3
"""Validate data/homepage.json against the current published registry."""

from __future__ import annotations
import json
import sys
from pathlib import Path

CATEGORY_RULES = {
    "males": lambda r: r.get("entity_type") == "doberman" and r.get("sex") == "male" and r.get("life_stage") != "puppy" and r.get("life_status") != "deceased",
    "females": lambda r: r.get("entity_type") == "doberman" and r.get("sex") == "female" and r.get("life_stage") != "puppy" and r.get("life_status") != "deceased",
    "kennels": lambda r: r.get("entity_type") == "kennel",
    "puppies": lambda r: r.get("entity_type") == "doberman" and r.get("life_stage") == "puppy" and r.get("life_status") != "deceased",
}

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def main() -> int:
    root = Path(__file__).resolve().parents[1]
    homepage_path = root / "data" / "homepage.json"
    registry_path = root / "data" / "registry.json"

    try:
        homepage = load(homepage_path)
        registry = load(registry_path)
    except Exception as exc:
        print(f"Homepage validation failed: {exc}", file=sys.stderr)
        return 1

    showcases = homepage.get("showcases")
    if not isinstance(showcases, dict):
        print("homepage.json: missing showcases object", file=sys.stderr)
        return 1

    published = {
        r.get("record_id"): r
        for r in registry.get("records", [])
        if isinstance(r, dict) and r.get("status") == "published" and r.get("record_id")
    }

    errors = []
    used = set()

    for category, rule in CATEGORY_RULES.items():
        ids = showcases.get(category)
        if not isinstance(ids, list):
            errors.append(f"{category}: expected an array")
            continue
        if len(ids) > 3:
            errors.append(f"{category}: maximum 3 showcase records")
        for record_id in ids:
            if record_id in used:
                errors.append(f"{record_id}: duplicated across homepage showcase categories")
                continue
            used.add(record_id)
            record = published.get(record_id)
            if not record:
                errors.append(f"{record_id}: not present as a published registry record")
                continue
            if not rule(record):
                errors.append(f"{record_id}: does not belong in homepage category '{category}'")

    if errors:
        print("Homepage showcase validation failed:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1

    count = sum(len(showcases.get(k, [])) for k in CATEGORY_RULES)
    print(f"homepage.json valid ({count} curated published records).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
