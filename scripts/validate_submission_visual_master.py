#!/usr/bin/env python3
"""Lock the approved Submission visual master and paired secure-intake runtime."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "assets/css/submit-v3.css": "E39B9989A9F3BD6324C49971D21F9D910CDB3798C86D94466BC5FD4D2273445D",
    "assets/js/zip-tools.js": "C2D00A7E08A013C574289BBBF2ACF1D7EBBF09EEE187053981D28DBE2221826E",
}

REQUIRED_SUBMIT_TOKENS = (
    'name="registered_name"',
    'name="sex"',
    'name="stud_service_status"',
    'name="hero_photo"',
    'name="head_photo"',
    'name="profile_photo"',
    'name="stack_photo"',
    'name="movement_video"',
)

RETIRED_AGGREGATE_FIELDS = (
    'name="litters_count"',
    'name="offspring_count"',
    'name="champion_offspring_count"',
    'name="export_countries"',
)


def locked_bytes(relative: str, path: Path) -> bytes:
    data = path.read_bytes()
    if relative == "submit.html":
        seo_only = b'<meta content="noindex,follow" name="robots"/>\n'
        if data.count(seo_only) != 1:
            raise ValueError("submit.html must contain exactly one approved SEO-only noindex meta tag")
        data = data.replace(seo_only, b"", 1)
    return data


def sha256(relative: str, path: Path) -> str:
    return hashlib.sha256(locked_bytes(relative, path)).hexdigest().upper()


def main() -> int:
    mismatches = []
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        actual = sha256(relative, path) if path.exists() else "MISSING"
        if actual != expected:
            mismatches.append(f"{relative}: expected {expected}, found {actual}")

    submit_path = ROOT / "submit.html"
    runtime_path = ROOT / "assets/js/submit-v3.js"
    submit = submit_path.read_text(encoding="utf-8") if submit_path.exists() else ""
    runtime = runtime_path.read_text(encoding="utf-8") if runtime_path.exists() else ""

    for token in REQUIRED_SUBMIT_TOKENS:
        if token not in submit:
            mismatches.append(f"submit.html missing required intake control: {token}")
    for token in RETIRED_AGGREGATE_FIELDS:
        if token in submit:
            mismatches.append(f"submit.html still exposes retired aggregate breeding control: {token}")

    if "reproduction:" not in runtime or "litter_ids: []" not in runtime or "stud_service_status" not in runtime:
        mismatches.append("submit-v3.js missing current reproduction relationship/status contract")
    for stale in ("litters_count", "offspring_count", "champion_offspring_count", "export_countries"):
        if stale in runtime:
            mismatches.append(f"submit-v3.js still reads retired aggregate breeding field: {stale}")

    if mismatches:
        print("Submission visual-master lock FAIL", file=sys.stderr)
        for mismatch in mismatches:
            print(f" - {mismatch}", file=sys.stderr)
        return 1

    print("Submission visual-master lock PASS (visual CSS/ZIP exact; intake HTML/runtime semantic contract current)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
