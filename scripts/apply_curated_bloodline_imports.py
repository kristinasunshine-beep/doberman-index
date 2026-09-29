#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import os
import re
import time
import html as html_lib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
import urllib.request

from PIL import Image, ImageOps, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "data/bloodline-curated-imports.json"
MANIFEST = ROOT / "data/bloodline-images.json"
BINDINGS = ROOT / "data/bloodline-photo-bindings.json"
GRAPH = ROOT / "data/pedigree-graph.json"
REPORT = ROOT / "data/bloodline-curated-import-report.json"

WORKER = os.environ.get(
    "DI_MEDIA_ADMIN_BASE",
    "https://doberman-index-media-admin.dobermanindex-records.workers.dev",
).rstrip("/")
TOKEN = os.environ.get("MEDIA_ADMIN_KEY", "").strip()
PUBLIC_PREFIX = WORKER + "/ancestors/"
MAX_OUTPUT = 350 * 1024
MATCH_THRESHOLD = 18

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136 Safari/537.36"

def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def save_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

class ImageCollector(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.urls = []
    def add(self, value: str):
        if not value:
            return
        value = html_lib.unescape(value.strip())
        if value.startswith(("data:", "javascript:", "#")):
            return
        u = urljoin(self.base_url, value)
        if u.startswith(("http://", "https://")) and u not in self.urls:
            self.urls.append(u)
    def handle_starttag(self, tag, attrs):
        d = {k.lower(): v for k, v in attrs if k and v}
        if tag.lower() in {"img","source"}:
            for key in ("src","data-src","data-original","data-lazy-src","data-image","data-large-file","data-medium-file"):
                self.add(d.get(key,""))
            for key in ("srcset","data-srcset"):
                for part in d.get(key,"").split(","):
                    self.add(part.strip().split(" ")[0])
        if tag.lower() == "meta":
            prop = (d.get("property") or d.get("name") or "").lower()
            if prop in {"og:image","og:image:url","twitter:image","twitter:image:src"}:
                self.add(d.get("content",""))
        if tag.lower() == "a":
            href = d.get("href","")
            if re.search(r"\.(?:jpe?g|png|webp)(?:\?|$)", href, re.I):
                self.add(href)
        style = d.get("style","")
        for m in re.findall(r"url\(['\"]?([^)'\"]+)", style, re.I):
            self.add(m)

def request_bytes(url: str, referer: str | None = None, timeout: int = 30) -> tuple[bytes, str]:
    headers = {
        "User-Agent": UA,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8" if re.search(r"\.(?:jpe?g|png|webp)(?:\?|$)", url, re.I) else "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "no-cache",
    }
    if referer:
        headers["Referer"] = referer
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read(), (response.headers.get("content-type") or "").lower()

def dhash_int(image: Image.Image, hash_size: int = 8) -> int:
    image = ImageOps.exif_transpose(image).convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    px = list(image.getdata())
    v = 0
    for y in range(hash_size):
        row = px[y*(hash_size+1):(y+1)*(hash_size+1)]
        for x in range(hash_size):
            v = (v << 1) | int(row[x] > row[x+1])
    return v

def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()

def decode_image(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data))
    image.load()
    return ImageOps.exif_transpose(image).convert("RGB")

