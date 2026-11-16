# Video Source Investigator

A local-first research helper for examining HTML/page source that you are authorized to inspect.

## Current capabilities

- Reads a saved HTML or page-source file (no network access required).
- Parses locally saved Přehraj.to search-result pages for visible title, result-page URL, file size, duration, and thumbnail metadata.
- Finds visible iframe embeds, video/source references, Open Graph/Twitter player metadata, and relevant player links.
- Recognizes common JW Player and Video.js configuration signatures in inline scripts.
- Classifies explicitly declared media types such as MP4, WebM, HLS playlists (M3U8), and MPEG-DASH manifests (MPD).
- Groups findings by hosting domain; reports host-level metadata only and does not print media paths or query strings.
- Exports a JSON report for research notes.

## Run

Requires Python 3.10+; no third-party packages.

```bash
python investigator.py saved-page.html
python investigator.py saved-page.html --json report.json
python prehraj_catalog.py saved-search-results.html --json catalog.json
python provider_inspector.py saved-page.html --base-url 'https://example.test/watch/...' --json providers.json
python -m unittest discover -s tests -v
```

On Android, save or share the page source as an HTML file, then run the script on a computer with Python. Use `prehraj_catalog.py` for a saved Přehraj.to search-results page, `investigator.py` for a saved video/detail page, and `provider_inspector.py` to map visible iframe/link hostnames and recognize player configuration patterns from a saved page.

## Relationship to the public reference project

The project [MatheusJey/stremio-prehraj](https://github.com/MatheusJey/stremio-prehraj) demonstrates a Přehraj.to search-to-stream workflow. This repository takes inspiration from its staged inspection approach, but focuses on offline analysis of supplied, authorized page source.

## Scope and limitations

- The tools do not crawl sites, call hidden AJAX endpoints, replay session cookies, resolve player pages, extract direct streams, or download media.
- Player signatures and hosting domains are technical clues, not proof of uploader identity or distribution rights.
- A public page or playable embed does not prove that distribution is licensed.
- Signed URLs can contain temporary access credentials; reports intentionally omit paths and query strings.
- For content you own or are authorized to inspect, use the original platform's documented export/API or provide a local sample page source for analysis.
