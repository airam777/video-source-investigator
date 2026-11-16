"""Stable document identities and deterministic observation identifiers."""
from __future__ import annotations
import hashlib, json, math, re, unicodedata
from dataclasses import dataclass
from typing import Any
_SHA256 = re.compile(r"[a-f0-9]{64}\Z")
_INT_MIN, _INT_MAX = -(2 ** 63), 2 ** 63 - 1
@dataclass(frozen=True, slots=True)
class DocumentIdentity:
    sha256: str
    size_bytes: int
    def __post_init__(self) -> None:
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256): raise ValueError("sha256 must be 64 lowercase hexadecimal characters.")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int) or self.size_bytes < 0: raise ValueError("size_bytes must be a non-negative integer.")
    @classmethod
    def from_bytes(cls, content: bytes) -> "DocumentIdentity":
        if not isinstance(content, bytes): raise TypeError("content must be bytes.")
        return cls(hashlib.sha256(content).hexdigest(), len(content))
class _PayloadValidator:
    def __init__(self, max_depth: int, max_total_elements: int, max_string_length: int, max_aggregated_string_bytes: int) -> None:
        self.max_depth, self.max_total_elements = max_depth, max_total_elements
        self.max_string_length, self.max_aggregated_string_bytes = max_string_length, max_aggregated_string_bytes
        self.element_count = 0; self.string_bytes = 0
    def _count(self) -> None:
        self.element_count += 1
        if self.element_count > self.max_total_elements: raise ValueError("Payload contains too many elements.")
    def _string(self, value: str) -> str:
        if len(value) > self.max_string_length: raise ValueError("Payload string exceeds the per-string limit.")
        normalized = unicodedata.normalize("NFC", value); self.string_bytes += len(normalized.encode("utf-8"))
        if self.string_bytes > self.max_aggregated_string_bytes: raise ValueError("Payload exceeds the aggregated UTF-8 string budget.")
        return normalized
    def validate(self, value: Any, depth: int = 0) -> Any:
        self._count()
        if depth > self.max_depth: raise ValueError("Payload nesting exceeds the maximum depth.")
        if value is None or isinstance(value, bool): return value
        if isinstance(value, str): return self._string(value)
        if isinstance(value, int):
            if not _INT_MIN <= value <= _INT_MAX: raise ValueError("Payload integer is outside signed 64-bit range.")
            return value
        if isinstance(value, float):
            if not math.isfinite(value): raise ValueError("Non-finite floats are not allowed.")
            return value
        if isinstance(value, (list, tuple)): return [self.validate(x, depth + 1) for x in value]
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                if not isinstance(key, str): raise ValueError("Payload dictionary keys must be strings.")
                normalized_key = self._string(key); self._count()
                if normalized_key in result: raise ValueError("Dictionary keys collide after NFC normalization.")
                result[normalized_key] = self.validate(item, depth + 1)
            return result
        raise ValueError("Unsupported payload value type.")
def canonicalize_payload(payload: Any, *, max_depth: int = 10, max_total_elements: int = 5000, max_string_length: int = 10000, max_aggregated_string_bytes: int = 512000) -> Any:
    limits = (max_depth, max_total_elements, max_string_length, max_aggregated_string_bytes)
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 1 for x in limits): raise ValueError("Payload limits must be positive integers.")
    return _PayloadValidator(*limits).validate(payload)
def compute_observation_id(document_sha256: str, source_type: str, locator: str, payload: Any, occurrence_index: int = 0, max_byte_budget: int = 1000000) -> str:
    if not isinstance(document_sha256, str) or not _SHA256.fullmatch(document_sha256): raise ValueError("document_sha256 must be a lowercase SHA-256 digest.")
    if not isinstance(source_type, str) or not source_type or not isinstance(locator, str) or not locator: raise ValueError("source_type and locator must be non-empty strings.")
    source_type, locator = unicodedata.normalize("NFC", source_type), unicodedata.normalize("NFC", locator)
    if len(source_type) > 256 or len(locator) > 2048: raise ValueError("source_type or locator exceeds its length limit.")
    if isinstance(occurrence_index, bool) or not isinstance(occurrence_index, int) or not 0 <= occurrence_index <= 2**31 - 1: raise ValueError("occurrence_index must be an integer in the supported range.")
    if isinstance(max_byte_budget, bool) or not isinstance(max_byte_budget, int) or max_byte_budget < 1: raise ValueError("max_byte_budget must be a positive integer.")
    structure = {"document_sha256": document_sha256, "source_type": source_type, "locator": locator, "payload": canonicalize_payload(payload), "occurrence_index": occurrence_index}
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False); digest = hashlib.sha256(); total = 0
    for chunk in encoder.iterencode(structure):
        encoded = chunk.encode("utf-8"); total += len(encoded)
        if total > max_byte_budget: raise ValueError("Canonical observation payload exceeds byte budget.")
        digest.update(encoded)
    return digest.hexdigest()
