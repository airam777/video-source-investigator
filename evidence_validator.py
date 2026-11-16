"""Validate provenance and evidence labels in offline investigation reports.

This module does not fetch URLs, resolve streams, inspect tokens, or attribute
uploads to people. It validates only the report data supplied to it.
"""
from __future__ import annotations

import re
from typing import Any

from evidence_schema_mapping import EVIDENCE_CAVEATS, EVIDENCE_VALIDATION_RULES

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.I)
_SENSITIVE_QUERY_RE = re.compile(
    r"[?&](?:token|expires|signature|sig|auth|key|policy|credential|jwt|session|pass)"
    r"(?:=|%3d)",
    re.I,
)
_SECRET_ASSIGNMENT_RE = re.compile(
    r"""\b(?:token|signature|authorization|cookie|session(?:_?id)?)\b\s*[:=]\s*["'][^"']+["']""",
    re.I,
)


def evidence_category(field: str) -> str:
    """Return the schema category for a named evidence field."""
    for category, fields in EVIDENCE_VALIDATION_RULES.items():
        if field in fields:
            return category
    return "unclassified"


def validate_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return validation errors/warnings without modifying the report."""
    errors: list[str] = []
    warnings: list[str] = []

    provenance = report.get("source_provenance", {})
    digest = provenance.get("raw_html_sha256")
    if digest is not None and not _SHA256_RE.fullmatch(str(digest)):
        errors.append("raw_html_sha256 must be a 64-character hexadecimal SHA-256 digest")

    byte_count = provenance.get("raw_html_bytes")
    if byte_count is not None and (not isinstance(byte_count, int) or byte_count < 0):
        errors.append("raw_html_bytes must be a non-negative integer")

    if provenance.get("raw_html_available_in_conversation") and not digest:
        warnings.append("source is marked available but no raw HTML digest is recorded")

    if provenance.get("project_parser_executed") is False:
        warnings.append("project parser execution is not established")

    observations = report.get("parsed_observations", {})
    if observations.get("cdn_hosts"):
        warnings.append(EVIDENCE_CAVEATS["cdn_storage_hosts"])
    if observations.get("uploader_label") or observations.get("uploader_string"):
        warnings.append(EVIDENCE_CAVEATS["uploader_string"])
    if observations.get("streaming_variants_mp4"):
        warnings.append(EVIDENCE_CAVEATS["streaming_variants_mp4"])

    for field in ("original_file_format", "original_file_size_bytes"):
        if field in observations:
            warnings.append(
                f"{field} is not accepted as a direct HTML observation; attach separate provenance"
            )

    serialized = _flatten_strings(report)
    for value in serialized:
        if _SENSITIVE_QUERY_RE.search(value):
            errors.append("report contains a URL with sensitive query parameters")
            break
        if _SECRET_ASSIGNMENT_RE.search(value):
            errors.append("report appears to contain a raw secret/token assignment")
            break

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": sorted(set(warnings)),
        "schema_categories": sorted(EVIDENCE_VALIDATION_RULES),
    }


def _flatten_strings(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _flatten_strings(key)
            yield from _flatten_strings(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _flatten_strings(item)
    elif isinstance(value, str):
        yield value


def safe_host_reference(url: str) -> str:
    """Reduce an HTTP(S) URL to scheme + hostname; discard path and query."""
    from urllib.parse import urlsplit

    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "[reference hidden]"
    return f"{parsed.scheme}://{parsed.hostname}/[reference hidden]"
