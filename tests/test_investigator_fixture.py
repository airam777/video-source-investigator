import json
import tempfile
import unittest
from pathlib import Path

from investigator import inspect_file


FIXTURE = Path(__file__).parent / "fixtures" / "ali_g_safe_fixture.html"


class AliGSafeFixtureTests(unittest.TestCase):
    def test_investigator_runs_on_redacted_fixture(self):
        report = inspect_file(FIXTURE)
        rendered = json.dumps(report, ensure_ascii=False)
        self.assertIn("pf-storage1.premiumcdn.net", rendered)
        self.assertIn("pf-storage3.premiumcdn.net", rendered)
        self.assertIn("pf-storage5.premiumcdn.net", rendered)
        self.assertNotIn("REDACTED", rendered)
        self.assertNotIn("sample_1080p.mp4", rendered)
        self.assertNotIn("signature=", rendered)
        self.assertEqual(report["title"], "#Ali G - Gdo bít já (2026) CZ DABING - online ke zhlédnutí a stažení - Přehraj.to")

    def test_fixture_is_synthetic_and_does_not_claim_original_hash(self):
        raw = FIXTURE.read_bytes()
        self.assertNotIn(b"token=", raw.replace(b"token=REDACTED", b""))
        self.assertIn(b"sample_1080p.mp4", raw)
        # This fixture is deliberately altered; its digest is not the supplied
        # original HTML digest and must never be represented as such.
        import hashlib
        self.assertNotEqual(
            hashlib.sha256(raw).hexdigest(),
            "a337f6d3ceaf376ee24c07a865a38f49362208c44429eb662ba8f1f1acd10077",
        )


if __name__ == "__main__":
    unittest.main()
