#!/usr/bin/env python3
from pathlib import Path
import re,sys
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'profiles'/'male'/'index.html').read_text(encoding='utf-8')
checks={
'raised Details action':'.hero-dossier .dossier-bold{',
'raised Details top':'top:calc(91svh - var(--hero-card-top) + 8px)',
'larger section descriptor':'.section-index span:last-child{',
'custom rail controller':'function installHorizontalRailScrollbars()',
'rail indicator':'.rail-scrollbar-indicator{',
'rail arrows':'.rail-scrollbar-arrow{',
'DCM dropdown':'class="dcm-dropdown" id="dcmDropdown"',
'structure rail':'id="structureRail"',
'temperament rail':'id="temperamentRail"',
'performance rail':'id="performanceRail"',
'related rail':'id="relatedRail"',
'live loader':'async function loadProfile()',
'live initializer':'async function initializeProfile()',
'hero identity only':'byId("heroMeta").innerHTML=`<span class="hero-identity">${escapeHTML(identity)}</span>`',
'title listing panel':'id="performanceDetails"',
'video support':'.visual-card img,.visual-card video',
'portal navigation':'href="../../index.html"',
'correct repository root':'const repoRoot=new URL("../../",document.baseURI);',
'pedigree intelligence':'id="pedigree-intelligence"',
'breeding lens':'id="breeding-lens"',
'bloodline mount':'window.DIBloodline.mount',
'offline accepted snapshot':'profileData={performanceDetails:',
'offline bloodline graph':'const offlineBloodlineNodes=[',
}
missing=[name for name,token in checks.items() if token not in text]
if not re.search(r'assets/bloodline-network_v\d+\.css(?:\?[^"\']*)?',text):
    missing.append('active bloodline stylesheet')
if not re.search(r'assets/bloodline-network_v\d+\.js(?:\?[^"\']*)?',text):
    missing.append('active bloodline runtime')
if 'href="#profile">DOBERMAN INDEX®</a>' in text:
    missing.append('legacy self-link still replaces portal navigation')
if missing:
    print('Male visual master FAIL')
    for x in missing: print('-',x)
    sys.exit(1)
print('Male visual master PASS')
