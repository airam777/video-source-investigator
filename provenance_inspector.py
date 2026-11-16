#!/usr/bin/env python3
"""Extract explicit uploader/author attribution from a locally saved HTML page.

This parser reports only attribution explicitly present in the supplied source.
It does not infer identities from hosting domains or contact site operators.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse


UPLOADER_LABEL = re.compile(
    r"\b(?:uploaded\s+by|uploader|uploaded\s+user|nahr[aá]l(?:a|o)?|"
    r"vlo[zž]il(?:a|o)?|u[zž]ivatel|pridal(?:a|o)?)\b",
    re.I,
)
AUTHOR_KEYS = {"author", "creator"}
UPLOADER_KEYS = {"uploader", "uploadby", "uploadedby", "user"}


def public_url(value: str, base_url: str = "") -> str | None:
    absolute = urljoin(base_url, value.strip())
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    # Attribution links are public references; remove query strings/fragments.
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


class AttributionParser(HTMLParser):
    def __init__(self, base_url: str = ""):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.meta: list[dict] = []
        self.microdata: list[dict] = []
        self.links: list[dict] = []
        self.scripts: list[str] = []
        self.current_script: list[str] | None = None
        self.current_link: dict | None = None
        self.expect_uploader_link = False
        self.pending_label = ""

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "").strip() for k, v in attrs if k}
        tag = tag.lower()
        if tag == "meta":
            key = (a.get("name") or a.get("property") or a.get("itemprop") or "").lower()
            value = a.get("content", "")
            if key in {"author", "article:author", "uploader", "video: uploader"} and value:
                self.meta.append({"kind": "uploader" if "uploader" in key else "page_author",
                                  "name": value, "url": None, "evidence": "meta:" + key})
        itemprop = a.get("itemprop", "").lower()
        if itemprop in {"author", "uploader", "creator"}:
            value = a.get("content") or a.get("title") or a.get("aria-label") or a.get("data-name")
            if value:
                self.microdata.append({
                    "kind": "uploader" if itemprop == "uploader" else "page_author",
                    "name": value, "url": public_url(a.get("href", ""), self.base_url),
                    "evidence": "itemprop:" + itemprop,
                })
        if tag == "a":
            rel = set(a.get("rel", "").lower().split())
            is_author = "author" in rel or a.get("itemprop", "").lower() in {"author", "uploader"}
            if is_author or self.expect_uploader_link:
                self.current_link = {
                    "kind": "uploader" if self.expect_uploader_link or a.get("itemprop", "").lower() == "uploader" else "page_author",
                    "name_parts": [],
                    "url": public_url(a.get("href", ""), self.base_url),
                    "evidence": "labelled_profile_link" if self.expect_uploader_link else "author_link",
                }
                self.expect_uploader_link = False
        if tag == "script":
            script_type = a.get("type", "").lower()
            if script_type == "application/ld+json":
                self.current_script = []

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_link["name_parts"].append(data.strip())
        elif UPLOADER_LABEL.search(data):
            self.pending_label = data.strip()
            self.expect_uploader_link = True
        if self.current_script is not None:
            self.current_script.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "a" and self.current_link is not None:
            item = self.current_link
            item["name"] = " ".join(x for x in item.pop("name_parts") if x).strip()
            if item["name"] or item["url"]:
                self.links.append(item)
            self.current_link = None
        if tag == "script" and self.current_script is not None:
            self.scripts.append("".join(self.current_script))
            self.current_script = None


def _walk_json(value, found):
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = re.sub(r"[^a-z]", "", str(key).lower())
            if normalized in UPLOADER_KEYS | AUTHOR_KEYS:
                entries = item if isinstance(item, list) else [item]
                for entry in entries:
                    if isinstance(entry, str):
                        found.append({
                            "kind": "uploader" if normalized in UPLOADER_KEYS else "page_author",
                            "name": entry, "url": None, "evidence": "json-ld:" + str(key),
                        })
                    elif isinstance(entry, dict):
                        name = entry.get("name") or entry.get("alternateName")
                        url = entry.get("url") or entry.get("@id")
                        if name or url:
                            found.append({
                                "kind": "uploader" if normalized in UPLOADER_KEYS else "page_author",
                                "name": str(name) if name else None,
                                "url": str(url) if url else None,
                                "evidence": "json-ld:" + str(key),
                            })
            _walk_json(item, found)
    elif isinstance(value, list):
        for item in value:
            _walk_json(item, found)


def inspect_html(html: str, base_url: str = "") -> dict:
    parser = AttributionParser(base_url)
    parser.feed(html)
    results = parser.meta + parser.microdata + parser.links
    for script in parser.scripts:
        try:
            data = json.loads(script)
        except (TypeError, ValueError):
            continue
        structured = []
        _walk_json(data, structured)
        results.extend(structured)

    normalized = []
    seen = set()
    for item in results:
        url = public_url(item.get("url") or "", base_url) if item.get("url") else None
        record = {
            "kind": item["kind"],
            "name": (item.get("name") or "").strip() or None,
            "public_profile_or_author_url": url,
            "evidence": item["evidence"],
        }
        key = tuple(record.values())
        if key not in seen:
            seen.add(key)
            normalized.append(record)

    return {
        "explicit_attributions": normalized,
        "uploader_identified": any(x["kind"] == "uploader" and (x["name"] or x["public_profile_or_author_url"])
                                   for x in normalized),
        "note": (
            "Only explicit attribution in the supplied HTML is reported. "
            "A page author is not necessarily the uploader; attribution does not prove ownership or licensing."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", type=Path)
    ap.add_argument("--base-url", default="")
    ap.add_argument("--json", dest="json_path", type=Path)
    args = ap.parse_args()
    report = inspect_html(args.html.read_text(encoding="utf-8", errors="replace"), args.base_url)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
