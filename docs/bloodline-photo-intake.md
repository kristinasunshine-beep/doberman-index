# Bloodline photo intake — Dante + Cowboy Lucky Luck

Updated: 2026-09-29

## Purpose

Operational queue for missing stance photos in the 4-generation Bloodline Network used by:

- DI-M-000001 — Dion Dante
- DI-M-000002 — Cowboy Lucky Luck di Altobello

A dog is listed here only when the active Bloodline renderer currently has no usable bound image from either:
1. `data/bloodline-photo-bindings.json`, or
2. a selected/suggested image in `data/bloodline-images.json`.

## Intake workflow

For each missing dog, send in chat:

1. the source page URL where the image was found;
2. the actual image as a chat attachment.

Do not rely on the remote image URL itself as the production asset.

Second-step processing:
- verify that the attached image matches the named dog;
- crop only empty margins if useful — never crop body parts from a stance;
- preserve the entire dog and stance geometry;
- correct orientation if needed;
- resize to a storage-efficient master suitable for the Bloodline viewer;
- encode/compress for R2 without visible quality loss;
- use a stable ancestor path;
- update the photo binding and source URL;
- test on both profiles where the ancestor is shared.

Preferred production target pattern:
`ancestors/<DI ancestor ID>/main.webp`
(or `main.jpg` when JPEG is materially smaller/better for the source).

## Missing stance-photo queue

| Priority | Ancestor ID | Dog | Registration | Dante | Cowboy | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | DI-A-000008 | Birbakira di Villa Conte | ROI 07/57679 | Gen 3 | Gen 2 | AWAITING URL + IMAGE |
| 2 | DI-A-000010 | Zulu Lady di Altobello | JR 701225 Dob | Gen 3 | Gen 2 | AWAITING URL + IMAGE |
| 3 | DI-A-000002 | Felicita Flair von Ashanti Legende | JR 713394 Dob | Gen 1 | — | AWAITING URL + IMAGE |
| 4 | DI-A-000036 | Regal di Villa Conte | DS 156252 | — | Gen 4 | AWAITING URL + IMAGE |

## Important audit notes

- **Freya Fleming di Altobello (DI-A-000004) is not actually missing in the active renderer.** The legacy image manifest says `missing`, but an existing local binding points to `profiles/male/assets/bloodline-submitted/freya-fleming-di-altobello.webp`, so she is already displayable.
- **Tahi-Reme Triniti (DI-A-000026)** and **Come As You Are della Baronessa (DI-A-000029)** are currently visible but still depend on external hotlinked image URLs. They are not part of the missing queue; after the four gaps above are filled, they should be migrated to R2 for long-term stability.

## Source log template

When a new image arrives, update the row/status and record:

- Ancestor ID:
- Registered name:
- Source page URL:
- Attachment received: yes/no
- Match checked: yes/no
- Original dimensions:
- Optimized dimensions:
- Output format:
- Output file size:
- R2 object path:
- Binding updated: yes/no
- Dante checked: yes/no / n-a
- Cowboy checked: yes/no / n-a
