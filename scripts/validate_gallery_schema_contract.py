#!/usr/bin/env python3
"""Validate legacy/new gallery schema compatibility and cardinality limits."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "registry.schema.json").read_text(encoding="utf-8"))


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def gallery_contract(entity: str) -> tuple[dict[str, Any], dict[str, Any]]:
    media = SCHEMA["$defs"][entity]["properties"]["media"]
    gallery = media["properties"]["gallery"]
    branches = gallery.get("items", {}).get("oneOf", [])
    if len(branches) != 2:
        raise AssertionError(f"{entity} gallery must use exactly two oneOf branches")
    legacy = next((branch for branch in branches if branch.get("type") == "string"), None)
    modern = next((branch for branch in branches if branch.get("$ref") == "#/$defs/galleryItem"), None)
    if not legacy or not modern:
        raise AssertionError(f"{entity} gallery must accept legacy string and galleryItem")
    if gallery.get("maxItems") != 10:
        raise AssertionError(f"{entity} gallery maxItems must be 10")
    return gallery, legacy


def valid_focal(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"x", "y"}
        and is_number(value["x"])
        and is_number(value["y"])
        and 0 <= value["x"] <= 100
        and 0 <= value["y"] <= 100
    )


def valid_item(value: Any, path_pattern: str) -> bool:
    if isinstance(value, str):
        return re.fullmatch(path_pattern, value) is not None
    if not isinstance(value, dict):
        return False
    allowed = {"path", "focal_point", "fit_mode", "caption"}
    if not {"path", "focal_point", "fit_mode"}.issubset(value) or not set(value).issubset(allowed):
        return False
    if not isinstance(value["path"], str) or re.fullmatch(path_pattern, value["path"]) is None:
        return False
    if not valid_focal(value["focal_point"]):
        return False
    if value["fit_mode"] not in {"cover", "contain"}:
        return False
    return "caption" not in value or value["caption"] is None or isinstance(value["caption"], str)


def valid_gallery(value: Any, path_pattern: str, maximum: int) -> bool:
    return isinstance(value, list) and len(value) <= maximum and all(valid_item(item, path_pattern) for item in value)


def main() -> int:
    errors: list[str] = []
    try:
        contracts = {entity: gallery_contract(entity) for entity in ("doberman", "kennel", "litter")}
        gallery_item = SCHEMA["$defs"]["galleryItem"]
        if set(gallery_item.get("required", [])) != {"path", "focal_point", "fit_mode"}:
            errors.append("galleryItem required fields drifted")
        if gallery_item.get("properties", {}).get("fit_mode", {}).get("enum") != ["cover", "contain"]:
            errors.append("galleryItem fit_mode must be cover / contain")
        path_pattern = contracts["doberman"][1]["pattern"]
        if gallery_item.get("properties", {}).get("path", {}).get("pattern") != path_pattern:
            errors.append("legacy and object gallery paths use different validation")

        legacy = "media/dobermans/DI-M-000001/gallery-01.jpg"
        modern = {"path": legacy, "focal_point": {"x": 50, "y": 50}, "fit_mode": "cover"}
        cases = {
            "A legacy string": valid_gallery([legacy], path_pattern, 10),
            "B new object": valid_gallery([modern], path_pattern, 10),
            "C focal below range": not valid_gallery([{**modern, "focal_point": {"x": -1, "y": 50}}], path_pattern, 10),
            "C focal above range": not valid_gallery([{**modern, "focal_point": {"x": 101, "y": 50}}], path_pattern, 10),
            "D invalid fit_mode": not valid_gallery([{**modern, "fit_mode": "stretch"}], path_pattern, 10),
            "E zero images": valid_gallery([], path_pattern, 10),
            "F one image": valid_gallery([modern], path_pattern, 10),
            "G ten images": valid_gallery([modern] * 10, path_pattern, 10),
            "H eleven images": not valid_gallery([modern] * 11, path_pattern, 10),
        }
        errors.extend(label for label, passed in cases.items() if not passed)
    except (AssertionError, KeyError, TypeError) as exc:
        errors.append(str(exc))

    if errors:
        print("Gallery schema contract FAIL", file=sys.stderr)
        for error in errors:
            print(f" - {error}", file=sys.stderr)
        return 1
    print("Gallery schema contract PASS (legacy + object; focal/fit limits; 0/1/10 valid; 11 rejected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