def collect_candidates(item: dict) -> list[str]:
    source = item["source_url"]
    urls = []
    for u in item.get("direct_candidates") or []:
        if u and u not in urls:
            urls.append(u)
    page, ctype = request_bytes(source)
    if "html" not in ctype and not source.lower().endswith((".jpg",".jpeg",".png",".webp")):
        raise RuntimeError(f"source page did not return HTML ({ctype})")
    if "html" not in ctype:
        urls.append(source)
        return urls
    text = page.decode("utf-8", "ignore")
    parser = ImageCollector(source)
    parser.feed(text)
    for u in parser.urls:
        if u not in urls:
            urls.append(u)
    # Also catch image URLs embedded inside JSON/script payloads.
    for raw in re.findall(r'https?:\\?/\\?/[^"\'<> ]+?\.(?:jpe?g|png|webp)(?:\?[^"\'<> ]*)?', text, re.I):
        u = raw.replace("\\/", "/")
        if u not in urls:
            urls.append(u)
    # Rank candidates so the exact user-selected dog image is tested first.
    tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", item.get("registered_name","")) if len(t) >= 4]
    hints = [str(x).lower() for x in (item.get("filename_hints") or [])]
    def rank(u: str):
        lu = u.lower()
        score = 0
        score += sum(8 for t in tokens if t in lu)
        score += sum(12 for t in hints if t in lu)
        if re.search(r"main|stand|stack|profile", lu): score += 3
        if re.search(r"thumb|icon|logo|banner|avatar", lu): score -= 8
        return score
    direct = list(item.get("direct_candidates") or [])
    rest = [u for u in urls if u not in direct]
    rest.sort(key=lambda u: (-rank(u), len(u)))
    return (direct + rest)[:28]

def choose_image(item: dict) -> tuple[bytes, str, dict]:
    target = int(item["expected_dhash"], 16)
    threshold = int(item.get("match_threshold") or MATCH_THRESHOLD)

    if item.get("force_direct_candidate") and item.get("direct_candidates"):
        url = item["direct_candidates"][0]
        try:
            data, ctype = request_bytes(url, referer=item["source_url"], timeout=20)
            image = decode_image(data)
            dist = hamming(target, dhash_int(image))
            if dist <= threshold:
                return data, url, {"forced_direct": True, "dhash_distance": dist, "candidate_size": image.size, "candidate_count": 1}
        except Exception:
            pass


    exp_w = int(item.get("expected_width") or 0)
    exp_h = int(item.get("expected_height") or 0)
    source_page = item["source_url"]
    candidates = collect_candidates(item)
    scored = []
    errors = []
    for idx, url in enumerate(candidates):
        try:
            data, ctype = request_bytes(url, referer=source_page, timeout=8)
            if len(data) < 1000 or "html" in ctype:
                continue
            image = decode_image(data)
            if image.width < 120 or image.height < 120:
                continue
            dist = hamming(target, dhash_int(image))
            ratio_penalty = 0
            if exp_w and exp_h:
                expected_ratio = exp_w / exp_h
                ratio_penalty = abs((image.width / image.height) - expected_ratio) * 8
            score = dist + ratio_penalty
            scored.append((score, dist, -image.width*image.height, idx, url, data, image.size))
            if dist <= 2:
                break
        except Exception as exc:
            errors.append((url, str(exc)))
    if not scored:
        raise RuntimeError(f"no decodable image candidates found; first errors: {errors[:3]}")
    scored.sort(key=lambda x: (x[0], x[1], x[2], x[3]))
    best = scored[0]
    threshold = int(item.get("match_threshold") or MATCH_THRESHOLD)
    if best[1] > threshold:
        top = [{"url":x[4],"dhash_distance":x[1],"size":x[6]} for x in scored[:5]]
        raise RuntimeError(f"no safe fingerprint match (best distance {best[1]} > {threshold}); candidates={top}")
    return best[5], best[4], {"dhash_distance":best[1], "candidate_size":best[6], "candidate_count":len(scored)}

def normalize_jpeg(data: bytes) -> tuple[bytes, tuple[int,int], int]:
    image = decode_image(data)
    # Never crop the dog. Only downscale oversized sources.
    if max(image.size) > 1800:
        scale = 1800 / max(image.size)
        image = image.resize((round(image.width*scale), round(image.height*scale)), Image.Resampling.LANCZOS)
    image = image.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=3))
    best = None
    for quality in (95, 93, 91, 89, 87, 85, 82, 80, 77, 74):
        out = io.BytesIO()
        image.save(out, "JPEG", quality=quality, optimize=True, progressive=True, subsampling=0)
        payload = out.getvalue()
        best = (payload, image.size, quality)
        if len(payload) <= MAX_OUTPUT:
            break
    if best is None:
        raise RuntimeError("JPEG normalization failed")
    return best

