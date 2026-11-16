import tempfile
import unittest
from pathlib import Path

from analyze_page import analyze


class CombinedReportTests(unittest.TestCase):
    def test_combines_provider_loader_and_media_evidence_without_playable_url(self):
        html = """
        <html><head><title>Authorized sample</title></head><body>
          <iframe data-src="https://voe.sx/e/example"></iframe>
          <video><source src="https://cdn.example.test/sample.mp4?token=secret" type="video/mp4"></video>
          <script>
            jwplayer("player").setup({file: "https://cdn.example.test/master.m3u8?sig=secret"});
            $.ajax({url: "/player/load", method: "POST", data: {id: "demo"}});
          </script>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "page.html"
            path.write_text(html, encoding="utf-8")
            report = analyze(path, "https://catalog.example.test/watch/1")

        self.assertEqual(report["title"], "Authorized sample")
        self.assertIn("voe.sx", report["provider_hosts"])
        self.assertTrue(report["deferred_loader"]["player_loader_present"])
        rendered = str(report)
        self.assertNotIn("secret", rendered)
        self.assertNotIn("sample.mp4", rendered)
        self.assertNotIn("master.m3u8", rendered)


if __name__ == "__main__":
    unittest.main()
