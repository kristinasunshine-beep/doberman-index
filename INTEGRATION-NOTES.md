# Breed Intelligence integration notes — 2026-09-18

## Source-of-truth order

1. Current production `main` repository: infrastructure, canonical data, schemas, lifecycle, SEO, litter system, submission flow and GitHub Actions.
2. Accepted Breed Intelligence handoff/prototypes: current Index, About, Male V27, Female V27, Kennel and Puppy presentation/product surfaces.
3. Legacy flat Male/Female pages: compatibility redirects only.

## Route model

- `profile.html?id=DI-ID` remains the lifecycle-aware public router.
- Adult male records route to `profiles/male/?id=DI-M-######`.
- Adult female records route to `profiles/female/?id=DI-F-######`.
- Puppies, kennels and litters continue through their approved shared templates.
- `records/DI-ID/` remains the canonical crawlable SEO surface.
- Root `male.html`, `female.html`, `kennel.html`, `puppy.html` pages are registry-backed category directories used by the accepted portal and are `noindex,follow`.

## Bloodline Network

- `data/pedigree-graph.json`: canonical pedigree nodes and parent relationships.
- `data/bloodline-images.json`: explicit ancestor image state (`selected` or `missing`) plus provenance for selected images.
- `profiles/male/assets/bloodline-network_v23.*` and `profiles/female/assets/bloodline-network_v23.*`: accepted V27 presentation/runtime.
- `scripts/validate_bloodline_network.py`: CI contract covering canonical nodes, repeated ancestry, image provenance and V27 integration.

## Compatibility and SEO

The old `profiles/male.html` and `profiles/female.html` URLs redirect to the new folder templates while preserving query/hash state. Shared digital cards and compatibility routes are `noindex,follow`, preventing duplicate competition with generated canonical record pages.

## Integration-only fixes

The accepted visible product was preserved. Technical fixes were limited to repository integration: correct repo-root resolution from folder templates, functional female `DI-F` hydration guards, hidden lifecycle target restoration, category/search routing, canonical graph files and updated CI contracts.
## IndexNow publisher

- `scripts/indexnow.py` is the single source of IndexNow publishing logic.
- `scripts/test_indexnow.py` provides an offline smoke test for canonical URL mapping and key-file validation.
- `.github/workflows/indexnow.yml` runs only after a successful Pages deployment (or manually), tests the publisher, and then calls the script. It contains no duplicate inline IndexNow implementation.
- Automatic deploy runs submit only canonical URLs affected by the deployed commit; manual runs submit the current sitemap.


## Dodo commerce boundary — 2026-09-22

- Dodo Payments is the only launch commerce provider.
- Public launch products: Doberman Intelligence Record (€149 one time) and Kennel Promotion Service (€149 / 12 months).
- The static site never stores API keys or webhook secrets.
- Frontend checkout requests go to the commerce Worker, which creates a fresh single-use Dodo Checkout Session.
- Successful payment is verified server-side before fulfillment guidance is shown.
- Intelligence Record fulfillment opens the existing reviewed owner-submission flow.
- Kennel Promotion uses the existing DI-K record when available; a kennel submission is only needed when the public kennel record is missing.
- Founding Network waivers remain invite-only and do not change the public €149 value anchor.
