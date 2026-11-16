"""Safe JSON and Markdown export for offline investigation reports.

The exporter is deliberately offline. It redacts credentials and hides resource
paths before writing reports; it never resolves, fetches, or downloads media.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from evidence_validator import validate_report

SENSITIVE_KEY = re.compile(
    r"token|expires|signature|sig|auth|key|policy|credential|jwt|session|pass",
    re.I,
)
SECRET_ASSIGNMENT = re.compile(
    r"""(?i)\b(token|signature|authorization|cookie|session(?:_?id)?)\b\s*([:=])\s*("[^"]*"|'[^']*'|[^\s,;&]+)"""
)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
RESOURCE_SUFFIXES = (".mp4", ".m3u8", ".mpd", ".webm", ".mov", ".m4v", ".vtt", ".srt")


def redact_url(value: str) -> str:
    """Keep only scheme/host for media references; redact sensitive query values."""
    candidate = value.rstrip("),;]")
    try:
        parts = urlsplit(candidate)
        if parts.scheme not in {"http", "https"} or not parts.hostname:
            return value
        host = parts.hostname
        if parts.port:
            host = f"{host}:{parts.port}"
        if parts.path.lower().endswith(RESOURCE_SUFFIXES):
            label = "track" if parts.path.lower().endswith((".vtt", ".srt")) else "media"
            return urlunsplit((parts.scheme, host, f"/[{label} URL hidden]", "", ""))
        query = [
            (key, "[REDACTED]" if SENSITIVE_KEY.search(key) else val)
            for key, val in parse_qsl(parts.query, keep_blank_values=True)
        ]
        return urlunsplit((parts.scheme, host, parts.path, urlencode(query), ""))
    except ValueError:
        return "[URL hidden]"


def sanitize_value(value: Any) -> Any:
    """Return a recursively sanitized copy; never mutate the caller's report."""
    if isinstance(value, dict):
        return {str(k): sanitize_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [sanitize_value(item) for item in value]
    if isinstance(value, str):
        text = URL_RE.sub(lambda match: redact_url(match.group(0)), value)
        return SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]", text)
    return value


def _markdown_value(value: Any) -> str:
    if value is None:
        return "_neuvedené_"
    if isinstance(value, (dict, list)):
        return "`" + json.dumps(value, ensure_ascii=False, sort_keys=True) + "`"
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: dict[str, Any]) -> str:
    """Render a sanitized report as a readable Markdown document."""
    safe = sanitize_value(report)
    lines = [
        "# Exportovaný technický report",
        "",
        "> Offline analýza dodaného HTML. Report nepreukazuje vlastníctvo obsahu ani licenciu.",
        "",
    ]
    for section in ("investigation_target", "evidence_status"):
        if section in safe:
            lines.append(f"- **{section}:** {_markdown_value(safe[section])}")
    for section in ("source_provenance", "parsed_observations", "not_verified_or_not_present", "security"):
        data = safe.get(section)
        if not isinstance(data, dict):
            continue
        lines.extend(["", f"## {section.replace('_', ' ').title()}", "", "| Pole | Hodnota |", "|---|---|"])
        for key, value in data.items():
            lines.append(f"| {_markdown_value(key)} | {_markdown_value(value)} |")
    validation = validate_report(report)
    lines.extend([
        "",
        "## Kontrola exportu",
        "",
        f"- **Vstupný report validný pred redakciou:** {'áno' if validation['valid'] else 'nie'}",
        f"- **Počet upozornení validátora:** {len(validation['warnings'])}",
        "- **Redakcia:** URL mediálnych/titulkových súborov a citlivé hodnoty sú skryté.",
        "- **Sieťové požiadavky:** nevykonávajú sa.",
        "",
    ])
    return "\n".join(lines)


def export_report(report: dict[str, Any], json_path: Path | None = None,
                  markdown_path: Path | None = None) -> dict[str, Any]:
    """Write requested sanitized formats and return the sanitized report."""
    safe = sanitize_value(report)
    if json_path is not None:
        json_path.write_text(json.dumps(safe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if markdown_path is not None:
        markdown_path.write_text(render_markdown(safe) + "", encoding="utf-8")
    return safe


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_json", type=Path, help="Existing JSON investigation report")
    parser.add_argument("--json", type=Path, help="Destination for sanitized JSON")
    parser.add_argument("--markdown", type=Path, help="Destination for Markdown report")
    args = parser.parse_args()
    report = json.loads(args.report_json.read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        parser.error("Input JSON must contain an object at its root")
    if args.json is None and args.markdown is None:
        parser.error("Specify at least one of --json or --markdown")
    export_report(report, args.json, args.markdown)
    print("Export completed with URL/secret redaction.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
