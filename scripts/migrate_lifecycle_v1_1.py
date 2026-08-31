#!/usr/bin/env python3
"""Migrate Doberman records to lifecycle schema v1.1.0.

Legacy ``life_stage: deceased`` becomes ``life_stage: unknown`` plus
``life_status: deceased``. Missing life status is never guessed as living.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


LIFE_STAGES = {"puppy", "junior", "adult", "veteran", "unknown"}
LIFE_STATUSES = {"living", "deceased", "unknown"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("record is not a JSON object")
    return value


def migrate(record: dict[str, Any]) -> bool:
    if record.get("entity_type") != "doberman" or not isinstance(record.get("doberman"), dict):
        return False

    before = json.dumps(record, sort_keys=True, ensure_ascii=False)
    dog = record["doberman"]
    identity = dog.setdefault("identity", {})
    source_stage = str(identity.get("life_stage") or "unknown").lower()
    legacy_deceased = source_stage == "deceased"

    identity["life_stage"] = "unknown" if legacy_deceased else (source_stage if source_stage in LIFE_STAGES else "unknown")
    source_status = str(identity.get("life_status") or ("deceased" if legacy_deceased else "unknown")).lower()
    identity["life_status"] = source_status if source_status in LIFE_STATUSES else "unknown"
    identity.setdefault("date_of_death", None)
    identity.setdefault("year_of_death", None)

    health = dog.setdefault("health", {})
    health.setdefault(
        "mortality",
        {"cause": None, "cause_disclosure": "not_provided", "evidence_source": None, "evidence_file": None},
    )

    if identity["life_status"] == "deceased":
        dog.setdefault("reproduction", {})["availability"] = "not_applicable"
        dog.setdefault("puppy_lifecycle", {})["current_status"] = "not_applicable"

    record["schema_version"] = "1.1.0"
    after = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return before != after


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", action="store_true", help="Write migrated records in place")
    args = parser.parse_args()

    paths = sorted((args.root / "data" / "dobermans").glob("DI-*.json"))
    changed: list[Path] = []
    errors: list[str] = []
    for path in paths:
        try:
            record = load(path)
            if migrate(record):
                changed.append(path)
                if args.write:
                    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")

    if errors:
        print("Lifecycle migration failed:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    if changed and not args.write:
        print(f"{len(changed)} record(s) require lifecycle migration. Run again with --write.", file=sys.stderr)
        return 1
    action = "migrated" if args.write else "current"
    print(f"Lifecycle records {action} ({len(paths)} checked, {len(changed)} changed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
