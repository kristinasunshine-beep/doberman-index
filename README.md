# DOBERMAN INDEX — PUBLIC GITHUB · v5.9.33 · 2026-08-31

Deployable public repository. Only this folder goes to the public GitHub repository.

## Portal
`index.html` is the approved data-driven portal. Search and Available Puppies read published records from `data/registry.json`; profile routing uses `profile.html?id=...`. The Male template is the only production-designed digital card at this release. Female, Puppy and Kennel are reserved registry routes and currently show the pending-design message.

## About
`about.html` keeps the accepted Forge/Mission design while using a professionally tightened editorial layer. The duplicate `Data, not opinion / Global standard / Real compatibility` section has been removed because the same operating principles already appear on the portal. `A registry. Built for clarity.` replaces the former verdict wording. Generic `animal/animals` wording has been removed in favour of breed-specific or kennel-specific language. Outside required brand/UI tokens, no content-bearing word appears more than twice; the About copy shares no four-, five- or six-word phrase, and no closely matching sentence, with the portal FAQ.

## Kennel promotion belt
`index.html` contains the paid kennel-logo belt immediately after **Explore the Index** and before **How it works**. Placements come from `data/promotion-belt.json`, use equal-size slots and a daily-rotated starting order, and the entire section stays hidden while there are no active placements. The commercial offer is one reviewed placement per kennel at **€149 per year**; no priority tier or paid ranking is supported.

Add approved transparent SVG, PNG or WebP logos under `media/kennels/<DI-K...>/`, then activate the matching dated entry in `data/promotion-belt.json`. `scripts/validate_promotion_belt.py` enforces the 24-placement limit, required local logo path, date term and approved destination format.

## Male digital card — current visual master
`profiles/male.html` is the live data-driven production version of the supplied `doberman-male-profile-forge-refined-v3` master. Its visual layer preserves the refined master, including:

- raised **Details** action in the yellow dossier;
- larger section descriptor after the numbered line;
- refined custom horizontal slider/rail controls;
- approved DCM dropdown;
- Gallery, Bloodline, Health, Structural Profile, Temperament, Performance, Stud Impact, Related, Pairing and Services section structures.
- Details prikazuje odvojene podatke `Life stage` i `Life status`; deceased zapis dodatno prikazuje `Life span`, dok se `Stud service status` automatski uklanja. Diskretna oznaka uz DI broj koristi format `DECEASED · 2014–2026`. Stud Impact ostaje ograničen na četiri postojeće metrike i čuva istorijske podatke.

Production-only differences are limited to canonical data binding, routing, empty states and movement-video support.

Registered Doberman names use a shared display-only normalizer across Portal, profile routing and the Male card. Canonical `registered_name` values remain unchanged. Known working/sport acronyms, Roman numerals and meaningful mixed alphanumeric tokens are preserved; linked indexed Dobermans receive the same display treatment, while unlinked pedigree text remains untouched.

Public hero and primary-role photographs read optional percentage focal points from canonical media metadata and apply them through `object-position`, with a backward-compatible 50/50 fallback. Hero, Head and Stack use 4:5 portrait presentation; Movement uses 3:2 landscape. Each additional Gallery item uses a 4:5 portrait frame and may be either a legacy string path or an object carrying `path`, `focal_point` and `fit_mode` (`cover` or `contain`). Legacy strings render with a 50/50 + `cover` fallback. Gallery accepts 0–10 items; 11 is rejected by schema validation. The approved horizontal Gallery & Movement rail is unchanged.

`scripts/validate_male_visual_master.py` protects these decisions in CI together with `validate_male_profile_contract.py`.

## Owner submission
`submit.html` is the five-step owner wizard. Structure and Temperament use controlled values only. Images accept JPG/JPEG, PNG or WebP up to 20 MB each; PDF evidence up to 25 MB each; MP4/MOV video up to 180 MB; the complete package is capped at 250 MB.

The exact v5.9.21 `submit.html` together with its `assets/css/submit-v3.css` is the locked Submission visual master. Typography, colours, spacing, step layout, field styling, upload surfaces and review presentation must not be redesigned. Lifecycle and canonical data-contract work is limited to fields and runtime logic.

Lifecycle is split into two fields: `life_stage` (`puppy`, `junior`, `adult`, `veteran`, `unknown`) and `life_status` (`living`, `deceased`, `unknown`). A deceased record keeps its Male, Female or Puppy registry classification and permanent DI number; only Male currently has an approved production card. Reproduction and puppy availability are forced to `not_applicable`; public cause-of-death evidence appears only when disclosure is explicitly set to `public`.

## Registry automation
`scripts/migrate_lifecycle_v1_1.py` converts legacy `life_stage: deceased` records without guessing their age or assuming that unconfirmed records are living. `scripts/build_registry.py` rebuilds `data/registry.json` from published canonical records. GitHub Actions validates lifecycle, controlled assessment, male profile, homepage showcase and kennel-promotion contracts before committing a rebuilt registry.

The targeted production validator accepts empty, first-record and multi-record production states. It requires an exact match between published canonical IDs in `data/dobermans`, `data/kennels`, `data/litters` and registry IDs. Missing, stale and duplicate IDs fail. `scripts/test_registry_consistency.py` protects these cases in the same workflow; no validator requires an empty registry.

## Privacy
Never upload owner submission ZIPs, private contact data, completed questionnaires, reservation ledgers or internal admin notes to this public repository.
