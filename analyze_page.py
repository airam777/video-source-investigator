#!/usr/bin/env python3
"""Create one consolidated, offline report from a saved HTML page.

The report combines visible page references, uploader attribution, player/provider
clues, deferred loader declarations, and declared media format/host evidence.
It never fetches URLs, executes JavaScript, sends AJAX requests, or exposes
playable media URLs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from authorized_stream_extractor import extract as inspect_media
from deferred_player_inspector import inspect_html as inspect_deferred
from investigator import inspect_file, safe_url
from prehraj_catalog import parse_catalog
from provenance_inspector import inspect_html as inspect_provenance
from provider_inspector import inspect as inspect_provider


def analyze(path: Path, base_url: str = "") -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    html = path.read_text(encoding="utf-8", errors="replace")
    page = inspect_file(path, base_url)
    providers = inspect_provider(path, base_url)
    deferred = inspect_deferred(path)
    media = inspect_media(path, base_url)
    provenance = inspect_provenance(html, base_url)
    catalog = parse_catalog(html)
    catalog_base = base_url or "https://prehraj.to/"
    for item in catalog:
        if item.get("page_url"):
            item["page_url"] = safe_url(item["page_url"], catalog_base)
        if item.get("thumbnail"):
            item["thumbnail"] = safe_url(item["thumbnail"], catalog_base)

    hosts = sorted({
        item["host"]
        for item in providers.get("provider_hosts", [])
        if item.get("host")
    })
    return {
        "input_file": path.name,
        "source_page": safe_url(base_url) if base_url else page.get("canonical_url"),
        "title": page.get("title") or providers.get("page_title") or None,
        "provider_hosts": hosts,
        "player_configurations": providers.get("player_configurations", []),
        "visible_references": page.get("candidates", []),
        "explicit_attributions": provenance["explicit_attributions"],
        "uploader_identified": provenance["uploader_identified"],
        "attribution_note": provenance["note"],
        "deferred_loader": deferred,
        "declared_media_evidence": media,
        "catalog_results": catalog,
        "interpretation": [
            "A referenced host is a technical clue, not proof of who uploaded the content.",
            "A page author is not necessarily the uploader.",
            "Explicit uploader attribution does not prove ownership or licensing.",
            "A media host or format does not establish distribution rights.",
            "Media paths and query credentials are intentionally hidden.",
            "This report is based only on the supplied local HTML; no remote requests were made.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="Locally saved HTML/page source")
    parser.add_argument("--base-url", default="", help="Original page URL for resolving relative references")
    parser.add_argument("--json", dest="json_path", type=Path, help="Write report to this JSON file")
    args = parser.parse_args()
    try:
        report = analyze(args.html, args.base_url)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
