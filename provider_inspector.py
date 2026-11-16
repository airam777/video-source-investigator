#!/usr/bin/env python3
"""Offline inspection of visible player/provider references in saved HTML.

This adapts the catalogue-first structure of stremio-prehraj for local,
authorized page-source research. It does not fetch pages or resolve streams.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


PLAYER_HOST_HINTS = (
    "voe.sx", "mixdrop", "vidsrc", "vidstream", "streamtape",
    "dood", "filemoon", "streamwish", "mp4upload",
)


class PageInspector(HTMLParser):
    def __init__(self, base_url: str = ""):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: dict[str, str] = {}
        self.references: list[dict[str, str | bool]] = []

    def handle_starttag(self, tag: str, attrs):
        a = {k.lower(): v for k, v in attrs if k and v is not None}
        if tag.lower() == "title":
            self.in_title = True
        if tag.lower() == "meta":
            key = a.get("property") or a.get("name") or ""
            value = a.get("content", "")
            if key and value:
                self.meta[key.lower()] = value
        if tag.lower() == "iframe":
            raw = a.get("src") or a.get("data-src") or a.get("data-lazy-src")
            if raw:
                self.add_reference("iframe", raw)
        elif tag.lower() == "a":
            raw = a.get("href")
            if raw:
                self.add_reference("link", raw)
        elif tag.lower() in ("video", "source"):
            raw = a.get("src") or a.get("data-src")
            if raw:
                self.add_reference("media-element", raw)

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data.strip())

    def add_reference(self, kind: str, raw: str):
        absolute = urljoin(self.base_url, raw)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return
        host = parsed.hostname.lower()
        player_hint = any(hint in host for hint in PLAYER_HOST_HINTS)
        # Deliberately do not print full paths or query strings: they may
        # contain opaque IDs or temporary access tokens.
        self.references.append({
            "kind": kind,
            "host": host,
            "player_host_hint": player_hint,
            "has_non_root_path": parsed.path not in ("", "/"),
            "has_query": bool(parsed.query),
        })


def inspect(path: Path, base_url: str = "") -> dict:
    parser = PageInspector(base_url)
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    unique = []
    seen = set()
    for item in parser.references:
        key = (item["kind"], item["host"], item["has_non_root_path"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    counts = Counter(x["host"] for x in unique)
    return {
        "file": path.name,
        "page_title": " ".join(x for x in parser.title_parts if x),
        "page_metadata": {
            k: parser.meta[k]
            for k in ("og:title", "og:url", "og:site_name", "twitter:player")
            if k in parser.meta
        },
        "provider_hosts": [
            {"host": host, "references": count}
            for host, count in counts.most_common()
        ],
        "references": unique,
        "note": (
            "Report contains visible host-level clues only. It does not resolve "
            "player pages, expose direct media URLs, or identify the uploader."
        ),
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("html", type=Path, help="Saved HTML/page-source file")
    cli.add_argument("--base-url", default="", help="Canonical page URL for resolving relative links")
    cli.add_argument("--json", dest="json_path", type=Path, help="Write JSON report")
    args = cli.parse_args()

    report = inspect(args.html, args.base_url)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
