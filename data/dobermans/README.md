# Doberman records

Place reviewed canonical `DI-M-xxxxxx.json` and `DI-F-xxxxxx.json` files here. Every file occupies its ID regardless of draft, pending-review or published status; only published records enter `registry.json`.

Canonical v1.1 records keep age in `identity.life_stage` and living/deceased state in `identity.life_status`. Run `python scripts/migrate_lifecycle_v1_1.py` before rebuilding the registry when older records are added.
