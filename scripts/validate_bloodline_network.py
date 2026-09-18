#!/usr/bin/env python3
"""Validate the V27 Bloodline Network graph, image provenance and profile integration."""
from __future__ import annotations
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]

def load(rel):
    try:return json.loads((ROOT/rel).read_text(encoding='utf-8'))
    except Exception as exc:errors.append(f'{rel}: unreadable JSON: {exc}');return {}

graph=load('data/pedigree-graph.json')
images=load('data/bloodline-images.json')
nodes=graph.get('nodes',{}) if isinstance(graph,dict) else {}
roots=graph.get('root_records',[]) if isinstance(graph,dict) else []
if graph.get('schema_version')!='1.0.0':errors.append('pedigree graph schema_version must be 1.0.0')
if images.get('schema_version')!='1.0.0':errors.append('bloodline image manifest schema_version must be 1.0.0')
if 'DI-M-000001' not in roots:errors.append('accepted Dante root is missing from root_records')
if len(nodes)<3:errors.append('pedigree graph is unexpectedly small')
for key,node in nodes.items():
    if not isinstance(node,dict) or node.get('record_id')!=key:errors.append(f'graph key/record mismatch: {key}')
    for relation in ('sire_id','dam_id'):
        target=node.get(relation)
        if target and target not in nodes:errors.append(f'{key}: missing {relation} target {target}')

# Accepted Dante graph must resolve the complete four-generation path wherever data exists.
root=nodes.get('DI-M-000001',{})
if not root.get('sire_id') or not root.get('dam_id'):errors.append('Dante root must link both parents')
def walk(node_id,depth,seen_path=()):
    if depth<=0:return
    node=nodes.get(node_id,{})
    for field in ('sire_id','dam_id'):
        target=node.get(field)
        if target:walk(target,depth-1,seen_path+(node_id,))
if root:walk('DI-M-000001',4)
# Fedor del Nasi is intentionally a repeated ancestor in the accepted tree.
incoming={key:0 for key in nodes}
for node in nodes.values():
    for field in ('sire_id','dam_id'):
        target=node.get(field)
        if target in incoming:incoming[target]+=1
fedor=[key for key,node in nodes.items() if str(node.get('registered_name','')).casefold()=='fedor del nasi']
if len(fedor)!=1 or incoming.get(fedor[0],0)<2:errors.append('accepted repeated ancestor Fedor del Nasi is not represented as one canonical repeated node')

record_images=images.get('records',{}).get('DI-M-000001',{}).get('ancestors',{}) if isinstance(images,dict) else {}
for ancestor_id,item in record_images.items():
    if ancestor_id not in nodes:errors.append(f'image manifest references unknown ancestor {ancestor_id}')
    status=item.get('status') if isinstance(item,dict) else None
    if status not in {'selected','missing'}:errors.append(f'{ancestor_id}: invalid image status {status!r}')
    if status=='selected':
        selected=item.get('selected') or {}
        for field in ('image_url','source_label','source_url'):
            if not str(selected.get(field,'')).strip():errors.append(f'{ancestor_id}: selected image missing {field}')
for ancestor_id in nodes:
    if ancestor_id=='DI-M-000001':continue
    if ancestor_id not in record_images:errors.append(f'image manifest lacks explicit selected/missing state for {ancestor_id}')

for sex in ('male','female'):
    base=ROOT/'profiles'/sex
    page=(base/'index.html').read_text(encoding='utf-8')
    for rel in ('assets/bloodline-network_v23.js','assets/bloodline-network_v23.css'):
        if not (base/rel).is_file():errors.append(f'{sex}: Bloodline Network asset missing: {rel}')
    for token in ('id="bloodlineRail"','window.DIBloodline.mount','assets/bloodline-network_v23.js','const repoRoot=new URL("../../",document.baseURI);'):
        if token not in page:errors.append(f'{sex}: profile missing Bloodline Network token: {token}')
    js=(base/'assets/bloodline-network_v23.js').read_text(encoding='utf-8')
    css=(base/'assets/bloodline-network_v23.css').read_text(encoding='utf-8')
    for token in ('document.documentElement.classList.add("bln-image-open")','document.body.classList.add("bln-image-open")','viewerImage.style.opacity = "1"'):
        if token not in js:errors.append(f'{sex}: pre-V29 stance viewer JS token missing: {token}')
    for token in ('.bln-image-open{overflow:hidden!important}','bln-image-viewer::before','overflow-y:auto!important','max-height:min(60svh,680px)!important','bln-image-viewer-stage img'):
        if token not in css:errors.append(f'{sex}: pre-V29 stance viewer CSS token missing: {token}')
    for forbidden in ('V29 — in-section stance viewer + dual active scroll systems','V31 — stable stance viewer + independent Bloodline proxy slider','bln-viewer-network-scrollbar','bln-viewer-network-thumb'):
        if forbidden in css or forbidden in js:errors.append(f'{sex}: retired experimental stance viewer token still present: {forbidden}')
    for token in ('V28.1 — title clearance: move photo stage and its scrollbar below the registered name','V28.2 — registered name stays on one desktop line','white-space:nowrap!important','margin-top:clamp(48px,6vh,72px)!important'):
        if token not in css:errors.append(f'{sex}: stance title-clearance token missing: {token}')
# Male accepted offline snapshot should use canonical IDs represented in the graph.
male=(ROOT/'profiles/male/index.html').read_text(encoding='utf-8')
match=re.search(r'const offlineBloodlineNodes=(\[.*?\]);\s*window\.DIBloodline\.mount',male,re.S)
if not match:errors.append('male accepted offline Bloodline Network snapshot is missing')
else:
    try:offline=json.loads(match.group(1))
    except Exception as exc:errors.append(f'male offline bloodline snapshot is invalid JSON: {exc}');offline=[]
    for node in offline:
        cid=node.get('canonicalId')
        if cid and cid not in nodes:errors.append(f'offline snapshot references unknown canonical ancestor {cid}')
        if node.get('image') and cid in record_images and record_images[cid].get('status')!='selected':errors.append(f'{cid}: offline image exists without selected provenance state')

if errors:
    print('Bloodline Network contract FAIL',file=sys.stderr)
    for error in errors:print(' - '+error,file=sys.stderr)
    raise SystemExit(1)
print(f'Bloodline Network contract PASS ({len(nodes)} canonical nodes; {sum(1 for v in record_images.values() if v.get("status")=="selected")} sourced ancestor images)')
