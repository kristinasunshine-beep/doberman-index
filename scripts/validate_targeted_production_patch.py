#!/usr/bin/env python3
"""Validate media contracts and production canonical/registry consistency."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_ID = re.compile(r"^DI-(M|F|K|L)-\d{6}$")
CANONICAL_FOLDERS = {
    "dobermans": ("doberman", {"M", "F"}),
    "kennels": ("kennel", {"K"}),
    "litters": ("litter", {"L"}),
}


def registry_consistency_errors(root: Path, registry: object) -> list[str]:
    """Reject missing, stale, malformed or duplicate IDs without a record-count cap."""
    errors: list[str] = []
    canonical_ids: dict[str, Path] = {}
    published_ids: set[str] = set()
    for folder, (entity, prefixes) in CANONICAL_FOLDERS.items():
        for path in sorted((root / "data" / folder).rglob("*.json")):
            try:
                record = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as exc:
                errors.append(f"cannot read canonical record {path.relative_to(root)}: {exc}")
                continue
            if not isinstance(record, dict):
                errors.append(f"canonical record must be an object: {path.relative_to(root)}")
                continue
            record_id = record.get("record_id")
            match = OFFICIAL_ID.fullmatch(record_id) if isinstance(record_id, str) else None
            if not match:
                errors.append(f"invalid canonical record_id in {path.relative_to(root)}")
                continue
            if record_id in canonical_ids:
                errors.append(f"duplicate canonical record ID: {record_id}")
            canonical_ids[record_id] = path
            if path.stem != record_id or match.group(1) not in prefixes or record.get("entity_type") != entity:
                errors.append(f"canonical ID/file/entity mismatch: {path.relative_to(root)}")
            if record.get("status") == "published":
                published_ids.add(record_id)

    entries = registry.get("records") if isinstance(registry, dict) else None
    if not isinstance(entries, list):
        return errors + ["registry.records must be an array"]
    registry_ids: set[str] = set()
    for entry in entries:
        record_id = entry.get("record_id") if isinstance(entry, dict) else None
        if not isinstance(record_id, str) or not OFFICIAL_ID.fullmatch(record_id):
            errors.append("registry entry has an invalid official record_id")
            continue
        if record_id in registry_ids:
            errors.append(f"duplicate registry record ID: {record_id}")
        registry_ids.add(record_id)
        if entry.get("status") != "published":
            errors.append(f"registry entry is not published: {record_id}")
    for record_id in sorted(published_ids - registry_ids):
        errors.append(f"published canonical record missing from registry: {record_id}")
    for record_id in sorted(registry_ids - published_ids):
        errors.append(f"registry ID has no published canonical record: {record_id}")
    return errors


def main() -> int:
    errors: list[str] = []
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    profile = (ROOT / "profile.html").read_text(encoding="utf-8")
    male = (ROOT / "profiles" / "male.html").read_text(encoding="utf-8")
    builder = (ROOT / "scripts" / "build_registry.py").read_text(encoding="utf-8")
    schema = json.loads((ROOT / "schemas" / "registry.schema.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "data" / "registry.json").read_text(encoding="utf-8"))

    for page, text in (("index", index), ("profile router", profile), ("male profile", male)):
        if "display-name.js" not in text:
            errors.append(f"{page} does not load the centralized registered-name display module")

    for page, text in (("index", index), ("male profile", male)):
        if "media-presentation.js" not in text:
            errors.append(f"{page} does not load the centralized focal-point presentation module")

    required_index = ["displayRegisteredName(record.registered_name", "applyFocalPoint(image, record.focalPoint)", "hero_focal_point"]
    required_male = [
        "displayRegisteredName(identity.registered_name",
        "focalPointFor(media,\"hero\")",
        "hero_focal_point",
        "object-position:",
        "frameSpecFor(role)",
        'data-media-role="${escapeHTML(role||"gallery")}"',
        'data-frame-orientation="${escapeHTML(frame.orientation)}"',
        'data-frame-fit="${escapeHTML(frameFit)}"',
        "normalizeGalleryItem(entry)",
        'focalPosition(item.focal_point)',
        'item.fit_mode',
    ]
    for token in required_index:
        if token not in index:
            errors.append(f"index missing targeted patch token: {token}")
    for token in required_male:
        if token not in male:
            errors.append(f"male profile missing targeted patch token: {token}")

    media_schema = schema.get("$defs", {}).get("doberman", {}).get("properties", {}).get("media", {})
    focal_schema = media_schema.get("properties", {}).get("focal_points", {})
    if not focal_schema or "focalPoint" not in schema.get("$defs", {}):
        errors.append("canonical schema does not define backward-compatible focal points")
    gallery_item = schema.get("$defs", {}).get("galleryItem", {})
    gallery_schema = media_schema.get("properties", {}).get("gallery", {})
    gallery_branches = gallery_schema.get("items", {}).get("oneOf", [])
    if not any(branch.get("type") == "string" for branch in gallery_branches):
        errors.append("Doberman gallery does not accept legacy string paths")
    if not any(branch.get("$ref") == "#/$defs/galleryItem" for branch in gallery_branches):
        errors.append("Doberman gallery is not bound to the galleryItem contract")
    if set(gallery_item.get("required", [])) != {"path", "focal_point", "fit_mode"}:
        errors.append("galleryItem does not require path, focal_point and fit_mode")
    if gallery_item.get("properties", {}).get("fit_mode", {}).get("enum") != ["cover", "contain"]:
        errors.append("galleryItem fit_mode is not limited to cover / contain")
    if 'gallery: Object.freeze({ aspectRatio: "4 / 5", orientation: "portrait", fit: "cover" })' not in (ROOT / "assets" / "js" / "media-presentation.js").read_text(encoding="utf-8"):
        errors.append("additional gallery public frame is not locked to 4:5 portrait")
    if "hero_focal_point" not in builder or 'focal_point(media, "hero")' not in builder:
        errors.append("registry builder does not carry hero focal point into reusable public cards")
    errors.extend(registry_consistency_errors(ROOT, registry))

    if errors:
        print("Targeted production patch FAIL", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    print(f"Public media patch PASS (role frames + gallery focal/fit + canonical/registry consistency; {len(registry['records'])} published records)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
