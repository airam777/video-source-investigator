#!/usr/bin/env python3
"""Create a consolidated, offline report from a saved HTML page.

The report combines page references, uploader attribution, player/provider
clues, deferred loader declarations, and declared media format/host evidence.
It never fetches URLs, executes JavaScript, sends AJAX requests, or exposes
playable media URLs. JSON and Markdown outputs pass through the safe exporter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from authorized_stream_extractor import extract as inspect_media
from deferred_player_inspector import inspect_html as inspect_deferred
from evidence_validator import validate_report
from investigator import inspect_file, safe_url
from prehraj_catalog import parse_catalog
from provenance_inspector import inspect_html as inspect_provenance
from provider_inspector import inspect as inspect_provider
from report_exporter import export_report
from core.document_context import AnalysisContext
from core.engine import EvidenceEngine
from core.exporter import export_evidence


def analyze(path: Path, base_url: str = "") -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    raw_bytes = path.read_bytes()
    html = raw_bytes.decode("utf-8", errors="replace")
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
    report = {
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
        "source_provenance": {
            "input_kind": "saved_html_file",
            "input_file_name": path.name,
            "raw_html_sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "raw_html_bytes": len(raw_bytes),
            "raw_html_available_to_local_analysis": True,
            "raw_html_committed_to_repository": False,
            "project_parser_executed": True,
            "analysis_environment": "local offline Python analysis; no network requests",
        },
        "interpretation": [
            "A referenced host is a technical clue, not proof of who uploaded the content.",
            "A page author is not necessarily the uploader.",
            "Explicit uploader attribution does not prove ownership or licensing.",
            "A media host or format does not establish distribution rights.",
            "Media paths and query credentials are intentionally hidden.",
            "This report is based only on the supplied local HTML; no remote requests were made.",
        ],
    }
    report["evidence_validation"] = validate_report(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path, help="Locally saved HTML/page source")
    parser.add_argument("--base-url", default="", help="Original page URL for resolving relative references")
    parser.add_argument("--json", dest="json_path", type=Path, help="Write sanitized JSON report")
    parser.add_argument("--markdown", dest="markdown_path", type=Path, help="Write sanitized Markdown report")
    parser.add_argument(
        "--export-evidence",
        dest="evidence_path",
        type=Path,
        metavar="FILE",
        help="Write a deterministic Evidence Graph audit JSON envelope (opt-in)",
    )
    args = parser.parse_args()
    try:
        report = analyze(args.html, args.base_url)
        safe_report = export_report(report, args.json_path, args.markdown_path)
        if args.evidence_path is not None:
            raw_bytes = args.html.read_bytes()
            context = AnalysisContext(
                content=raw_bytes,
                source_name=args.html.name,
                base_url=args.base_url or None,
            )
            graph = EvidenceEngine().process(report, context)
            export_evidence(graph, args.evidence_path)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(json.dumps(safe_report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
