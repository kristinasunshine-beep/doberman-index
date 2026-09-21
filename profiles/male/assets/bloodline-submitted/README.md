# Bloodline photo workflow

This is the simple manual-photo path for the male Bloodline Network.

1. Put the supplied image in:
   `profiles/male/assets/bloodline-submitted/`

2. Add one entry to:
   `data/bloodline-photo-bindings.json`

Example:

```json
"DI-A-000004": {
  "asset_path": "profiles/male/assets/bloodline-submitted/freya-fleming-di-altobello.jpg",
  "label": "Submitted stance photo"
}
```

That is all.

The profile loads `bloodline-photo-bindings.json` at runtime and these manual bindings take priority over the older `bloodline-images.json` sources. No HTML snapshot edit, cache-bust suffix, or Bloodline JS edit is needed for a normal photo replacement.

When a new photo is provided in chat, use the ancestor's canonical ID from `data/pedigree-graph.json`, save the photo in the folder above, and update one JSON entry.
