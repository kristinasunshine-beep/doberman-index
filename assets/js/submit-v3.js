(function () {
  "use strict";

  const form = document.getElementById("submission-form");
  const steps = Array.from(document.querySelectorAll(".form-step"));
  const progressItems = Array.from(document.querySelectorAll(".progress li"));
  const progressFill = document.getElementById("progress-fill");
  const nextButton = document.getElementById("next-button");
  const backButton = document.getElementById("back-button");
  const prepareButton = document.getElementById("prepare-button");
  const returnReviewButton = document.getElementById("return-review-button");
  const errorBox = document.getElementById("form-error");
  const review = document.getElementById("review-summary");
  const saveStatus = document.getElementById("save-status");
  const successPanel = document.getElementById("success-panel");
  const storageKey = "doberman-index-owner-submission-v2-canonical";
  const IMAGE_MAX_BYTES = 20 * 1024 * 1024;
  const PDF_MAX_BYTES = 25 * 1024 * 1024;
  const VIDEO_MAX_BYTES = 180 * 1024 * 1024;
  const PACKAGE_MAX_BYTES = 250 * 1024 * 1024;
  let currentStep = 0;
  let maxStepReached = 0;
  let saveTimer;

  const fileFields = [
    { name: "pedigree_file", role: "pedigree", base: "pedigree" },
    { name: "health_evidence", role: "evidence", base: "health-evidence", multiple: true },
    { name: "mortality_evidence", role: "evidence_mortality", base: "mortality-evidence" },
    { name: "hero_photo", role: "hero", base: "main-photo" },
    { name: "head_photo", role: "head", base: "head-photo" },
    { name: "profile_photo", role: "profile", base: "side-profile" },
    { name: "stack_photo", role: "stack", base: "standing-pose" },
    { name: "movement_photo", role: "movement", base: "movement-photo" },
    { name: "movement_video", role: "movement_video", base: "movement-video" },
  ];

  function value(name) {
    const selected = form.querySelector(`[name="${name}"]:checked`);
    if (selected) return selected.value;
    const field = form.elements.namedItem(name);
    return field && typeof field.value === "string" ? field.value.trim() : "";
  }

  function checkedValues(name) {
    return Array.from(form.querySelectorAll(`[name="${name}"]:checked`)).map((field) => field.value);
  }

  function structureValues(name) {
    return checkedValues(name).slice(0, 2);
  }

  function numberValue(name) {
    const raw = value(name);
    return raw === "" || Number.isNaN(Number(raw)) ? null : Number(raw);
  }

  function listValue(name) {
    return value(name).split(/[\n,]+/).map((item) => item.trim()).filter(Boolean);
  }

  function safeExtension(file) {
    const match = file.name.toLowerCase().match(/\.([a-z0-9]{1,8})$/);
    if (match) return `.${match[1]}`;
    const subtype = (file.type.split("/")[1] || "bin").replace(/[^a-z0-9]/g, "");
    return `.${subtype || "bin"}`;
  }

  function safeSlug(text) {
    return (text || "DOBERMAN")
      .normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "")
      .toUpperCase().slice(0, 52) || "DOBERMAN";
  }

  function makeTest(result) {
    return { result: result || null, lab: null, date: null, report_number: null, evidence_file: null };
  }

  function evidenceBlock(source = "owner_declaration") {
    return { source_type: source, issuer: null, date: null, reference: null, file: null };
  }

  function totalFileSize() {
    return fileFields.reduce((sum, config) => {
      const input = form.elements.namedItem(config.name);
      return sum + Array.from(input.files || []).reduce((fileSum, file) => fileSum + file.size, 0);
    }, 0);
  }

  function setError(message, field) {
    errorBox.textContent = message;
    errorBox.hidden = false;
    if (field) {
      field.setAttribute("aria-invalid", "true");
      field.focus({ preventScroll: true });
      field.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function clearError() {
    errorBox.hidden = true;
    errorBox.textContent = "";
    form.querySelectorAll('[aria-invalid="true"]').forEach((field) => field.removeAttribute("aria-invalid"));
  }

  function fileKind(file) {
    const name = file.name.toLowerCase();
    if (file.type.startsWith("image/") || /\.(jpe?g|png|webp)$/.test(name)) return "image";
    if (file.type === "application/pdf" || name.endsWith(".pdf")) return "pdf";
    if (["video/mp4", "video/quicktime"].includes(file.type) || /\.(mp4|mov)$/.test(name)) return "video";
    return "unsupported";
  }

  function validateFileField(field) {
    for (const file of Array.from(field.files || [])) {
      const kind = fileKind(file);
      if (kind === "unsupported") {
        setError(`${file.name} uses an unsupported format. Choose JPG, PNG, WebP, PDF, MP4 or MOV.`, field);
        return false;
      }
      if (kind === "image" && file.size > IMAGE_MAX_BYTES) {
        setError(`${file.name} is too large. Keep each image below 20 MB.`, field);
        return false;
      }
      if (kind === "pdf" && file.size > PDF_MAX_BYTES) {
        setError(`${file.name} is too large. Keep each PDF below 25 MB.`, field);
        return false;
      }
      if (kind === "video" && file.size > VIDEO_MAX_BYTES) {
        setError(`${file.name} is too large. Keep the movement video below 180 MB.`, field);
        return false;
      }
    }
    return true;
  }

  function validateStep(index) {
    clearError();
    const fields = Array.from(steps[index].querySelectorAll("input, select, textarea"));
    for (const field of fields) {
      if (!field.checkValidity()) {
        const label = field.closest("label, fieldset")?.querySelector("span, legend")?.textContent.replace("Required", "").trim();
        setError(label ? `Please check: ${label}.` : "Please complete the highlighted field.", field);
        return false;
      }
      if (field.type === "file" && !validateFileField(field)) return false;
    }
    if (index === 3) {
      const totalBytes = totalFileSize();
      const megabytes = totalBytes / (1024 * 1024);
      if (totalBytes > PACKAGE_MAX_BYTES) {
        setError(`The selected files are ${Math.ceil(megabytes)} MB. Please keep the total below 250 MB.`);
        return false;
      }
    }
    return true;
  }

  function showStep(index, { preserveReached = false } = {}) {
    currentStep = Math.max(0, Math.min(steps.length - 1, index));
    if (!preserveReached) maxStepReached = Math.max(maxStepReached, currentStep);
    steps.forEach((step, stepIndex) => {
      const active = stepIndex === currentStep;
      step.hidden = !active;
      step.classList.toggle("is-active", active);
    });
    progressItems.forEach((item, itemIndex) => {
      item.classList.toggle("is-active", itemIndex === currentStep);
      item.classList.toggle("is-complete", itemIndex < maxStepReached);
      item.classList.toggle("is-available", itemIndex <= maxStepReached);
      const button = item.querySelector("button");
      if (button) button.setAttribute("aria-disabled", itemIndex > maxStepReached ? "true" : "false");
    });
    progressFill.style.width = `${(maxStepReached / (steps.length - 1)) * 100}%`;
    backButton.hidden = currentStep === 0;
    nextButton.hidden = currentStep === steps.length - 1;
    prepareButton.hidden = currentStep !== steps.length - 1;
    returnReviewButton.hidden = !(maxStepReached === steps.length - 1 && currentStep !== steps.length - 1);
    if (currentStep === steps.length - 1) buildReview();
    clearError();
    document.querySelector(".wizard-card").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function escapeHtml(text) {
    const node = document.createElement("div");
    node.textContent = String(text);
    return node.innerHTML;
  }

  function buildReview() {
    const selectedFiles = fileFields.reduce((count, config) => count + form.elements.namedItem(config.name).files.length, 0);
    const healthFields = ["dm", "vwd", "hd", "ed", "thyroid", "eyes", "dcm1", "dcm2", "dcm3", "dcm4", "dcm5", "dcm_clinical_status"];
    const healthResults = healthFields.filter((name) => value(name)).length;
    const hasPedigree = Boolean(value("sire_name") || value("dam_name") || form.elements.namedItem("pedigree_file").files.length);
    const achievementCount = listValue("titles").length + listValue("working_exams").length + listValue("sports").length;
    const structureFields = ["structure_type","structure_head","structure_body","structure_angulation","structure_movement","structure_balance"];
    const temperamentFields = ["stability","drive","social_behaviour","defense","confidence"];
    const controlledCount = structureFields.reduce((sum, name) => sum + structureValues(name).length, 0) + temperamentFields.filter((name) => value(name)).length;
    const groups = [
      { step: 0, kicker: "01 / ABOUT", title: value("registered_name") || "Doberman details", meta: [`${value("life_stage") || "—"} · ${value("life_status") || "—"} · ${value("sex") || "—"}`, value("country") || "Country not added"].join(" · ") },
      { step: 1, kicker: "02 / PEDIGREE & HEALTH", title: hasPedigree ? "Pedigree included" : "Pedigree not added", meta: healthResults ? `${healthResults} health entr${healthResults === 1 ? "y" : "ies"}` : "No health details added" },
      { step: 2, kicker: "03 / PROFILE TRAITS & RESULTS", title: controlledCount ? `${controlledCount} standardized trait${controlledCount === 1 ? "" : "s"} selected` : "No profile traits selected", meta: achievementCount ? `${achievementCount} documented result entr${achievementCount === 1 ? "y" : "ies"}` : "No documented results added" },
      { step: 3, kicker: "04 / PHOTOS & MOVEMENT", title: `${selectedFiles} file${selectedFiles === 1 ? "" : "s"} selected`, meta: form.elements.namedItem("hero_photo").files.length ? "Main photo ready" : "Main photo required" },
    ];
    review.innerHTML = groups.map((group) => `
      <article class="review-section-card">
        <div><span>${escapeHtml(group.kicker)}</span><strong>${escapeHtml(group.title)}</strong><small>${escapeHtml(group.meta)}</small></div>
        <button type="button" class="review-edit" data-review-edit="${group.step}">Edit</button>
      </article>`).join("");
    review.querySelectorAll("[data-review-edit]").forEach((button) => button.addEventListener("click", () => showStep(Number(button.dataset.reviewEdit), { preserveReached: true })));
  }

  function updateConditionalFields() {
    const isPuppy = value("life_stage") === "puppy";
    const isDeceased = value("life_status") === "deceased";
    const isAdultMale = !isPuppy && !isDeceased && value("sex") === "male";
    document.querySelectorAll(".puppy-only").forEach((element) => { element.hidden = !isPuppy; });
    document.querySelectorAll(".adult-only").forEach((element) => { element.hidden = isPuppy; });
    document.querySelectorAll(".deceased-only").forEach((element) => { element.hidden = !isDeceased; });
    document.querySelectorAll(".adult-male-only").forEach((element) => { element.hidden = !isAdultMale; });
    if (!isPuppy || isDeceased) form.querySelectorAll('[name="puppy_availability"]').forEach((field) => { field.checked = false; });
    if (isDeceased) form.elements.namedItem("stud_service_status").value = "unknown";
    if (!isDeceased) {
      ["date_of_death", "year_of_death", "cause_of_death"].forEach((name) => { form.elements.namedItem(name).value = ""; });
      form.elements.namedItem("cause_disclosure").value = "not_provided";
      const evidence = form.elements.namedItem("mortality_evidence");
      evidence.value = "";
      updateFileLabel(evidence);
    }
  }

  function buildCanonicalRecord() {
    const now = new Date().toISOString();
    const sex = value("sex");
    const lifeStage = value("life_stage");
    const lifeStatus = value("life_status");
    const isPuppy = lifeStage === "puppy";
    const isDeceased = lifeStatus === "deceased";
    const isAdultMale = !isPuppy && !isDeceased && sex === "male";
    return {
      schema_version: "1.1.0",
      entity_type: "doberman",
      record_id: null,
      status: "draft",
      created_at: now,
      updated_at: now,
      submission: {
        submitter_name: value("contact_name"),
        submitter_email: value("contact_email"),
        relationship: value("relationship") || "owner",
        consent_publication: Boolean(form.elements.namedItem("publication_consent").checked),
        notes: null,
      },
      doberman: {
        identity: {
          registered_name: value("registered_name"),
          sex,
          life_stage: lifeStage,
          life_status: lifeStatus,
          date_of_birth: value("date_of_birth"),
          date_of_death: isDeceased ? (value("date_of_death") || null) : null,
          year_of_death: isDeceased ? numberValue("year_of_death") : null,
          color: value("color"),
          country: value("country"),
          location: value("location") || null,
          registration_authority: value("registration_authority") || null,
          registration_number: value("registration_number") || null,
          kennel_id: null,
          kennel_name: value("kennel_name") || null,
          breeder: value("breeder_name") || null,
          owner: value("public_owner_name") || null,
        },
        parentage: {
          sire_id: null,
          sire_name: value("sire_name") || null,
          sire_registration: value("sire_registration") || null,
          dam_id: null,
          dam_name: value("dam_name") || null,
          dam_registration: value("dam_registration") || null,
          litter_id: null,
          pedigree_source: form.elements.namedItem("pedigree_file").files.length ? "owner_upload" : null,
          pedigree_file: null,
          pedigree_verified: false,
          pedigree_nodes: [],
          pedigree_extraction: { status: "not_started", reviewed_by: null, reviewed_at: null },
        },
        health: {
          dm: makeTest(value("dm")),
          vwd: makeTest(value("vwd")),
          hd: makeTest(value("hd")),
          ed: makeTest(value("ed")),
          thyroid: makeTest(value("thyroid")),
          eyes: makeTest(value("eyes")),
          dcm_clinical: {
            status: value("dcm_clinical_status") || null,
            evaluation_method: value("dcm_method") || null,
            evaluation_date: value("dcm_date") || null,
            veterinarian_or_clinic: value("dcm_clinic") || null,
            evidence_file: null,
          },
          dcm_markers: {
            dcm_1: makeTest(value("dcm1")), dcm_2: makeTest(value("dcm2")), dcm_3: makeTest(value("dcm3")),
            dcm_4: makeTest(value("dcm4")), dcm_5: makeTest(value("dcm5")),
          },
          mortality: {
            cause: isDeceased ? (value("cause_of_death") || null) : null,
            cause_disclosure: isDeceased ? (value("cause_disclosure") || "not_provided") : "not_provided",
            evidence_source: isDeceased && form.elements.namedItem("mortality_evidence").files.length ? "owner_upload" : null,
            evidence_file: null,
          },
        },
        structure: {
          type: structureValues("structure_type"),
          head: structureValues("structure_head"),
          body: structureValues("structure_body"),
          angulation: structureValues("structure_angulation"),
          movement: structureValues("structure_movement"),
          balance: structureValues("structure_balance"),
          evaluator: ["owner", "breeder", "trainer"].includes(value("relationship")) ? value("relationship") : "not_declared",
          evidence: evidenceBlock(),
        },
        temperament: {
          stability: value("stability") || null,
          drive: value("drive") || null,
          social_behaviour: value("social_behaviour") || null,
          defense: value("defense") || null,
          confidence: value("confidence") || null,
          evaluator: value("temperament_evaluator") || "not_declared",
          evidence: evidenceBlock(),
        },
        performance: {
          shows_count: numberValue("shows_count"),
          titles: listValue("titles"),
          working_exams: listValue("working_exams"),
          sports: listValue("sports"),
          evidence_files: [],
        },
        reproduction: {
          litters_count: isPuppy ? null : numberValue("litters_count"),
          offspring_count: isPuppy ? null : numberValue("offspring_count"),
          champion_offspring_count: isPuppy ? null : numberValue("champion_offspring_count"),
          export_countries: isPuppy ? [] : listValue("export_countries"),
          litter_ids: [],
          availability: isAdultMale ? (value("stud_service_status") || "unknown") : "not_applicable",
        },
        puppy_lifecycle: {
          birth_weight_g: isPuppy ? numberValue("birth_weight_g") : null,
          current_status: isPuppy && !isDeceased ? (value("puppy_availability") || "unknown") : "not_applicable",
          evaluation: isPuppy ? (value("puppy_evaluation") || null) : null,
          training: isPuppy ? (value("puppy_training") || null) : null,
          current_owner: isPuppy ? (value("puppy_current_owner") || null) : null,
          achievements: isPuppy ? listValue("puppy_achievements") : [],
        },
        media: {
          hero: null, head: null, profile: null, stack: null, movement: null,
          gallery: [], movement_video: null, movement_video_seconds: null, movement_video_audio: "natural_sound",
        },
        publication: {
          last_updated_label: null,
          profile_template: isPuppy ? "puppy" : sex,
        },
      },
    };
  }

  function privateContact() {
    return {
      name: value("contact_name"), email: value("contact_email"), phone: value("contact_phone"),
      relationship: value("relationship") || "owner",
    };
  }

  function manifestAndEntries() {
    const uploads = [];
    const entries = [];
    fileFields.forEach((config) => {
      const input = form.elements.namedItem(config.name);
      Array.from(input.files || []).forEach((file, index) => {
        const suffix = config.multiple ? `-${String(index + 1).padStart(2, "0")}` : "";
        const packageName = `uploads/${config.role.startsWith("evidence") ? "health/" : ""}${config.base}${suffix}${safeExtension(file)}`;
        uploads.push({
          role: config.role,
          package_file: packageName,
          original_name: file.name,
          media_type: file.type || "application/octet-stream",
          size_bytes: file.size,
        });
        entries.push({ name: packageName, data: file, lastModified: file.lastModified });
      });
    });
    return { uploads, entries };
  }

  function saveDraft() {
    const values = {};
    const groups = new Map();
    Array.from(form.elements).forEach((field) => {
      if (!field.name || field.type === "file") return;
      if (field.type === "radio" || field.type === "checkbox") {
        if (!groups.has(field.name)) groups.set(field.name, []);
        if (field.checked) groups.get(field.name).push(field.value || true);
      } else values[field.name] = field.value;
    });
    groups.forEach((selected, name) => {
      const fields = form.querySelectorAll(`[name="${CSS.escape(name)}"]`);
      if (fields[0]?.type === "radio") values[name] = selected[0] || "";
      else values[name] = fields.length > 1 ? selected : (selected[0] || false);
    });
    localStorage.setItem(storageKey, JSON.stringify(values));
    saveStatus.textContent = "Text answers saved on this device";
  }

  function restoreDraft() {
    let values;
    try { values = JSON.parse(localStorage.getItem(storageKey) || "null"); } catch (_) { values = null; }
    if (!values) return;
    Object.entries(values).forEach(([name, stored]) => {
      const fields = form.querySelectorAll(`[name="${CSS.escape(name)}"]`);
      fields.forEach((field) => {
        if (field.type === "radio") field.checked = String(field.value) === String(stored);
        else if (field.type === "checkbox") {
          const selected = Array.isArray(stored) ? stored : [stored];
          field.checked = selected.map(String).includes(String(field.value || true));
        } else field.value = stored;
      });
    });
    saveStatus.textContent = "Saved text answers restored · reattach files if needed";
    updateConditionalFields();
  }

  function queueSave() {
    clearTimeout(saveTimer);
    saveStatus.textContent = "Saving…";
    saveTimer = setTimeout(saveDraft, 250);
  }

  function updateFileLabel(input) {
    const label = document.querySelector(`[data-file-label="${input.name}"]`);
    if (!label) return;
    const files = Array.from(input.files || []);
    label.textContent = !files.length
      ? (input.name.includes("evidence") ? "No files selected" : input.closest(".upload-card") ? `Choose ${input.accept.includes("video") ? "video" : "photo"}` : "No file selected")
      : files.length === 1 ? `${files[0].name} · click to replace` : `${files.length} files selected · click to change`;
    input.closest(".upload-card")?.classList.toggle("has-file", files.length > 0);
  }

  async function prepareSubmission() {
    if (!validateStep(4)) return;
    clearError();
    prepareButton.disabled = true;
    prepareButton.firstChild.textContent = "Preparing… ";
    try {
      const { uploads, entries } = manifestAndEntries();
      const submission = {
        package_version: "2.0",
        package_type: "doberman_owner_submission",
        submission_reference: globalThis.crypto?.randomUUID?.() || `submission-${Date.now()}`,
        created_at: new Date().toISOString(),
        canonical_record: buildCanonicalRecord(),
        private_contact: privateContact(),
        owner_notes: null,
        consent: {
          accuracy_confirmed: true,
          publication_understood: true,
          confirmed_at: new Date().toISOString(),
        },
        uploads,
      };
      entries.unshift({ name: "submission.json", data: `${JSON.stringify(submission, null, 2)}\n` });
      const archive = await window.DIZip.create(entries);
      const url = URL.createObjectURL(archive);
      const link = document.createElement("a");
      link.href = url;
      link.download = `DOBERMAN-INDEX-${safeSlug(value("registered_name"))}-SUBMISSION.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      successPanel.hidden = false;
      successPanel.scrollIntoView({ behavior: "smooth", block: "center" });
    } catch (error) {
      setError(`We could not prepare the package. ${error.message || "Please try again."}`);
    } finally {
      prepareButton.disabled = false;
      prepareButton.firstChild.textContent = "Prepare my submission ";
    }
  }

  form.querySelectorAll('.structure-choice').forEach((field) => {
    field.addEventListener('change', () => {
      if (!field.checked) return;
      const selected = checkedValues(field.name);
      if (selected.length <= 2) return;
      field.checked = false;
      const row = field.closest('.assessment-row');
      row?.classList.remove('is-limit');
      void row?.offsetWidth;
      row?.classList.add('is-limit');
      setTimeout(() => row?.classList.remove('is-limit'), 380);
    });
  });

  nextButton.addEventListener("click", () => { if (validateStep(currentStep)) showStep(currentStep + 1); });
  backButton.addEventListener("click", () => showStep(currentStep - 1));
  document.querySelectorAll("[data-step-link]").forEach((button) => button.addEventListener("click", () => {
    const target = Number(button.dataset.stepLink);
    if (target <= maxStepReached) showStep(target, { preserveReached: true });
  }));
  returnReviewButton.addEventListener("click", () => showStep(steps.length - 1, { preserveReached: true }));
  form.addEventListener("submit", (event) => { event.preventDefault(); prepareSubmission(); });
  form.addEventListener("input", (event) => { if (["life_stage", "life_status", "sex"].includes(event.target.name)) updateConditionalFields(); queueSave(); });
  form.addEventListener("change", (event) => {
    if (event.target.type === "file") updateFileLabel(event.target);
    if (["life_stage", "life_status", "sex"].includes(event.target.name)) updateConditionalFields();
    if (event.target.type !== "file") queueSave();
  });
  document.getElementById("reset-button").addEventListener("click", () => {
    if (!confirm("Clear all answers and selected files from this form?")) return;
    form.reset();
    localStorage.removeItem(storageKey);
    fileFields.forEach((config) => updateFileLabel(form.elements.namedItem(config.name)));
    successPanel.hidden = true;
    updateConditionalFields();
    maxStepReached = 0;
    showStep(0);
    saveStatus.textContent = "Text answers save on this device";
  });

  restoreDraft();
  fileFields.forEach((config) => updateFileLabel(form.elements.namedItem(config.name)));
  updateConditionalFields();
  showStep(0, { preserveReached: true });
})();
