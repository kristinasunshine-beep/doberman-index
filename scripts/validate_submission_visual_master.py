#!/usr/bin/env python3
"""Lock the approved Submission visual master and paired secure-intake runtime."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "submit.html": "7E2D5EBA1351756B839F8F48C52A2049BB6D38CE9CE41435C08230D4597F31E7",
    "assets/css/submit-v3.css": "E39B9989A9F3BD6324C49971D21F9D910CDB3798C86D94466BC5FD4D2273445D",
    "assets/js/submit-v3.js": "6D8B7806E8DCA007843A71F3C799C8BFDAACE0BDA741311C11D8452784309FD7",
    "assets/js/zip-tools.js": "C2D00A7E08A013C574289BBBF2ACF1D7EBBF09EEE187053981D28DBE2221826E",
}


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

    if mismatches:
        print("Submission visual-master lock FAIL", file=sys.stderr)
        for mismatch in mismatches:
            print(f" - {mismatch}", file=sys.stderr)
        return 1

    print("Submission visual-master lock PASS (approved secure-intake HTML/CSS/runtime and ZIP tools exact)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
