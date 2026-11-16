#!/usr/bin/env python3
"""Inspect saved HTML for video embeds and publicly exposed metadata.

This is a passive, local parser: it does not make network requests or attempt
to bypass authentication, DRM, anti-bot controls, or signed URL restrictions.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


VIDEO_META_KEYS = {
    "og:video", "og:video:url", "og:video:secure_url",
    "twitter:player", "twitter:player:stream",
}
VIDEO_EXTENSIONS = (".mp4", ".m3u8", ".mpd", ".webm", ".mov", ".m4v")


def absolute_or_raw(value: str) -> str:
    return value.strip()


class PageInspector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[dict[str, str]] = []
        self.meta: dict[str, str] = {}
        self.canonical: str | None = None
        self.title_parts: list[str] = []
        self.in_title = False

    def handle_starttag(self, tag: str, attrs) -> None:
        a = {k.lower(): (v or "").strip() for k, v in attrs if k}
        tag = tag.lower()

        if tag == "title":
            self.in_title = True

        if tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            content = a.get("content", "")
            if key and content:
                self.meta[key] = content
                if key in VIDEO_META_KEYS:
                    self.items.append({"kind": "metadata", "attribute": key, "url": content})

        if tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href") or None

        if tag == "iframe" and a.get("src"):
            self.items.append({"kind": "iframe", "attribute": "src", "url": a["src"]})

        if tag == "video":
            for attr in ("src", "poster"):
                if a.get(attr):
                    self.items.append({"kind": "video", "attribute": attr, "url": a[attr]})

        if tag == "source" and a.get("src"):
            self.items.append({"kind": "source", "attribute": "src", "url": a["src"]})

        if tag in {"script", "a"}:
            value = a.get("src") if tag == "script" else a.get("href")
            if value and re.search(r"video|player|embed|stream|\.m3u8|\.mpd|\.mp4", value, re.I):
                self.items.append({"kind": tag, "attribute": "src" if tag == "script" else "href", "url": value})

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data.strip())


def host_for(url: str) -> str:
    parsed = urlparse(url)
    return parsed.hostname or "(relative or non-URL reference)"


def inspect(path: Path) -> dict:
    html = path.read_text(encoding="utf-8", errors="replace")
    parser = PageInspector()
    parser.feed(html)

    # Also catch literal media URLs embedded in inline script/config text.
    for match in re.findall(r"""https?://[^\s"'<>\\]+""", html, flags=re.I):
        cleaned = match.rstrip("),;]")
        if any(ext in urlparse(cleaned).path.lower() for ext in VIDEO_EXTENSIONS):
            parser.items.append({"kind": "literal-media-url", "attribute": "text", "url": cleaned})

    unique = []
    seen = set()
    for item in parser.items:
        key = (item["kind"], item["attribute"], item["url"])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    hosts: dict[str, list[str]] = defaultdict(list)
    for item in unique:
        host = host_for(item["url"])
        if item["url"] not in hosts[host]:
            hosts[host].append(item["url"])

    return {
        "file": str(path),
        "title": " ".join(parser.title_parts).strip() or None,
        "canonical_url": parser.canonical,
        "video_metadata": {k: v for k, v in parser.meta.items() if k in VIDEO_META_KEYS},
        "candidates": unique,
        "hosts": dict(sorted(hosts.items())),
        "notice": (
            "A discovered URL or host is only a technical clue. It does not "
            "establish who uploaded the video or whether distribution is authorized."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html_file", type=Path, help="Saved HTML/page-source file")
    ap.add_argument("--json", dest="json_path", type=Path, help="Also write report to this JSON file")
    args = ap.parse_args()

    if not args.html_file.is_file():
        ap.error(f"File not found: {args.html_file}")

    report = inspect(args.html_file)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"\nReport saved to {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
