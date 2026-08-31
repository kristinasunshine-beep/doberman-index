"use strict";

const assert = require("node:assert/strict");
const { displayRegisteredName, displayKennelName } = require("../assets/js/display-name.js");

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
  ["COWBOY LUCKY LUCK DI ALTOBELLO", "Cowboy Lucky Luck di Altobello"],
  ["FELICITA FLAIR VON ASHANTI LEGENDE", "Felicita Flair von Ashanti Legende"],
  ["CASA DI ROMA", "Casa di Roma"],
  ["VON EXAMPLE", "Von Example"],
  ["DE LA TORRE", "De la Torre"],
  ["McExample von Ashanti", "McExample von Ashanti"],
  ["Dion DANTE", "Dion DANTE"],
  ["iDante di ROMA", "iDante di ROMA"],
  ["EXAMPLE VON VOM VAN DE DEL DI DA DER DEN OF THE LA LE", "Example von vom van de del di da der den of the la le"],
]);

for (const [input, expected] of cases) assert.equal(displayRegisteredName(input), expected, input);

const canonical = { registered_name: "DION DANTE" };
assert.equal(displayRegisteredName(canonical.registered_name), "Dion Dante");
assert.equal(canonical.registered_name, "DION DANTE", "canonical official name must remain unchanged");
console.log(`Registered-name display normalization PASS (${cases.size} cases; canonical preserved)`);

const kennels = new Map([
  ["SIEMPRE PELIGROSO", "Siempre Peligroso"],
  ["VON EXAMPLE", "Von Example"],
  ["CASA DI ROMA", "Casa di Roma"],
  ["EXAMPLE VON VOM VAN DE DEL DI DA DER DEN OF THE LA LE", "Example von vom van de del di da der den of the la le"],
  ["Siempre Peligroso", "Siempre Peligroso"],
  ["McExample Dobermans", "McExample Dobermans"],
  ["Casa di ROMA", "Casa di ROMA"],
  ["iDoberman", "iDoberman"],
  ["ŽIVA DI CASA", "Živa di Casa"],
  ["FCI VOM HAUSE X", "FCI vom Hause X"],
  ["VON-EXAMPLE", "Von-Example"],
  ["123", "123"],
  [null, ""],
]);
for (const [input, expected] of kennels) assert.equal(displayKennelName(input), expected, input);
const identity = Object.freeze({ kennel_name: "SIEMPRE PELIGROSO" });
assert.equal(displayKennelName(identity.kennel_name), "Siempre Peligroso");
assert.equal(identity.kennel_name, "SIEMPRE PELIGROSO");
console.log(`Kennel display normalization PASS (${kennels.size} cases; canonical preserved)`);
