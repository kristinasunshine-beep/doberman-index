#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/bloodline-images.json"
BINDINGS = ROOT / "data/bloodline-photo-bindings.json"
GRAPH = ROOT / "data/pedigree-graph.json"
REPORT = ROOT / "data/bloodline-r2-migration-report.json"

WORKER = os.environ.get(
    "DI_MEDIA_ADMIN_BASE",
    "https://doberman-index-media-admin.dobermanindex-records.workers.dev",
).rstrip("/")
TOKEN = os.environ.get("MEDIA_ADMIN_KEY", "").strip()
PUBLIC_PREFIX = WORKER + "/ancestors/"
ALLOWED_INTERNAL = (
    "doberman-index.com",
    "doberman-index-media-admin.dobermanindex-records.workers.dev",
    "media.doberman-index.com",
)

try:
    from PIL import Image
except Exception as exc:
    raise SystemExit("Pillow is required: " + str(exc))


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_external(url: str) -> bool:
    if not str(url or "").startswith(("http://", "https://")):
        return False
    host = (urlparse(url).hostname or "").lower()
    return not any(host == h or host.endswith("." + h) for h in ALLOWED_INTERNAL)


def is_r2_internal(url: str) -> bool:
    return str(url or "").startswith(PUBLIC_PREFIX)


def clean_repo_path(value: str) -> str:
    return str(value or "").split("?", 1)[0].lstrip("/")


def fetch_external(url: str) -> bytes:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": f"{urlparse(url).scheme}://{urlparse(url).netloc}/",
    }
    last = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as response:
                data = response.read()
                ctype = (response.headers.get("content-type") or "").lower()
            if len(data) < 500:
                raise ValueError(f"response too small ({len(data)} bytes)")
            if "text/html" in ctype:
                raise ValueError("received HTML instead of image")
            return data
        except Exception as exc:
            last = exc
            time.sleep(1.25 * (attempt + 1))
    raise last


def normalize_jpeg(data: bytes) -> bytes:
    with Image.open(io.BytesIO(data)) as image:
        image = image.convert("RGB")
        max_side = 1800
        if max(image.size) > max_side:
            ratio = max_side / max(image.size)
            image = image.resize(
                (round(image.width * ratio), round(image.height * ratio)),
                Image.Resampling.LANCZOS,
            )
        out = io.BytesIO()
        image.save(out, "JPEG", quality=90, optimize=True, progressive=True)
        return out.getvalue()


def upload(key: str, data: bytes, name: str, source_url: str) -> None:
    if not TOKEN:
        raise RuntimeError("MEDIA_ADMIN_KEY is not configured")
    endpoint = f"{WORKER}/v1/admin/media/{key}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "image/jpeg",
        "X-DI-Registered-Name": name,
        "X-DI-Role": "bloodline_ancestor",
        "X-DI-Source-Url": source_url,
        "User-Agent": "Doberman-Index-R2-Migrator/2.0",
    }
    req = urllib.request.Request(endpoint, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=45) as response:
        body = response.read()
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"upload HTTP {response.status}: {body[:200]!r}")


def selected_for_roots(doc: dict, aid: str) -> list[tuple[str, dict, dict]]:
    found = []
    for root, record in (doc.get("records") or {}).items():
        item = (record.get("ancestors") or {}).get(aid)
        if not isinstance(item, dict):
            continue
        selected = item.get("selected") if item.get("status") == "selected" else None
        found.append((root, item, selected or {}))
    return found


def first_nonempty(values) -> str:
    for value in values:
        value = str(value or "").strip()
        if value:
            return value
    return ""


