# Video Source Investigator

A local-first research helper for examining HTML/page source that you are authorized to inspect.

## Current capabilities

- Reads a saved HTML or page-source file (no network access required).
- Parses locally saved Přehraj.to search-result pages for visible title, result-page URL, file size, duration, and thumbnail metadata.
- Finds visible iframe embeds, video/source references, Open Graph/Twitter player metadata, and relevant player links.
- Recognizes common JW Player and Video.js configuration signatures in inline scripts.
- Classifies explicitly declared media types such as MP4, WebM, HLS playlists (M3U8), and MPEG-DASH manifests (MPD).
- Inspects deferred player-loader declarations in saved HTML, including declared AJAX endpoint, method, parameter names, and related DOM selectors, without sending the request.
- Includes an offline extractor for media URLs explicitly present in locally saved, authorized HTML.
- Exports JSON reports for research notes.

## Run

Requires Python 3.10+; no third-party packages.

```bash
python investigator.py saved-page.html
python investigator.py saved-page.html --json report.json
python prehraj_catalog.py saved-search-results.html --json catalog.json
python provider_inspector.py saved-page.html --base-url 'https://example.test/watch/...' --json providers.json
python deferred_player_inspector.py saved-page.html --json loader.json
python authorized_stream_extractor.py authorized-page.html --base-url 'https://example.test/watch/...' --json streams.json
python -m unittest discover -s tests -v
```

The authorized extractor recognizes explicit MP4, WebM, HLS, and DASH references in standard HTML media elements, selected social metadata, and plainly quoted `file`/`src` values in inline player configuration. Query strings are redacted by default. For an authorized test fixture only, `--show-full-urls` displays the complete URL, which may contain temporary credentials.

The deferred-player inspector is static: it reports that a page declares a loader request and summarizes its visible configuration. It does not call the endpoint, fetch provider pages, replay browser sessions, or resolve streams.

On Android, save or share the page source as an HTML file, then run the script on a computer with Python. Use `prehraj_catalog.py` for a saved Přehraj.to search-results page, `investigator.py` for a saved video/detail page, and `provider_inspector.py` to map visible iframe/link hostnames and recognize player configuration patterns from a saved page.

## Relationship to the public reference project

The project [MatheusJey/stremio-prehraj](https://github.com/MatheusJey/stremio-prehraj) demonstrates a Přehraj.to search-to-stream workflow. This repository takes inspiration from its staged inspection approach, but focuses on offline analysis of supplied, authorized page source.

## Scope and limitations

- The tools do not crawl sites, call hidden AJAX endpoints, replay session cookies, resolve third-party player pages, execute JavaScript, bypass access controls, or download media.
- The extractor only reports media URLs explicitly declared in the local HTML supplied to it; it does not discover URLs hidden behind provider-side requests or runtime protections.
- Player signatures and hosting domains are technical clues, not proof of uploader identity or distribution rights.
- A public page or playable embed does not prove that distribution is licensed.
- Signed URLs can contain temporary access credentials; reports intentionally omit query strings unless the explicit full-URL option is used for authorized test material.
