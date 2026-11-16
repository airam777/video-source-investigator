"""Immutable normalized evidence records and a validated directed evidence graph."""
from __future__ import annotations
import math, re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any
from .identity import canonicalize_payload
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
class EvidenceStatus(str, Enum):
    FACT = "fact"
    DERIVED = "derived"
    UNKNOWN = "unknown"
class RelationType(str, Enum):
    OBSERVED_IN = "observed_in"
    DECLARES = "declares"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    RELATED_TO = "related_to"
def _freeze(value: Any) -> Any:
    if isinstance(value, dict): return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    return value
@dataclass(frozen=True, slots=True)
class NormalizedValue:
    value_type: str
    value: Any
    def __post_init__(self) -> None:
        allowed = {"string", "integer", "number", "boolean", "null", "object", "array"}
        if self.value_type not in allowed: raise ValueError("Unsupported normalized value type.")
        normalized = canonicalize_payload(self.value)
        valid = {
            "string": isinstance(normalized, str),
            "integer": isinstance(normalized, int) and not isinstance(normalized, bool),
            "number": isinstance(normalized, (int, float)) and not isinstance(normalized, bool),
            "boolean": isinstance(normalized, bool), "null": normalized is None,
            "object": isinstance(normalized, dict), "array": isinstance(normalized, list),
        }
        if not valid[self.value_type]: raise ValueError(f"{self.value_type} value_type does not match value.")
        object.__setattr__(self, "value", _freeze(normalized))
@dataclass(frozen=True, slots=True)
class EvidenceObservation:
    observation_id: str
    kind: str
    value: NormalizedValue
    document_sha256: str
    locator: str
    evidence_status: EvidenceStatus = EvidenceStatus.FACT
    detector_confidence: float | None = None
    adapter_id: str = "generic"
    adapter_version: str = "1"
    caveats: tuple[str, ...] = ()
    def __post_init__(self) -> None:
        if not isinstance(self.observation_id, str) or not _ID.fullmatch(self.observation_id): raise ValueError("Invalid observation_id.")
        if not isinstance(self.kind, str) or not _ID.fullmatch(self.kind): raise ValueError("Invalid observation kind.")
        if not isinstance(self.document_sha256, str) or not _SHA256.fullmatch(self.document_sha256): raise ValueError("document_sha256 must be a lowercase SHA-256 digest.")
        if not isinstance(self.locator, str) or not self.locator or len(self.locator) > 2048: raise ValueError("locator must be a non-empty string of at most 2048 characters.")
        if not isinstance(self.value, NormalizedValue): raise TypeError("value must be a NormalizedValue.")
        if not isinstance(self.evidence_status, EvidenceStatus): object.__setattr__(self, "evidence_status", EvidenceStatus(self.evidence_status))
        if self.detector_confidence is not None and (isinstance(self.detector_confidence, bool) or not isinstance(self.detector_confidence, (int, float)) or not math.isfinite(self.detector_confidence) or not 0 <= self.detector_confidence <= 1):
            raise ValueError("detector_confidence must be finite and within [0, 1].")
        if not isinstance(self.adapter_id, str) or not _ID.fullmatch(self.adapter_id): raise ValueError("Invalid adapter_id.")
        if not isinstance(self.adapter_version, str) or not self.adapter_version or len(self.adapter_version) > 64: raise ValueError("Invalid adapter_version.")
        if not isinstance(self.caveats, (tuple, list)) or len(self.caveats) > 100 or any(not isinstance(x, str) or len(x) > 1000 for x in self.caveats): raise ValueError("Invalid caveats.")
        object.__setattr__(self, "caveats", tuple(self.caveats))
@dataclass(frozen=True, slots=True)
class EvidenceRelation:
    relation_id: str
    relation_type: RelationType
    source_id: str
    target_id: str
    source_observation_ids: tuple[str, ...]
    evidence_status: EvidenceStatus = EvidenceStatus.FACT
    def __post_init__(self) -> None:
        if not isinstance(self.relation_id, str) or not _ID.fullmatch(self.relation_id): raise ValueError("Invalid relation_id.")
        if not isinstance(self.relation_type, RelationType): object.__setattr__(self, "relation_type", RelationType(self.relation_type))
        for name in ("source_id", "target_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not _ID.fullmatch(value): raise ValueError("Invalid relation endpoint.")
        ids = tuple(self.source_observation_ids)
        if not ids or any(not isinstance(x, str) or not _ID.fullmatch(x) for x in ids): raise ValueError("Relations must cite one or more valid source observations.")
        object.__setattr__(self, "source_observation_ids", ids)
        if not isinstance(self.evidence_status, EvidenceStatus): object.__setattr__(self, "evidence_status", EvidenceStatus(self.evidence_status))
@dataclass(frozen=True, slots=True)
class EvidenceGraphContainer:
    observations: tuple[EvidenceObservation, ...]
    relations: tuple[EvidenceRelation, ...] = ()
    def __post_init__(self) -> None:
        observations, relations = tuple(self.observations), tuple(self.relations)
        if len(observations) > 10000 or len(relations) > 20000: raise ValueError("Evidence graph exceeds configured size limits.")
        if any(not isinstance(x, EvidenceObservation) for x in observations): raise TypeError("observations must contain EvidenceObservation values.")
        if any(not isinstance(x, EvidenceRelation) for x in relations): raise TypeError("relations must contain EvidenceRelation values.")
        obs_by_id = {x.observation_id: x for x in observations}
        if len(obs_by_id) != len(observations): raise ValueError("Duplicate observation IDs.")
        rel_ids = [x.relation_id for x in relations]
        if len(set(rel_ids)) != len(rel_ids): raise ValueError("Duplicate relation IDs.")
        for edge in relations:
            if edge.source_id not in obs_by_id or edge.target_id not in obs_by_id: raise ValueError("Relation endpoint does not exist.")
            if any(x not in obs_by_id for x in edge.source_observation_ids): raise ValueError("Relation cites a missing source observation.")
        self._validate_derived_acyclic(relations)
        object.__setattr__(self, "observations", observations)
        object.__setattr__(self, "relations", relations)
    @staticmethod
    def _validate_derived_acyclic(relations: tuple[EvidenceRelation, ...]) -> None:
        adjacency: dict[str, list[str]] = {}
        for edge in relations:
            if edge.relation_type == RelationType.DERIVED_FROM: adjacency.setdefault(edge.source_id, []).append(edge.target_id)
        visited: set[str] = set(); visiting: set[str] = set()
        for root in adjacency:
            if root in visited: continue
            stack = [(root, False)]
            while stack:
                node, leaving = stack.pop()
                if leaving:
                    visiting.discard(node); visited.add(node); continue
                if node in visiting: raise ValueError("DERIVED_FROM relations must form an acyclic graph.")
                if node in visited: continue
                visiting.add(node); stack.append((node, True))
                for child in adjacency.get(node, ()):
                    if child in visiting: raise ValueError("DERIVED_FROM relations must form an acyclic graph.")
                    if child not in visited: stack.append((child, False))
