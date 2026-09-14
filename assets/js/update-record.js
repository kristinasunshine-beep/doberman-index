(() => {
  "use strict";
  const form = document.getElementById("update-form");
  const steps = [...document.querySelectorAll(".form-step")];
  const nav = [...document.querySelectorAll("[data-step-link]")];
  const next = document.getElementById("next-button");
  const back = document.getElementById("back-button");
  const submitButton = document.getElementById("submit-button");
  const errorBox = document.getElementById("form-error");
  const success = document.getElementById("success-panel");
  const fill = document.getElementById("progress-fill");
  const review = document.getElementById("review-summary");
  const reset = document.getElementById("reset-button");
  const saveStatus = document.getElementById("save-status");
  const recordBadge = document.getElementById("record-type-badge");
  const storageKey = "doberman-index-record-update-v1";
  const IMAGE_MAX = 20 * 1024 * 1024;
  const PDF_MAX = 25 * 1024 * 1024;
  const VIDEO_MAX = 180 * 1024 * 1024;
  const PACKAGE_MAX = 250 * 1024 * 1024;
  let current = 0;
  let maxReached = 0;

  const value = (name) => (form.elements.namedItem(name)?.value || "").trim();
  const selectedTypes = () => [...form.querySelectorAll('[name="update_types"]:checked')].map((el) => el.value);
  const lines = (name) => value(name).split(/\r?\n/).map((v) => v.trim()).filter(Boolean);
  const esc = (v) => String(v ?? "").replace(/[&<>]/g, (x) => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[x]));
  const safe = (v) => (v || "RECORD").normalize("NFKD").replace(/[\u0300-\u036f]/g, "").replace(/[^a-zA-Z0-9]+/g, "-").replace(/^-|-$/g, "").toUpperCase().slice(0, 60) || "RECORD";
  const ext = (file) => ((file.name || "").match(/\.[a-zA-Z0-9]+$/) || [""])[0].toLowerCase();
  const fileKind = (file) => file.type.startsWith("image/") ? "image" : file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf") ? "pdf" : file.type.startsWith("video/") ? "video" : "other";

  function setError(message = "", field) {
    errorBox.hidden = !message;
    errorBox.textContent = message;
    if (message) {
      field?.focus?.({ preventScroll: true });
      errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function inferRecordType() {
    const id = value("record_id").toUpperCase();
    const map = { "DI-M": "Male Doberman record", "DI-F": "Female Doberman record", "DI-K": "Kennel record", "DI-L": "Litter record" };
    const prefix = Object.keys(map).find((p) => id.startsWith(`${p}-`));
    recordBadge.textContent = prefix ? map[prefix] : "Record type will be detected automatically.";
  }

  function updatePanels() {
    const chosen = new Set(selectedTypes());
    document.querySelectorAll("[data-update-panel]").forEach((panel) => { panel.hidden = !chosen.has(panel.dataset.updatePanel); });
  }

  function showStep(index, preserveReached = false) {
    current = Math.max(0, Math.min(steps.length - 1, index));
    if (!preserveReached) maxReached = Math.max(maxReached, current);
    steps.forEach((s, i) => { s.hidden = i !== current; s.classList.toggle("is-active", i === current); });
    nav.forEach((b, i) => {
      const li = b.closest("li");
      li.classList.toggle("is-active", i === current);
      li.classList.toggle("is-complete", i < maxReached);
      li.classList.toggle("is-available", i <= maxReached);
      b.setAttribute("aria-disabled", i > maxReached ? "true" : "false");
    });
    fill.style.width = `${(maxReached / (steps.length - 1)) * 100}%`;
    back.hidden = current === 0;
    next.hidden = current === steps.length - 1;
    submitButton.hidden = current !== steps.length - 1;
    if (current === steps.length - 1) renderReview();
    setError();
    document.querySelector(".wizard-card").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function validateConditional() {
    const types = new Set(selectedTypes());
    const required = [];
    if (types.has("title") && !lines("new_titles").length) required.push(["new_titles", "Add at least one exact title or result."]);
    if (types.has("health") && (!value("health_test") || !value("health_result"))) required.push(["health_test", "Add the health test/evaluation and result."]);
    if (types.has("media") && !value("media_note")) required.push(["media_note", "Describe the media that should be added or replaced."]);
    if (types.has("reproduction") && !value("reproduction_note")) required.push(["reproduction_note", "Add the new litter or offspring information."]);
    if (types.has("status") && (!value("status_field") || !value("status_value"))) required.push(["status_field", "Add the field/status and its new value."]);
    if (types.has("correction") && (!value("correction_field") || !value("correction_value"))) required.push(["correction_field", "Show what is incorrect and the correct information."]);
    if (types.has("other") && !value("other_note")) required.push(["other_note", "Describe the update."]);
    if (required.length) {
      const [name, message] = required[0];
      setError(message, form.elements.namedItem(name));
      return false;
    }
    return true;
  }

  function validateFiles() {
    let total = 0;
    for (const input of form.querySelectorAll('input[type="file"]')) {
      for (const file of [...input.files]) {
        total += file.size;
        const kind = fileKind(file);
        if (kind === "image" && file.size > IMAGE_MAX) { setError(`${file.name} is larger than 20 MB.`, input); return false; }
        if (kind === "pdf" && file.size > PDF_MAX) { setError(`${file.name} is larger than 25 MB.`, input); return false; }
        if (kind === "video" && file.size > VIDEO_MAX) { setError(`${file.name} is larger than 180 MB.`, input); return false; }
      }
    }
    if (total > PACKAGE_MAX) { setError("The complete update package is larger than 250 MB."); return false; }
    return true;
  }

  function validStep(index) {
    setError();
    for (const field of steps[index].querySelectorAll("input,select,textarea")) {
      if (!field.checkValidity()) { field.reportValidity(); return false; }
    }
    if (index === 0) {
      const id = value("record_id").toUpperCase();
      form.elements.namedItem("record_id").value = id;
      if (!/^DI-[MFKL]-\d{6}$/.test(id)) { setError("Use the permanent Record ID, for example DI-M-000001.", form.elements.namedItem("record_id")); return false; }
    }
    if (index === 1) {
      if (!selectedTypes().length) { setError("Select at least one type of update."); return false; }
      if (!validateConditional()) return false;
    }
    if (index === 2 && !validateFiles()) return false;
    return true;
  }

  function renderReview() {
    const types = selectedTypes();
    const labels = { title:"New title / result", health:"Health / genetics", media:"New media", reproduction:"Reproduction / litter", status:"Status / detail", correction:"Correction", other:"Other update" };
    const evidence = form.elements.namedItem("evidence_files").files.length;
    const media = form.elements.namedItem("public_media").files.length;
    const cards = [
      [0, "RECORD", `${value("record_id")} · ${value("record_name")}`, value("contact_email")],
      [1, "CHANGES", types.map((t) => labels[t]).join(" · "), `${types.length} update categor${types.length === 1 ? "y" : "ies"}`],
      [2, "EVIDENCE", `${evidence} evidence file(s) · ${media} public media file(s)`, value("admin_note") ? "Additional note included" : "No additional note"],
    ];
    review.innerHTML = cards.map(([step,label,title,small]) => `<article class="review-section-card"><div><span>${esc(label)}</span><strong>${esc(title)}</strong><small>${esc(small)}</small></div><button class="review-edit" type="button" data-edit-step="${step}">Edit</button></article>`).join("");
    review.querySelectorAll("[data-edit-step]").forEach((btn) => btn.addEventListener("click", () => showStep(Number(btn.dataset.editStep), true)));
  }

  function packageFiles() {
    const uploads = [], entries = [];
    const addFiles = (inputName, role, base) => {
      const input = form.elements.namedItem(inputName);
      [...input.files].forEach((file, i) => {
        const path = `uploads/${base}-${String(i + 1).padStart(2,"0")}${ext(file)}`;
        uploads.push({ role, package_file:path, original_name:file.name, media_type:file.type || "application/octet-stream", size_bytes:file.size });
        entries.push({ name:path, data:file, lastModified:file.lastModified });
      });
    };
    addFiles("evidence_files", "update_evidence", "evidence");
    addFiles("public_media", "public_media", "public-media");
    return { uploads, entries };
  }

  function buildUpdatePayload(uploads) {
    return {
      package_version: "1.0",
      package_type: "record_update_submission",
      submission_kind: "update",
      record_id: value("record_id").toUpperCase(),
      supersedes_submission_reference: null,
      submission_reference: globalThis.crypto?.randomUUID?.() || `update-${Date.now()}`,
      created_at: new Date().toISOString(),
      private_contact: { name:value("contact_name"), email:value("contact_email"), phone:value("contact_phone"), relationship:value("relationship") || "owner" },
      update_request: {
        record_name: value("record_name"),
        categories: selectedTypes(),
        title: selectedTypes().includes("title") ? { entries:lines("new_titles"), date:value("title_date") || null, issuer:value("title_issuer") || null } : null,
        health: selectedTypes().includes("health") ? { test:value("health_test"), result:value("health_result"), date:value("health_date") || null, issuer:value("health_issuer") || null, note:value("health_note") || null } : null,
        media: selectedTypes().includes("media") ? { note:value("media_note") } : null,
        reproduction: selectedTypes().includes("reproduction") ? { note:value("reproduction_note") } : null,
        status: selectedTypes().includes("status") ? { field:value("status_field"), new_value:value("status_value"), note:value("status_note") || null } : null,
        correction: selectedTypes().includes("correction") ? { current_or_field:value("correction_field"), correct_value:value("correction_value"), note:value("correction_note") || null } : null,
        other: selectedTypes().includes("other") ? { note:value("other_note") } : null,
        admin_note: value("admin_note") || null,
      },
      consent: { accuracy_confirmed:true, publication_understood:true, asset_rights_confirmed:true, confirmed_at:new Date().toISOString() },
      uploads,
    };
  }

  async function sendUpdate() {
    if (!validStep(3)) return;
    submitButton.disabled = true;
    setError();
    submitButton.firstChild.textContent = "Preparing… ";
    try {
      if (!window.DISubmissionUpload) throw new Error("Secure submission service is unavailable.");
      const { uploads, entries } = packageFiles();
      const submission = buildUpdatePayload(uploads);
      entries.unshift({ name:"update.json", data:`${JSON.stringify(submission,null,2)}\n` });
      const archive = await window.DIZip.create(entries);
      const filename = `DOBERMAN-INDEX-${safe(submission.record_id)}-${safe(value("record_name"))}-UPDATE.zip`;
      const result = await window.DISubmissionUpload.send({
        archive,
        filename,
        submission,
        entityName: `${value("record_name")} · ${submission.record_id}`,
        packageType: "record-update",
        onProgress: ({ phase, percent }) => { submitButton.firstChild.textContent = phase === "finalizing" ? "Finalizing… " : `Sending… ${percent}% `; },
      });
      const ref = esc(result.submissionReference || submission.submission_reference);
      success.innerHTML = `<strong>Update received.</strong><span>Your update was sent securely to Doberman Index Records. Reference: ${ref}</span>`;
      success.hidden = false;
      success.scrollIntoView({ behavior:"smooth", block:"center" });
      localStorage.removeItem(storageKey);
      saveStatus.textContent = "Update received";
      submitButton.firstChild.textContent = "Submitted ";
    } catch (e) {
      setError(`We could not send the update. Your answers and selected files are still here. Check the connection and try again. ${e.message || ""}`.trim());
      submitButton.disabled = false;
      submitButton.firstChild.textContent = "Submit update ";
    }
  }

  function save() {
    const data = {};
    [...form.elements].forEach((el) => {
      if (!el.name || el.type === "file") return;
      if (el.type === "checkbox" || el.type === "radio") data[`${el.name}::${el.value || "checked"}`] = el.checked;
      else data[el.name] = el.value;
    });
    localStorage.setItem(storageKey, JSON.stringify(data));
    saveStatus.textContent = "Text answers saved on this device";
  }

  function restore() {
    try {
      const data = JSON.parse(localStorage.getItem(storageKey) || "{}");
      [...form.elements].forEach((el) => {
        if (!el.name || el.type === "file") return;
        if (el.type === "checkbox" || el.type === "radio") {
          const key = `${el.name}::${el.value || "checked"}`;
          if (key in data) el.checked = Boolean(data[key]);
        } else if (el.name in data) el.value = data[el.name];
      });
    } catch (_) {}
  }

  function applyQueryPrefill() {
    const q = new URLSearchParams(location.search);
    if (q.get("record")) form.elements.namedItem("record_id").value = q.get("record").toUpperCase();
    if (q.get("name")) form.elements.namedItem("record_name").value = q.get("name");
  }

  form.addEventListener("input", () => { updatePanels(); inferRecordType(); clearTimeout(form._saveTimer); form._saveTimer = setTimeout(save, 250); });
  form.addEventListener("change", (e) => {
    updatePanels(); inferRecordType();
    if (e.target.type === "file") {
      const label = document.querySelector(`[data-file-label="${e.target.name}"]`);
      const files = [...e.target.files];
      if (label) label.textContent = files.length ? (files.length === 1 ? files[0].name : `${files.length} files selected`) : (e.target.name === "public_media" ? "Choose media" : "Choose files");
      e.target.closest(".upload-card")?.classList.toggle("has-file", files.length > 0);
    }
    save();
  });
  next.addEventListener("click", () => { if (validStep(current)) showStep(current + 1); });
  back.addEventListener("click", () => showStep(current - 1, true));
  nav.forEach((b, i) => b.addEventListener("click", () => { if (i <= maxReached) showStep(i, true); }));
  form.addEventListener("submit", (e) => { e.preventDefault(); sendUpdate(); });
  reset.addEventListener("click", () => { if (!confirm("Clear this saved record update?")) return; form.reset(); localStorage.removeItem(storageKey); current = 0; maxReached = 0; success.hidden = true; updatePanels(); inferRecordType(); showStep(0); });

  restore();
  applyQueryPrefill();
  updatePanels();
  inferRecordType();
  showStep(0);
})();
