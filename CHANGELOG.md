# Changelog

## v6.5 COMPREHENSIVE SEO — 2026-09-06

- Added registry-generated clean canonical pages at `records/DI-ID/` for every published Doberman, kennel and litter record.
- Preserved the complete `profile.html?id=DI-ID` digital-card route as a backward-compatible `noindex,follow` experience.
- Added unique titles, descriptions, canonicals, Open Graph, Twitter card metadata and semantically conservative Schema.org JSON-LD.
- Added a published-record directory, bidirectional relationship links and breadcrumb navigation.
- Added registry-driven `sitemap.xml`, crawl controls in `robots.txt` and automatic rebuilds in GitHub Actions.
- Added metadata runtime support for shared card templates without depending on JavaScript for the indexable canonical pages.
- Added comprehensive SEO, internal-link, structured-data, accessibility-markup and performance checks.
- Kept the approved Submission HTML/CSS/JS master byte-for-byte locked and excluded its utility route from crawling and the sitemap.
- Preserved the approved About body, Male visual master, Dante canonical content/media, Litter lifecycle contract and `CNAME`.

## v6.4 LITTERS FOUNDATION — 2026-09-06

- Added the public `profiles/litter.html` renderer for canonical `DI-L-######` records.
- Connected the profile router to the Litter page only after the renderer existed.
- Added Litter-to-kennel, Litter-to-parent and Litter-to-offspring public navigation.
- Added Doberman, Puppy and Kennel links back to published Litter records.
- Expanded the public registry projection with planned date, editorial status, litter status, permanent puppy IDs, current availability and cover media.
- Updated the schema for planned litters, unknown relationships, empty offspring states and permanent sex-coded puppy IDs.
- Tightened daily lifecycle synchronization so `available_puppy_ids` contains only published, under-9-month records explicitly marked available.
- Preserved `puppy_ids` history and prevented lifecycle automation from changing litter status.
- Added Node and Python Litter system tests and wired them into GitHub Actions.
