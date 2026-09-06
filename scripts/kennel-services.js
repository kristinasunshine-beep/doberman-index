/* Kennel service projections. Canonical kennel, Doberman and litter records remain the source. */
(function (root) {
  const list = value => Array.isArray(value) ? value : [];
  const object = value => value && typeof value === 'object' && !Array.isArray(value) ? value : {};
  const hasValue = value => value !== null && value !== undefined && value !== '' && (!Array.isArray(value) || value.length > 0);
  const countPresent = value => Object.values(object(value)).filter(hasValue).length;
  function countEvidence(value) {
    if (Array.isArray(value)) return value.reduce((total, item) => total + countEvidence(item), 0);
    if (!value || typeof value !== 'object') return 0;
    return Object.entries(value).reduce((total, [key, item]) => {
      if (key === 'evidence_file' || key === 'evidence_files') return total + (Array.isArray(item) ? item.filter(Boolean).length : item ? 1 : 0);
      return total + countEvidence(item);
    }, 0);
  }

  function deriveServiceInput(kennelRecord, dogRecords = [], litterRecords = []) {
    const kennel = object(kennelRecord?.kennel);
    const dogs = list(dogRecords).filter(record => record?.status === 'published' && record?.doberman).map(record => record.doberman);
    const litters = list(litterRecords).filter(record => record?.status === 'published');
    const facts = {
      kennel_fields: ['name', 'registration_prefix', 'registration_authority', 'country', 'location', 'founded_year', 'owner_or_founder', 'focus', 'bloodline_tags'].filter(key => hasValue(kennel[key])).length,
      indexed_dobermans: dogs.length,
      litter_records: litters.length,
      pedigree_links: dogs.reduce((total, dog) => total + ['sire_id', 'sire_name', 'dam_id', 'dam_name', 'litter_id'].filter(key => hasValue(dog.parentage?.[key])).length, 0),
      health_results: dogs.reduce((total, dog) => {
        const health = object(dog.health);
        return total + ['hd', 'ed', 'dm', 'vwd', 'thyroid', 'eyes', 'dcm_clinical'].filter(key => hasValue(health[key]?.result ?? health[key]?.status)).length + Object.values(object(health.dcm_markers)).filter(item => hasValue(item?.result)).length;
      }, 0),
      temperament_attributes: dogs.reduce((total, dog) => total + countPresent(dog.temperament), 0),
      structure_attributes: dogs.reduce((total, dog) => total + countPresent(dog.structure), 0),
      performance_records: dogs.reduce((total, dog) => total + list(dog.performance?.titles).length + list(dog.performance?.working_exams).length + list(dog.performance?.sports).length, 0),
      evidence_files: list(dogRecords).reduce((total, record) => total + countEvidence(record?.doberman), 0)
    };
    const evidenceCategories = ['pedigree_links', 'health_results', 'temperament_attributes', 'structure_attributes', 'performance_records'].filter(key => facts[key] > 0).length;
    const gaps = [];
    if (!kennel.focus?.length) gaps.push('breeding-program priorities');
    if (facts.indexed_dobermans < 2) gaps.push('a representative indexed population');
    if (!facts.pedigree_links) gaps.push('structured pedigree links');
    if (!facts.health_results) gaps.push('documented health results');
    if (!facts.temperament_attributes) gaps.push('structured temperament records');
    if (!facts.structure_attributes) gaps.push('structured conformation records');
    if (!facts.performance_records) gaps.push('performance evidence');
    if (!facts.litter_records) gaps.push('published litter relationships');
    return {
      kennel_id: kennelRecord?.record_id || null,
      kennel_name: kennel.name || kennelRecord?.record_id || 'Indexed kennel',
      record_status: kennelRecord?.status || 'unknown',
      facts,
      gaps,
      analysis_sufficient: facts.indexed_dobermans >= 2 && evidenceCategories >= 3,
      trajectory_supported: facts.litter_records > 0 && facts.indexed_dobermans >= 2
    };
  }

  function lineageKeys(records) {
    return new Set(list(records).flatMap(record => {
      const parentage = object(record?.doberman?.parentage);
      return [parentage.sire_id, parentage.sire_name, parentage.dam_id, parentage.dam_name].filter(Boolean).map(value => String(value).trim().toLowerCase());
    }));
  }

  function buildComparisonInput(currentBundle, secondBundle) {
    const current = deriveServiceInput(currentBundle.kennelRecord, currentBundle.dogRecords, currentBundle.litterRecords);
    const second = deriveServiceInput(secondBundle.kennelRecord, secondBundle.dogRecords, secondBundle.litterRecords);
    const currentLineage = lineageKeys(currentBundle.dogRecords);
    const secondLineage = lineageKeys(secondBundle.dogRecords);
    const sharedLineage = [...currentLineage].filter(value => secondLineage.has(value)).length;
    const comparableEvidenceAreas = ['health_results', 'temperament_attributes', 'structure_attributes', 'performance_records'].filter(key => current.facts[key] > 0 && second.facts[key] > 0).length;
    return {
      current,
      second,
      shared_lineage_references: sharedLineage,
      comparable_evidence_areas: comparableEvidenceAreas,
      sufficient: current.analysis_sufficient && second.analysis_sufficient && comparableEvidenceAreas >= 2,
      gaps: [...new Set([...current.gaps.map(value => `${current.kennel_name}: ${value}`), ...second.gaps.map(value => `${second.kennel_name}: ${value}`)])]
    };
  }

  function findKennelCandidates(registry, currentKennelId) {
    return list(registry?.records)
      .filter(item => item?.entity_type === 'kennel' && item?.status === 'published' && item?.record_id !== currentKennelId)
      .map(item => ({
        id: item.record_id,
        name: item.kennel_name || item.name || item.registered_name || item.record_id,
        path: item.path || `data/kennels/${item.record_id}.json`
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  const dataUrl = path => path.startsWith('../') ? path : `../${path.replace(/^\/+/, '')}`;

  async function loadKennelBundle(candidate, registry, fetchJson) {
    const registryRecords = list(registry?.records);
    const kennelRecord = await fetchJson(dataUrl(candidate.path || `data/kennels/${candidate.id}.json`));
    const kennel = object(kennelRecord.kennel);
    const dogIds = new Set([
      ...list(kennel.dog_ids),
      ...registryRecords.filter(item => item?.entity_type === 'doberman' && item?.kennel_id === kennelRecord.record_id).map(item => item.record_id)
    ]);
    const dogRecords = (await Promise.all([...dogIds].map(async id => {
      const summary = registryRecords.find(item => item?.record_id === id);
      try { return await fetchJson(dataUrl(summary?.path || `data/dobermans/${id}.json`)); } catch { return null; }
    }))).filter(record => record?.status === 'published');
    const litterIds = new Set([
      ...list(kennel.litter_ids),
      ...dogRecords.flatMap(record => list(record?.doberman?.reproduction?.litter_ids)),
      ...registryRecords.filter(item => item?.entity_type === 'litter' && item?.kennel_id === kennelRecord.record_id).map(item => item.record_id)
    ]);
    const litterRecords = (await Promise.all([...litterIds].map(async id => {
      const summary = registryRecords.find(item => item?.record_id === id);
      try { return await fetchJson(dataUrl(summary?.path || `data/litters/${id}.json`)); } catch { return null; }
    }))).filter(record => record?.status === 'published');
    return { kennelRecord, dogRecords, litterRecords };
  }

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function safeCheckoutUrl(value) {
    try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; } catch { return null; }
  }

  function checkoutReady(service) {
    const checkout = object(service.checkout);
    return Boolean(checkout.product_id && checkout.variant_id && safeCheckoutUrl(checkout.checkout_url));
  }

  async function mount({ fetchJson }) {
    const module = document.querySelector('[data-kennel-services]');
    if (!module) return;
    const configuration = await fetchJson('../data/kennel-services.json?v=20260905-4');
    const services = list(configuration.services);
    const selector = module.querySelector('[data-service-selector]');
    const cards = services.map(service => {
        const checkoutUrl = checkoutReady(service) ? safeCheckoutUrl(service.checkout.checkout_url) : null;
        const button = node(checkoutUrl ? 'a' : 'button', 'service-option');
        if (checkoutUrl) button.href = checkoutUrl;
        else {
          button.type = 'button';
          button.setAttribute('aria-disabled', 'true');
        }
        button.dataset.serviceId = service.id;
        const number = node('span', 'service-option-number', service.number);
        const copy = node('span', 'service-option-copy');
        copy.append(node('strong', '', service.name));
        const description = node('span', 'service-option-description', service.descriptor);
        const pricing = node('span', 'service-option-pricing');
        pricing.append(node('small', 'service-fee-label', 'One-time fee'), node('span', 'service-option-price', `€${service.price_eur}`));
        button.append(number, copy, description, pricing);
        return button;
      });
    const ghost = node('span', 'services-ghost', 'TOOLS');
    ghost.setAttribute('aria-hidden', 'true');
    selector.replaceChildren(...cards, ghost);
  }

  function showLoadError() {
    const selector = document.querySelector('[data-service-selector]');
    if (selector) selector.setAttribute('data-config-status', 'unavailable');
  }

  root.KennelServices = { deriveServiceInput, buildComparisonInput, findKennelCandidates, loadKennelBundle, mount, showLoadError };
})(globalThis);
