# Video Source Investigator

Local-first tooling for documenting the public structure of a video page from HTML that you are authorized to inspect.

## What it does

- Parses saved Přehraj.to catalog HTML for visible title, page URL, file size, duration, and thumbnail.
- Finds visible iframe references, lazy-loaded embed attributes, video/source elements, and Open Graph/Twitter player metadata.
- Recognizes common JW Player and Video.js configuration signatures.
- Identifies declared media formats (MP4, WebM, HLS/M3U8, MPEG-DASH/MPD) and the associated host.
- Inspects declared deferred-loader requests (such as jQuery AJAX) without sending them.
- Produces one consolidated JSON report using `analyze_page.py`.
- Redacts media paths and sensitive query parameters. It does not output playable media URLs.

## Quick start

Requires Python 3.10+; no third-party packages.

```bash
python analyze_page.py saved-page.html --base-url 'https://prehraj.to/your/video/page' --json report.json
```

Focused tools:

```bash
python investigator.py saved-page.html --base-url 'https://prehraj.to/your/video/page'
python prehraj_catalog.py saved-search-results.html --json catalog.json
python provider_inspector.py saved-page.html --base-url 'https://prehraj.to/your/video/page' --json providers.json
python deferred_player_inspector.py saved-page.html --json loader.json
python -m unittest discover -s tests -v
```

## Report contents

The consolidated report includes:

- page title and source URL;
- provider/iframe hostnames and player-library clues;
- visible reference attributes, with media paths hidden;
- static deferred-loader declarations, endpoint path, HTTP method, and parameter names;
- media format and host evidence;
- catalog metadata if the supplied HTML is a search-results page.

## Android source capture

Use the browser's ordinary **Save page** or **Share** option if it can export the page as HTML. If the browser only displays source text, save that text as a UTF-8 `.html` file. Transfer the file to a computer and run the quick-start command above. Keep the original file unchanged for evidence integrity.

Do not paste account cookies, authorization headers, or signed media URLs into GitHub issues or commits. You can attach the HTML file privately in the ChatGPT conversation for analysis.

## Reference implementation

The public project [MatheusJey/stremio-prehraj](https://github.com/MatheusJey/stremio-prehraj) demonstrates a Přehraj.to search-to-stream workflow. Its public source was reviewed to understand the stages of search, catalog parsing, detail-page inspection, and player configuration.

This repository deliberately implements offline inspection only. It does not fetch pages, call hidden AJAX endpoints, replay browser sessions, resolve third-party player pages, execute JavaScript, bypass access controls, download media, or expose direct playback URLs.

## Interpretation and limitations

- A referenced host is a technical clue, not proof of who uploaded the content.
- A media host or format does not establish distribution rights.
- A public page or playable embed does not prove that distribution is licensed.
- Dynamic content loaded only at runtime will not appear in a static HTML report.
- To investigate the actual Přehraj.to item, the saved HTML source of that exact detail page is still required.

## Development and CI

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
```

GitHub Actions runs compilation and unit tests on Python 3.10, 3.11, and 3.12 for pushes and pull requests.