def main():
    doc = load_json(MANIFEST)
    bindings_doc = load_json(BINDINGS) if BINDINGS.is_file() else {}
    bindings = bindings_doc.get("photos") or {}
    graph = load_json(GRAPH)
    nodes = graph.get("nodes") or {}

    # Canonical ancestor IDs referenced anywhere in the image manifest.
    ancestor_ids = set()
    for record in (doc.get("records") or {}).values():
        ancestor_ids.update((record.get("ancestors") or {}).keys())

    report = {
        "attempted": 0,
        "migrated": [],
        "already_internal": [],
        "pending": [],
        "failed": [],
        "completed": False,
    }
    auth_failures = []

    for aid in sorted(ancestor_ids):
        roots = selected_for_roots(doc, aid)
        if not roots:
            continue

        selected_entries = [selected for _, _, selected in roots if selected]
        existing_urls = [
            str(selected.get("image_url") or "").strip()
            for selected in selected_entries
            if str(selected.get("image_url") or "").strip()
        ]

        # If every selected reference is already on our R2 media edge, leave it alone.
        if existing_urls and all(is_r2_internal(url) for url in existing_urls):
            report["already_internal"].append({"record_id": aid, "urls": sorted(set(existing_urls))})
            continue

        binding = bindings.get(aid) if isinstance(bindings.get(aid), dict) else {}
        binding_path = clean_repo_path(binding.get("asset_path"))
        local_file = ROOT / binding_path if binding_path else None

        source_url = first_nonempty(
            [binding.get("source_url")]
            + [selected.get("source_url") for selected in selected_entries]
        )
        source_label = first_nonempty(
            [binding.get("label")]
            + [selected.get("source_label") for selected in selected_entries]
            + ["Curated Bloodline source"]
        )
        external_url = first_nonempty(
            [
                selected.get("image_url")
                for selected in selected_entries
                if is_external(str(selected.get("image_url") or ""))
            ]
        )

        source_kind = ""
        raw = None

        # Priority 1: verified/manual local binding.
        if local_file and local_file.is_file():
            if not source_url:
                report["pending"].append(
                    {
                        "record_id": aid,
                        "reason": "local binding exists but source provenance URL is missing",
                        "asset_path": binding_path,
                    }
                )
                print(f"[{aid}] local binding pending provenance")
                continue
            raw = local_file.read_bytes()
            source_kind = "local_binding"

        # Priority 2: currently selected repository-local image.
        if raw is None:
            for selected in selected_entries:
                local_path = clean_repo_path(selected.get("asset_path") or selected.get("image_url"))
                candidate = ROOT / local_path if local_path else None
                if candidate and candidate.is_file():
                    if not source_url:
                        report["pending"].append(
                            {
                                "record_id": aid,
                                "reason": "repository-local selected image is missing source provenance URL",
                                "asset_path": local_path,
                            }
                        )
                        print(f"[{aid}] repository-local image pending provenance")
                        candidate = None
                        break
                    raw = candidate.read_bytes()
                    source_kind = "repository_local"
                    break

        # Priority 3: legacy external URL. Failure is non-destructive.
        if raw is None and external_url:
            try:
                raw = fetch_external(external_url)
                source_kind = "external_fetch"
            except Exception as exc:
                report["failed"].append(
                    {
                        "record_id": aid,
                        "from": external_url,
                        "error": str(exc),
                        "preserved": True,
                    }
                )
                print(f"[{aid}] external fetch failed; existing manifest preserved: {exc}")
                continue

        if raw is None:
            # Missing entries and already-curated states without a transferable source are not errors.
            continue

        report["attempted"] += 1
        name = (nodes.get(aid) or {}).get("registered_name", aid)
        print(f"[{aid}] {name} <- {source_kind}")

        try:
            jpg = normalize_jpeg(raw)
            key = f"ancestors/{aid}/main.jpg"
            upload(key, jpg, name, source_url or external_url)
            internal_url = f"{PUBLIC_PREFIX}{aid}/main.jpg"

            # Mirror the one canonical R2 object to every root that references this ancestor.
            for root, item, old_selected in roots:
                prior = dict(old_selected)
                item["status"] = "selected"
                item["selected"] = {
                    "image_url": internal_url,
                    "source_label": source_label,
                    "source_url": source_url or external_url,
                }
                if binding_path:
                    item["selected"]["migrated_from_asset"] = binding_path
                elif prior.get("image_url"):
                    item["selected"]["migrated_from"] = prior.get("image_url")

            report["migrated"].append(
                {
                    "record_id": aid,
                    "name": name,
                    "source_kind": source_kind,
                    "from": binding_path or external_url,
                    "to": internal_url,
                    "bytes": len(jpg),
                }
            )
            print("  -> migrated")
        except Exception as exc:
            # Never destroy a known-good selected state because transport/upload failed.
            error_text = str(exc)
            report["failed"].append(
                {
                    "record_id": aid,
                    "from": binding_path or external_url,
                    "error": error_text,
                    "preserved": True,
                }
            )
            if "HTTP Error 401" in error_text or "Unauthorized" in error_text:
                auth_failures.append({"record_id": aid, "error": error_text})
            print(f"  -> upload/normalize failed; existing manifest preserved: {exc}")

    # Migration is complete only when no selected external or repository-local image remains.
    leftovers = []
    for root, record in (doc.get("records") or {}).items():
        for aid, item in (record.get("ancestors") or {}).items():
            if not isinstance(item, dict) or item.get("status") != "selected":
                continue
            selected = item.get("selected") or {}
            url = str(selected.get("image_url") or selected.get("asset_path") or "").strip()
            if url and not is_r2_internal(url):
                leftovers.append({"root": root, "record_id": aid, "image_ref": url})

    report["leftovers"] = leftovers
    report["completed"] = not leftovers and not report["failed"] and not report["pending"]

    MANIFEST.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    summary = {
        "attempted": report["attempted"],
        "migrated": len(report["migrated"]),
        "already_internal": len(report["already_internal"]),
        "pending": len(report["pending"]),
        "failed": len(report["failed"]),
        "leftovers": len(report["leftovers"]),
        "completed": report["completed"],
    }
    print(json.dumps(summary, indent=2))

    if auth_failures:
        raise SystemExit(
            "R2 AUTHENTICATION FAILURE: media-admin returned 401 Unauthorized. "
            "GitHub Actions MEDIA_ADMIN_KEY does not match the Worker production secret "
            "or the Cloudflare secret change has not been deployed."
        )


if __name__ == "__main__":
    main()
