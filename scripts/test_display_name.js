"use strict";

const assert = require("node:assert/strict");
const { displayRegisteredName } = require("../assets/js/display-name.js");

const cases = new Map([
  ["DION DANTE", "Dion Dante"],
  ["Dion Dante", "Dion Dante"],
  ["dion dante", "Dion Dante"],
  ["DANTE VOM HAUSE X", "Dante vom Hause X"],
  ["ARON VON DER BURG", "Aron von der Burg"],
  ["MAX DE GRANDE VINKO", "Max de Grande Vinko"],
  ["ŽIVA DI CASA", "Živa di Casa"],
  ["DANTE IGP3", "Dante IGP3"],
  ["DANTE A-12", "Dante A-12"],
]);

for (const [input, expected] of cases) assert.equal(displayRegisteredName(input), expected, input);

const canonical = { registered_name: "DION DANTE" };
assert.equal(displayRegisteredName(canonical.registered_name), "Dion Dante");
assert.equal(canonical.registered_name, "DION DANTE", "canonical official name must remain unchanged");
console.log(`Registered-name display normalization PASS (${cases.size} cases; canonical preserved)`);
