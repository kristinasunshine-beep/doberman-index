#!/usr/bin/env python3
"""Deterministic pedigree analysis for Doberman Index.

COI is calculated from canonical pedigree nodes using the tabular additive
relationship matrix. AI/LLM output is never used for numeric pedigree values.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from typing import Dict, Iterable, List, Optional, Tuple

@dataclass(frozen=True)
class Node:
    id: str
    sire_id: Optional[str] = None
    dam_id: Optional[str] = None


def _topological_order(nodes: Dict[str, Node]) -> List[str]:
    visiting, visited, out = set(), set(), []
    def visit(node_id: str):
        if node_id in visited:
            return
        if node_id in visiting:
            raise ValueError(f"Pedigree cycle detected at {node_id}")
        visiting.add(node_id)
        node = nodes[node_id]
        for parent in (node.sire_id, node.dam_id):
            if parent and parent in nodes:
                visit(parent)
        visiting.remove(node_id)
        visited.add(node_id)
        out.append(node_id)
    for node_id in nodes:
        visit(node_id)
    return out


def relationship_matrix(node_iter: Iterable[Node]) -> Tuple[List[str], List[List[float]]]:
    """Return ordered IDs and numerator/additive relationship matrix A.

    Unknown parents are treated as unrelated founders. This makes the resulting
    COI explicitly a pedigree COI conditional on known ancestry.
    """
    nodes = {n.id: n for n in node_iter}
    order = _topological_order(nodes)
    index = {node_id: i for i, node_id in enumerate(order)}
    n = len(order)
    A = [[0.0] * n for _ in range(n)]
    for i, node_id in enumerate(order):
        node = nodes[node_id]
        s = index.get(node.sire_id) if node.sire_id else None
        d = index.get(node.dam_id) if node.dam_id else None
        for j in range(i):
            sj = A[s][j] if s is not None else 0.0
            dj = A[d][j] if d is not None else 0.0
            A[i][j] = A[j][i] = 0.5 * (sj + dj)
        parental_relationship = A[s][d] if s is not None and d is not None else 0.0
        A[i][i] = 1.0 + 0.5 * parental_relationship
    return order, A


def coi(node_id: str, node_iter: Iterable[Node]) -> float:
    nodes = list(node_iter)
    order, A = relationship_matrix(nodes)
    if node_id not in order:
        raise KeyError(node_id)
    i = order.index(node_id)
    return max(0.0, A[i][i] - 1.0)


def relationship(a: str, b: str, node_iter: Iterable[Node]) -> float:
    nodes = list(node_iter)
    order, A = relationship_matrix(nodes)
    idx = {v: i for i, v in enumerate(order)}
    return A[idx[a]][idx[b]]


def _ancestor_occurrences(root_id: str, nodes: Dict[str, Node], max_generations: int) -> Counter:
    counts = Counter()
    frontier = [(root_id, 0)]
    while frontier:
        node_id, depth = frontier.pop()
        if depth >= max_generations or node_id not in nodes:
            continue
        node = nodes[node_id]
        for parent in (node.sire_id, node.dam_id):
            if parent:
                counts[parent] += 1
                frontier.append((parent, depth + 1))
    return counts


def pedigree_completeness(root_id: str, nodes: Dict[str, Node], generations: int) -> float:
    """Percent of known ancestor slots through N generations."""
    if generations <= 0:
        return 100.0
    known_slots = 0
    expected_slots = sum(2 ** g for g in range(1, generations + 1))
    frontier = [(root_id, 0)]
    while frontier:
        node_id, depth = frontier.pop()
        if depth >= generations or node_id not in nodes:
            continue
        node = nodes[node_id]
        for parent in (node.sire_id, node.dam_id):
            if parent:
                known_slots += 1
                frontier.append((parent, depth + 1))
    return 100.0 * known_slots / expected_slots if expected_slots else 100.0


def analyze(root_id: str, node_iter: Iterable[Node], generations: int = 6) -> dict:
    nodes = {n.id: n for n in node_iter}
    if root_id not in nodes:
        raise KeyError(root_id)
    occ = _ancestor_occurrences(root_id, nodes, generations)
    repeated = {k: v for k, v in occ.items() if v > 1}
    return {
        "coi": coi(root_id, nodes.values()),
        "coi_percent": round(coi(root_id, nodes.values()) * 100, 6),
        "completeness_percent": round(pedigree_completeness(root_id, nodes, generations), 3),
        "unique_ancestors_count": len(occ),
        "repeated_ancestors_count": len(repeated),
        "repeated_ancestors": repeated,
        "generation_depth": generations,
        "calculation_method": "tabular_relationship_matrix",
    }


def projected_offspring_analysis(sire_id: str, dam_id: str, node_iter: Iterable[Node], generations: int = 6) -> dict:
    nodes = list(node_iter)
    virtual_id = "__PROJECTED_OFFSPRING__"
    if sire_id == dam_id:
        raise ValueError("Sire and dam must be different canonical records")
    nodes.append(Node(virtual_id, sire_id, dam_id))
    result = analyze(virtual_id, nodes, generations)
    result["sire_id"] = sire_id
    result["dam_id"] = dam_id
    result["projected"] = True
    return result
