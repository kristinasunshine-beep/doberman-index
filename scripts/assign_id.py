#!/usr/bin/env python3
"""Suggest or explicitly reserve the next Doberman Index record ID.

Reading/suggesting never writes a file. A reservation is written only when
both --reserve and --admin are supplied.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^DI-(M|F|K|L)-(\d{6})$")
TYPE_TO_PREFIX = {
    "male": "M",
    "m": "M",
    "di-m": "M",
    "female": "F",
    "f": "F",
    "di-f": "F",
    "kennel": "K",
    "k": "K",
    "di-k": "K",
    "litter": "L",
    "l": "L",
    "di-l": "L",
}
PREFIX_LABEL = {"M": "male", "F": "female", "K": "kennel", "L": "litter"}
RECORD_FOLDERS = ("dobermans", "kennels", "litters")


def load_json(path: Path, *, optional: bool = False) -> Any:
    if optional and not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ValueError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def collect_record_ids(value: Any) -> set[str]:
    """Collect official record_id values without treating relationship IDs as occupied."""
    found: set[str] = set()
    if isinstance(value, dict):
        record_id = value.get("record_id")
        if isinstance(record_id, str) and ID_RE.fullmatch(record_id.strip().upper()):
            found.add(record_id.strip().upper())
        for collection_name in ("records", "reservations"):
            collection = value.get(collection_name)
            if isinstance(collection, list):
                found.update(collect_record_ids(collection))
    elif isinstance(value, list):
        for item in value:
            found.update(collect_record_ids(item))
    return found


def collect_record_file_ids(data_root: Path) -> tuple[set[str], int]:
    """Scan every canonical JSON file, regardless of publication status."""
    found: set[str] = set()
    scanned = 0
    for folder_name in RECORD_FOLDERS:
        folder = data_root / folder_name
        if not folder.exists():
            continue
        if not folder.is_dir():
            raise ValueError(f"Record path is not a directory: {folder}")
        for path in sorted(folder.rglob("*.json")):
            scanned += 1
            filename_id = path.stem.strip().upper()
            if ID_RE.fullmatch(filename_id):
                found.add(filename_id)

            record = load_json(path)
            content_ids = collect_record_ids(record)
            found.update(content_ids)

            top_level_id = record.get("record_id") if isinstance(record, dict) else None
            if (
                ID_RE.fullmatch(filename_id)
                and isinstance(top_level_id, str)
                and ID_RE.fullmatch(top_level_id.strip().upper())
                and filename_id != top_level_id.strip().upper()
            ):
                raise ValueError(
                    f"Record ID mismatch: {path} contains {top_level_id!r}"
                )
    return found, scanned


def next_id(prefix: str, used_ids: set[str]) -> str:
    numbers = [
        int(match.group(2))
        for record_id in used_ids
        if (match := ID_RE.fullmatch(record_id)) and match.group(1) == prefix
    ]
    number = max(numbers, default=0) + 1
    if number > 999999:
        raise ValueError(f"ID range exhausted for DI-{prefix}")
    return f"DI-{prefix}-{number:06d}"


def normalize_reservations(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get("reservations"), list):
        return value
    if isinstance(value, list):
        return {"schema_version": "1.0", "reservations": value}
    if value in ({}, None):
        return {"schema_version": "1.0", "reservations": []}
    raise ValueError("Reservations file must contain a list or a reservations list")


def write_reservation(path: Path, record_id: str, admin: str, note: str) -> None:
    data = normalize_reservations(load_json(path, optional=True))
    existing = collect_record_ids(data)
    if record_id in existing:
        raise ValueError(f"ID is already reserved: {record_id}")
    data["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    data["reservations"].append(
        {
            "record_id": record_id,
            "reserved_by": admin.strip(),
            "reserved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "note": note.strip(),
            "status": "reserved",
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    script_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--type",
        required=True,
        help="male, female, kennel, litter (or DI-M / DI-F / DI-K / DI-L)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=script_root / "data" / "registry.json",
        help="Path to registry.json",
    )
    parser.add_argument(
        "--reservations",
        type=Path,
        default=script_root / ".private" / "id-reservations.json",
        help="Private reservation ledger (never commit it to the public repository)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        help="Data folder containing dobermans/, kennels/ and litters/ (defaults to the registry folder)",
    )
    parser.add_argument("--reserve", action="store_true", help="Write an explicit reservation")
    parser.add_argument("--admin", default="", help="Admin name; required with --reserve")
    parser.add_argument("--note", default="", help="Optional private reservation note")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    prefix = TYPE_TO_PREFIX.get(args.type.strip().lower())
    if not prefix:
        print("Unknown type. Use male, female, kennel, litter, DI-M, DI-F, DI-K or DI-L.", file=sys.stderr)
        return 2
    if args.reserve and not args.admin.strip():
        print("--admin is required when --reserve is used.", file=sys.stderr)
        return 2

    try:
        registry = load_json(args.registry)
        reservations = load_json(args.reservations, optional=True)
        data_root = args.data_root.resolve() if args.data_root else args.registry.resolve().parent
        record_file_ids, scanned_record_files = collect_record_file_ids(data_root)
        used_ids = (
            collect_record_ids(registry)
            | collect_record_ids(reservations)
            | record_file_ids
        )
        suggested = next_id(prefix, used_ids)
        if args.reserve:
            write_reservation(args.reservations, suggested, args.admin, args.note)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    result = {
        "record_type": PREFIX_LABEL[prefix],
        "record_id": suggested,
        "reserved": bool(args.reserve),
        "registry": str(args.registry),
        "reservations": str(args.reservations),
        "data_root": str(data_root),
        "scanned_record_files": scanned_record_files,
        "occupied_record_ids": len(used_ids),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif args.reserve:
        print(f"Reserved {PREFIX_LABEL[prefix]} ID: {suggested}")
    else:
        print(f"Next {PREFIX_LABEL[prefix]} ID: {suggested}")
        print("No reservation was written. Add --reserve --admin \"Name\" to reserve it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
