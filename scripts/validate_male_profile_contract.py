#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]
profile=(ROOT/'profiles/male/index.html').read_text(encoding='utf-8')
submit=(ROOT/'submit.html').read_text(encoding='utf-8')
schema=json.loads((ROOT/'schemas/registry.schema.json').read_text(encoding='utf-8'))
dob=schema['$defs']['doberman']['properties']
health=dob['health']['properties']
identity=dob['identity']['properties']
publication=dob['publication']['properties']
if 'additional_tests' in health: errors.append('schema still exposes additional_tests')
if 'health_summary' in submit: errors.append('owner form still exposes health_summary')
for orphan in ['call_name','microchip_number','breeding_status']:
    if orphan in identity: errors.append('identity schema still exposes orphan field: '+orphan)
for token in ['name="call_name"','name="microchip"','name="breeding_status"']:
    if token in submit: errors.append('owner form still exposes orphan identity control: '+token)
for orphan in ['featured_title','notes_internal']:
    if orphan in publication: errors.append('publication schema still exposes unused field: '+orphan)
for token in ['DM:testView(health.dm','vWD:testView(health.vwd','HD:testView(health.hd','ED:testView(health.ed','DCM clinical','Thyroid:testView(health.thyroid','Eyes:testView(health.eyes']:
    if token not in profile: errors.append('male profile missing health contract token: '+token)
for token in ['Shows:numberOrDash(performance.shows_count)','Titles:array(performance.titles).length','"Working exams":array(performance.working_exams).length','Sports:array(performance.sports).length']:
    if token not in profile: errors.append('male profile missing performance contract token: '+token)
for token in ['lifeStage,lifeStatus,lifeSpan:lifespan||"—"','studServiceStatus,profileId:recordId','lifeStage:"Life stage",lifeStatus:"Life status",lifeSpan:"Life span"','studServiceStatus:"Stud service status"','id="lifeStatusBadge"','const isDeceased=lifecycleState==="deceased"','lifecycleState==="living"?""']:
    if token not in profile: errors.append('male profile missing Details contract token: '+token)
# V27 replaced owner-entered aggregate breeding counters with graph-derived connections.
for token in ['"Notable progeny": named.length?named.join(" · "):"—"','"Connected descendants":connected.length','"Connected litters":array(reproduction.litter_ids).length','"Source":connected.length?"Connected":"Owner entry"']:
    if token not in profile: errors.append('male profile missing connected-descendants contract token: '+token)
if 'name="stud_service_status"' not in submit: errors.append('owner form is missing Stud service status in About')
if 'name="breeding_availability"' in submit: errors.append('owner form still exposes legacy breeding_availability control')
if schema.get('properties',{}).get('schema_version',{}).get('const') != '1.1.0': errors.append('canonical schema is not v1.1.0')
if set(identity.get('life_stage',{}).get('enum',[])) != {'puppy','junior','adult','veteran','unknown'}: errors.append('life_stage enum is incorrect')
if set(identity.get('life_status',{}).get('enum',[])) != {'living','deceased','unknown'}: errors.append('life_status enum is incorrect')
if 'Balance:present(structure.balance),Evaluator:' in profile: errors.append('Structure accidentally includes Evaluator card')
if 'profileData.titles.slice(0,2)' in profile or 'hero-credentials' in profile.split('function heroMetadata(){',1)[1].split('function gallery(){',1)[0]: errors.append('hero identity block still renders titles')
for token in ['id="performanceDetails"','performanceDetails:{Shows:array(performance.show_results),Titles:array(performance.titles)','function togglePerformanceListing(card)','data-metric-key="${escapeHTML(k)}"']:
    if token not in profile: errors.append('male performance listing contract missing: '+token)
for token in ['window.DIBloodline.mount','data/pedigree-graph.json','data/bloodline-images.json']:
    if token not in profile: errors.append('male bloodline contract missing: '+token)
if not re.search(r'assets/bloodline-network_v\d+\.css(?:\?[^"\']*)?',profile):
    errors.append('male bloodline contract missing: active Bloodline stylesheet')
if not re.search(r'assets/bloodline-network_v\d+\.js(?:\?[^"\']*)?',profile):
    errors.append('male bloodline contract missing: active Bloodline runtime')
if errors:
    print('Male profile contract FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('Male profile contract PASS')
