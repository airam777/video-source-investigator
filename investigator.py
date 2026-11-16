#!/usr/bin/env python3
"""Passively inspect saved HTML for video embeds and hosting clues.

No network requests, cookies, authentication, hidden endpoints, or stream downloads.
Direct media URLs are reported by host/type only; temporary query tokens are hidden.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

VIDEO_META_KEYS = {"og:video", "og:video:url", "og:video:secure_url",
                   "twitter:player", "twitter:player:stream"}
MEDIA_EXTENSIONS = (".mp4", ".m3u8", ".mpd", ".webm", ".mov", ".m4v")
SENSITIVE_KEY_PATTERN = re.compile(r"token|expires|signature|sig|auth|key|policy|credential|jwt|session|pass", re.I)


def safe_url(value: str, base: str | None = None) -> str:
    absolute = urljoin(base or "", value.strip())
    p = urlparse(absolute)
    # Keep non-sensitive query parameters; hide credentials and signed tokens.
    query = [(k, "[REDACTED]" if SENSITIVE_KEY_PATTERN.search(k) else v)
             for k, v in parse_qsl(p.query, keep_blank_values=True)]
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(query), ""))


def is_media_url(value: str) -> bool:
    return urlparse(value).path.lower().endswith(MEDIA_EXTENSIONS)


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items = []
        self.meta = {}
        self.canonical = None
        self.title = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "").strip() for k, v in attrs if k}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            key = (a.get("property") or a.get("name") or a.get("itemprop") or "").lower()
            if key and a.get("content"):
                self.meta[key] = a["content"]
                if key in VIDEO_META_KEYS:
                    self.items.append({"kind": "metadata", "attribute": key, "url": a["content"]})
        if tag == "link" and "canonical" in a.get("rel", "").lower().split():
            self.canonical = a.get("href")
        if tag == "iframe":
            for attr in ("src", "data-src", "data-lazy-src", "data-original"):
                if a.get(attr):
                    self.items.append({"kind": "embed", "attribute": attr, "url": a[attr]})
                    break
        if tag == "video":
            for attr in ("src", "data-src", "poster"):
                if a.get(attr):
                    self.items.append({"kind": "video", "attribute": attr, "url": a[attr]})
        if tag == "source":
            for attr in ("src", "data-src"):
                if a.get(attr):
                    self.items.append({"kind": "source", "attribute": attr, "url": a[attr]})
                    break
        if tag in {"script", "a"}:
            attr = "src" if tag == "script" else "href"
            value = a.get(attr)
            if value and re.search(r"video|player|embed|stream", value, re.I):
                self.items.append({"kind": tag, "attribute": attr, "url": value})

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data.strip())


def inspect_html(html: str, source_name: str = "<memory>", base_url: str = "") -> dict:
    parser = Inspector()
    parser.feed(html)
    base = parser.canonical or base_url or ""
    # Catch visible literal media URLs in inline player configuration, but
    # do not return their full signed paths or query strings.
    for match in re.findall(r"""https?://[^\s"'<>\\]+""", html, flags=re.I):
        candidate = match.rstrip("),;]")
        if is_media_url(candidate):
            parser.items.append({"kind": "media-reference", "attribute": "inline",
                                 "url": candidate})

    candidates, seen = [], set()
    hosts = defaultdict(list)
    for item in parser.items:
        raw = item["url"]
        resolved = safe_url(raw, base)
        parsed = urlparse(resolved)
        media = is_media_url(resolved)
        # Hide direct media paths: report provider host and media type only.
        shown = parsed.scheme + "://" + parsed.netloc + "/[media URL hidden]" if media else resolved
        key = (item["kind"], item["attribute"], shown)
        if key in seen:
            continue
        seen.add(key)
        candidates.append({"kind": item["kind"], "attribute": item["attribute"],
                           "url": shown, "host": parsed.hostname or "(relative)",
                           "media_reference": media})
        if parsed.hostname and parsed.hostname not in hosts[item["kind"]]:
            hosts[item["kind"]].append(parsed.hostname)

    return {
        "source": source_name,
        "title": " ".join(x for x in parser.title if x) or None,
        "canonical_url": safe_url(parser.canonical, base) if parser.canonical else None,
        "video_metadata": {k: _safe_reference(v, base) for k, v in parser.meta.items()
                           if k in VIDEO_META_KEYS},
        "candidates": candidates,
        "hosts_by_kind": dict(sorted(hosts.items())),
        "notice": "Host identification is a technical clue only; it does not identify an uploader or prove licensing."
    }


def _safe_reference(value: str, base: str = "") -> str:
    resolved = safe_url(value, base)
    parsed = urlparse(resolved)
    if is_media_url(resolved):
        return f"{parsed.scheme}://{parsed.netloc}/[media URL hidden]"
    return resolved


def inspect_file(path: Path, base_url: str = "") -> dict:
    return inspect_html(path.read_text(encoding="utf-8", errors="replace"), str(path), base_url)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html_file", type=Path, help="Saved HTML/page-source file")
    ap.add_argument("--base-url", default="", help="Original page URL for resolving relative references")
    ap.add_argument("--json", dest="json_path", type=Path, help="Write report to a JSON file")
    args = ap.parse_args()
    if not args.html_file.is_file():
        ap.error(f"File not found: {args.html_file}")
    report = inspect_file(args.html_file, args.base_url)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")
        print(f"Report saved to {args.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
