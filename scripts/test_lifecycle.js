"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "assets/js/lifecycle.js"), "utf8");
const context = { window: {}, Date, console };
vm.runInNewContext(source, context);
const L = context.window.DILifecycle;
const policy = { puppy_until_months: 9, junior_until_months: 18, veteran_from_years: 8 };
const at = iso => new Date(`${iso}T00:00:00Z`);
const base = Object.freeze({
  record_id: "DI-F-009999", entity_type: "doberman", sex: "female",
  life_status: "living", life_stage: "puppy", date_of_birth: "2026-01-31",
  template: "puppy", lifecycle_mode: "automatic"
});
const before = JSON.stringify(base);
assert.equal(L.stageFor(base, policy, at("2026-10-30")), "puppy");
assert.equal(L.templateFor(base, policy, at("2026-10-30")), "puppy");
assert.equal(L.stageFor(base, policy, at("2026-10-31")), "junior");
assert.equal(L.templateFor(base, policy, at("2026-10-31")), "female");
assert.equal(L.stageFor(base, policy, at("2027-07-31")), "adult");
assert.equal(L.templateFor(base, policy, at("2027-07-31")), "female");
assert.equal(L.stageFor(base, policy, at("2034-01-31")), "veteran");
const manual = { ...base, lifecycle_mode: "manual", life_stage: "puppy", template: "puppy" };
assert.equal(L.stageFor(manual, policy, at("2034-01-31")), "puppy");
assert.equal(L.templateFor(manual, policy, at("2034-01-31")), "puppy");
const deceased = { ...base, life_status: "deceased", life_stage: "adult", template: "female" };
assert.equal(L.stageFor(deceased, policy, at("2034-01-31")), "adult");
assert.equal(L.templateFor(deceased, policy, at("2034-01-31")), "female");
assert.equal(JSON.stringify(base), before, "Lifecycle renderer must not mutate registry input");
console.log("Lifecycle browser contract PASS (puppy→junior card switch, adult/veteran stages, manual/deceased preservation)");
