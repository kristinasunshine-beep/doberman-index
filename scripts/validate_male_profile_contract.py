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
# Live family network uses actual linked records, never owner-entered aggregate counters.
for token in ['function buildRelated(recordId,parentage,reproduction={})','add(parentage.sire_id||currentRecord.sire_id,"Sire",parentage.sire_name);','id="relatedRail"','<span>02B</span><i></i><span>Live family network</span>']:
    if token not in profile: errors.append('male live-family-network contract missing: '+token)
for stale in ['data-desk-tab="lineage"','data-desk-panel="lineage"','id="reproductionRail"','id="impact"','"Recorded litters"','"Recorded offspring"','"Champion offspring"','profileData.reproduction']:
    if stale in profile: errors.append('male profile still exposes retired breeding-counter UI: '+stale)
for retired_field in ['name="litters_count"','name="offspring_count"','name="champion_offspring_count"','name="export_countries"']:
    if retired_field in submit: errors.append('owner form still exposes retired aggregate field: '+retired_field)
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

if 'requestedRecordId && requestedRecordId!=="DI-M-000001"' not in profile: errors.append('Dante must bypass full dynamic hydration')
if 'refreshDanteRelatedFromRegistry()' not in profile: errors.append('Dante fast path missing lightweight live-family refresh')
if profile.find('id="related"') > profile.find('id="bloodline"'): errors.append('male Related Dobermans must appear before Bloodline Network')
if "document.querySelectorAll('[data-work-nav],[data-di-work-layer=\"dog\"]')" not in profile: errors.append('Dante hard Work guard missing')
# Dynamic profile first-paint and long-name contract.
for token in [
    'profile-hydration-pending',
    'function balancedHeroLines(name)',
    'function fitHeroName()',
    'function renderHeroName(name)',
    'renderHeroName(profileData.name);',
    '.hero-title[data-lines="3"]',
    'white-space:nowrap',
    'initializeProfile().then(revealHydratedProfile).catch(error=>failHydratedProfile(requestedRecordId,error))'
]:
    if token not in profile:
        errors.append('male dynamic hero contract missing: '+token)
if '<h1 class="hero-title" id="dogName" aria-label="Dion Dante"><span>Dion</span><span>Dante.</span></h1>' in profile:
    errors.append('male dynamic hero still exposes Dante as static first-paint fallback')
if 'accepted review snapshot remains visible' in profile:
    errors.append('male dynamic profile still falls back to another dog after hydration failure')


for token in [
    'function hydrateMovementObservation()',
    'function hydrateRecordDesk()',
    'function hydratePedigreeDeepDive()',
    'hydrateMovementObservation();',
    'hydrateRecordDesk();',
    'hydratePedigreeDeepDive();',
    'movementObservation:{',
    'recordDesk:{',
    'pedigreeDeep:{'
]:
    if token not in profile:
        errors.append('male profile-derived intelligence contract missing: '+token)

if errors:
    print('Male profile contract FAIL')
    for e in errors: print('-',e)
    sys.exit(1)
print('Male profile contract PASS')
