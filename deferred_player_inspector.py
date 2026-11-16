#!/usr/bin/env python3
"""Offline inspector for deferred player-loader declarations in saved HTML.

It reports what the page source declares; it never calls the endpoint.
"""
from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts: list[str] = []
        self.current: list[str] | None = None
        self.targets: set[str] = set()
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag.lower() == "script":
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.current is not None:
            self.scripts.append("".join(self.current))
            self.current = None


def inspect_html(path: Path) -> dict:
    parser = Inspector()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    source = "\n".join(parser.scripts)

    ajax_blocks = re.findall(r"\$\.ajax\s*\(\s*\{(.*?)\}\s*\)", source, re.S)
    declarations = []
    for block in ajax_blocks:
        url_match = re.search(r"""\burl\s*:\s*['"]([^'"]+)['"]""", block)
        method_match = re.search(r"""\bmethod\s*:\s*['"]([^'"]+)['"]""", block, re.I)
        type_match = re.search(r"""\btype\s*:\s*['"]([^'"]+)['"]""", block, re.I)
        data_match = re.search(r"\bdata\s*:\s*\{(.*?)\}", block, re.S)
        keys = []
        values = {}
        if data_match:
            for key, _quote, _value in re.findall(r"""([A-Za-z_$][\w$]*)\s*:\s*(['"])(.*?)\2""", data_match.group(1), re.S):
                keys.append(key)
                # Values can contain content identifiers; do not expose arbitrary values.
                values[key] = "[redacted]"
        endpoint = url_match.group(1) if url_match else None
        if endpoint:
            parsed_endpoint = urlparse(endpoint)
            endpoint = (parsed_endpoint.netloc + parsed_endpoint.path) if parsed_endpoint.netloc else parsed_endpoint.path
        declarations.append({
            "endpoint_declared_in_source": endpoint,
            "method": (method_match or type_match).group(1).upper() if (method_match or type_match) else "unspecified",
            "parameter_names": keys,
            "parameter_values": values,
            "invokes_network_request": True,
            "request_performed_by_this_tool": False,
        })

    selectors = sorted(set(re.findall(r"""\$\(\s*['"]#([^'"]+)['"]\s*\)""", source)))
    return {
        "file": path.name,
        "page_element_ids": sorted(parser.ids),
        "jquery_ajax_declarations": declarations,
        "jquery_id_selectors_in_scripts": selectors,
        "player_loader_present": bool(declarations),
        "media_urls_found": 0,
        "note": (
            "Static inspection only. This report does not call the declared endpoint, "
            "load third-party player pages, replay cookies, or resolve media streams."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("html", type=Path)
    ap.add_argument("--json", dest="json_path", type=Path)
    args = ap.parse_args()
    report = inspect_html(args.html)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.json_path:
        args.json_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
