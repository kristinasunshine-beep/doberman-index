# Doberman Index SEO contract · v6.5

## Public URL model

- `https://doberman-index.com/records/DI-ID/` is the crawlable canonical summary for each published record.
- `profile.html?id=DI-ID` remains the complete backward-compatible digital card.
- Shared profile renderers and prototypes use `noindex,follow`; they are not included in the sitemap.
- The byte-locked owner-submission utility route is disallowed in `robots.txt` and omitted from the sitemap.
- A future published `DI-L-######` record receives the same clean URL automatically after the registry and SEO build run.

This split is deliberate for GitHub Pages: crawlers receive unique titles, descriptions, canonicals and JSON-LD directly in static HTML, without requiring JavaScript to discover record metadata.

## Generated surfaces

`scripts/build_seo.py` reads only published entries from `data/registry.json` and generates:

- `records/index.html`;
- one `records/DI-ID/index.html` file per published record;
- `data/seo-manifest.json` for the compatibility-page metadata runtime;
- `sitemap.xml` with clean canonical URLs only.

The generator removes only stale record directories whose names match the official DI record-ID pattern. Technical data, scripts, schemas, work areas, documentation and the locked submission utility are excluded through `robots.txt`.

## Metadata and structured data

Every crawlable page has one unique title, description and canonical, plus Open Graph and Twitter metadata. Record JSON-LD uses conservative Schema.org vocabulary: `WebSite`, `WebPage` or `CollectionPage`, `Thing` for dogs/litters, `Organization` for kennels, `PropertyValue`, `ImageObject` and `BreadcrumbList`. It does not claim ratings, reviews or unsupported rich-result eligibility.

## Internal graph

Clean pages link only to other published canonical records. Relationships are derived from kennel, sire, dam, litter and offspring IDs. Every page also links to the public records directory and its complete compatibility card.

## Release and monitoring

The GitHub workflow rebuilds lifecycle data, registry and SEO surfaces, then fails on missing or stale pages, duplicate metadata, invalid canonical URLs, unsupported structured data, missing semantic landmarks/alt attributes, broken expected relationship links or performance-policy regressions.

After deployment, the site owner should submit `https://doberman-index.com/sitemap.xml` in Google Search Console, inspect representative URLs and monitor indexing reports. Search Console access and site verification are external editorial/ownership steps and are not embedded in the public package.
