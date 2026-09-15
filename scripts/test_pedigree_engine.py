#!/usr/bin/env python3
from pedigree_engine import Node, coi, relationship, analyze, projected_offspring_analysis

def close(a,b,eps=1e-12):
    assert abs(a-b) < eps, (a,b)

# Unrelated founders -> unrelated child has F=0.
nodes=[Node('A'),Node('B'),Node('C','A','B')]
close(coi('C',nodes),0.0)

# Full-sib mating: parents C and D share both founders -> offspring F=0.25.
nodes=[Node('A'),Node('B'),Node('C','A','B'),Node('D','A','B'),Node('E','C','D')]
close(relationship('C','D',nodes),0.5)
close(coi('E',nodes),0.25)
assert analyze('E',nodes,3)['repeated_ancestors_count'] >= 2

# Parent x offspring mating also yields F=0.25.
nodes=[Node('A'),Node('B'),Node('C','A','B'),Node('D'),Node('E','C','D'),Node('F','C','E')]
close(coi('F',nodes),0.25)

# Projected offspring uses the exact same deterministic engine.
nodes=[Node('A'),Node('B'),Node('C','A','B'),Node('D','A','B')]
projected=projected_offspring_analysis('C','D',nodes,3)
close(projected['coi'],0.25)
print('pedigree_engine: all fixture tests passed')
