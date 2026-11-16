#!/usr/bin/env python3
"""Extract explicitly declared media URLs from a locally saved, authorized HTML file.

This is deliberately offline: it does not request pages, execute JavaScript,
call AJAX endpoints, replay cookies, resolve embeds, or bypass access controls.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, urljoin, urlunparse

MEDIA_TYPES = {
    ".mp4": "MP4",
    ".m4v": "M4V",
    ".webm": "WebM",
    ".m3u8": "HLS",
    ".mpd": "MPEG-DASH",
}


def classify(url: str, mime: str = "") -> str | None:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in MEDIA_TYPES:
        return MEDIA_TYPES[suffix]
    return {
        "video/mp4": "MP4",
        "video/webm": "WebM",
        "application/vnd.apple.mpegurl": "HLS",
        "application/x-mpegurl": "HLS",
        "application/dash+xml": "MPEG-DASH",
    }.get(mime.lower().split(";", 1)[0].strip())


def safe_url(url: str, show_full: bool) -> str:
    if show_full:
        return url
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, p.path, "", "REDACTED" if p.query else "", ""))


class MediaParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.items: list[dict[str, str]] = []
        self.in_script = False
        self.script: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): v for k, v in attrs if k and v is not None}
        if tag.lower() == "script":
            self.in_script, self.script = True, []
        if tag.lower() in {"video", "source"}:
            raw = a.get("src") or a.get("data-src")
            if raw:
                self.add(raw, a.get("type", ""), tag.lower())
        # Only explicit media URLs in standard markup are considered.
        if tag.lower() in {"meta"}:
            key = (a.get("property") or a.get("name") or "").lower()
            if key in {"og:video", "og:video:url", "twitter:player:stream"} and a.get("content"):
                self.add(a["content"], a.get("type", ""), "metadata")

    def handle_data(self, data):
        if self.in_script:
            self.script.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_script:
            text = "".join(self.script)
            # Read only plainly quoted file/src values; no JS execution or deobfuscation.
            pattern = re.compile(r"""(?:file|src)\s*[:=]\s*["'](https?://[^"'\s]+)["']""", re.I)
            for match in pattern.finditer(text):
                self.add(match.group(1), "", "player-config")
            self.in_script, self.script = False, []

    def add(self, raw: str, mime: str, source: str):
        url = urljoin(self.base_url, raw.strip())
        parsed = urlparse(url)
        kind = classify(url, mime)
        if parsed.scheme in {"http", "https"} and parsed.hostname and kind:
            self.items.append({"type": kind, "source": source, "url": url})


def extract(path: Path, base_url: str = "", show_full: bool = False):
    parser = MediaParser(base_url)
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    unique, seen = [], set()
    for item in parser.items:
        key = (item["type"], item["url"])
        if key not in seen:
            seen.add(key)
            unique.append({
                "type": item["type"],
                "source": item["source"],
                "host": urlparse(item["url"]).hostname,
                "url": safe_url(item["url"], show_full),
            })
    return {
        "input_file": path.name,
        "matches": unique,
        "count": len(unique),
        "full_urls_shown": show_full,
        "limitations": [
            "Local HTML only; no network requests or JavaScript execution.",
            "Does not inspect provider pages, hidden endpoints, cookies, or browser sessions.",
            "Only explicit MP4, WebM, HLS, and DASH references are recognized.",
            "Query strings are redacted unless --show-full-urls is explicitly supplied.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", type=Path, help="Saved HTML from an authorized test page")
    ap.add_argument("--base-url", default="", help="Page URL for resolving relative media paths")
    ap.add_argument("--show-full-urls", action="store_true", help="Show query strings; use only for authorized test material")
    ap.add_argument("--json", dest="json_path", type=Path, help="Write report to a JSON file")
    args = ap.parse_args()
    report = extract(args.html, args.base_url, args.show_full_urls)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
