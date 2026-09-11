#!/usr/bin/env python3
"""Keep generated caches and retired IndexNow implementations out of production source."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
for path in ROOT.rglob("__pycache__"):
    if ".git" not in path.parts:
        errors.append(f"tracked/generated Python cache present: {path.relative_to(ROOT)}")
for path in ROOT.rglob("*.pyc"):
    if ".git" not in path.parts:
        errors.append(f"Python bytecode present: {path.relative_to(ROOT)}")
for relative in ("scripts/indexnow.py", "scripts/test_indexnow.py"):
    if (ROOT / relative).exists():
        errors.append(f"retired duplicate IndexNow implementation present: {relative}")
gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
for token in ("__pycache__/", "*.pyc"):
    if token not in gitignore:
        errors.append(f".gitignore missing {token}")
if errors:
    print("Repository hygiene validation FAIL", file=sys.stderr)
    for error in errors:
        print(" -", error, file=sys.stderr)
    raise SystemExit(1)
print("Repository hygiene validation PASS")
