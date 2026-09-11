(() => {
  "use strict";

  async function writeClipboard(value) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(value);
      return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = value;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    textarea.remove();
    if (!copied) throw new Error("Clipboard copy failed");
  }

  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-copy-text],[data-copy-html]");
    if (!button) return;
    const value = button.dataset.copyHtml || button.dataset.copyText || "";
    if (!value) return;
    const original = button.textContent;
    try {
      await writeClipboard(value);
      button.textContent = "Copied";
      button.dataset.copyState = "success";
    } catch (_error) {
      button.textContent = "Copy failed";
      button.dataset.copyState = "error";
    }
    window.setTimeout(() => {
      button.textContent = original;
      delete button.dataset.copyState;
    }, 1800);
  });
})();
