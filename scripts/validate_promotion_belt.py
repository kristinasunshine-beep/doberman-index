#!/usr/bin/env python3
"""Validate the paid kennel promotion belt contract and local assets."""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ID_RE = re.compile(r"^DI-K-\d{6}$")
LOGO_RE = re.compile(r"^media/kennels/(DI-K-\d{6})/[^/]+\.(svg|png|webp)$")
LOCAL_DESTINATION_RE = re.compile(r"^profile\.html\?id=(DI-K-\d{6})$")
ALLOWED_STATUS = {"planned", "active", "expired"}
REQUIRED = {"kennel_id", "kennel_name", "country", "logo", "destination", "starts_on", "ends_on", "status"}


def parse_day(value: object, label: str, errors: list[str]) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        errors.append(f"{label}: expected YYYY-MM-DD")
        return None


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    config_path = root / "data" / "promotion-belt.json"
    errors: list[str] = []
    try:
        data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        print(f"Promotion belt validation failed: {exc}", file=sys.stderr)
        return 1

    if data.get("schema_version") != "1.0.0":
        errors.append("schema_version: expected 1.0.0")
    placements = data.get("placements")
    if not isinstance(placements, list):
        errors.append("placements: expected an array")
        placements = []
    if len(placements) > 24:
        errors.append("placements: maximum 24 paid kennel placements")

    used: set[str] = set()
    for index, placement in enumerate(placements, start=1):
        label = f"placement {index}"
        if not isinstance(placement, dict):
            errors.append(f"{label}: expected an object")
            continue
        missing = REQUIRED - placement.keys()
        extra = placement.keys() - REQUIRED
        if missing:
            errors.append(f"{label}: missing {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{label}: unsupported fields {', '.join(sorted(extra))}")

        kennel_id = str(placement.get("kennel_id") or "")
        if not ID_RE.fullmatch(kennel_id):
            errors.append(f"{label}: invalid kennel_id")
        elif kennel_id in used:
            errors.append(f"{label}: duplicate kennel_id {kennel_id}")
        used.add(kennel_id)

        for field, maximum in (("kennel_name", 100), ("country", 80)):
            value = str(placement.get(field) or "").strip()
            if len(value) < 2 or len(value) > maximum:
                errors.append(f"{label}: invalid {field}")

        logo = str(placement.get("logo") or "")
        logo_match = LOGO_RE.fullmatch(logo)
        if not logo_match:
            errors.append(f"{label}: logo must be SVG, PNG or WebP inside media/kennels/<DI-K-ID>/")
        else:
            if logo_match.group(1) != kennel_id:
                errors.append(f"{label}: logo folder must match kennel_id")
            if not (root / logo).is_file():
                errors.append(f"{label}: logo file is missing: {logo}")

        destination = str(placement.get("destination") or "")
        local_match = LOCAL_DESTINATION_RE.fullmatch(destination)
        if local_match:
            if local_match.group(1) != kennel_id:
                errors.append(f"{label}: local destination ID must match kennel_id")
        else:
            parsed = urlparse(destination)
            if parsed.scheme != "https" or not parsed.netloc:
                errors.append(f"{label}: destination must be a local kennel profile or an HTTPS URL")

        starts = parse_day(placement.get("starts_on"), f"{label}.starts_on", errors)
        ends = parse_day(placement.get("ends_on"), f"{label}.ends_on", errors)
        if starts and ends and ends <= starts:
            errors.append(f"{label}: ends_on must be later than starts_on")
        if placement.get("status") not in ALLOWED_STATUS:
            errors.append(f"{label}: invalid status")

    if errors:
        print("Promotion belt validation failed:", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    print(f"Promotion belt valid ({len(placements)} configured placements; maximum 24).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
