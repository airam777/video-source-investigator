# Video Source Investigator

A local-first research helper for examining HTML/page source that you are authorized to inspect.

## Current capabilities

- Reads a saved HTML or page-source file (no network access required).
- Finds visible `iframe` embeds, `video`/`source` references, Open Graph/Twitter player metadata, and relevant player links.
- Groups findings by hosting domain and labels direct media references separately from embed/player pages.
- Redacts common temporary credentials in query strings and hides direct media paths in reports.
- Exports a JSON report for research notes.

## Run

Requires Python 3.10+; no third-party packages.

```bash
python investigator.py saved-page.html
python investigator.py saved-page.html --json report.json
python -m unittest discover -s tests -v
```

On Android, save or share the page source as an HTML file, then run the script on a computer with Python. The project currently analyses local files; it does not crawl sites.

## Relationship to the public reference project

The project [MatheusJey/stremio-prehraj](https://github.com/MatheusJey/stremio-prehraj) demonstrates a Přehraj.to search-to-stream workflow. Its implementation searches result pages, parses result metadata, and resolves player pages to short-lived direct MP4 stream URLs. It also accepts session cookies and forwards them with playback requests.

This project deliberately implements the safer research subset: inspect supplied/saved page source and identify visible embed/provider clues. It does not automate searches for copyrighted works, replay session cookies, bypass access controls, or resolve/download signed media streams.

## Important limitations

- A hosting domain is not proof of who uploaded a file.
- A public page or playable embed does not prove that distribution is licensed.
- Signed URLs can contain temporary access credentials; reports redact common token parameters, but inspect reports before sharing.
- If you need to verify rights, contact the platform or rights holder and retain the canonical page URL and relevant evidence.
