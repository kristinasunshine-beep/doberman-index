"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const read = relative => fs.readFileSync(path.join(root, relative), "utf8");
const male = read("profiles/male/index.html");
const female = read("profiles/female/index.html");
const index = read("index.html");
const router = read("profile.html");
const DIName = require("../assets/js/display-name.js");
const DIBloodline = require("../profiles/male/assets/bloodline-network_v23.js");

function assertTokens(source, tokens, label) {
  for (const token of tokens) assert.ok(source.includes(token), `${label} missing: ${token}`);
}

// Homepage keeps the accepted visual shell, central registry search and the Dante example card.
assertTokens(index, [
  'data-search-anchor="males"', 'data-search-anchor="females"', 'data-search-anchor="kennels"', 'data-search-anchor="puppies"',
  'id="recordSearchInput"', 'class="hero-search-submit"', 'class="puppy-shortcut"', 'id="recordSearchResults"',
  'Available puppies', 'Search the records', 'search-results-head', 'data/registry.json', 'profile.html?id=',
  'href="profiles/male/?id=DI-M-000001"', 'Example digital card', 'media/dobermans/DI-M-000001/hero.png'
], "homepage");

assertTokens(router, [
  'male:"./profiles/male/"', 'female:"./profiles/female/"',
  'puppy:"./profiles/puppy.html"', 'kennel:"./profiles/kennel-concept.html"', 'litter:"./profiles/litter.html"'
], "profile router");

for (const [label, html] of [["male", male], ["female", female]]) {
  assertTokens(html, [
    'const repoRoot=new URL("../../",document.baseURI);',
    'href="../../index.html"',
    'assets/bloodline-network_v23.css', 'assets/bloodline-network_v23.js',
    'async function loadProfile()', 'async function initializeProfile()',
    'window.DIBloodline.mount', 'id="bloodlineRail"',
    'id="structureRail"', 'id="temperamentRail"', 'id="performanceRail"', 'id="relatedRail"',
    'preload="metadata"', 'loading="${index?"lazy":"eager"}"'
  ], `${label} V27`);
  assert.match(html, /<meta[^>]+name=["']robots["'][^>]+content=["']noindex,follow["']/i);
}

// Centralized registered-name presentation remains available to every renderer.
assert.equal(DIName.displayRegisteredName("  COWBOY   LUCKY LUCK DI ALTOBELLO "), "Cowboy Lucky Luck di Altobello");

// Bloodline Network contract: normalize a tiny canonical tree and verify expansion depth.
const fixture = [
  { path:"S", canonicalId:"A", name:"Sire", gen:1 },
  { path:"D", canonicalId:"B", name:"Dam", gen:1 },
  { path:"SS", canonicalId:"C", name:"Sire sire", gen:2 },
  { path:"SD", canonicalId:"D", name:"Sire dam", gen:2 },
  { path:"DS", canonicalId:"E", name:"Dam sire", gen:2 },
  { path:"DD", canonicalId:"F", name:"Dam dam", gen:2 },
];
const normalized = DIBloodline.normalizeNodes(fixture, 4);
assert.equal(normalized.find(node => node.path === "S").name, "Sire");
assert.equal(normalized.find(node => node.path === "DD").canonicalId, "F");
const expandable = DIBloodline.allExpandablePaths(normalized);
assert.ok(expandable.includes("S"));
assert.ok(expandable.includes("D"));
const visible = DIBloodline.visibleTree(normalized, new Set(["S", "D"]), 4);
assert.ok(visible.nodes.some(node => node.path === "SS"));
assert.ok(visible.nodes.some(node => node.path === "DD"));

console.log("Public UI integration PASS (accepted portal + V27 folder profiles + Bloodline Network)");
