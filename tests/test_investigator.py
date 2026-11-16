import unittest

from investigator import inspect_html


class InspectorTests(unittest.TestCase):
    def test_finds_embed_and_host(self):
        report = inspect_html(
            '<html><head><title>Demo</title>'
            '<link rel="canonical" href="https://example.test/watch/1">'
            '</head><body><iframe src="https://player.example.test/embed/abc"></iframe>'
            '</body></html>'
        )
        self.assertEqual(report["title"], "Demo")
        self.assertTrue(any(x["kind"] == "embed" and
                            x["host"] == "player.example.test"
                            for x in report["candidates"]))

    def test_detects_lazy_embed_and_redacts_media_metadata_path(self):
        html = '''<html><head><meta property="og:video" content="https://cdn.example.test/private/movie.mp4?token=secret"></head>
        <body><iframe data-src="//voe.sx/e/abc"></iframe></body></html>'''
        report = inspect_html(html, base_url="https://prehraj.to/watch/1")
        self.assertEqual(report["candidates"][0]["host"], "voe.sx")
        rendered = str(report)
        self.assertNotIn("movie.mp4", rendered)
        self.assertNotIn("secret", rendered)
        self.assertIn("[media URL hidden]", rendered)

    def test_hides_signed_media_url(self):
        report = inspect_html(
            '<video><source src="https://cdn.example.test/movie.mp4?token=secret&expires=123"></video>'
        )
        media = [x for x in report["candidates"] if x["media_reference"]]
        self.assertTrue(media)
        self.assertNotIn("secret", str(media))
        self.assertNotIn("movie.mp4", str(media))


if __name__ == "__main__":
    unittest.main()
