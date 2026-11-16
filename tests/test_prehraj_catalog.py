import unittest

from prehraj_catalog import parse_catalog, parse_duration, parse_size


class CatalogParserTests(unittest.TestCase):
    def test_parses_visible_result_metadata(self):
        html = '''
        <a class="video--link" href="/video/test-123">
          <h3 class="video__title">Demo film</h3>
          <span class="video__tag--size">1.5 GB</span>
          <span class="video__tag--time">1:42:03</span>
          <img src="/thumb/demo.jpg">
        </a>
        '''
        results = parse_catalog(html)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Demo film")
        self.assertEqual(results[0]["size_bytes"], round(1.5 * 1024**3))
        self.assertEqual(results[0]["duration_seconds"], 6123)
        self.assertEqual(results[0]["page_url"], "https://prehraj.to/video/test-123")

    def test_parsers(self):
        self.assertEqual(parse_duration("01:02"), 62)
        self.assertEqual(parse_size("10 MB"), 10 * 1024**2)


if __name__ == "__main__":
    unittest.main()
