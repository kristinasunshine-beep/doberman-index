#!/usr/bin/env python3
"""Validate launch commerce naming, Dodo provider and public product contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []

commerce = json.loads((ROOT / "data" / "commerce.json").read_text(encoding="utf-8"))
if commerce.get("provider") != "dodo_payments":
    errors.append("data/commerce.json provider must be dodo_payments")
if commerce.get("currency") != "EUR":
    errors.append("commerce currency must be EUR")
if commerce.get("tax_inclusive") is not True:
    errors.append("launch products must be configured as tax inclusive")

products = commerce.get("products", {})
expected = {
    "doberman-intelligence-record": ("Doberman Intelligence Record", 149),
    "kennel-promotion-service": ("Kennel Promotion Service", 149),
}
for key, (name, price) in expected.items():
    product = products.get(key)
    if not product:
        errors.append(f"missing commerce product: {key}")
        continue
    if product.get("name") != name:
        errors.append(f"{key} name mismatch")
    if product.get("price_eur") != price:
        errors.append(f"{key} price must be EUR {price}")

homepage = (ROOT / "index.html").read_text(encoding="utf-8")
for forbidden in ("Indexing Service", "Start Indexing", "Start indexing"):
    if forbidden in homepage:
        errors.append(f"legacy homepage commerce label remains: {forbidden}")
for required in ("Doberman Intelligence Record", "Kennel Promotion Service", "assets/js/commerce.js"):
    if required not in homepage:
        errors.append(f"homepage commerce contract missing: {required}")

for path in [ROOT / "data" / "kennel-services.json", ROOT / "scripts" / "kennel-services.js"]:
    text = path.read_text(encoding="utf-8").lower()
    if "lemon_squeezy" in text or "lemon squeezy" in text:
        errors.append(f"legacy Lemon Squeezy coupling remains in {path.relative_to(ROOT)}")

seo_source = (ROOT / "scripts" / "build_seo.py").read_text(encoding="utf-8")
if "breed intelligence system" not in seo_source.lower():
    errors.append("generated SEO source is not aligned with Breed Intelligence positioning")

if errors:
    raise SystemExit("\n".join(f"- {error}" for error in errors))
print("commerce contract: ok")