def upload_r2(key: str, data: bytes, item: dict) -> str:
    if not TOKEN:
        raise RuntimeError("MEDIA_ADMIN_KEY is not configured")
    endpoint = f"{WORKER}/v1/admin/media/{key}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "image/jpeg",
        "Content-Length": str(len(data)),
        "X-DI-Registered-Name": item["registered_name"],
        "X-DI-Role": "bloodline_ancestor",
        "X-DI-Source-Url": item["source_url"],
        "User-Agent": "Doberman-Index-Curated-Bloodline/1.0",
    }
    req = urllib.request.Request(endpoint, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=45) as response:
        body = json.loads(response.read().decode("utf-8"))
        if response.status not in (200,201):
            raise RuntimeError(f"R2 upload HTTP {response.status}: {body}")
        return body.get("public_url") or (WORKER + "/" + key)

def ensure_root_item(manifest: dict, root: str, aid: str) -> dict:
    record = manifest.setdefault("records", {}).setdefault(root, {})
    return record.setdefault("ancestors", {}).setdefault(aid, {})

def main():
    queue = load_json(QUEUE)
    manifest = load_json(MANIFEST)
    bindings = load_json(BINDINGS)
    roots = queue.get("target_roots") or ["DI-M-000001"]
    report = {"processed": [], "failed": [], "root_updates": roots}

    for item in queue.get("imports") or []:
        if item.get("status") == "done":
            continue
        aid = item["ancestor_id"]
        action = item["action"]
        item_roots = item.get("target_roots") or roots
        try:
            if action == "remove_from_roots":
                for root in item_roots:
                    entry = ensure_root_item(manifest, root, aid)
                    entry.clear()
                    entry.update({
                        "status": "missing",
                        "note": item.get("note") or "Image removed by curator."
                    })
                # Remove old manual override so the root-specific manifest can control visibility.
                (bindings.get("photos") or {}).pop(aid, None)
                item["status"] = "done"
                report["processed"].append({"record_id":aid,"action":action})
                continue

            raw, matched_url, match_meta = choose_image(item)
            jpg, size, quality = normalize_jpeg(raw)
            public_url = upload_r2(item["r2_key"], jpg, item)

            for root in item_roots:
                entry = ensure_root_item(manifest, root, aid)
                entry.clear()
                entry.update({
                    "status": "selected",
                    "selected": {
                        "image_url": public_url,
                        "source_label": item["source_label"],
                        "source_url": item["source_url"],
                        "curated_match_url": matched_url
                    }
                })

            # Curated R2 selections should not be shadowed by a legacy repository-local override.
            (bindings.get("photos") or {}).pop(aid, None)

            item["status"] = "done"
            item["public_url"] = public_url
            item["matched_image_url"] = matched_url
            item["optimized_bytes"] = len(jpg)
            item["optimized_dimensions"] = [size[0], size[1]]
            item["jpeg_quality"] = quality
            item["match"] = match_meta
            report["processed"].append({
                "record_id":aid,
                "name":item["registered_name"],
                "action":action,
                "to":public_url,
                "bytes":len(jpg),
                "dimensions":size,
                "quality":quality,
                "match":match_meta
            })
        except Exception as exc:
            item["status"] = "failed"
            item["error"] = str(exc)
            report["failed"].append({"record_id":aid,"name":item.get("registered_name"),"error":str(exc)})

    save_json(QUEUE, queue)
    save_json(MANIFEST, manifest)
    save_json(BINDINGS, bindings)
    report["ok"] = not report["failed"]
    save_json(REPORT, report)

    print(json.dumps(report, indent=2))
    if report["failed"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
