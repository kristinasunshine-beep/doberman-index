#!/usr/bin/env python3
"""Offline smoke tests for scripts/indexnow.py."""
from pathlib import Path
import importlib.util
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("indexnow", HERE / "indexnow.py")
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

base = "https://doberman-index.com"

cases = {
    "index.html": f"{base}/",
    "about.html": f"{base}/about.html",
    "records/DI-M-000001/index.html": f"{base}/records/DI-M-000001/",
    "records/DI-L-000001/index.html": f"{base}/records/DI-L-000001/",
    "profiles/male.html": None,
    "profile.html": None,
    "submit.html": None,
    "assets/js/seo-runtime.js": None,
}

for path, expected in cases.items():
    actual = mod.canonical_url_for_path(path, base)
    assert actual == expected, (path, actual, expected)

with tempfile.TemporaryDirectory() as tmp:
    key = "a" * 32
    p = Path(tmp) / f"{key}.txt"
    p.write_text(key, encoding="utf-8")
    assert mod.key_value(p) == key

print("IndexNow offline smoke tests passed.")
