import json
import tempfile
import unittest
from pathlib import Path

from analyze_page import analyze
from core.document_context import AnalysisContext
from core.engine import EvidenceEngine
from core.evidence_model import EvidenceGraphContainer, EvidenceStatus, RelationType


SAMPLE = """<!doctype html>
<html><head>
<title>Engine integration sample</title>
<link rel="canonical" href="https://example.test/item/123">
<meta property="og:title" content="Engine integration sample">
<meta property="og:video" content="https://cdn.example.test/private/video.mp4?token=ENGINE_CANARY">
<meta name="author" content="Example Editorial">
</head><body>
<iframe src="https://embed.example.test/player/123"></iframe>
<video><source src="https://cdn.example.test/private/movie.mp4?signature=ENGINE_CANARY" type="video/mp4"></video>
<script>var player = "videojs";</script>
</body></html>"""


class EvidenceEngineIntegrationTests(unittest.TestCase):
    def _analyze_sample(self):
        raw = SAMPLE.encode("utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "engine-sample.html"
            path.write_bytes(raw)
            report = analyze(path, "https://example.test/item/123")
        context = AnalysisContext(
            raw,
            source_name="engine-sample.html",
            base_url="https://example.test/item/123",
        )
        return report, context

    def test_full_legacy_report_to_immutable_graph_flow(self):
        report, context = self._analyze_sample()
        graph = EvidenceEngine().process(report, context)

        self.assertIsInstance(graph, EvidenceGraphContainer)
        self.assertTrue(graph.observations)
        self.assertTrue(all(
            item.document_sha256 == context.document_sha256
            for item in graph.observations
        ))
        self.assertTrue(all(
            item.evidence_status in (EvidenceStatus.FACT, EvidenceStatus.DERIVED, EvidenceStatus.UNKNOWN)
            for item in graph.observations
        ))
        observation_ids = {item.observation_id for item in graph.observations}
        for edge in graph.relations:
            self.assertIn(edge.source_id, observation_ids)
            self.assertIn(edge.target_id, observation_ids)
            self.assertTrue(set(edge.source_observation_ids).issubset(observation_ids))

    def test_engine_output_is_deterministic(self):
        report, context = self._analyze_sample()
        engine = EvidenceEngine()
        first = engine.process(report, context)
        second = engine.process(report, context)

        self.assertEqual(first, second)
        self.assertEqual(
            [item.observation_id for item in first.observations],
            sorted(item.observation_id for item in first.observations),
        )
        self.assertEqual(
            [item.relation_id for item in first.relations],
            sorted(item.relation_id for item in first.relations),
        )

    def test_graph_preserves_provenance_backed_reference_relations(self):
        report, context = self._analyze_sample()
        graph = EvidenceEngine().process(report, context)

        reference_edges = [
            edge for edge in graph.relations
            if edge.relation_type == RelationType.REFERENCES
        ]
        self.assertTrue(reference_edges)
        for edge in reference_edges:
            self.assertEqual(edge.source_observation_ids, (edge.source_id,))

    def test_canary_secrets_and_media_paths_are_absent_from_graph(self):
        report, context = self._analyze_sample()
        graph = EvidenceEngine().process(report, context)
        rendered = json.dumps([
            {
                "id": item.observation_id,
                "kind": item.kind,
                "value": item.value.value,
                "locator": item.locator,
            }
            for item in graph.observations
        ], default=str)

        self.assertNotIn("ENGINE_CANARY", rendered)
        self.assertNotIn("private/video.mp4", rendered)
        self.assertNotIn("private/movie.mp4", rendered)

    def test_engine_does_not_accumulate_records_between_calls(self):
        report, context = self._analyze_sample()
        engine = EvidenceEngine()
        first = engine.process(report, context)
        second = engine.process({}, context)

        self.assertEqual(first, EvidenceEngine().process(report, context))
        self.assertEqual(second.observations, ())
        self.assertEqual(second.relations, ())

    def test_rejects_invalid_context(self):
        with self.assertRaisesRegex(TypeError, "AnalysisContext"):
            EvidenceEngine().process({}, {})


if __name__ == "__main__":
    unittest.main()
