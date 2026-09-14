(function (global) {
  "use strict";

  const API_BASE = "https://doberman-index-intake.dobermanindex-records.workers.dev";
  const MAX_PACKAGE_BYTES = 250 * 1024 * 1024;
  const DEFAULT_CHUNK_BYTES = 8 * 1024 * 1024;
  const MAX_RETRIES = 3;

  function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

  async function jsonRequest(path, options = {}, retries = 0) {
    let lastError;
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      try {
        const response = await fetch(`${API_BASE}${path}`, {
          ...options,
          headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body.error || `HTTP ${response.status}`);
        return body;
      } catch (error) {
        lastError = error;
        if (attempt < retries) await sleep(700 * (attempt + 1));
      }
    }
    throw lastError || new Error("Request failed");
  }

  async function uploadPart({ key, uploadId, token, partNumber, blob }) {
    let lastError;
    for (let attempt = 0; attempt < MAX_RETRIES; attempt += 1) {
      try {
        const params = new URLSearchParams({ key, uploadId, token, partNumber: String(partNumber) });
        const response = await fetch(`${API_BASE}/v1/submissions/part?${params}`, {
          method: "PUT",
          headers: { "Content-Type": "application/octet-stream" },
          body: blob,
        });
        const body = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(body.error || `Part ${partNumber} failed`);
        return body;
      } catch (error) {
        lastError = error;
        if (attempt < MAX_RETRIES - 1) await sleep(900 * (attempt + 1));
      }
    }
    throw lastError || new Error(`Part ${partNumber} failed`);
  }

  async function send({ archive, filename, submission, entityName, packageType, onProgress }) {
    if (!(archive instanceof Blob)) throw new Error("Submission package is unavailable.");
    if (archive.size <= 0) throw new Error("Submission package is empty.");
    if (archive.size > MAX_PACKAGE_BYTES) throw new Error("Submission package exceeds the 250 MB limit.");

    onProgress?.({ phase: "starting", percent: 0 });
    const created = await jsonRequest("/v1/submissions/create", {
      method: "POST",
      body: JSON.stringify({
        filename,
        sizeBytes: archive.size,
        submissionReference: submission.submission_reference,
        packageType,
        entityName,
        submitterEmail: submission.private_contact?.email || submission.canonical_record?.submission?.submitter_email || "",
        submitterName: submission.private_contact?.name || submission.canonical_record?.submission?.submitter_name || "",
        submissionKind: submission.submission_kind || "initial",
        recordId: submission.record_id || null,
        supersedesSubmissionReference: submission.supersedes_submission_reference || null,
      }),
    }, 2);

    const chunkSize = Number(created.chunkSize) || DEFAULT_CHUNK_BYTES;
    const parts = [];
    const partCount = Math.ceil(archive.size / chunkSize);

    try {
      for (let index = 0; index < partCount; index += 1) {
        const start = index * chunkSize;
        const end = Math.min(start + chunkSize, archive.size);
        const result = await uploadPart({
          key: created.key,
          uploadId: created.uploadId,
          token: created.token,
          partNumber: index + 1,
          blob: archive.slice(start, end),
        });
        parts.push({ partNumber: result.partNumber, etag: result.etag });
        onProgress?.({ phase: "uploading", percent: Math.max(1, Math.round((end / archive.size) * 96)) });
      }

      onProgress?.({ phase: "finalizing", percent: 98 });
      const completed = await jsonRequest("/v1/submissions/complete", {
        method: "POST",
        body: JSON.stringify({
          key: created.key,
          uploadId: created.uploadId,
          token: created.token,
          parts,
        }),
      }, 2);
      onProgress?.({ phase: "complete", percent: 100 });
      return completed;
    } catch (error) {
      jsonRequest("/v1/submissions/abort", {
        method: "POST",
        body: JSON.stringify({ key: created.key, uploadId: created.uploadId, token: created.token }),
      }).catch(() => {});
      throw error;
    }
  }

  global.DISubmissionUpload = { send };
})(window);
