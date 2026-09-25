# Doberman Index media architecture

## Scale target

Design target: at least 10,000 published Doberman records without storing the media library in GitHub Pages.

GitHub remains the source of code, schemas and small structured records. Binary media is stored in Cloudflare R2.

## Storage classes

### A. Private intake originals

Owner submissions already arrive through the secure intake service as a ZIP package.

Keep the original submission package private while the record is under review. It may contain:
- the high-resolution pedigree scan;
- up to 10 owner-selected photos;
- one movement video (3-15 seconds);
- health/evidence files;
- private contact data.

These files are never committed to the public GitHub repository.

Recommended lifecycle:
1. keep the complete private package during review;
2. publish only approved derivatives to the public media bucket;
3. after publication, retain the private source package only for the chosen recovery/evidence retention period.

### B. Public record media

Public media belongs in the public R2 media bucket under deterministic keys:

```
dogs/{RECORD_ID}/hero.jpg
dogs/{RECORD_ID}/head.jpg
dogs/{RECORD_ID}/profile.jpg
dogs/{RECORD_ID}/stack.jpg
dogs/{RECORD_ID}/movement.jpg
dogs/{RECORD_ID}/gallery/01.jpg
...
dogs/{RECORD_ID}/gallery/10.jpg
dogs/{RECORD_ID}/movement/main.mp4
```

The record JSON stores the public URL/key, not the binary file.

### C. Pedigree ancestor media

Ancestor photos are global assets and are never duplicated per descendant record.

```
ancestors/{ANCESTOR_ID}/main.jpg
```

Example:

```
ancestors/DI-A-000011/main.jpg
```

The canonical ancestor ID is the permanent media key. If the same ancestor appears in 500 pedigrees, all 500 positions resolve to the same object.

The selected internet source URL is retained as provenance metadata. A separate high-resolution archive copy is not required for ancestor photos.

## Human workflow

1. Submission received.
2. System extracts the 4-generation pedigree.
3. Human checks the extracted names.
4. Canonical ancestor IDs are resolved/created.
5. System checks which ancestor IDs already have media.
6. Only missing ancestor images enter the manual image queue.
7. Human selects the correct image and uploads it to the matching ancestor ID.
8. Selection itself is the human verification; there is no second VERIFY step.
9. When the object exists in R2, status becomes READY.

Suggested statuses:
- MISSING
- ADDED
- READY

## Owner gallery workflow

Owner media and ancestor media are separate.

The owner may submit:
- one required main photo;
- optional head/profile/stack/movement photos;
- additional gallery photos, with a maximum of 10 owner photos in total;
- one movement video, 3-15 seconds.

During admin review the owner media can be mapped/reordered into the public Gallery & Movement presentation.

## Public media domain

Recommended custom domain:

```
https://media.doberman-index.com
```

Public URLs are deterministic, for example:

```
https://media.doberman-index.com/ancestors/DI-A-000011/main.jpg
https://media.doberman-index.com/dogs/DI-M-000123/gallery/01.jpg
```

## Repository rule

Do not add new public binary media to the GitHub Pages repository after the R2 migration is enabled.

Existing Dante media can remain temporarily for backwards compatibility and be migrated separately.
