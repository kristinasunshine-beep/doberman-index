#!/usr/bin/env python3
from pathlib import Path
import json
from html.parser import HTMLParser


class InputCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        if tag == "input":
            self.inputs.append(dict(attrs))


ROOT=Path(__file__).resolve().parents[1]
standard=json.loads((ROOT/"data"/"assessment-standard.json").read_text(encoding="utf-8"))
schema=json.loads((ROOT/"schemas"/"registry.schema.json").read_text(encoding="utf-8"))
html=(ROOT/"submit.html").read_text(encoding="utf-8")
collector=InputCollector()
collector.feed(html)
errors=[]
dob=schema["$defs"]["doberman"]["properties"]
name_map={"type":"structure_type","head":"structure_head","body":"structure_body","angulation":"structure_angulation","movement":"structure_movement","balance":"structure_balance"}
for key,allowed in standard["structure"].items():
    spec=dob["structure"]["properties"][key]
    if spec.get("type") != ["array","null"] or spec.get("maxItems") != 2 or spec.get("uniqueItems") is not True or spec.get("items",{}).get("enum") != allowed:
        errors.append(f"schema drift: structure.{key}")
    name=name_map[key]
    found=[el.get("value") for el in collector.inputs if el.get("type")=="checkbox" and el.get("name")==name and "structure-choice" in (el.get("class") or "").split()]
    if found != allowed: errors.append(f"owner form drift: structure.{key}: {found!r}")
for key,allowed in standard["temperament"].items():
    spec=dob["temperament"]["properties"][key]
    if spec.get("enum") != [None]+allowed: errors.append(f"schema drift: temperament.{key}")
    found=[el.get("value") for el in collector.inputs if el.get("type")=="radio" and el.get("name")==key and "temperament-choice" in (el.get("class") or "").split()]
    if found != allowed: errors.append(f"owner form drift: temperament.{key}: {found!r}")
if 'Tick one or two.' not in html: errors.append('owner form missing Structure cardinality instruction')
if 'Tick one.' not in html: errors.append('owner form missing Temperament cardinality instruction')
for forbidden in ('temperament_summary','structure_summary','How would you describe','Character summary','Structure summary'):
    if forbidden.lower() in html.lower(): errors.append(f"forbidden free-text/subjective prompt remains: {forbidden}")
if errors:
    print('Controlled profile validation FAILED:')
    for e in errors: print(' -',e)
    raise SystemExit(1)
print('Controlled profile validation PASS.')
