import tempfile
import unittest
from pathlib import Path

from authorized_stream_extractor import extract


class AuthorizedStreamExtractorTests(unittest.TestCase):
    def test_extracts_explicit_media_and_redacts_query_by_default(self):
        html = """
        <html><head>
          <meta property="og:video" content="https://cdn.example.test/trailer.mp4?token=secret">
        </head><body>
          <video><source src="https://cdn.example.test/clip.webm" type="video/webm"></video>
          <script>jwplayer("p").setup({file: "https://cdn.example.test/master.m3u8?sig=secret"});</script>
        </body></html>
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "authorized.html"
            path.write_text(html, encoding="utf-8")
            report = extract(path)

        self.assertEqual(report["count"], 3)
        rendered = str(report)
        self.assertNotIn("secret", rendered)
        self.assertIn("REDACTED", rendered)
        self.assertIn("MP4", rendered)
        self.assertIn("WebM", rendered)
        self.assertIn("HLS", rendered)

    def test_full_urls_are_only_shown_when_explicitly_requested(self):
        html = '<video src="https://cdn.example.test/movie.mp4?token=abc"></video>'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "authorized.html"
            path.write_text(html, encoding="utf-8")
            report = extract(path, show_full=True)

        self.assertIn("token=abc", report["matches"][0]["url"])


if __name__ == "__main__":
    unittest.main()
