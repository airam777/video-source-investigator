"""Immutable context for offline analysis of one supplied document."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import PurePath
from typing import Mapping, Any
from types import MappingProxyType
import hashlib
from .identity import DocumentIdentity, canonicalize_payload
from .sanitization import validate_url

def _freeze(value):
    if isinstance(value, dict): return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    return value

@dataclass(frozen=True, slots=True)
class AnalysisContext:
    content: bytes = field(repr=False)
    source_name: str = "<memory>"
    base_url: str | None = None
    capture_metadata: Mapping[str, Any] = field(default_factory=dict)
    identity: DocumentIdentity = field(init=False)
    def __post_init__(self) -> None:
        if not isinstance(self.content, bytes): raise TypeError("content must be immutable bytes.")
        if not isinstance(self.source_name, str) or not self.source_name or len(self.source_name) > 512:
            raise ValueError("source_name must be a non-empty string of at most 512 characters.")
        if "\\x00" in self.source_name: raise ValueError("source_name must not contain NUL.")
        object.__setattr__(self, "source_name", PurePath(self.source_name.replace("\\\\", "/")).name or "<memory>")
        if self.base_url is not None: validate_url(self.base_url)
        metadata = canonicalize_payload(dict(self.capture_metadata))
        object.__setattr__(self, "capture_metadata", _freeze(metadata))
        object.__setattr__(self, "identity", DocumentIdentity(hashlib.sha256(self.content).hexdigest(), len(self.content)))
    @property
    def text(self) -> str: return self.content.decode("utf-8", errors="replace")
    @property
    def document_sha256(self) -> str: return self.identity.sha256
    @property
    def size_bytes(self) -> int: return self.identity.size_bytes
