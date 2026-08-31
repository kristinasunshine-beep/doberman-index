#!/usr/bin/env python3
"""Lock the approved v5.9.21 Submission visual master and paired runtime."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "submit.html": "58C6B172113D080ABFFE886B14802ACFFB3176C56C603652C2BA3BE28001DCF0",
    "assets/css/submit-v3.css": "23FD5A395F5D24F663F0E67AF987F7316E9EBB6E913165B617E43B1C0CC1B357",
    "assets/js/submit-v3.js": "3772C11FD6196F7E161011431018EA086A2EABEEA20FC7F330FA787F8F029340",
    "assets/js/zip-tools.js": "C2D00A7E08A013C574289BBBF2ACF1D7EBBF09EEE187053981D28DBE2221826E",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> int:
    mismatches = []
    for relative, expected in EXPECTED.items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else "MISSING"
        if actual != expected:
            mismatches.append(f"{relative}: expected {expected}, found {actual}")

    if mismatches:
        print("v5.9.21 Submission visual-master lock FAIL", file=sys.stderr)
        for mismatch in mismatches:
            print(f" - {mismatch}", file=sys.stderr)
        return 1

    print("v5.9.21 Submission visual-master lock PASS (HTML, CSS, lifecycle JS and ZIP tools exact)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
