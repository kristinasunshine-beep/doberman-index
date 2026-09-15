#!/usr/bin/env python3
"""Apply deterministic pedigree intelligence to published Doberman records.

The canonical graph is intentionally separate from display pedigrees. A name
match alone never establishes identity. Numeric lineage values are published
only when the subject has canonical ancestry mapped. Missing ancestry remains
visible through pedigree completeness.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from pedigree_engine import Node, analyze

ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "data" / "pedigree-graph.json"
DOG_DIR = ROOT / "data" / "dobermans"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical_nodes(graph: dict) -> list[Node]:
    return [Node(node_id, item.get("sire_id"), item.get("dam_id")) for node_id, item in graph.get("nodes", {}).items()]


def status_payload(message: str, generations: int = 6) -> dict:
    return {
        "status": "pending_canonical_mapping",
        "coi_percent": None,
        "avk_percent": None,
        "completeness_percent": None,
        "unique_ancestors_count": None,
        "maximum_ancestor_slots": None,
        "repeated_ancestors_count": None,
        "generation_depth": generations,
        "calculation_method": "tabular_relationship_matrix",
        "note": message,
    }


def intelligence_for(record_id: str, graph: dict, generations: int) -> dict:
    item = graph.get("nodes", {}).get(record_id)
    if not item:
        return status_payload("Pedigree supplied; canonical ancestor mapping is required before publishing pedigree calculations.", generations)
    if not item.get("sire_id") or not item.get("dam_id"):
        return status_payload("Canonical sire and dam must both be mapped before publishing pedigree COI.", generations)
    result = analyze(record_id, canonical_nodes(graph), generations)
    return {
        "status": "calculated",
        "coi_percent": result["coi_percent"],
        "avk_percent": result["avk_percent"],
        "completeness_percent": result["completeness_percent"],
        "unique_ancestors_count": result["unique_ancestors_count"],
        "maximum_ancestor_slots": result["maximum_ancestor_slots"],
        "repeated_ancestors_count": result["repeated_ancestors_count"],
        "generation_depth": result["generation_depth"],
        "calculation_method": result["calculation_method"],
        "note": "Pedigree COI and AVK are calculated from currently mapped canonical ancestry; unknown ancestors reduce pedigree completeness.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write calculated values back to Doberman JSON records")
    parser.add_argument("--generations", type=int, default=6)
    args = parser.parse_args()

    graph = load_json(GRAPH_PATH)
    changed = 0
    for path in sorted(DOG_DIR.glob("*.json")):
        payload = load_json(path)
        record_id = payload.get("record_id")
        dog = payload.get("doberman") or {}
        if not record_id or not dog:
            continue
        current_depth = ((dog.get("pedigree_intelligence") or {}).get("generation_depth"))
        generations = int(current_depth or args.generations)
        result = intelligence_for(record_id, graph, generations)
        if dog.get("pedigree_intelligence") != result:
            dog["pedigree_intelligence"] = result
            changed += 1
            if args.write:
                dump_json(path, payload)
        suffix = f" · COI {result['coi_percent']}% · AVK {result['avk_percent']}%" if result['coi_percent'] is not None else ""
        print(f"{record_id}: {result['status']}{suffix}")

    if args.write:
        print(f"Pedigree intelligence sync complete: {changed} record(s) updated.")
    else:
        print(f"Pedigree intelligence dry run: {changed} record(s) would change.")


if __name__ == "__main__":
    main()
