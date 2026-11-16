import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analyze_page import analyze
from core.document_context import AnalysisContext
from core.engine import EvidenceEngine
from core.evidence_model import (
    EvidenceGraphContainer,
    EvidenceObservation,
    EvidenceStatus,
    NormalizedValue,
)
from core.exporter import build_evidence_payload, render_evidence_json


SAMPLE = """<!doctype html>
<html><head>
<title>Evidence export sample</title>
<link rel="canonical" href="https://example.test/evidence/1">
<meta property="og:video" content="https://cdn.example.test/private/file.mp4?token=EXPORT_CANARY">
</head><body><iframe src="https://embed.example.test/player/1"></iframe></body></html>"""


class EvidenceExporterTests(unittest.TestCase):
    def _graph(self):
        raw = SAMPLE.encode("utf-8")
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "sample.html"
            source.write_bytes(raw)
            report = analyze(source, "https://example.test/evidence/1")
        context = AnalysisContext(
            raw,
            source_name="sample.html",
            base_url="https://example.test/evidence/1",
        )
        return EvidenceEngine().process(report, context)

    def test_manifest_statistics_and_hash_are_consistent(self):
        graph = self._graph()
        payload = build_evidence_payload(graph)
        manifest = payload["manifest"]
        stats = payload["statistics"]

        self.assertEqual(stats["total_observations"], len(manifest["observations"]))
        self.assertEqual(stats["total_relations"], len(manifest["relations"]))
        self.assertEqual(
            sum(stats["epistemic_breakdown"].values()),
            stats["total_observations"],
        )
        canonical = json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(payload["content_hash"], hashlib.sha256(canonical).hexdigest())

    def test_export_is_byte_for_byte_deterministic(self):
        graph = self._graph()
        self.assertEqual(render_evidence_json(graph), render_evidence_json(graph))

    def test_serialization_preserves_all_model_fields(self):
        graph = self._graph()
        payload = build_evidence_payload(graph)
        self.assertEqual(
            [item["id"] for item in payload["manifest"]["observations"]],
            sorted(item.observation_id for item in graph.observations),
        )
        self.assertEqual(
            [item["id"] for item in payload["manifest"]["relations"]],
            sorted(item.relation_id for item in graph.relations),
        )
        for item in payload["manifest"]["observations"]:
            self.assertIn("document_sha256", item)
            self.assertIn("normalized_value", item)
            self.assertIn("epistemic_status", item)

    def test_unknown_status_is_counted_without_rewriting_records(self):
        digest = "a" * 64
        observation = EvidenceObservation(
            observation_id="unknown-1",
            kind="test.unknown",
            value=NormalizedValue("string", "unresolved"),
            document_sha256=digest,
            locator="test.unknown",
            evidence_status=EvidenceStatus.UNKNOWN,
        )
        graph = EvidenceGraphContainer((observation,))
        payload = build_evidence_payload(graph)
        self.assertEqual(payload["statistics"]["epistemic_breakdown"]["unknown"], 1)
        self.assertEqual(observation.evidence_status, EvidenceStatus.UNKNOWN)

    def test_cli_export_twice_produces_identical_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "input.html"
            first = root / "first.json"
            second = root / "second.json"
            source.write_text(SAMPLE, encoding="utf-8")

            for destination in (first, second):
                subprocess.run(
                    [
                        sys.executable,
                        "analyze_page.py",
                        str(source),
                        "--base-url",
                        "https://example.test/evidence/1",
                        "--export-evidence",
                        str(destination),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            first_bytes = first.read_bytes()
            second_bytes = second.read_bytes()
            self.assertEqual(first_bytes, second_bytes)
            exported = json.loads(first_bytes)
            self.assertEqual(exported["audit_metadata"]["generated_at"], None)
            self.assertNotIn("EXPORT_CANARY", first_bytes.decode("utf-8"))
            self.assertNotIn("private/file.mp4", first_bytes.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
