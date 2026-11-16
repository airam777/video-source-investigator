"""Compatibility bridge from legacy Video Core reports to the Evidence Model.

The adapter consumes already-produced report dictionaries. It never parses HTML,
fetches URLs, executes scripts, or invokes legacy analyzers itself.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from .document_context import AnalysisContext
from .evidence_model import (
    EvidenceGraphContainer,
    EvidenceObservation,
    EvidenceRelation,
    EvidenceStatus,
    NormalizedValue,
    RelationType,
)
from .identity import compute_observation_id
from .sanitization import validate_url

_SENSITIVE_KEY = re.compile(
    r"token|signature|authorization|cookie|session|password|credential|secret|"
    r"raw_url|media_url|file_path|local_path",
    re.I,
)
_SECRET_ASSIGNMENT = re.compile(
    r"""\b(?:token|signature|authorization|cookie|session(?:_?id)?)\b\s*[:=]\s*['"][^'"]+['"]""",
    re.I,
)
_FIELD_STATUS = {
    "title": EvidenceStatus.FACT,
    "provider_hosts": EvidenceStatus.FACT,
    "player_configurations": EvidenceStatus.FACT,
    "visible_references": EvidenceStatus.FACT,
    "explicit_attributions": EvidenceStatus.FACT,
    "declared_media_evidence": EvidenceStatus.FACT,
    "deferred_loader": EvidenceStatus.FACT,
    "catalog_results": EvidenceStatus.FACT,
    "source_provenance": EvidenceStatus.FACT,
    "uploader_identified": EvidenceStatus.DERIVED,
    "attribution_note": EvidenceStatus.DERIVED,
    "interpretation": EvidenceStatus.DERIVED,
}
_ALLOWED_FIELDS = frozenset(_FIELD_STATUS)


def _host_reference(value: str) -> str:
    try:
        validate_url(value)
        parsed = urlsplit(value)
    except ValueError:
        return "[reference hidden]"
    return f"{parsed.scheme.lower()}://{parsed.netloc}/[reference hidden]"


def _safe_value(value: Any, key: str = "") -> Any:
    """Copy report data while removing secrets and URL paths."""
    if key and _SENSITIVE_KEY.search(key):
        return None
    if isinstance(value, dict):
        safe = {}
        for child_key, child_value in value.items():
            if not isinstance(child_key, str) or _SENSITIVE_KEY.search(child_key):
                continue
            cleaned = _safe_value(child_value, child_key)
            if cleaned is not None:
                safe[child_key] = cleaned
        return safe
    if isinstance(value, (list, tuple)):
        return [cleaned for item in value
                if (cleaned := _safe_value(item)) is not None]
    if isinstance(value, str):
        candidate = value.strip()
        if _SECRET_ASSIGNMENT.search(candidate):
            return "[sensitive value redacted]"
        if candidate.startswith(("http://", "https://")):
            return _host_reference(candidate)
        def redact_match(match: re.Match[str]) -> str:
            raw_url = match.group(0).rstrip(".,;)]}")
            suffix = match.group(0)[len(raw_url):]
            return _host_reference(raw_url) + suffix
        return re.sub(r"https?://\\S+", redact_match, candidate)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:1000]


def _value_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


class LegacyReportAdapter:
    """Adapt the stable, redacted output of analyze_page.analyze()."""

    adapter_id = "video-core-legacy-report"
    adapter_version = "1"

    def adapt(
        self,
        report: dict[str, Any],
        context: AnalysisContext,
    ) -> EvidenceGraphContainer:
        if not isinstance(report, dict):
            raise TypeError("report must be a dictionary returned by the legacy analyzer")
        if not isinstance(context, AnalysisContext):
            raise TypeError("context must be an AnalysisContext")

        observations: list[EvidenceObservation] = []
        field_observations: dict[str, list[EvidenceObservation]] = {}

        for field_name in sorted(_ALLOWED_FIELDS):
            if field_name not in report:
                continue
            safe_value = _safe_value(report[field_name], field_name)
            if safe_value is None:
                continue
            status = _FIELD_STATUS[field_name]
            locator = f"report.{field_name}"
            observation = self._observation(
                context=context,
                kind=f"legacy_report.{field_name}",
                locator=locator,
                value=safe_value,
                status=status,
                occurrence_index=0,
            )
            observations.append(observation)
            field_observations[field_name] = [observation]

        # Preserve explicit host references as separate observations and connect
        # each visible-reference record to its host with a provenance-backed edge.
        relations: list[EvidenceRelation] = []
        for index, item in enumerate(report.get("visible_references", [])):
            if not isinstance(item, dict):
                continue
            host = item.get("host")
            source = next(
                (obs for obs in field_observations.get("visible_references", [])
                 if obs.locator == "report.visible_references"),
                None,
            )
            if not source or not isinstance(host, str) or not host:
                continue
            host_observation = self._observation(
                context=context,
                kind="legacy_report.reference_host",
                locator=f"report.visible_references[{index}].host",
                value=host,
                status=EvidenceStatus.FACT,
                occurrence_index=index + 1,
            )
            observations.append(host_observation)
            relation_payload = {
                "source": source.observation_id,
                "target": host_observation.observation_id,
                "relation": RelationType.REFERENCES.value,
            }
            relation_id = compute_observation_id(
                context.document_sha256,
                "legacy_relation",
                f"report.visible_references[{index}].host",
                relation_payload,
                occurrence_index=index,
            )
            relations.append(EvidenceRelation(
                relation_id=relation_id,
                relation_type=RelationType.REFERENCES,
                source_id=source.observation_id,
                target_id=host_observation.observation_id,
                source_observation_ids=(source.observation_id,),
                evidence_status=EvidenceStatus.FACT,
            ))

        return EvidenceGraphContainer(
            observations=tuple(observations),
            relations=tuple(relations),
        )

    def _observation(
        self,
        *,
        context: AnalysisContext,
        kind: str,
        locator: str,
        value: Any,
        status: EvidenceStatus,
        occurrence_index: int,
    ) -> EvidenceObservation:
        observation_id = compute_observation_id(
            context.document_sha256,
            self.adapter_id,
            locator,
            {"kind": kind, "value": value, "status": status.value},
            occurrence_index=occurrence_index,
        )
        return EvidenceObservation(
            observation_id=observation_id,
            kind=kind,
            value=NormalizedValue(_value_type(value), value),
            document_sha256=context.document_sha256,
            locator=locator,
            evidence_status=status,
            adapter_id=self.adapter_id,
            adapter_version=self.adapter_version,
        )
