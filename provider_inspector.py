#!/usr/bin/env python3
"""Offline inspection of visible player/provider references in saved HTML.

Reports host-level clues and player configuration formats from a local,
authorized HTML file. It never fetches pages or prints media URLs/tokens.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

PLAYER_HOST_HINTS = (
    "voe.sx", "mixdrop.co", "mixdrop.to", "vidsrc.me", "vidsrc.to",
    "streamtape.com", "doodstream.com", "dood.to", "filemoon.sx",
    "streamwish.to", "mp4upload.com",
)
MEDIA_EXTENSIONS = {
    ".mp4": "MP4", ".m4v": "M4V", ".webm": "WebM",
    ".m3u8": "HLS playlist", ".mpd": "MPEG-DASH manifest",
    ".mp3": "MP3 audio", ".m4a": "M4A audio",
}


def media_kind(value: str, mime: str = "") -> str:
    suffix = Path(urlparse(value).path).suffix.lower()
    if suffix in MEDIA_EXTENSIONS:
        return MEDIA_EXTENSIONS[suffix]
    mime = mime.lower().split(";", 1)[0].strip()
    known = {
        "video/mp4": "MP4", "application/vnd.apple.mpegurl": "HLS playlist",
        "application/x-mpegurl": "HLS playlist",
        "application/dash+xml": "MPEG-DASH manifest",
        "video/webm": "WebM", "audio/mpeg": "MP3 audio",
    }
    return known.get(mime, "unspecified / unknown")


class PageInspector(HTMLParser):
    def __init__(self, base_url: str = ""):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.in_title = False
        self.in_script = False
        self.script_parts: list[str] = []
        self.meta: dict[str, str] = {}
        self.references: list[dict[str, str | bool]] = []
        self.player_configs: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs):
        a = {k.lower(): v for k, v in attrs if k and v is not None}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        if tag == "script":
            self.in_script = True
            self.script_parts = []
        if tag == "meta":
            key = a.get("property") or a.get("name") or ""
            value = a.get("content", "")
            if key and value:
                self.meta[key.lower()] = value
        if tag == "iframe":
            raw = a.get("src") or a.get("data-src") or a.get("data-lazy-src")
            if raw:
                self.add_reference("iframe", raw)
        elif tag == "a":
            raw = a.get("href")
            if raw:
                self.add_reference("link", raw)
        elif tag in ("video", "source"):
            raw = a.get("src") or a.get("data-src")
            if raw:
                self.add_reference("media-element", raw, a.get("type", ""))
        if tag == "video" and a.get("data-setup"):
            self.player_configs.append({"player": "Video.js", "configuration": "data-setup attribute"})

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if tag == "script" and self.in_script:
            self.inspect_script("".join(self.script_parts))
            self.in_script = False
            self.script_parts = []

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data.strip())
        if self.in_script:
            self.script_parts.append(data)

    def add_reference(self, kind: str, raw: str, mime: str = ""):
        absolute = urljoin(self.base_url, raw)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return
        host = parsed.hostname.lower()
        self.references.append({
            "kind": kind,
            "host": host,
            "player_host_hint": any(host == hint or host.endswith("." + hint) for hint in PLAYER_HOST_HINTS),
            "media_type": media_kind(absolute, mime) if kind == "media-element" else "",
            "has_non_root_path": parsed.path not in ("", "/"),
            "has_query": bool(parsed.query),
        })

    def inspect_script(self, script: str):
        lower = script.lower()
        if "jwplayer(" in lower or "jwplayer." in lower:
            self.player_configs.append({"player": "JW Player", "configuration": "setup/config reference"})
        if "videojs(" in lower or "video.js" in lower:
            self.player_configs.append({"player": "Video.js", "configuration": "initialization/config reference"})
        source_pattern = re.compile(
            r"""(?:file|src|contenturl)\s*["']?\s*[:=]\s*["']([^"']+)["']""",
            re.I,
        )
        type_pattern = re.compile(r"""["']type["']\s*:\s*["']([^"']+)["']""", re.I)
        default_mime = type_pattern.search(script)
        for match in source_pattern.finditer(script):
            raw = match.group(1).strip()
            if raw.startswith("//"):
                raw = "https:" + raw
            parsed = urlparse(urljoin(self.base_url, raw))
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                continue
            self.references.append({
                "kind": "player-config-source",
                "host": parsed.hostname.lower(),
                "player_host_hint": any(parsed.hostname.lower() == hint or parsed.hostname.lower().endswith("." + hint) for hint in PLAYER_HOST_HINTS),
                "media_type": media_kind(raw, default_mime.group(1) if default_mime else ""),
                "has_non_root_path": parsed.path not in ("", "/"),
                "has_query": bool(parsed.query),
            })


def inspect(path: Path, base_url: str = "") -> dict:
    parser = PageInspector(base_url)
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    unique = []
    seen = set()
    for item in parser.references:
        key = (item["kind"], item["host"], item["media_type"])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    counts = Counter(x["host"] for x in unique)
    configs = []
    config_seen = set()
    for config in parser.player_configs:
        key = (config["player"], config["configuration"])
        if key not in config_seen:
            config_seen.add(key)
            configs.append(config)
    return {
        "file": path.name,
        "page_title": " ".join(x for x in parser.title_parts if x),
        "page_metadata": {
            k: parser.meta[k]
            for k in ("og:title", "og:url", "og:site_name", "twitter:player")
            if k in parser.meta
        },
        "player_configurations": configs,
        "provider_hosts": [
            {"host": host, "references": count}
            for host, count in counts.most_common()
        ],
        "references": unique,
        "note": (
            "Offline report only: URLs are reduced to host-level metadata. "
            "No player pages, AJAX endpoints, sessions, cookies, or streams are fetched/resolved."
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
