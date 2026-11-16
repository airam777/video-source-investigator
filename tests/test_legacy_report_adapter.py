import json
import unittest

from core.adapters import LegacyReportAdapter
from core.document_context import AnalysisContext
from core.evidence_model import EvidenceStatus, RelationType


class LegacyReportAdapterTests(unittest.TestCase):
    def setUp(self):
        self.context = AnalysisContext(
            b"<html><title>Example</title></html>",
            source_name="saved-page.html",
            base_url="https://example.test/item/1",
        )
        self.report = {
            "title": "Example video",
            "provider_hosts": ["cdn.example.test"],
            "uploader_identified": False,
            "visible_references": [
                {
                    "kind": "media-reference",
                    "attribute": "inline",
                    "url": "https://cdn.example.test/private/movie.mp4?token=DO_NOT_KEEP",
                    "host": "cdn.example.test",
                    "media_reference": True,
                }
            ],
            "interpretation": ["A host does not prove uploader identity."],
            "unrecognized_internal_field": "must not be copied",
        }

    def test_adapts_allowlisted_legacy_fields_to_observations(self):
        graph = LegacyReportAdapter().adapt(self.report, self.context)
        kinds = {item.kind for item in graph.observations}
        self.assertIn("legacy_report.title", kinds)
        self.assertIn("legacy_report.provider_hosts", kinds)
        self.assertNotIn("legacy_report.unrecognized_internal_field", kinds)

    def test_marks_extracted_facts_and_interpretations_separately(self):
        graph = LegacyReportAdapter().adapt(self.report, self.context)
        by_kind = {item.kind: item for item in graph.observations}
        self.assertEqual(by_kind["legacy_report.title"].evidence_status, EvidenceStatus.FACT)
        self.assertEqual(by_kind["legacy_report.interpretation"].evidence_status, EvidenceStatus.DERIVED)
        self.assertEqual(by_kind["legacy_report.uploader_identified"].evidence_status, EvidenceStatus.DERIVED)

    def test_redacts_urls_and_sensitive_fields_recursively(self):
        graph = LegacyReportAdapter().adapt(self.report, self.context)
        rendered = json.dumps([
            {"kind": item.kind, "value": item.value.value}
            for item in graph.observations
        ], default=str)
        self.assertIn("cdn.example.test", rendered)
        self.assertNotIn("private/movie.mp4", rendered)
        self.assertNotIn("DO_NOT_KEEP", rendered)
        self.assertNotIn("token", rendered)

    def test_redacts_urls_embedded_in_report_text(self):
        report = {"interpretation": [
            "Reference: https://cdn.example.test/private/file.mp4?token=DO_NOT_KEEP."
        ]}
        graph = LegacyReportAdapter().adapt(report, self.context)
        rendered = json.dumps([item.value.value for item in graph.observations], default=str)
        self.assertIn("cdn.example.test", rendered)
        self.assertNotIn("private/file.mp4", rendered)
        self.assertNotIn("DO_NOT_KEEP", rendered)

    def test_rejects_host_field_containing_url_path_or_query(self):
        report = {
            "visible_references": [{
                "host": "cdn.example.test/private/path?token=DO_NOT_KEEP",
                "url": "https://cdn.example.test/private/path?token=DO_NOT_KEEP",
            }]
        }
        graph = LegacyReportAdapter().adapt(report, self.context)
        rendered = json.dumps(
            [{"kind": item.kind, "value": item.value.value} for item in graph.observations],
            default=str,
        )
        self.assertNotIn("private/path", rendered)
        self.assertNotIn("DO_NOT_KEEP", rendered)
        self.assertFalse(any(item.kind == "legacy_report.reference_host" for item in graph.observations))
        self.assertEqual(len(graph.relations), 0)

    def test_builds_provenance_backed_reference_relation(self):
        graph = LegacyReportAdapter().adapt(self.report, self.context)
        self.assertEqual(len(graph.relations), 1)
        relation = graph.relations[0]
        self.assertEqual(relation.relation_type, RelationType.REFERENCES)
        self.assertEqual(relation.evidence_status, EvidenceStatus.FACT)
        self.assertEqual(relation.source_observation_ids, (relation.source_id,))
        self.assertIn(relation.target_id, {item.observation_id for item in graph.observations})

    def test_adaptation_is_deterministic(self):
        adapter = LegacyReportAdapter()
        first = adapter.adapt(self.report, self.context)
        second = adapter.adapt(self.report, self.context)
        self.assertEqual(
            [item.observation_id for item in first.observations],
            [item.observation_id for item in second.observations],
        )
        self.assertEqual(
            [item.relation_id for item in first.relations],
            [item.relation_id for item in second.relations],
        )

    def test_rejects_wrong_input_types(self):
        adapter = LegacyReportAdapter()
        with self.assertRaises(TypeError):
            adapter.adapt([], self.context)
        with self.assertRaises(TypeError):
            adapter.adapt(self.report, {})


if __name__ == "__main__":
    unittest.main()
