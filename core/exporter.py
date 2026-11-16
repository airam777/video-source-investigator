"""Deterministic JSON export for immutable evidence graphs.

The manifest is a read-only serialization of the evidence model. Statistics
are derived separately and the SHA-256 digest covers only canonical manifest
bytes, avoiding a self-referential checksum.
"""
from __future__ import annotations

import hashlib
import json
from enum import Enum
from pathlib import Path
from typing import Any

from .evidence_model import EvidenceGraphContainer, EvidenceObservation, EvidenceRelation


SCHEMA_VERSION = "1.0"
TOOL_NAME = "video-source-investigator"


def _plain_value(value: Any) -> Any:
    """Convert immutable model values into JSON-compatible primitives."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict) or hasattr(value, "items"):
        return {str(key): _plain_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_value(item) for item in value]
    return value


def _serialize_observation(item: EvidenceObservation) -> dict[str, Any]:
    return {
        "id": item.observation_id,
        "kind": item.kind,
        "document_sha256": item.document_sha256,
        "locator": item.locator,
        "epistemic_status": item.evidence_status.value,
        "confidence": item.detector_confidence,
        "adapter_id": item.adapter_id,
        "adapter_version": item.adapter_version,
        "normalized_value": {
            "value_type": item.value.value_type,
            "value": _plain_value(item.value.value),
        },
        "caveats": list(item.caveats),
    }


def _serialize_relation(item: EvidenceRelation) -> dict[str, Any]:
    return {
        "id": item.relation_id,
        "relation_type": item.relation_type.value,
        "source_id": item.source_id,
        "target_id": item.target_id,
        "source_observation_ids": list(item.source_observation_ids),
        "epistemic_status": item.evidence_status.value,
    }


def build_evidence_payload(graph: EvidenceGraphContainer) -> dict[str, Any]:
    """Build a deterministic audit envelope without mutating the graph.

    generated_at and engine_version are null until the project defines a
    reproducible build/version source. A wall-clock timestamp would make two
    exports of identical evidence differ byte-for-byte.
    """
    if not isinstance(graph, EvidenceGraphContainer):
        raise TypeError("graph must be an EvidenceGraphContainer.")

    observations = sorted(graph.observations, key=lambda item: item.observation_id)
    relations = sorted(graph.relations, key=lambda item: item.relation_id)
    manifest = {
        "observations": [_serialize_observation(item) for item in observations],
        "relations": [_serialize_relation(item) for item in relations],
    }

    status_counts = {"fact": 0, "derived": 0, "unknown": 0}
    for item in observations:
        status_counts[item.evidence_status.value] += 1

    canonical_manifest = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    content_hash = hashlib.sha256(canonical_manifest).hexdigest()

    return {
        "schema_version": SCHEMA_VERSION,
        "audit_metadata": {
            "tool_name": TOOL_NAME,
            "generated_at": None,
            "engine_version": None,
        },
        "statistics": {
            "total_observations": len(observations),
            "total_relations": len(relations),
            "epistemic_breakdown": status_counts,
        },
        "manifest": manifest,
        "content_hash": content_hash,
    }


def render_evidence_json(graph: EvidenceGraphContainer) -> str:
    """Return the complete audit envelope as stable, UTF-8 JSON text."""
    payload = build_evidence_payload(graph)
    return json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    ) + "\n"


def export_evidence(graph: EvidenceGraphContainer, destination: Path) -> dict[str, Any]:
    """Write a deterministic evidence audit envelope and return its payload."""
    path = Path(destination)
    rendered = render_evidence_json(graph)
    path.write_bytes(rendered.encode("utf-8"))
    return json.loads(rendered)
