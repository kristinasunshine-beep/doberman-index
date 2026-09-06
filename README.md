# DOBERMAN INDEX — GITHUB READY · v6.5 COMPREHENSIVE SEO · 2026-09-06

This folder is the complete public web root. Copy its contents—not the enclosing `public` folder—into the root of the Doberman Index GitHub Pages repository.

## Included public system

- data-driven portal search and curated Explore the Index examples;
- final About page;
- male and female digital-card templates;
- data-complete puppy-card prototype;
- final kennel profile with connected-record panels, kennel archive and configured profile actions;
- public DI-L litter digital card with kennel, parent, offspring, availability and media connections;
- one generated clean canonical page under `records/DI-ID/` for every published registry record;
- registry-driven sitemap, unique metadata, Open Graph/Twitter cards and conservative Schema.org JSON-LD;
- canonical record schema, public registry builder and validation scripts;
- reviewed owner-submission interface and media rules.

## Primary routes

- `index.html`
- `about.html`
- `profile.html?id=DI-M-000001`
- `records/DI-M-000001/` (crawlable canonical summary)
- `profiles/male.html?id=DI-M-000001`
- `profiles/female.html?id=DI-F-…`
- `profiles/kennel-concept.html?id=DI-K-000001`
- `profiles/puppy.html`
- `profile.html?id=DI-L-######`
- `profiles/litter.html?id=DI-L-######`
- `submit.html`

Kennel Archive links use `view=gallery#gallery-movement` so the destination opens only the indexed Doberman's Gallery & Movement surface. Regular registry links continue to open the complete profile.

## Data workflow

1. Review the private submission outside this repository.
2. Reserve the next DI number with `scripts/assign_id.py` and a private reservation ledger.
3. Create or update the canonical JSON record under `data/`.
4. Place approved public media under `media/`.
5. Run the validators and rebuild `data/registry.json`, `data/seo-manifest.json`, `records/` and `sitemap.xml`.
6. Publish only after the complete checks pass.

Do not invent missing values. Unconfirmed public fields remain null or use the interface's approved neutral unavailable state.

## Privacy rule

Never upload owner submission ZIPs, private contact data, completed questionnaires, reservation ledgers, internal admin notes or unapproved source files to this repository.


## v6.3 lifecycle automation

Doberman records keep one permanent sex-coded DI ID for life. There is no public DI-P ID namespace.
Age presentation is automatic from `date_of_birth` using `data/lifecycle-policy.json`: puppy before 9 months, junior from 9 to before 18 months, adult from 18 months, veteran from 8 years. The puppy visual template is used only while the effective stage is `puppy`; after that the record routes to its male/female card without changing its ID. The browser derives the effective stage immediately, and GitHub Actions synchronizes canonical JSON plus litter `available_puppy_ids` daily.

Movement video is 3–15 seconds. The owner submission UI now validates the actual selected video duration and records the measured duration in the draft JSON.

## v6.4 litter foundation

Canonical litter records use permanent `DI-L-######` IDs. Their `puppy_ids` array is the permanent historical offspring list and accepts only `DI-M-######` / `DI-F-######` records. `available_puppy_ids` is a current subset: the daily lifecycle job removes records that are no longer published, no longer marked available or have reached the 9-month Puppy cutoff. The job never changes the litter's editorial/business status.

No sample litter has been invented in this package. The new public renderer becomes live automatically when an editorially reviewed `data/litters/DI-L-######.json` record is published and the registry is rebuilt.

## v6.5 comprehensive SEO

Every published record receives a server-delivered, crawlable clean URL at `records/DI-ID/`. The complete digital card remains available at `profile.html?id=DI-ID`; this compatibility route and the shared renderer templates are `noindex,follow` so they cannot compete with the clean canonical page. The owner-submission master remains byte-for-byte locked and is excluded from crawling and the sitemap.

Run `python scripts/build_registry.py` and then `python scripts/build_seo.py` after approved public data changes. GitHub Actions performs both steps automatically on relevant pushes and during the daily lifecycle synchronization. The SEO validator fails when any published record lacks its canonical page, unique title/description, canonical, social metadata, supported JSON-LD, semantic main/H1 or expected internal record links.

See `SEO-STRATEGY.md` for the URL, crawl and rollout contract.
