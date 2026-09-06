/* Public kennel projections. Read-only: canonical records remain the source. */
(function (root) {
  'use strict';
  const list = value => Array.isArray(value) ? value.filter(Boolean) : [];
  const present = value => value !== null && value !== undefined && value !== '';
  const text = value => Array.isArray(value) ? value.map(text).join(' · ') : typeof value === 'object' && value ? String(value.name || value.title || value.result || value.label || 'Not provided') : present(value) ? String(value) : 'Not provided';
  const displayAcronyms = new Set(['BH','BH-VT','DCM','DM','DNA','ED','FCI','HD','IGP','IPO','VWD','ZTP']);
  const canonicalDisplayTerms = new Map([['DI','Di'],['VWD','vWD'],['HIPS','HIPS'],['ELBOWS','ELBOWS']]);
  const displayMinorWords = new Set(['and','at','by','for','from','in','of','the','to','with']);
  function displayCase(value) {
    const source = text(value);
    if (/^DI-[A-Z]-\d+$/i.test(source)) return source.toLocaleUpperCase();
    if (/^(?:HD|ED)(?:[-\s][A-Z0-9]+)?$/i.test(source)) return source.toLocaleUpperCase();
    const letters = [...source].filter(character => /\p{L}/u.test(character)).join('');
    let rendered = source;
    if (letters && letters === letters.toLocaleUpperCase()) {
      let wordIndex = 0;
      rendered = source.toLocaleLowerCase().replace(/\p{L}[\p{L}\p{M}'’.-]*/gu, word => {
        const upper = word.toLocaleUpperCase();
        const index = wordIndex++;
        if (displayAcronyms.has(upper)) return canonicalDisplayTerms.get(upper) || upper;
        if (index > 0 && displayMinorWords.has(word)) return word;
        return word.charAt(0).toLocaleUpperCase() + word.slice(1);
      });
    }
    return rendered.replace(/\p{L}+/gu, word => canonicalDisplayTerms.get(word.toLocaleUpperCase()) || word);
  }
  function displayDogName(value) {
    const rendered = displayCase(value);
    if (/^DI-[A-Z]-\d+$/i.test(rendered)) return rendered.toLocaleUpperCase();
    return rendered.replace(/\bDI\b/gu,'Di');
  }
  const row = (label, value, href) => ({ label, value: text(value), href });
  const profileHref = (record, anchor = '', view = '') => `${record.doberman?.identity?.sex === 'female' ? 'female' : 'male'}.html?id=${encodeURIComponent(record.record_id)}${view ? '&view=' + encodeURIComponent(view) : ''}${anchor ? '#' + anchor : ''}`;
  const champion = record => list(record.doberman?.performance?.titles).some(title => /champion|\bch\b/i.test(text(title)));
  function publicRecords(kennelRecord, records) {
    const explicit = new Set(list(kennelRecord.kennel?.dog_ids));
    return [...new Map(records.filter(record => record?.entity_type === 'doberman' && record.status === 'published' &&
      (record.doberman?.identity?.kennel_id === kennelRecord.record_id || (!record.doberman?.identity?.kennel_id && explicit.has(record.record_id))))
      .map(record => [record.record_id, {record_id:record.record_id,entity_type:record.entity_type,status:record.status,doberman:record.doberman}])).values()];
  }
  function healthRows(health, keys) {
    return keys.flatMap(([key, label]) => {
      const item = health[key];
      if (!item || !present(item.result ?? item.status)) return [];
      const rows = [row(label, item.result ?? item.status)];
      [['evaluation_method','Method'],['evaluation_date','Date'],['date','Date'],['lab','Laboratory'],['veterinarian_or_clinic','Clinic'],['report_number','Report']].forEach(([field, title]) => {
        if (present(item[field])) rows.push(row(`${label} / ${title}`, item[field]));
      });
      if (item.evidence_file) rows.push(row(`${label} / Document`, 'Open attachment', item.evidence_file));
      return rows;
    });
  }
  function evidenceRows(value, prefix = '') {
    if (!value || typeof value !== 'object') return [];
    return Object.entries(value).flatMap(([key, item]) => {
      const label = [prefix, key.replaceAll('_',' ')].filter(Boolean).join(' / ');
      if (key === 'evidence_file') return item ? [row(label, 'Open attachment', item)] : [];
      if (key === 'evidence_files') return list(item).map((path,index) => row(`${label} ${index + 1}`, 'Open attachment', typeof path === 'string' ? path : path.path));
      return evidenceRows(item, label);
    });
  }
  function buildModel(kennelRecord, records, litters = []) {
    const kennel = kennelRecord.kennel || {};
    const dogs = publicRecords(kennelRecord, records);
    const publishedLitters = litters.filter(item => item?.status === 'published');
    const group = (record, rows, anchor) => ({ name: displayDogName(record.doberman?.identity?.registered_name || record.record_id), id: record.record_id, href: profileHref(record, anchor), rows: rows.length ? rows : [row('Record', 'No results submitted for this category.')] });
    const each = (fn, anchor) => dogs.map(record => group(record, fn(record.doberman || {}, record), anchor));
    const owner = (rows,source='Kennel questionnaire') => ({name:kennel.name || 'Kennel', id:kennelRecord.record_id, source, rows});
    const panels = {
      focus: {title:'Breeding focus', groups:[owner([row('Program priorities', list(kennel.focus).length ? kennel.focus : null)]), ...each(dog => [
        ...Object.entries(dog.structure || {}).filter(([key]) => ['type','head','body','angulation','movement','balance'].includes(key)).map(([key,value]) => row(key,value)),
        ...Object.entries(dog.temperament || {}).filter(([key]) => ['stability','drive','social_behaviour','defense','confidence'].includes(key)).map(([key,value]) => row(key.replaceAll('_',' '),value))
      ], 'structure')]},
      bloodline: {title:'Bloodline view', groups:[owner([row('Bloodline tags', list(kennel.bloodline_tags).length ? kennel.bloodline_tags : null)]), ...each(dog => {
        const p = dog.parentage || {};
        return [row('Sire',displayDogName(p.sire_name || p.sire_id)),row('Dam',displayDogName(p.dam_name || p.dam_id)),...list(p.pedigree_nodes).map(node => row(node.role || 'Ancestor',displayDogName(node.name || node.registered_name)))];
      }, 'bloodline')]},
      links: {title:'Record links', groups:[...each((dog,record) => [row('Doberman record',record.record_id),row('Kennel record',kennelRecord.record_id),row('Sire',displayDogName(dog.parentage?.sire_id || dog.parentage?.sire_name)),row('Dam',displayDogName(dog.parentage?.dam_id || dog.parentage?.dam_name)),row('Birth litter',dog.parentage?.litter_id),row('Linked litter IDs',list(dog.reproduction?.litter_ids).length ? dog.reproduction.litter_ids : null)], 'related'), ...publishedLitters.map(item => ({name:item.litter?.name || item.record_id,id:item.record_id,rows:[row('Sire',displayDogName(item.litter?.sire_id)),row('Dam',displayDogName(item.litter?.dam_id)),row('Puppy records',item.litter?.puppy_ids)]}))]},
      totals: {title:'Derived totals', groups:[owner([row('Published Dobermans',dogs.length),row('Published litter records',publishedLitters.length)],'Connected records'),...each(dog => [row('Titles',list(dog.performance?.titles).length),row('Working exams',list(dog.performance?.working_exams).length),row('Sports',list(dog.performance?.sports).length),row('Reported litters',dog.reproduction?.litters_count),row('Reported offspring',dog.reproduction?.offspring_count)],'impact')]},
      cardiac: {title:'Cardiac',groups:each(dog => healthRows(dog.health || {},[['dcm_clinical','Clinical DCM']]),'health')},
      genetics: {title:'Genetics',groups:each(dog => healthRows(dog.health?.dcm_markers || {},['dcm_1','dcm_2','dcm_3','dcm_4','dcm_5'].map((key,i)=>[key,`DCM ${i+1}`])),'health')},
      orthopedic: {title:'Orthopedic',groups:each(dog => healthRows(dog.health || {},[['hd','HD'],['ed','ED']]),'health')},
      clinical: {title:'Additional tests',groups:each(dog => healthRows(dog.health || {},[['dm','DM'],['vwd','vWD'],['thyroid','Thyroid'],['eyes','Eyes']]),'health')},
      evidence: {title:'Evidence',groups:each(dog => [...evidenceRows(dog.health,'Health'),...evidenceRows(dog.performance,'Performance'),...evidenceRows(dog.structure,'Structure'),...evidenceRows(dog.temperament,'Temperament')],'health')},
      champions: {title:'Indexed champions',groups:dogs.filter(champion).map(record=>group(record,list(record.doberman.performance.titles).map(title=>row('Title',title)),'performance'))},
      titles: {title:'Show titles',groups:each(dog=>list(dog.performance?.titles).map(title=>row('Title',title)),'performance')},
      working: {title:'Working results',groups:each(dog=>[...list(dog.performance?.working_exams).map(value=>row('Working exam',value)),...list(dog.performance?.sports).map(value=>row('Sport',value))],'performance')},
      reach: {title:'Countries represented',groups:each(dog=>[row('Profile country',dog.identity?.country),row('Reported export countries',list(dog.reproduction?.export_countries).length ? dog.reproduction.export_countries : null)],'impact')}
    };
    return {dogs,panels,champions:dogs.filter(champion).length};
  }
  function safeHref(value) {
    if (typeof value !== 'string' || /[\\\x00-\x1f]/.test(value)) return null;
    if (/^(male|female)\.html\?id=DI-[MFP]-\d+(?:&view=gallery)?(?:#[a-z-]+)?$/.test(value)) return value;
    if (/^media\/[a-zA-Z0-9_./-]+$/.test(value) && !value.includes('..')) return '../' + value;
    return null;
  }
  function installDetails(model) {
    const mappings = {kennelProgramRail:['focus','bloodline','links','totals'],kennelHealthRail:['cardiac','genetics','orthopedic','clinical','evidence'],kennelPerformanceRail:['champions','titles','working','reach']};
    for (const [railId,keys] of Object.entries(mappings)) {
      const rail = document.getElementById(railId);
      const panel = document.createElement('div');
      panel.id = railId + 'Details'; panel.className = 'performance-detail'; panel.hidden = true; panel.setAttribute('aria-live','polite');
      rail.parentElement.append(panel);
      let activeCard = null;
      const closePanel = (restoreFocus = false) => {
        const returnTarget = activeCard;
        [...rail.children].forEach(item => {item.setAttribute('aria-expanded','false');item.classList.remove('selected');});
        panel.hidden = true;
        activeCard = null;
        if (restoreFocus) returnTarget?.focus();
      };
      panel.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();closePanel(true);}});
      [...rail.children].forEach((card,index) => {
        const key = keys[index];
        card.setAttribute('role','button'); card.tabIndex = 0; card.dataset.detailKey = key;
        card.setAttribute('aria-controls',panel.id); card.setAttribute('aria-expanded','false');
        const toggle = () => {
          const opening = panel.hidden || activeCard !== card;
          if (!opening) {closePanel(true);return;}
          closePanel(false);
          panel.hidden = false;
          activeCard = card;
          card.setAttribute('aria-expanded','true'); card.classList.add('selected');
          const content = model.panels[key];
          const head = document.createElement('div'); head.className = 'performance-detail-head';
          const title = document.createElement('h3'); title.textContent = content.title + '.';
          const close = document.createElement('button');close.type='button';close.className='performance-detail-close';close.textContent='Close';close.setAttribute('aria-label',`Close ${content.title} details`);close.addEventListener('click',()=>closePanel(true));
          head.append(title,close);
          panel.replaceChildren(head);
          if (!content.groups.length) {const empty=document.createElement('p');empty.textContent='No published records available for this category.';panel.append(empty);}
          content.groups.forEach(group => {
            const section = document.createElement('section'); section.className='detail-record';
            const name=document.createElement('h4'); const target=safeHref(group.href);
            section.classList.add(target?'is-dog':'is-kennel');
            const displayName=displayCase(group.name);name.title=displayName;
            if(target){const link=document.createElement('a');link.href=target;link.textContent=displayName;name.append(link);}else name.textContent=displayName;
            const source=document.createElement('small');source.textContent=[group.id,group.source || 'Published profile'].filter(Boolean).join(' · ');
            const rows=document.createElement('dl');rows.className='performance-title-list';
            group.rows.forEach(item=>{const line=document.createElement('div');const label=document.createElement('dt');const displayLabel=displayCase(item.label);label.textContent=displayLabel;label.title=displayLabel;const value=document.createElement('dd');const href=safeHref(item.href);const displayValue=displayCase(item.value);value.title=displayValue;if(href){const link=document.createElement('a');link.className='attachment-link';link.href=href;link.textContent=displayValue;value.append(link);}else value.textContent=displayValue;line.append(label,value);rows.append(line);});
            section.append(name,source,rows);panel.append(section);
          });
          requestAnimationFrame(()=>{
            const behavior=root.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches?'auto':'smooth';
            panel.scrollIntoView({behavior,block:'start'});
          });
        };
        card.addEventListener('click',toggle);
        card.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();toggle();}else if(event.key==='Escape'&&activeCard){event.preventDefault();closePanel(true);}});
      });
    }
  }
  function renderArchive(records) {
    const rail=document.getElementById('kennelArchiveRail'); rail.replaceChildren();
    records.forEach(record=>{
      const dog=record.doberman;const link=document.createElement('a');link.className='archive-profile-card';link.href=profileHref(record,'gallery-movement','gallery');
      const media=document.createElement('div');media.className='archive-profile-image';
      const fullDog=[dog.media?.hero,dog.media?.profile,dog.media?.stack].map(value=>typeof value==='string'?value:value?.path).find(value=>safeHref(value));
      if(fullDog){const img=document.createElement('img');img.src=safeHref(fullDog);img.alt=dog.identity.registered_name;img.loading='lazy';media.append(img);}else{media.textContent='Image not provided';}
      const copy=document.createElement('span');copy.className='archive-profile-copy';
      const id=document.createElement('small');id.textContent=record.record_id;
      const name=document.createElement('strong');name.textContent=displayCase(dog.identity.registered_name);
      const meta=document.createElement('span');meta.textContent=[dog.identity.kennel_name,dog.identity.country].filter(Boolean).join(' · ');
      const action=document.createElement('em');action.textContent='Gallery & movement';
      copy.append(id,name,meta,action);link.append(media,copy);rail.append(link);
    });
    if(!records.length){const empty=document.createElement('p');empty.textContent='No published Doberman profiles linked.';rail.append(empty);}
  }
  function alignHeroLogo() {
    const frame=document.querySelector('.kennel-logo-frame'),image=frame?.querySelector('img'),word=document.querySelector('[data-kennel-name-line="rest"]');
    if(!image||!word)return;
    const update=()=>{const box=frame.getBoundingClientRect(),title=word.getBoundingClientRect(),height=image.getBoundingClientRect().height;const inset=height/2+12;const center=Math.max(inset,Math.min(box.height-inset,title.top+title.height/2-box.top));frame.style.setProperty('--logo-center',`${center}px`);};
    image.addEventListener('load',update);window.addEventListener('resize',update);document.fonts?.ready.then(update);update();
  }
  root.KennelNetwork={buildModel,publicRecords,profileHref,safeHref,displayCase,displayDogName,installDetails,renderArchive,alignHeroLogo};
})(globalThis);
