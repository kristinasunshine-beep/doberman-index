#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/'profiles'/'male.html').read_text(encoding='utf-8')
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
'hero identity only':'byId("heroMeta").innerHTML=`<span class="hero-identity">${escapeHTML(identity)}</span>`',
'title listing panel':'id="performanceDetails"',
'video support':'.visual-card img,.visual-card video',
'portal navigation':'href="../index.html"',
}
missing=[name for name,token in checks.items() if token not in text]
for forbidden in ['const profileData={\n      name:"Dion Dante"','href="#profile">DOBERMAN INDEX®</a>']:
    if forbidden in text: missing.append('static demo content leaked into production')
if missing:
    print('Male visual master FAIL')
    for x in missing: print('-',x)
    sys.exit(1)
print('Male visual master PASS')
