"""Orchestrate legacy report adaptation into a validated evidence graph.

This module deliberately does not invoke the legacy analyzer. Callers provide
its already-produced report together with the immutable context for the exact
source document. The engine performs no I/O or network activity.
"""
from __future__ import annotations

from .adapters import LegacyReportAdapter
from .document_context import AnalysisContext
from .evidence_model import EvidenceGraphContainer
from .registry import EvidenceRegistry


class EvidenceEngine:
    """Convert one legacy analysis report into a deterministic evidence graph.

    Each call uses a fresh registry, so the returned graph represents exactly
    one report/document and cannot accidentally include records from a prior
    invocation. Adapter and registry validation errors are intentionally
    propagated to the caller without being hidden or reclassified.
    """

    def __init__(self, adapter: LegacyReportAdapter | None = None) -> None:
        self._adapter = adapter if adapter is not None else LegacyReportAdapter()

    def process(
        self,
        report: dict,
        context: AnalysisContext,
    ) -> EvidenceGraphContainer:
        """Adapt a legacy report and return its validated immutable graph."""
        if not isinstance(context, AnalysisContext):
            raise TypeError("context must be an AnalysisContext.")

        adapted_graph = self._adapter.adapt(report, context)
        if not isinstance(adapted_graph, EvidenceGraphContainer):
            raise TypeError("adapter must return an EvidenceGraphContainer.")

        registry = EvidenceRegistry()
        registry.register_graph(adapted_graph)
        return registry.build()
