#!/usr/bin/env python3
"""Build a deterministic admin backlog for the next safe public relationship records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "relationship-opportunities.json"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def build(root: Path = ROOT) -> dict[str, Any]:
    registry = load(root / "data" / "registry.json")
    kennel_sources = {}
    for path in sorted((root / "data" / "kennels").glob("DI-K-*.json")):
        item = load(path)
        kennel_sources[clean(item.get("record_id")).upper()] = item

    opportunities: list[dict[str, Any]] = []
    for summary in registry.get("records", []):
        if not isinstance(summary, dict) or summary.get("status") != "published" or summary.get("entity_type") != "doberman":
            continue
        record_id = clean(summary.get("record_id")).upper()
        source_path = root / clean(summary.get("path"))
        if not source_path.is_file():
            continue
        source = load(source_path)
        dog = source.get("doberman") or {}
        identity = dog.get("identity") or {}
        parentage = dog.get("parentage") or {}
        reproduction = dog.get("reproduction") or {}

        kennel_id = clean(identity.get("kennel_id")).upper()
        if kennel_id:
            kennel = kennel_sources.get(kennel_id)
            if kennel and kennel.get("status") != "published":
                opportunities.append({
                    "source_record_id": record_id,
                    "relationship": "kennel",
                    "candidate_record_id": kennel_id,
                    "candidate_name": clean((kennel.get("kennel") or {}).get("name")),
                    "state": clean(kennel.get("status")) or "unpublished",
                    "next_action": "Admin review: confirm public kennel fields before publication.",
                })

        for role in ("sire", "dam"):
            related_id = clean(parentage.get(f"{role}_id")).upper()
            related_name = clean(parentage.get(f"{role}_name"))
            registration = clean(parentage.get(f"{role}_registration"))
            if not related_id and related_name:
                opportunities.append({
                    "source_record_id": record_id,
                    "relationship": role,
                    "candidate_record_id": None,
                    "candidate_name": related_name,
                    "registration": registration or None,
                    "state": "unmatched",
                    "next_action": "Match an existing DI record or create a new record only after source review.",
                })

        declared = reproduction.get("litters_count")
        linked = [clean(value).upper() for value in (reproduction.get("litter_ids") or []) if clean(value)]
        if isinstance(declared, int) and declared > len(linked):
            opportunities.append({
                "source_record_id": record_id,
                "relationship": "offspring_litters",
                "declared_count": declared,
                "linked_count": len(linked),
                "missing_count": declared - len(linked),
                "state": "source_records_needed",
                "next_action": "Collect and review litter source material before creating DI-L records.",
            })

    opportunities.sort(key=lambda item: (item["source_record_id"], item["relationship"], clean(item.get("candidate_record_id") or item.get("candidate_name"))))
    return {
        "schema_version": "1.0.0",
        "generated_from_registry": registry.get("generated_at"),
        "publications_created": 0,
        "policy": "Planning artifact only. It never publishes pending or unmatched entities.",
        "opportunity_count": len(opportunities),
        "opportunities": opportunities,
    }


def main() -> int:
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Relationship opportunities built: {data['opportunity_count']} item(s); 0 records auto-published")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
