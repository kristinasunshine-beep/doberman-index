(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.DIName = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const PARTICLES = new Set(["von", "vom", "van", "de", "del", "di", "da", "der", "den", "of", "the", "la", "le"]);
  const KNOWN_ACRONYMS = new Set(["AD", "BH", "CH", "FCI", "IDC", "IGP", "IPO", "ZTP"]);
  const COMPOUND_SEPARATOR = /([-‐‑‒–—'’])/u;

  function titleSegment(value) {
    const lower = String(value || "").toLocaleLowerCase();
    const letters = Array.from(lower);
    if (!letters.length) return "";
    return letters[0].toLocaleUpperCase() + letters.slice(1).join("");
  }

  function preservedToken(value) {
    const token = String(value || "");
    const upper = token.toLocaleUpperCase();
    if (KNOWN_ACRONYMS.has(upper)) return upper;
    if (/^[IVXLCDM]+$/u.test(upper) && upper.length <= 8) return upper;
    if (/\p{N}/u.test(token) || /[./&+_]/u.test(token)) return token;
    return "";
  }

  function titleToken(value) {
    const preserved = preservedToken(value);
    if (preserved) return preserved;
    return String(value || "")
      .split(COMPOUND_SEPARATOR)
      .map((part, index) => index % 2 ? part : titleSegment(part))
      .join("");
  }

  function editorialCase(source) {
    return source.split(" ").map((token, index) => {
      const lower = token.toLocaleLowerCase();
      if (index > 0 && PARTICLES.has(lower)) return lower;
      return titleToken(token);
    }).join(" ");
  }

  function displayRegisteredName(value) {
    const source = String(value ?? "").normalize("NFC").trim().replace(/\s+/gu, " ");
    if (!source) return "";
    // Preserve intentional mixed capitalization; retain legacy lowercase-input support.
    const mixedCase = source !== source.toLocaleUpperCase() && source !== source.toLocaleLowerCase();
    return mixedCase ? source : editorialCase(source);
  }

  function displayKennelName(value) {
    const source = String(value ?? "").normalize("NFC").trim().replace(/\s+/gu, " ");
    // Normalize shouting-case identity metadata; preserve intentional brand casing.
    const hasCasedLetters = source.toLocaleLowerCase() !== source.toLocaleUpperCase();
    return hasCasedLetters && source === source.toLocaleUpperCase()
      ? editorialCase(source)
      : source;
  }

  return Object.freeze({ displayRegisteredName, displayKennelName });
});
