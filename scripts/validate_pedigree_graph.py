#!/usr/bin/env python3
"""Validate canonical pedigree graph identity and relationship integrity."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "data" / "pedigree-graph.json"


def fail(msg: str) -> None:
    print(f"Pedigree graph FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    graph = json.loads(PATH.read_text(encoding="utf-8"))
    if graph.get("schema_version") != "1.0.0" or not isinstance(graph.get("nodes"), dict):
        fail("invalid graph envelope")
    nodes = graph["nodes"]
    regs = {}
    for node_id, node in nodes.items():
        if not node.get("registered_name"):
            fail(f"{node_id} has no registered_name")
        for rel in ("sire_id", "dam_id"):
            parent = node.get(rel)
            if parent and parent not in nodes:
                fail(f"{node_id}.{rel} points to missing node {parent}")
            if parent == node_id:
                fail(f"{node_id} cannot be its own parent")
        for reg in node.get("registration_numbers", []):
            key = reg.strip().upper()
            if key and key in regs and regs[key] != node_id:
                fail(f"registration number {reg!r} is assigned to both {regs[key]} and {node_id}")
            if key:
                regs[key] = node_id
    # relationship engine performs the final cycle check
    sys.path.insert(0, str(ROOT / "scripts"))
    from pedigree_engine import Node, relationship_matrix
    relationship_matrix(Node(i, n.get("sire_id"), n.get("dam_id")) for i, n in nodes.items())
    print(f"Pedigree graph PASS · {len(nodes)} canonical node(s)")


if __name__ == "__main__":
    main()
