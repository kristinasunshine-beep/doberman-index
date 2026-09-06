#!/usr/bin/env python3
"""Lock v6.3 accepted copy, puppy identity, movement and lifecycle automation."""
from __future__ import annotations
import importlib.util, json, tempfile
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
errors=[]
about=(ROOT/'about.html').read_text(encoding='utf-8')
for token in ('The Doberman world, connected through one living record.','Structured records. Connected bloodlines.','class="details-link"','>Details<','>Mission<','Not a ranking.','03 / Decide','context for decision-making'):
    if token not in about: errors.append(f'About accepted token missing: {token}')
submit=(ROOT/'submit.html').read_text(encoding='utf-8'); submit_js=(ROOT/'assets/js/submit-v3.js').read_text(encoding='utf-8')
schema=json.loads((ROOT/'schemas/registry.schema.json').read_text(encoding='utf-8'))
if '3–15 seconds' not in submit: errors.append('Submission movement copy must say 3–15 seconds')
if schema['$defs']['doberman']['properties']['media']['properties']['movement_video_seconds'].get('minimum')!=3: errors.append('Schema movement-video minimum must be 3 seconds')
for token in ('MOVEMENT_VIDEO_MIN_SECONDS = 3','MOVEMENT_VIDEO_MAX_SECONDS = 15','validateMovementVideoDuration','dataset.durationSeconds'):
    if token not in submit_js: errors.append(f'Movement duration enforcement missing: {token}')
puppy=json.loads((ROOT/'data/prototypes/puppy-card.json').read_text(encoding='utf-8'))
if not puppy['record_id'].startswith('DI-F-') and not puppy['record_id'].startswith('DI-M-'): errors.append('Puppy prototype must demonstrate permanent sex-coded ID')
if 'DI-P-' in (ROOT/'profiles/puppy.html').read_text(encoding='utf-8'): errors.append('Puppy profile must not imply a DI-P permanent ID prefix')
router=(ROOT/'profile.html').read_text(encoding='utf-8')
for token in ('window.DILifecycle.templateFor','puppy:"./profiles/puppy.html"','female:"./profiles/female.html"','male:"./profiles/male.html"'):
    if token not in router: errors.append(f'Lifecycle router missing: {token}')
if 'if(/^DI-M-' in router: errors.append('Male-prefix shortcut would bypass puppy routing')
workflow=(ROOT/'.github/workflows/build-registry.yml').read_text(encoding='utf-8')
for token in ('cron: "17 3 * * *"','python scripts/apply_lifecycle_policy.py --write','git add data/dobermans data/litters data/registry.json'):
    if token not in workflow: errors.append(f'Daily lifecycle workflow missing: {token}')
# registry/browser automation must preserve explicit manual lifecycle overrides
build=(ROOT/'scripts/build_registry.py').read_text(encoding='utf-8')
lifecycle_js=(ROOT/'assets/js/lifecycle.js').read_text(encoding='utf-8')
portal=(ROOT/'index.html').read_text(encoding='utf-8')
if '"lifecycle_mode": publication.get("lifecycle_mode", "automatic")' not in build:
    errors.append('Registry must expose lifecycle_mode for browser routing')
if 'record.lifecycle_mode||"automatic"' not in lifecycle_js or '==="manual"' not in lifecycle_js:
    errors.append('Browser lifecycle runtime must preserve manual lifecycle overrides')
for token in ('window.DILifecycle.stageFor(record, lifecyclePolicy)','window.DILifecycle.templateFor(record, lifecyclePolicy)'):
    if token not in portal: errors.append(f'Portal must derive current lifecycle at runtime: {token}')
# unit-test age boundaries from the exact production synchronizer
spec=importlib.util.spec_from_file_location('life',ROOT/'scripts/apply_lifecycle_policy.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
policy=json.loads((ROOT/'data/lifecycle-policy.json').read_text(encoding='utf-8'))
dob=date(2026,1,31)
checks=[(date(2026,10,30),'puppy'),(date(2026,10,31),'junior'),(date(2027,7,30),'junior'),(date(2027,7,31),'adult'),(date(2034,1,31),'veteran')]
for today,want in checks:
    got=mod.derived_stage(dob,today,policy)
    if got!=want: errors.append(f'Lifecycle boundary {today}: expected {want}, got {got}')
# End-to-end file mutation contract: permanent ID remains; puppy availability is pruned, history remains.
with tempfile.TemporaryDirectory() as temp_dir:
    temp=Path(temp_dir); (temp/'data/dobermans').mkdir(parents=True); (temp/'data/litters').mkdir(parents=True)
    pup_path=temp/'data/dobermans/DI-F-009999.json'
    pup={'schema_version':'1.1.0','entity_type':'doberman','record_id':'DI-F-009999','status':'published','doberman':{'identity':{'sex':'female','life_status':'living','life_stage':'puppy','date_of_birth':'2026-01-31'},'publication':{'profile_template':'puppy','lifecycle_mode':'automatic'}}}
    pup_path.write_text(json.dumps(pup),encoding='utf-8')
    changed,stage=mod.update_doberman(pup_path,policy,date(2026,10,31),True)
    updated=json.loads(pup_path.read_text(encoding='utf-8'))
    if not changed or stage!='junior': errors.append('Puppy must transition to junior on 9-month birthday')
    if updated.get('record_id')!='DI-F-009999': errors.append('Lifecycle transition must never change permanent DI ID')
    if updated['doberman']['publication'].get('profile_template')!='female': errors.append('Female puppy must switch to female visual card at 9 months')
    litter_path=temp/'data/litters/DI-L-009999.json'
    litter={'record_id':'DI-L-009999','entity_type':'litter','litter':{'puppy_ids':['DI-F-009999'],'available_puppy_ids':['DI-F-009999']}}
    litter_path.write_text(json.dumps(litter),encoding='utf-8')
    mod.prune_litters(temp,set(),True)
    litter2=json.loads(litter_path.read_text(encoding='utf-8'))['litter']
    if litter2.get('available_puppy_ids')!=[]: errors.append('Aged-out puppy must leave litter available_puppy_ids')
    if litter2.get('puppy_ids')!=['DI-F-009999']: errors.append('Historical litter puppy_ids must never be pruned')
if errors:
    print('v6.3 contract FAIL')
    for e in errors: print('-',e)
    raise SystemExit(1)
print('v6.3 contract PASS')
