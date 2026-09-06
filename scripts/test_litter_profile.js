const assert = require("node:assert/strict");
const litterProfile = require("../assets/js/litter-profile.js");

const registry = {
  records: [
    {record_id:"DI-K-000101",entity_type:"kennel",status:"published",name:"North Star"},
    {record_id:"DI-M-000201",entity_type:"doberman",status:"published",registered_name:"SIRE ONE",hero:"media/dobermans/DI-M-000201/hero.webp"},
    {record_id:"DI-F-000202",entity_type:"doberman",status:"published",registered_name:"DAM ONE"},
    {record_id:"DI-M-000301",entity_type:"doberman",status:"published",registered_name:"PUPPY ONE",life_stage:"puppy"},
    {record_id:"DI-F-000302",entity_type:"doberman",status:"published",registered_name:"PUPPY TWO",life_stage:"junior"},
    {record_id:"DI-F-000399",entity_type:"doberman",status:"draft",registered_name:"PRIVATE DRAFT"}
  ]
};

const born = litterProfile.buildModel({
  record_id:"DI-L-000001",
  entity_type:"litter",
  status:"published",
  updated_at:"2026-09-06T00:00:00Z",
  litter:{
    name:"A litter",
    kennel_id:"DI-K-000101",
    sire_id:"DI-M-000201",
    dam_id:"DI-F-000202",
    date_of_birth:"2026-02-15",
    planned_date:null,
    status:"open",
    puppy_ids:["DI-M-000301","DI-F-000302","DI-F-000399"],
    available_puppy_ids:["DI-M-000301","DI-F-000399"],
    media:{cover:"media/litters/DI-L-000001/cover.webp",gallery:[]}
  }
}, registry, {doberman:value=>value.toLowerCase(),kennel:value=>value.toUpperCase()});

assert.equal(born.name,"A litter");
assert.equal(born.litter_status_label,"Open");
assert.equal(born.date.label,"Date of birth");
assert.equal(born.date.value,"15 Feb 2026");
assert.equal(born.kennel.name,"NORTH STAR");
assert.equal(born.sire.name,"sire one");
assert.equal(born.dam.href,"../profile.html?id=DI-F-000202");
assert.equal(born.puppy_count,3);
assert.equal(born.available_count,1,"draft puppy records must not become public availability links");
assert.equal(born.puppies[1].life_stage,"junior");
assert.equal(born.puppies[2].linked,false);

const planned = litterProfile.buildModel({
  record_id:"DI-L-000002",
  entity_type:"litter",
  status:"published",
  litter:{name:null,kennel_id:null,sire_id:null,dam_id:null,date_of_birth:null,planned_date:"2027-05-01",status:"planned",puppy_ids:[],available_puppy_ids:[],media:{cover:null,gallery:[]}}
}, []);

assert.equal(planned.name,"Litter DI-L-000002");
assert.equal(planned.date.label,"Planned date");
assert.equal(planned.litter_status_label,"Planned litter");
assert.equal(planned.sire.name,"Not linked");
assert.equal(planned.kennel.linked,false);
assert.deepEqual(planned.puppies,[]);

assert.throws(()=>litterProfile.buildModel({record_id:"DI-P-000001",entity_type:"litter",litter:{}},[]),/Invalid litter record/);
assert.equal(litterProfile.profileHref("DI-L-000001"),"../profile.html?id=DI-L-000001");

console.log("Public litter model PASS (planned/born states, published links, permanent puppy IDs and availability)");
