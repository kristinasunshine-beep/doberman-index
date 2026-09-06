# Litter records

Place reviewed canonical `DI-L-xxxxxx.json` files here. Draft and pending-review files still occupy their IDs but do not enter the live registry.

Every litter block carries its designation, optional kennel/sire/dam links, date of birth or planned date, editorial/business status, permanent `puppy_ids`, current `available_puppy_ids` and public media. Unknown relationships use `null`; an empty puppy list uses `[]`.

- `puppy_ids` is permanent history and accepts only `DI-M-######` / `DI-F-######` IDs.
- `available_puppy_ids` must be a subset of `puppy_ids`.
- the lifecycle job prunes availability but never changes the litter status;
- no puppy receives a separate temporary namespace.

Run `python scripts/build_registry.py` after a record is approved, then run the full QA workflow before publication.
