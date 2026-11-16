#!/usr/bin/env python3
"""Extract visible catalog metadata from a locally saved Přehraj.to search page.

This parser is intentionally offline: it does not perform searches, log in,
fetch detail pages, or resolve playback URLs.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse


BASE = "https://prehraj.to"


def parse_size(value: str) -> int | None:
    match = re.search(r"([\d.,]+)\s*(KB|MB|GB|TB)", value or "", re.I)
    if not match:
        return None
    amount = float(match.group(1).replace(",", "."))
    factor = {"KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    return round(amount * factor[match.group(2).upper()])


def parse_duration(value: str) -> int | None:
    parts = (value or "").strip().split(":")
    if not parts or not all(p.isdigit() for p in parts):
        return None
    total = 0
    for part in parts:
        total = total * 60 + int(part)
    return total


class CatalogParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results = []
        self.current = None
        self.capture = None
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = {k.lower(): (v or "").strip() for k, v in attrs if k}
        classes = set(attrs.get("class", "").split())
        if tag.lower() == "a" and ({"video--link", "video"} & classes or
                                   any("video" in c for c in classes)):
            href = attrs.get("href", "")
            if href.startswith("/"):
                self.current = {"url": urljoin(BASE, href), "title": "",
                                "size_text": "", "duration_text": "",
                                "thumbnail": ""}
        if self.current is None:
            return
        if tag.lower() == "img" and attrs.get("src"):
            self.current["thumbnail"] = urljoin(BASE, attrs["src"])
        if tag.lower() in {"h3", "span", "div"}:
            class_text = attrs.get("class", "").lower()
            if "video__title" in class_text or tag.lower() == "h3":
                self.capture = "title"
                self.text_parts = []
            elif "video__tag--size" in class_text or "video__size" in class_text:
                self.capture = "size_text"
                self.text_parts = []
            elif "video__tag--time" in class_text or "video__time" in class_text:
                self.capture = "duration_text"
                self.text_parts = []

    def handle_data(self, data):
        if self.current is not None and self.capture:
            self.text_parts.append(data.strip())

    def handle_endtag(self, tag):
        if self.current is None:
            return
        if self.capture and tag.lower() in {"h3", "span", "div"}:
            value = " ".join(x for x in self.text_parts if x).strip()
            if value and not self.current.get(self.capture):
                self.current[self.capture] = value
            self.capture = None
            self.text_parts = []
        if tag.lower() == "a":
            title = self.current.get("title") or self.current.get("title_text") or ""
            title = title.strip()
            if title:
                item = {
                    "title": title,
                    "page_url": self.current["url"],
                    "size_bytes": parse_size(self.current["size_text"]),
                    "duration_seconds": parse_duration(self.current["duration_text"]),
                    "thumbnail": self.current["thumbnail"] or None,
                }
                if not any(x["page_url"] == item["page_url"] for x in self.results):
                    self.results.append(item)
            self.current = None
            self.capture = None


def parse_catalog(html: str) -> list[dict]:
    parser = CatalogParser()
    parser.feed(html)
    return parser.results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html_file", type=Path)
    ap.add_argument("--json", dest="json_path", type=Path)
    args = ap.parse_args()
    if not args.html_file.is_file():
        ap.error(f"File not found: {args.html_file}")
    html = args.html_file.read_text(encoding="utf-8", errors="replace")
    results = parse_catalog(html)
    rendered = json.dumps({"results": results, "count": len(results)},
                          ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
