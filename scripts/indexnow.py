#!/usr/bin/env python3
"""
Doberman Index — IndexNow publisher.

Designed for GitHub Pages:
- runs only after a successful Pages deployment;
- verifies the already-hosted IndexNow key;
- submits only canonical/indexable URLs affected by the deployed commit;
- submits all sitemap URLs only for a manual verification run or a rare sitemap-only change.

No third-party Python packages are required.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET


DEFAULT_BASE_URL = "https://doberman-index.com"
DEFAULT_API_URL = "https://api.indexnow.org/indexnow"
DEFAULT_KEY_FILE = "52dbc20591774f4897c62364d22b8cbe.txt"


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def changed_paths(base: str, head: str) -> list[str]:
    """Return both sides of renames so deleted and new canonical URLs can be notified."""
    output = run_git("diff", "--name-status", "--find-renames", base, head, "--")
    paths: list[str] = []
    for raw in output.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        status = parts[0]
        if status.startswith(("R", "C")) and len(parts) >= 3:
            paths.extend([parts[-2], parts[-1]])
        elif len(parts) >= 2:
            paths.append(parts[-1])
    return sorted(set(paths))


def canonical_url_for_path(path: str, base_url: str) -> str | None:
    path = path.replace("\\", "/").lstrip("./")

    if path == "index.html":
        return f"{base_url}/"
    if path == "about.html":
        return f"{base_url}/about.html"

    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "records" and parts[1].startswith("DI-"):
        # Every published registry record has a clean canonical directory URL.
        return f"{base_url}/records/{parts[1]}/"

    return None


def sitemap_urls(sitemap_path: Path, base_url: str) -> list[str]:
    if not sitemap_path.exists():
        raise FileNotFoundError(f"Missing sitemap: {sitemap_path}")

    root = ET.parse(sitemap_path).getroot()
    urls: list[str] = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            value = element.text.strip()
            if value.startswith(base_url.rstrip("/") + "/") or value == base_url.rstrip("/"):
                urls.append(value)
    return sorted(set(urls))


def key_value(key_path: Path) -> str:
    if not key_path.exists():
        raise FileNotFoundError(
            f"IndexNow key file is missing: {key_path}. "
            "Host the generated key file in the repository root first."
        )
    key = key_path.read_text(encoding="utf-8").strip()
    if not key or key != key_path.stem:
        raise ValueError("IndexNow key filename and file contents must match exactly.")
    return key


def http_get_text(url: str, attempts: int = 4) -> str:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "DobermanIndex-IndexNow/1.0",
                    "Cache-Control": "no-cache",
                },
            )
            with urllib.request.urlopen(req, timeout=20) as response:
                return response.read().decode("utf-8").strip()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Could not verify public IndexNow key at {url}: {last_error}")


def verify_public_key(key: str, key_location: str) -> None:
    public_value = http_get_text(key_location)
    if public_value != key:
        raise RuntimeError(
            "Public IndexNow key verification failed: "
            "the hosted file does not contain the expected key."
        )


def submit(urls: list[str], host: str, key: str, key_location: str, api_url: str) -> int:
    payload = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")

    retryable = {429, 500, 502, 503, 504}
    last_status = None

    for attempt in range(4):
        request = urllib.request.Request(
            api_url,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "DobermanIndex-IndexNow/1.0",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                status = response.getcode()
                if status in (200, 202):
                    return status
                last_status = status
        except urllib.error.HTTPError as exc:
            last_status = exc.code
            if exc.code not in retryable:
                body = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(
                    f"IndexNow rejected the request with HTTP {exc.code}: {body[:500]}"
                ) from exc
        except urllib.error.URLError as exc:
            last_status = "network-error"
            if attempt == 3:
                raise RuntimeError(f"IndexNow network error: {exc}") from exc

        if attempt < 3:
            time.sleep(5 * (2 ** attempt))

    raise RuntimeError(f"IndexNow submission failed after retries; last status: {last_status}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("changed", "all"), default="changed")
    parser.add_argument("--base", default="HEAD^")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--key-file", default=DEFAULT_KEY_FILE)
    parser.add_argument("--sitemap", default="sitemap.xml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-key-check",
        action="store_true",
        help="For local tests only; production workflow does not use this.",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    host = urllib.parse.urlsplit(base_url).netloc
    key_path = Path(args.key_file)
    key = key_value(key_path)
    key_location = f"{base_url}/{key_path.name}"

    if args.mode == "all":
        urls = sitemap_urls(Path(args.sitemap), base_url)
        reason = "manual all-from-sitemap verification"
    else:
        try:
            paths = changed_paths(args.base, args.head)
        except subprocess.CalledProcessError:
            # Safe fallback for unusual shallow/first-commit history.
            urls = sitemap_urls(Path(args.sitemap), base_url)
            reason = "git range unavailable; safe sitemap fallback"
        else:
            urls = sorted(
                {
                    url
                    for path in paths
                    if (url := canonical_url_for_path(path, base_url))
                }
            )
            if not urls and "sitemap.xml" in paths:
                urls = sitemap_urls(Path(args.sitemap), base_url)
                reason = "sitemap changed without directly mapped canonical files"
            else:
                reason = "canonical URLs changed in deployed commit"

    print(f"IndexNow mode: {args.mode}")
    print(f"Reason: {reason}")
    print(f"Candidate URLs: {len(urls)}")
    for url in urls:
        print(f"  {url}")

    if not urls:
        print("No indexable canonical URLs changed. Nothing to submit.")
        return 0

    if len(urls) > 10000:
        raise RuntimeError("IndexNow accepts at most 10,000 URLs in one request.")

    if args.dry_run:
        print("Dry run complete; no network request sent.")
        return 0

    if not args.skip_key_check:
        print(f"Verifying public key: {key_location}")
        verify_public_key(key, key_location)
        print("Public key verified.")

    status = submit(urls, host, key, key_location, args.api_url)
    print(f"IndexNow accepted {len(urls)} URL(s). HTTP {status}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
