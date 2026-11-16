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
