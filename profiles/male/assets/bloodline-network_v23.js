(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.DIBloodline = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const SIDES = ["S", "D"];
  const SIDE_LABELS = { S: "Sire", D: "Dam" };
  const raf = callback => typeof requestAnimationFrame === "function" ? requestAnimationFrame(callback) : callback();

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>'"]/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
    })[char]);
  }

  function dataAttr(name, value) {
    if (value === null || value === undefined) return "";
    const normalized = String(value).trim();
    return normalized ? ` data-${name}="${escapeHTML(normalized)}"` : "";
  }

  function pedigreeRoleLabel(path, fallbackRole) {
    const normalized = String(path || "");
    if (!normalized) return fallbackRole || "Indexed Doberman";
    if (normalized === "S") return "Sire";
    if (normalized === "D") return "Dam";
    const prefix = normalized.charAt(0) === "S" ? "Paternal" : "Maternal";
    const sexTerm = normalized.charAt(normalized.length - 1) === "S" ? "grandsire" : "granddam";
    if (normalized.length === 2) return `${prefix} ${sexTerm}`;
    const greats = Array.from({ length: normalized.length - 2 }, () => "great").join("-");
    return `${prefix} ${greats}-${sexTerm}`;
  }

  function contributionLabel(path, occurrences = 1) {
    const depth = String(path || "").length;
    if (!depth) return "";
    const total = (100 / Math.pow(2, depth)) * Math.max(1, Number(occurrences) || 1);
    return `${total.toFixed(2)}%`;
  }

  function imageActionAttrs(entry, generationLabel) {
    const occurrencePaths = Array.isArray(entry.occurrencePaths) ? entry.occurrencePaths.filter(Boolean) : [];
    const position = entry.positionLabel || (occurrencePaths.length > 1 ? `Paths ${occurrencePaths.join(" + ")}` : occurrencePaths[0] ? `Path ${occurrencePaths[0]}` : "");
    return [
      "data-bloodline-image",
      dataAttr("image-src", entry.image || ""),
      dataAttr("image-name", entry.name || ""),
      dataAttr("image-registration", entry.registration || ""),
      dataAttr("image-generation", generationLabel || entry.generationLabel || ""),
      dataAttr("image-source", entry.imageSource || ""),
      dataAttr("image-source-url", entry.imageSourceUrl || ""),
      dataAttr("image-country", entry.country || ""),
      dataAttr("image-role", entry.pedigreeRole || entry.role || ""),
      dataAttr("image-position", position),
      dataAttr("image-record", entry.canonicalId || entry.recordId || ""),
      dataAttr("image-mode", entry.viewerMode || ""),
      dataAttr("image-occurrences", entry.repeatCount || ""),
      dataAttr("image-contribution", entry.contribution || ""),
      dataAttr("image-shared", entry.sharedStatus || ""),
      dataAttr("image-linebreeding", entry.linebreedingPath || ""),
      dataAttr("image-note", entry.viewerNote || ""),
      dataAttr("image-profile-url", entry.url || "")
    ].filter(Boolean).join("");
  }

  function parentPath(path) {
    return String(path || "").slice(0, -1);
  }

  function childPaths(path, byPath) {
    return SIDES.map(side => `${path}${side}`).filter(candidate => byPath.has(candidate));
  }

  function normalizeNodes(nodes) {
    return (Array.isArray(nodes) ? nodes : [])
      .filter(node => node && /^[SD]+$/.test(String(node.path || "")))
      .map(node => ({ ...node, path: String(node.path), gen: Number(node.gen) || String(node.path).length }))
      .sort((a, b) => a.gen - b.gen || a.path.localeCompare(b.path));
  }

  function visibleTree(nodes, expandedPaths = []) {
    const normalized = normalizeNodes(nodes);
    const byPath = new Map(normalized.map(node => [node.path, node]));
    const expanded = expandedPaths instanceof Set ? expandedPaths : new Set(expandedPaths);
    const visible = [];
    const edges = [];

    function visit(path) {
      const node = byPath.get(path);
      if (!node) return;
      visible.push(node);
      if (!expanded.has(path)) return;
      childPaths(path, byPath).forEach(child => {
        edges.push({ parent: path, child });
        visit(child);
      });
    }

    SIDES.forEach(path => {
      if (!byPath.has(path)) return;
      edges.push({ parent: "", child: path });
      visit(path);
    });

    return {
      nodes: visible,
      edges,
      byPath,
      maxGeneration: visible.reduce((maximum, node) => Math.max(maximum, node.gen), 0),
    };
  }

  function layoutWeights(path, tree, memo = new Map()) {
    if (memo.has(path)) return memo.get(path);
    const children = tree.edges.filter(edge => edge.parent === path).map(edge => edge.child);
    const weight = children.length ? children.reduce((sum, child) => sum + layoutWeights(child, tree, memo), 0) : 1;
    memo.set(path, weight);
    return weight;
  }

  function horizontalPositions(tree) {
    const positions = new Map([["", 0.5]]);
    const weights = new Map();
    layoutWeights("", tree, weights);

    function place(path, left, right) {
      const children = tree.edges.filter(edge => edge.parent === path).map(edge => edge.child);
      if (!children.length) {
        positions.set(path, (left + right) / 2);
        return positions.get(path);
      }
      const total = children.reduce((sum, child) => sum + (weights.get(child) || 1), 0);
      let cursor = left;
      children.forEach(child => {
        const span = (right - left) * ((weights.get(child) || 1) / total);
        place(child, cursor, cursor + span);
        cursor += span;
      });
      positions.set(path, children.reduce((sum, child) => sum + positions.get(child), 0) / children.length);
      return positions.get(path);
    }

    place("", 0, 1);
    return positions;
  }

  function densityFor(count, maxGeneration) {
    if (count >= 25 || maxGeneration >= 4) return 4;
    if (count >= 15) return 3;
    if (count >= 8) return 2;
    if (count >= 5) return 1;
    return 0;
  }

  function widthCaps(density) {
    return [
      [330, 304, 268, 232, 204],
      [286, 264, 232, 204, 178],
      [246, 226, 204, 176, 154],
      [220, 204, 184, 158, 138],
      [214, 202, 178, 150, 124],
    ][density];
  }

  function generationSpacing(generation, nodes, positions, width, anchors = new Map()) {
    const row = generation === 0 ? [{ path: "" }] : nodes.filter(node => node.gen === generation);
    const xs = [...new Set(row.map(node => {
      const anchor = anchors.get(node.path) || node.path;
      return Math.round(positions.get(anchor) * width * 1000) / 1000;
    }))].sort((a, b) => a - b);
    if (xs.length < 2) return width;
    let minimum = width;
    for (let index = 1; index < xs.length; index += 1) minimum = Math.min(minimum, xs[index] - xs[index - 1]);
    return minimum;
  }

  function computeDesktopLayout(nodes, expandedPaths, width, viewportHeight = 0) {
    const tree = visibleTree(nodes, expandedPaths);
    const subject = { path: "", gen: 0 };
    const allNodes = [subject, ...tree.nodes];
    const positions = horizontalPositions(tree);
    const density = densityFor(allNodes.length, tree.maxGeneration);
    const caps = widthCaps(density);
    const safeWidth = Math.max(280, Number(width) || 1200);
    const horizontalPad = density >= 3 ? 8 : Math.min(34, safeWidth * 0.025);
    const usableWidth = safeWidth - horizontalPad * 2;
    const widths = new Map();
    const lanes = new Map();
    const anchors = new Map();

    // Preserve the established rectangular G4 block: each of the four
    // sire/dam combinations receives its own horizontal lane, while cards in
    // that lane stay anchored to their G2 family branch.
    const deepestRow = tree.nodes.filter(node => node.gen === tree.maxGeneration);
    const packedDeepestGeneration = tree.maxGeneration >= 4 && deepestRow.length > 0;
    const compactHeight = packedDeepestGeneration && Number(viewportHeight) > 0 && Number(viewportHeight) <= 940;
    const roomyLaneIndex = { SS: 0, SD: 1, DS: 2, DD: 3 };
    tree.nodes.forEach(node => {
      const packed = packedDeepestGeneration && node.gen === tree.maxGeneration;
      const lane = roomyLaneIndex[node.path.slice(-2)];
      lanes.set(node.path, packed ? lane : 0);
      anchors.set(node.path, packed ? node.path.slice(0, -2) : node.path);
    });
    lanes.set("", 0);
    anchors.set("", "");

    allNodes.forEach(node => {
      if (node.path === "") {
        const subjectCap = [460, 440, 420, 420, 420][density];
        widths.set(node.path, Math.min(subjectCap, usableWidth * .72));
        return;
      }
      const spacing = generationSpacing(node.gen, tree.nodes, positions, usableWidth, anchors);
      const packed = packedDeepestGeneration && node.gen === tree.maxGeneration;
      const generationCap = packed ? [278, 256, 238, 222, 210][density] : caps[Math.min(node.gen, caps.length - 1)];
      const gap = density >= 4 ? 10 : density >= 2 ? 12 : 16;
      const minimum = density >= 4 ? (packed ? 104 : 64) : 88;
      widths.set(node.path, Math.max(minimum, Math.min(generationCap, spacing - gap)));
    });

    const x = new Map();
    allNodes.forEach(node => {
      const anchor = anchors.get(node.path) || node.path;
      x.set(node.path, horizontalPad + positions.get(anchor) * usableWidth);
    });
    return { tree, allNodes, density, x, widths, lanes, anchors, packedDeepestGeneration, compactHeight, horizontalPad, usableWidth };
  }

  function allExpandablePaths(nodes) {
    const normalized = normalizeNodes(nodes);
    const byPath = new Map(normalized.map(node => [node.path, node]));
    return normalized.filter(node => childPaths(node.path, byPath).length).map(node => node.path);
  }

  function collapseBranch(expanded, path) {
    [...expanded].forEach(item => {
      if (item === path || item.startsWith(path)) expanded.delete(item);
    });
  }

  function metadata(node) {
    return [node.registration, node.country].filter(Boolean).join(" · ") || "Canonical pedigree node";
  }

  function pictureMarkup(node, generation, eager = false, view = "desktop") {
    const role = node.role || SIDE_LABELS[node.path.slice(-1)] || "Ancestor";
    const roleShort = role === "Paternal line" ? "PL" : role === "Maternal line" ? "ML" : "";
    const suppressRole = /grand(?:sire|dam)/i.test(role);
    const showRole = !suppressRole && (view !== "desktop" || !roleShort);
    const roleClass = roleShort ? " class=\"has-short\"" : "";
    const shortMarkup = roleShort ? `<span class="bln-role-short" aria-hidden="true">${roleShort}</span>` : "";
    const roleMarkup = showRole ? `<i${roleClass}><span class="bln-role-full">${escapeHTML(role)}</span>${shortMarkup}</i>` : "";
    return `<div class="bln-photo is-textual" aria-hidden="true"><span class="bln-generation"><b>G${generation}</b>${roleMarkup}</span></div>`;
  }

  function imageNameMarkup(node) {
    const label = escapeHTML(node.name);
    if (!node.image) {
      return `<strong class="bln-name-static"><span class="bln-name-text">${label}</span></strong>`;
    }
    return `<button type="button" class="bln-name-action" ${imageActionAttrs(node, `G${node.gen || ""}`)} aria-label="Open full stance image of ${label}"><span class="bln-name-text">${label}</span><span class="bln-name-arrow" aria-hidden="true">→</span></button>`;
  }

  function nodeCopy(node) {
    return `<div class="bln-copy">${imageNameMarkup(node)}<span class="bln-identity">${escapeHTML(metadata(node))}</span></div>`;
  }

  function nodeMarkup(node, tree, expanded, view, eager = false) {
    const expandable = childPaths(node.path, tree.byPath).length > 0;
    const repeated = Number(node.repeatCount) > 1;
    const open = expanded.has(node.path);
    const treeAction = expandable
      ? `<button type="button" class="bln-tree-action" data-bloodline-path="${escapeHTML(node.path)}" aria-expanded="${open ? "true" : "false"}" aria-label="${open ? "Show ancestry route through" : "Open parents of"} ${escapeHTML(node.name)}"></button>`
      : "";
    const label = expandable ? "" : ` aria-label="${escapeHTML(node.name)}, mapped pedigree boundary"`;
    return `<article class="bln-node${expandable ? " is-expandable" : " is-boundary"}${repeated ? " is-repeat" : ""}" data-path="${escapeHTML(node.path)}" data-canonical-id="${escapeHTML(node.canonicalId || "")}"${expandable ? ` data-expanded="${open ? "true" : "false"}"` : ""}${label}>${pictureMarkup(node, node.gen, eager, view)}${nodeCopy(node)}${treeAction}</article>`;
  }

  function subjectMarkup(subject, compact = false) {
    const role = compact ? "Focal record" : "Indexed Doberman · tree root";
    const label = escapeHTML(subject.name);
    const nameMarkup = subject.image
      ? `<button type="button" class="bln-name-action" ${imageActionAttrs(subject, "DI")} aria-label="Open full stance image of ${label}"><span class="bln-name-text">${label}</span><span class="bln-name-arrow" aria-hidden="true">→</span></button>`
      : `<strong class="bln-name-static"><span class="bln-name-text">${label}</span></strong>`;
    return `<article class="bln-node bln-subject${compact ? " is-compact" : ""}" data-path="" aria-label="${label}, focal Doberman and tree root"><div class="bln-photo is-textual" aria-hidden="true"><span class="bln-generation"><b>DI</b><i>${role}</i></span></div><div class="bln-copy">${nameMarkup}<span class="bln-identity">${escapeHTML([subject.registration, subject.country].filter(Boolean).join(" · ") || subject.recordId || "Doberman Index")}</span></div></article>`;
  }

  function mobileBranchRows(nodes, expandedPaths, activeFocusPath = "") {
    const normalized = normalizeNodes(nodes);
    const byPath = new Map(normalized.map(node => [node.path, node]));
    const expanded = expandedPaths instanceof Set ? expandedPaths : new Set(expandedPaths);
    const route = String(activeFocusPath || "");
    const roots = SIDES.map(side => byPath.get(side)).filter(Boolean);
    const rows = roots.length ? [{ generation: 1, parentPath: "", nodes: roots }] : [];
    if (!route) return rows;

    for (let generation = 2; generation <= 4; generation += 1) {
      const selectedParentPath = route.slice(0, generation - 1);
      if (!selectedParentPath || !expanded.has(selectedParentPath) || !byPath.has(selectedParentPath)) break;
      const parents = childPaths(selectedParentPath, byPath).map(path => byPath.get(path)).filter(Boolean);
      if (!parents.length) break;
      rows.push({ generation, parentPath: selectedParentPath, nodes: parents });
      if (route.length < generation) break;
    }
    return rows;
  }

  function mobileRouteMarkup(tree, expanded, activeFocusPath) {
    const rows = mobileBranchRows([...tree.byPath.values()], expanded, activeFocusPath);
    return `<div class="bln-mobile-lineage">${rows.map(({ generation, parentPath: selectedParentPath, nodes: row }) => {
      const parentName = selectedParentPath ? tree.byPath.get(selectedParentPath)?.name : "";
      const descriptor = generation === 1 ? "Dante’s parents" : `Parents of ${parentName || "selected ancestor"}`;
      return `<div class="bln-mobile-generation" data-generation="${generation}"${selectedParentPath ? ` data-parent-path="${escapeHTML(selectedParentPath)}"` : ""}><div class="bln-mobile-generation-label"><span>G${generation}</span><b title="${escapeHTML(descriptor)}">${escapeHTML(descriptor)}</b></div><div class="bln-mobile-row${row.length === 1 ? " is-single" : " is-parent-pair"}" aria-label="${escapeHTML(descriptor)}">${row.map(node => nodeMarkup(node, tree, expanded, "mobile", node.gen === 1)).join("")}</div></div>`;
    }).join("")}</div>`;
  }


  function bindImageFallbacks(root) {
    root.querySelectorAll(".bln-photo img").forEach(image => {
      const classify = () => {
        if (!image.naturalWidth || !image.naturalHeight) return;
        image.closest(".bln-photo")?.setAttribute("data-orientation", image.naturalHeight > image.naturalWidth ? "portrait" : "landscape");
      };
      if (image.complete) classify();
      else image.addEventListener("load", classify, { once: true });
      image.addEventListener("error", () => {
        image.hidden = true;
        const photo = image.closest(".bln-photo");
        photo?.classList.remove("has-image");
        const cue = photo?.querySelector(".bln-photo-action");
        if (cue) cue.hidden = true;
      }, { once: true });
    });
  }

  function fitNodeNames(container) {
    container.querySelectorAll(".bln-name-action,.bln-name-static").forEach(label => {
      label.style.removeProperty("font-size");
    });
  }

  function mount(options) {
    const root = options && options.root;
    if (!root) throw new Error("Bloodline root is required");
    const subjectSource = options.subject || {};
    const baseNodes = normalizeNodes(options.nodes);
    const pathGroups = baseNodes.reduce((map, node) => {
      if (!node.canonicalId) return map;
      const bucket = map.get(node.canonicalId) || [];
      bucket.push(node.path);
      map.set(node.canonicalId, bucket);
      return map;
    }, new Map());
    const subject = {
      ...subjectSource,
      pedigreeRole: subjectSource.pedigreeRole || "Indexed Doberman · tree root",
      positionLabel: subjectSource.positionLabel || "Profile record",
      viewerMode: subjectSource.viewerMode || "basic",
      occurrencePaths: ["DI"]
    };
    const nodes = baseNodes.map(node => {
      const occurrencePaths = Array.isArray(node.occurrencePaths) && node.occurrencePaths.length ? node.occurrencePaths : (node.canonicalId ? (pathGroups.get(node.canonicalId) || [node.path]) : [node.path]);
      const repeatCount = Math.max(1, Number(node.repeatCount) || occurrencePaths.length || 1);
      const contribution = node.contribution || contributionLabel(node.path, repeatCount);
      const pedigreeRole = node.pedigreeRole || pedigreeRoleLabel(node.path, node.role);
      const sharedStatus = node.sharedStatus || (repeatCount > 1 ? `Repeated ancestor · ${repeatCount} occurrences within analysed depth` : "Single occurrence within analysed depth");
      const linebreedingPath = node.linebreedingPath || (repeatCount > 1 ? occurrencePaths.join(" + ") : node.path || "");
      const positionLabel = node.positionLabel || (repeatCount > 1 ? `Paths ${occurrencePaths.join(" + ")}` : node.path ? `Path ${node.path}` : "");
      const viewerMode = node.viewerMode || ((repeatCount > 1 || Number(node.gen) <= 1) ? "expanded" : "basic");
      return { ...node, occurrencePaths, repeatCount, contribution, pedigreeRole, sharedStatus, linebreedingPath, positionLabel, viewerMode };
    });
    const expanded = new Set(options.expandedPaths || []);
    const history = [];
    const previousPositions = new Map();
    let previousVisible = new Set([""]);
    let lastActionPath = "";
    let activeFocusPath = "";
    let mobileActiveSide = "S";
    let lastWidth = 0;
    let resizeFrame = 0;

    root.innerHTML = `<div class="bln-toolbar"><div><span class="bln-count" aria-live="polite"></span><span class="bln-instruction">Use the yellow edge to unfold ancestry.</span></div><div class="bln-interaction-note"><span><b>YELLOW EDGE</b> unfold / refold parents</span><span><b>NAME →</b> open stance image</span></div><div class="bln-toolbar-actions"><button type="button" data-bloodline-action="all">Open full pedigree</button><button type="button" data-bloodline-action="back" aria-label="Back one pedigree step" hidden>Back one step</button><button type="button" data-bloodline-action="reset" hidden>Reset</button></div></div><div class="bln-desktop" aria-label="Interactive four-generation pedigree"><div class="bln-stage-shell" id="bloodlineStageScroll"><div class="bln-stage"><svg class="bln-connectors" aria-hidden="true"></svg><div class="bln-node-layer"></div></div></div><div class="bln-stage-scrollbar" role="group" aria-controls="bloodlineStageScroll" aria-label="Bloodline horizontal navigation"><div class="bln-stage-scrollbar-track"><div class="bln-stage-scrollbar-thumb" role="scrollbar" tabindex="0" aria-controls="bloodlineStageScroll" aria-orientation="horizontal" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"></div></div></div></div><div class="bln-mobile" aria-label="Interactive four-generation pedigree"></div><div class="bln-image-viewer" role="dialog" aria-modal="true" aria-label="Full stance image" hidden><div class="bln-image-viewer-top"><div class="bln-image-viewer-kicker">Stance archive</div><strong class="bln-image-viewer-name"></strong><button type="button" class="bln-image-viewer-close" data-bloodline-image-close aria-label="Close full image">×</button></div><div class="bln-image-viewer-stage"><img alt=""><aside class="bln-image-viewer-panel" hidden><div class="bln-image-viewer-panel-mode"></div><div class="bln-image-viewer-panel-grid"></div></aside></div><div class="bln-image-viewer-meta"><div class="bln-image-viewer-data"></div></div></div>`;

    const count = root.querySelector(".bln-count");
    const desktop = root.querySelector(".bln-desktop");
    const shell = root.querySelector(".bln-stage-shell");
    const stage = root.querySelector(".bln-stage");
    const svg = root.querySelector(".bln-connectors");
    const layer = root.querySelector(".bln-node-layer");
    const mobile = root.querySelector(".bln-mobile");
    const imageViewer = root.querySelector(".bln-image-viewer");
    const viewerStage = imageViewer.querySelector(".bln-image-viewer-stage");
    const viewerImage = viewerStage.querySelector("img");
    const viewerPanel = imageViewer.querySelector(".bln-image-viewer-panel");
    const networkScrollbar = root.querySelector(".bln-stage-scrollbar");
    const networkTrack = networkScrollbar.querySelector(".bln-stage-scrollbar-track");
    const networkThumb = networkScrollbar.querySelector(".bln-stage-scrollbar-thumb");
    const viewerPanelMode = imageViewer.querySelector(".bln-image-viewer-panel-mode");
    const viewerPanelGrid = imageViewer.querySelector(".bln-image-viewer-panel-grid");
    const viewerName = imageViewer.querySelector(".bln-image-viewer-name");
    const viewerData = imageViewer.querySelector(".bln-image-viewer-data");
    const viewerClose = imageViewer.querySelector("[data-bloodline-image-close]");
    let imageTrigger = null;
    const reset = root.querySelector('[data-bloodline-action="reset"]');
    const back = root.querySelector('[data-bloodline-action="back"]');
    const openAll = root.querySelector('[data-bloodline-action="all"]');
    function rememberState() {
      history.push({ expanded: [...expanded], activeFocusPath });
      if (history.length > 64) history.shift();
    }

    function restorePreviousState() {
      const previous = history.pop();
      if (!previous) return;
      expanded.clear();
      previous.expanded.forEach(path => expanded.add(path));
      activeFocusPath = previous.activeFocusPath;
      lastActionPath = "";
      render();
    }

    function alignSection() {
      raf(() => root.closest(".section")?.scrollIntoView({ block: "start" }));
    }

    function syncNetworkScrollbar() {
      const maximum = Math.max(0, shell.scrollWidth - shell.clientWidth);
      const trackWidth = networkTrack.clientWidth;
      if (!trackWidth) return;
      const thumbWidth = Math.max(46, Math.min(trackWidth, trackWidth * (shell.clientWidth / Math.max(shell.scrollWidth, 1))));
      const travel = Math.max(0, trackWidth - thumbWidth);
      const progress = maximum ? Math.min(1, Math.max(0, shell.scrollLeft / maximum)) : 0;
      networkThumb.style.width = `${thumbWidth}px`;
      networkThumb.style.transform = `translate3d(${travel * progress}px,0,0)`;
      networkThumb.setAttribute("aria-valuenow", String(Math.round(progress * 100)));
      networkScrollbar.classList.toggle("is-disabled", maximum < 2);
    }

    function scrollNetworkTo(target) {
      const maximum = Math.max(0, shell.scrollWidth - shell.clientWidth);
      shell.scrollLeft = Math.min(maximum, Math.max(0, target));
      syncNetworkScrollbar();
    }

    networkThumb.addEventListener("pointerdown", event => {
      event.preventDefault();
      const maximum = Math.max(0, shell.scrollWidth - shell.clientWidth);
      const startX = event.clientX;
      const startScroll = shell.scrollLeft;
      const trackWidth = networkTrack.clientWidth;
      const thumbWidth = networkThumb.getBoundingClientRect().width;
      const travel = Math.max(1, trackWidth - thumbWidth);
      networkThumb.setPointerCapture(event.pointerId);
      const move = moveEvent => {
        if (!networkThumb.hasPointerCapture(moveEvent.pointerId)) return;
        scrollNetworkTo(startScroll + ((moveEvent.clientX - startX) / travel) * maximum);
      };
      const finish = finishEvent => {
        if (networkThumb.hasPointerCapture(finishEvent.pointerId)) networkThumb.releasePointerCapture(finishEvent.pointerId);
        networkThumb.removeEventListener("pointermove", move);
        networkThumb.removeEventListener("pointerup", finish);
        networkThumb.removeEventListener("pointercancel", finish);
      };
      networkThumb.addEventListener("pointermove", move);
      networkThumb.addEventListener("pointerup", finish);
      networkThumb.addEventListener("pointercancel", finish);
    });
    networkTrack.addEventListener("pointerdown", event => {
      if (event.target === networkThumb) return;
      const rect = networkTrack.getBoundingClientRect();
      const maximum = Math.max(0, shell.scrollWidth - shell.clientWidth);
      const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / Math.max(rect.width, 1)));
      scrollNetworkTo(maximum * ratio);
    });
    networkThumb.addEventListener("keydown", event => {
      const maximum = Math.max(0, shell.scrollWidth - shell.clientWidth);
      if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        event.preventDefault();
        scrollNetworkTo(shell.scrollLeft + (event.key === "ArrowLeft" ? -1 : 1) * Math.max(180, shell.clientWidth * .28));
      } else if (event.key === "Home" || event.key === "End") {
        event.preventDefault();
        scrollNetworkTo(event.key === "Home" ? 0 : maximum);
      }
    });
    shell.addEventListener("scroll", syncNetworkScrollbar, { passive:true });

    function setNodePosition(element, position, prior) {
      const width = position.width;
      element.style.width = `${width}px`;
      element.style.opacity = "0";
      const start = prior || { x: position.x, y: Math.max(0, position.y - 20) };
      element.style.transform = `translate3d(${start.x - width / 2}px,${start.y}px,0) scale(${prior ? 1 : .82})`;
      raf(() => {
        element.style.opacity = "1";
        element.style.transform = `translate3d(${position.x - width / 2}px,${position.y}px,0) scale(1)`;
      });
    }

    function renderDesktop(tree) {
      const viewportWidth = Math.max(280, Math.round(shell.clientWidth || root.clientWidth || 1200));
      // Keep the complete pedigree inside the visible desktop viewport.
      // Density/width caps below handle compact cards; the stage itself never
      // grows beyond its shell, so Bloodline Network needs no horizontal pan.
      const width = viewportWidth;
      stage.style.width = "100%";
      const layout = computeDesktopLayout(nodes, expanded, width, typeof window === "object" ? window.innerHeight : 0);
      stage.dataset.density = String(layout.density);
      stage.dataset.viewportFit = layout.compactHeight ? "compact" : "roomy";
      layer.innerHTML = subjectMarkup(subject) + layout.tree.nodes.map(node => nodeMarkup(node, layout.tree, expanded, "desktop", node.gen === 1)).join("");

      const elements = new Map([...layer.querySelectorAll(".bln-node")].map(element => [element.dataset.path || "", element]));
      if (activeFocusPath && elements.has(activeFocusPath)) {
        elements.get(activeFocusPath).classList.add("is-route-focus");
        elements.get(activeFocusPath).querySelector(".bln-tree-action")?.setAttribute("aria-current", "true");
      }
      layout.allNodes.forEach(node => elements.get(node.path).style.width = `${layout.widths.get(node.path)}px`);
      fitNodeNames(layer);

      const rowHeights = new Map();
      layout.allNodes.forEach(node => {
        const height = elements.get(node.path).getBoundingClientRect().height;
        const key = `${node.gen}:${layout.lanes.get(node.path) || 0}`;
        rowHeights.set(key, Math.max(rowHeights.get(key) || 0, height));
      });
      const gap = layout.density >= 4 ? 5 : layout.compactHeight ? 7 : [26, 22, 18, 12, 7][layout.density];
      const laneGap = layout.density >= 4 ? 3 : layout.compactHeight ? 5 : [14, 12, 9, 6, 4][layout.density];
      const rootGap = layout.density >= 4 ? 8 : layout.compactHeight ? 12 : [38, 32, 26, 18, 10][layout.density];
      const rowY = new Map();
      let cursor = layout.density >= 4 ? 2 : layout.compactHeight ? 3 : layout.density >= 3 ? 5 : 10;
      for (let generation = layout.tree.maxGeneration; generation >= 1; generation -= 1) {
        const generationLanes = [...new Set(layout.tree.nodes.filter(node => node.gen === generation).map(node => layout.lanes.get(node.path) || 0))].sort();
        generationLanes.forEach((lane, laneIndex) => {
          const key = `${generation}:${lane}`;
          rowY.set(key, cursor);
          const followingGap = laneIndex < generationLanes.length - 1 ? laneGap : generation === 1 ? rootGap : gap;
          cursor += (rowHeights.get(key) || 0) + followingGap;
        });
      }
      rowY.set("0:0", cursor);
      cursor += rowHeights.get("0:0") || 0;
      const height = Math.max(layout.tree.maxGeneration ? (layout.density >= 4 ? 520 : 430) : 360, cursor + (layout.density >= 3 ? 5 : 10));
      stage.style.height = `${height}px`;
      syncNetworkScrollbar();
      svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
      svg.setAttribute("width", String(width));
      svg.setAttribute("height", String(height));

      const nextPositions = new Map();
      layout.allNodes.forEach(node => {
        const element = elements.get(node.path);
        const rowKey = `${node.gen}:${layout.lanes.get(node.path) || 0}`;
        const position = { x: layout.x.get(node.path), y: rowY.get(rowKey), width: layout.widths.get(node.path), height: element.getBoundingClientRect().height };
        nextPositions.set(node.path, position);
        const prior = previousPositions.get(node.path) || previousPositions.get(parentPath(node.path));
        setNodePosition(element, position, prior);
      });

      const activeWidth = [7, 6.5, 6, 5, 4][layout.density];
      svg.style.setProperty("--bln-active-line", `${activeWidth}px`);
      svg.innerHTML = layout.tree.edges.map(edge => {
        const start = nextPositions.get(edge.parent);
        const end = nextPositions.get(edge.child);
        if (!start || !end) return "";
        const startY = start.y;
        const endY = end.y + end.height;
        const branchY = endY + (startY - endY) * .48;
        const active = activeFocusPath
          ? activeFocusPath.startsWith(edge.child) || edge.parent === activeFocusPath
          : edge.parent === "";
        const fresh = edge.parent === lastActionPath && !previousVisible.has(edge.child);
        const packedChild = layout.packedDeepestGeneration && edge.child.length === layout.tree.maxGeneration;
        const direction = edge.child.endsWith("S") ? -1 : 1;
        const rawDetourX = end.x + direction * (end.width / 2 + 7);
        const detourX = Math.max(4, Math.min(width - 4, rawDetourX));
        const exitY = Math.max(endY + 5, startY - 12);
        const route = packedChild
          ? `M ${start.x.toFixed(2)} ${startY.toFixed(2)} V ${exitY.toFixed(2)} H ${detourX.toFixed(2)} V ${(endY + 5).toFixed(2)} H ${end.x.toFixed(2)} V ${endY.toFixed(2)}`
          : `M ${start.x.toFixed(2)} ${startY.toFixed(2)} V ${branchY.toFixed(2)} H ${end.x.toFixed(2)} V ${endY.toFixed(2)}`;
        const signal = active ? `<path class="bln-connector-signal" pathLength="1" d="${route}"></path>` : "";
        return `<path class="bln-connector${active ? " is-active" : ""}${fresh ? " is-new" : ""}" pathLength="1" d="${route}"></path>${signal}`;
      }).join("");

      previousPositions.clear();
      nextPositions.forEach((value, key) => previousPositions.set(key, value));
      previousVisible = new Set(layout.allNodes.map(node => node.path));
      bindImageFallbacks(desktop);
    }

    function renderMobile(tree) {
      mobile.innerHTML = `<div class="bln-mobile-root-label"><span>DI</span><strong>Indexed dog · tree root</strong></div>${subjectMarkup(subject, true)}${mobileRouteMarkup(tree, expanded, activeFocusPath)}`;
      mobile.classList.toggle("is-focused", Boolean(activeFocusPath));
      mobile.querySelectorAll("[data-bloodline-path]").forEach(action => {
        const path = action.dataset.bloodlinePath || "";
        const element = action.closest(".bln-node");
        if (activeFocusPath && (activeFocusPath.startsWith(path) || parentPath(path) === activeFocusPath)) element?.classList.add("is-route-lineage");
        if (path === activeFocusPath) {
          element?.classList.add("is-route-focus");
          action.setAttribute("aria-current", "true");
        }
      });
      fitNodeNames(mobile);
      bindImageFallbacks(mobile);
    }



    function flyImage(source, target, reverse = false) {
      if (!source || !target || matchMedia("(prefers-reduced-motion: reduce)").matches) return Promise.resolve();
      const from = (reverse ? target : source).getBoundingClientRect();
      const to = (reverse ? source : target).getBoundingClientRect();
      if (!from.width || !from.height || !to.width || !to.height) return Promise.resolve();
      const clone = source.cloneNode(true);
      clone.removeAttribute("loading");
      clone.className = "bln-flight-image";
      Object.assign(clone.style, { left:`${from.left}px`, top:`${from.top}px`, width:`${from.width}px`, height:`${from.height}px`, opacity:"1" });
      document.body.appendChild(clone);
      return new Promise(resolve => {
        const animation = clone.animate([
          { left:`${from.left}px`, top:`${from.top}px`, width:`${from.width}px`, height:`${from.height}px`, opacity:1 },
          { left:`${to.left}px`, top:`${to.top}px`, width:`${to.width}px`, height:`${to.height}px`, opacity:1 }
        ], { duration:540, easing:"cubic-bezier(.16,1,.3,1)", fill:"forwards" });
        animation.addEventListener("finish", () => { clone.remove(); resolve(); }, { once:true });
        animation.addEventListener("cancel", () => { clone.remove(); resolve(); }, { once:true });
      });
    }

    function viewerRow(label, value) {
      if (!value) return "";
      return `<div class="bln-image-viewer-row"><span>${escapeHTML(label)}</span><strong>${escapeHTML(value)}</strong></div>`;
    }

    function renderViewerPanel(dataset) {
      const mode = (dataset.imageMode || "basic").toLowerCase() === "expanded" ? "expanded" : "basic";
      const position = [dataset.imageRole, dataset.imagePosition].filter(Boolean).join(" · ");
      const lineage = mode === "expanded"
        ? [dataset.imageOccurrences ? `${dataset.imageOccurrences}×` : "", dataset.imageContribution || ""].filter(Boolean).join(" · ")
        : "";
      const rows = [
        ["REG", dataset.imageRegistration || ""],
        ["POSITION", position],
        ["LINEAGE", lineage]
      ].filter(([, value]) => value);
      viewerPanelMode.textContent = "STANCE RECORD";
      viewerPanelGrid.innerHTML = rows.slice(0, 3).map(([label, value]) => viewerRow(label, value)).join("");
      viewerPanel.hidden = rows.length === 0;
    }

    function syncViewerStageClearance() {
      if (imageViewer.hidden) return;
      const desktopMode = typeof matchMedia === "function" ? matchMedia("(min-width: 821px)").matches : true;
      viewerStage.style.setProperty("margin-top", "0px", "important");
      const stageTop = viewerStage.getBoundingClientRect().top;
      const titleBottom = viewerName.getBoundingClientRect().bottom;
      const closeBottom = viewerClose.getBoundingClientRect().bottom;
      const topBottom = imageViewer.querySelector(".bln-image-viewer-top")?.getBoundingClientRect().bottom || 0;
      const safeGap = desktopMode ? 32 : 20;
      const desiredTop = Math.max(titleBottom, closeBottom, topBottom) + safeGap;
      const shift = Math.max(0, Math.ceil(desiredTop - stageTop));
      viewerStage.style.setProperty("margin-top", `${shift}px`, "important");
      if (desktopMode && typeof window === "object") {
        const downwardExtension = 38; // ≈ 1 cm: extend only below the solved title/clearance zone.
        const available = Math.max(300, Math.floor(window.innerHeight - desiredTop - 74));
        const extendedHeight = available + downwardExtension;
        viewerStage.style.setProperty("height", `${extendedHeight}px`, "important");
        viewerStage.style.setProperty("max-height", `${extendedHeight}px`, "important");
      } else {
        viewerStage.style.removeProperty("height");
        viewerStage.style.removeProperty("max-height");
      }
    }

    async function openImageViewer(action) {
      const imageSrc = action.dataset.imageSrc || "";
      if (!imageSrc) return;
      imageTrigger = action;
      const name = action.dataset.imageName || "Doberman";
      const registration = action.dataset.imageRegistration || "";
      const generation = action.dataset.imageGeneration || "";
      const role = action.dataset.imageRole || "";
      const sourceLabel = action.dataset.imageSource || "";
      imageViewer.dataset.name = name;
      viewerName.textContent = name;
      viewerData.textContent = [generation, registration].filter(Boolean).join(" · ");
      renderViewerPanel(action.dataset);
      viewerImage.src = imageSrc;
      viewerImage.alt = `${name} in stance`;
      viewerImage.style.opacity = "0";
      imageViewer.hidden = false;
      document.documentElement.classList.add("bln-image-open");
      document.body.classList.add("bln-image-open");
      raf(() => imageViewer.classList.add("is-open"));
      try { await viewerImage.decode(); } catch (_) {}
      await new Promise(resolve => raf(resolve));
      syncViewerStageClearance();
      viewerImage.style.opacity = "1";
      viewerClose.focus({ preventScroll:true });
    }

    async function closeImageViewer() {
      if (imageViewer.hidden) return;
      imageViewer.classList.remove("is-open");
      document.documentElement.classList.remove("bln-image-open");
      document.body.classList.remove("bln-image-open");
      setTimeout(() => {
        imageViewer.hidden = true;
        viewerImage.removeAttribute("src");
        viewerPanel.hidden = true;
        viewerPanelGrid.innerHTML = "";
        imageTrigger?.focus({ preventScroll:true });
        imageTrigger = null;
      }, matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 260);
    }

    function render(focusPath = "", restoreFocus = false) {
      const tree = visibleTree(nodes, expanded);
      const visibleCount = tree.nodes.length + 1;
      count.textContent = `${String(visibleCount).padStart(2, "0")} visible · G0–G${tree.maxGeneration}`;
      const fullyOpen = allExpandablePaths(nodes).every(path => expanded.has(path));
      openAll.hidden = fullyOpen;
      back.hidden = history.length === 0;
      reset.hidden = expanded.size === 0;
      renderDesktop(tree);
      renderMobile(tree);
      lastActionPath = "";
      if (restoreFocus && focusPath) raf(() => {
        const view = matchMedia("(max-width: 720px)").matches ? mobile : desktop;
        view.querySelector(`[data-bloodline-path="${focusPath}"]`)?.focus({ preventScroll: true });
      });
    }

    function toggle(path, restoreFocus) {
      const tree = visibleTree(nodes, expanded);
      if (!tree.byPath.has(path) || childPaths(path, tree.byPath).length === 0) return;
      mobileActiveSide = path.charAt(0) === "D" ? "D" : "S";
      if (expanded.has(path)) {
        // An open ancestor remains selectable. Re-selecting it restores the
        // route signal from Dante to that dog and on to its visible parents.
        // Branch removal is deliberately left to Back/Reset, so a user never
        // loses an already opened lineage while trying to inspect it again.
        if (activeFocusPath !== path) rememberState();
        lastActionPath = "";
        activeFocusPath = path;
      } else {
        rememberState();
        lastActionPath = path;
        expanded.add(path);
        activeFocusPath = path;
      }
      render(path, restoreFocus);
    }

    root.addEventListener("click", event => {
      const imageAction = event.target.closest("[data-bloodline-image]");
      if (imageAction && root.contains(imageAction)) {
        openImageViewer(imageAction);
        return;
      }
      if (event.target.closest("[data-bloodline-image-close]")) {
        closeImageViewer();
        return;
      }
      const actionTarget = event.target.closest("[data-bloodline-action]");
      const action = actionTarget?.dataset.bloodlineAction;
      if (action === "all") {
        rememberState();
        allExpandablePaths(nodes).forEach(path => expanded.add(path));
        lastActionPath = "";
        activeFocusPath = "";
        render();
        alignSection();
        return;
      }
      if (action === "back") {
        restorePreviousState();
        return;
      }
      if (action === "reset") {
        rememberState();
        expanded.clear();
        lastActionPath = "";
        activeFocusPath = "";
        render();
        return;
      }
      const button = event.target.closest("[data-bloodline-path]");
      if (button && root.contains(button)) toggle(button.dataset.bloodlinePath || "", event.detail === 0);
    });

    imageViewer.addEventListener("click", event => {
      if (event.target === imageViewer) closeImageViewer();
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && !imageViewer.hidden) closeImageViewer();
    });
    if (typeof window === "object") {
      window.addEventListener("resize", () => {
        syncNetworkScrollbar();
        if (!imageViewer.hidden) raf(syncViewerStageClearance);
      }, { passive:true });
    }

    function highlightRepeated(target, state) {
      const node = target.closest("[data-canonical-id]");
      const canonicalId = node?.dataset.canonicalId;
      if (!canonicalId) return;
      root.querySelectorAll(`[data-canonical-id="${canonicalId}"]`).forEach(element => element.classList.toggle("is-related-repeat", state));
    }
    root.addEventListener("pointerover", event => highlightRepeated(event.target, true));
    root.addEventListener("pointerout", event => highlightRepeated(event.target, false));
    root.addEventListener("focusin", event => highlightRepeated(event.target, true));
    root.addEventListener("focusout", event => highlightRepeated(event.target, false));

    if (typeof ResizeObserver === "function") {
      const observer = new ResizeObserver(entries => {
        const width = Math.round(entries[0]?.contentRect?.width || 0);
        if (!width || Math.abs(width - lastWidth) < 2) return;
        lastWidth = width;
        if (resizeFrame && typeof cancelAnimationFrame === "function") cancelAnimationFrame(resizeFrame);
        resizeFrame = raf(() => render());
      });
      // The desktop shell is display:none on mobile, so its width becomes zero
      // and cannot report orientation or split-view changes. The network root
      // remains measurable in both modes and lets name fitting rerun reliably.
      observer.observe(root);
    }

    render();
    return Object.freeze({
      expandedPaths: expanded,
      openAll() { rememberState(); allExpandablePaths(nodes).forEach(path => expanded.add(path)); activeFocusPath = ""; render(); alignSection(); },
      back() { restorePreviousState(); },
      reset() { rememberState(); expanded.clear(); activeFocusPath = ""; render(); },
      toggle(path) { toggle(path, false); },
    });
  }

  return Object.freeze({
    normalizeNodes,
    visibleTree,
    horizontalPositions,
    computeDesktopLayout,
    mobileBranchRows,
    allExpandablePaths,
    collapseBranch,
    mount,
  });
});
