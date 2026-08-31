#!/usr/bin/env python3
"""Rebuild data/registry.json from canonical Doberman Index records."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^DI-(M|F|K|L)-(\d{6})$")
SOURCE_RULES = {
    "dobermans": ("doberman", {"M", "F"}),
    "kennels": ("kennel", {"K"}),
    "litters": ("litter", {"L"}),
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Record must be a JSON object: {path}")
    return value


def validate_record(path: Path, data: dict[str, Any], expected: str, prefixes: set[str]) -> str:
    record_id = str(data.get("record_id") or "").strip().upper()
    match = ID_RE.fullmatch(record_id)
    if not match:
        raise ValueError(f"Invalid or missing record_id in {path}: {record_id or '(empty)'}")
    if match.group(1) not in prefixes:
        allowed = ", ".join(f"DI-{prefix}" for prefix in sorted(prefixes))
        raise ValueError(f"{record_id} is in the wrong folder; expected {allowed}")
    if data.get("entity_type") != expected:
        raise ValueError(f"{record_id} declares entity_type={data.get('entity_type')!r}; expected {expected!r}")
    if data.get(expected) is None:
        raise ValueError(f"{record_id} is missing its canonical {expected} block")
    return record_id


def focal_point(media: dict[str, Any], role: str) -> dict[str, float]:
    source = (media.get("focal_points") or {}).get(role) or {}
    def coordinate(key: str) -> float:
        try:
            value = float(source.get(key, 50))
        except (TypeError, ValueError):
            value = 50
        return min(100, max(0, value))
    return {"x": coordinate("x"), "y": coordinate("y")}


def doberman_entry(path: Path, data: dict[str, Any], root: Path) -> dict[str, Any]:
    dog = data["doberman"]
    identity = dog.get("identity") or {}
    parentage = dog.get("parentage") or {}
    media = dog.get("media") or {}
    performance = dog.get("performance") or {}
    reproduction = dog.get("reproduction") or {}
    puppy = dog.get("puppy_lifecycle") or {}
    publication = dog.get("publication") or {}
    source_life_stage = str(identity.get("life_stage") or "").lower()
    legacy_deceased = source_life_stage == "deceased"
    life_stage = "unknown" if legacy_deceased else source_life_stage
    life_status = str(identity.get("life_status") or ("deceased" if legacy_deceased else "unknown")).lower()
    sex = str(identity.get("sex") or "").lower()
    template = publication.get("profile_template") or ("puppy" if life_stage == "puppy" else sex)
    availability = puppy.get("current_status") if life_stage == "puppy" else reproduction.get("availability")
    if life_status == "deceased" or availability in ("not_applicable", "unknown"):
        availability = None
    return {
        "record_id": data["record_id"],
        "entity_type": "doberman",
        "status": "published",
        "template": template,
        "registered_name": identity.get("registered_name"),
        "sex": sex,
        "life_stage": life_stage,
        "life_status": life_status,
        "date_of_birth": identity.get("date_of_birth"),
        "date_of_death": identity.get("date_of_death"),
        "year_of_death": identity.get("year_of_death"),
        "country": identity.get("country"),
        "location": identity.get("location"),
        "kennel_id": identity.get("kennel_id"),
        "kennel_name": identity.get("kennel_name"),
        "litter_id": parentage.get("litter_id"),
        "sire_id": parentage.get("sire_id"),
        "dam_id": parentage.get("dam_id"),
        "availability": availability,
        "hero": media.get("hero"),
        "hero_focal_point": focal_point(media, "hero"),
        "titles": performance.get("titles") or [],
        "path": path.relative_to(root).as_posix(),
    }


def kennel_entry(path: Path, data: dict[str, Any], root: Path) -> dict[str, Any]:
    kennel = data["kennel"]
    return {
        "record_id": data["record_id"],
        "entity_type": "kennel",
        "status": "published",
        "template": "kennel",
        "name": kennel.get("name"),
        "country": kennel.get("country"),
        "hero": (kennel.get("media") or {}).get("cover"),
        "path": path.relative_to(root).as_posix(),
    }


def litter_entry(path: Path, data: dict[str, Any], root: Path) -> dict[str, Any]:
    litter = data["litter"]
    return {
        "record_id": data["record_id"],
        "entity_type": "litter",
        "status": "published",
        "template": "litter",
        "name": litter.get("name"),
        "kennel_id": litter.get("kennel_id"),
        "sire_id": litter.get("sire_id"),
        "dam_id": litter.get("dam_id"),
        "date_of_birth": litter.get("date_of_birth"),
        "status_label": litter.get("status"),
        "available_puppy_ids": litter.get("available_puppy_ids") or [],
        "hero": (litter.get("media") or {}).get("cover"),
        "path": path.relative_to(root).as_posix(),
    }


def build(root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    seen: dict[str, Path] = {}
    builders = {"doberman": doberman_entry, "kennel": kennel_entry, "litter": litter_entry}
    for folder, (entity_type, prefixes) in SOURCE_RULES.items():
        source = root / "data" / folder
        if not source.exists():
            continue
        for path in sorted(source.glob("DI-*.json")):
            data = load_json(path)
            record_id = validate_record(path, data, entity_type, prefixes)
            if record_id in seen:
                raise ValueError(f"Duplicate record_id {record_id}: {seen[record_id]} and {path}")
            seen[record_id] = path
            if data.get("status") != "published":
                continue
            records.append(builders[entity_type](path, data, root))
    records.sort(key=lambda item: item["record_id"])
    return {"schema_version": "1.1.0", "records": records}


def comparable(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {key: item for key, item in value.items() if key != "generated_at"}


def parse_args() -> argparse.Namespace:
    default_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=default_root, help="Repository root")
    parser.add_argument("--output", type=Path, help="Override data/registry.json output")
    parser.add_argument("--check", action="store_true", help="Fail if registry is out of date; do not write")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "data" / "registry.json"
    try:
        fresh = build(root)
        existing = load_json(output) if output.exists() else None
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    changed = comparable(existing) != comparable(fresh)
    if args.check:
        if changed:
            print(f"Registry is out of date: {output}", file=sys.stderr)
            return 1
        print(f"Registry is current ({len(fresh['records'])} published records).")
        return 0
    if not changed:
        print(f"Registry unchanged ({len(fresh['records'])} published records).")
        return 0
    fresh["generated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"registry.json rebuilt: {len(fresh['records'])} published records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
