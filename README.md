# DOBERMAN INDEX — GITHUB READY · v6.3 FINAL · 2026-09-06

This folder is the complete public web root. Copy its contents—not the enclosing `public` folder—into the root of the Doberman Index GitHub Pages repository.

## Included public system

- data-driven portal search and curated Explore the Index examples;
- final About page;
- male and female digital-card templates;
- data-complete puppy-card prototype;
- final kennel profile with connected-record panels, kennel archive and configured profile actions;
- canonical record schema, public registry builder and validation scripts;
- reviewed owner-submission interface and media rules.

## Primary routes

- `index.html`
- `about.html`
- `profile.html?id=DI-M-000001`
- `profiles/male.html?id=DI-M-000001`
- `profiles/female.html?id=DI-F-…`
- `profiles/kennel-concept.html?id=DI-K-000001`
- `profiles/puppy.html`
- `submit.html`

Kennel Archive links use `view=gallery#gallery-movement` so the destination opens only the indexed Doberman's Gallery & Movement surface. Regular registry links continue to open the complete profile.

## Data workflow

1. Review the private submission outside this repository.
2. Reserve the next DI number with `scripts/assign_id.py` and a private reservation ledger.
3. Create or update the canonical JSON record under `data/`.
4. Place approved public media under `media/`.
5. Run the validators and rebuild `data/registry.json`.
6. Publish only after the complete checks pass.

Do not invent missing values. Unconfirmed public fields remain null or use the interface's approved neutral unavailable state.

## Privacy rule

Never upload owner submission ZIPs, private contact data, completed questionnaires, reservation ledgers, internal admin notes or unapproved source files to this repository.


## v6.3 lifecycle automation

Doberman records keep one permanent sex-coded DI ID for life. There is no public DI-P ID namespace.
Age presentation is automatic from `date_of_birth` using `data/lifecycle-policy.json`: puppy before 9 months, junior from 9 to before 18 months, adult from 18 months, veteran from 8 years. The puppy visual template is used only while the effective stage is `puppy`; after that the record routes to its male/female card without changing its ID. The browser derives the effective stage immediately, and GitHub Actions synchronizes canonical JSON plus litter `available_puppy_ids` daily.

Movement video is 3–15 seconds. The owner submission UI now validates the actual selected video duration and records the measured duration in the draft JSON.
