# Reference project analysis: MatheusJey/stremio-prehraj

Reviewed against the public source on 2026-11-16.

Reference: https://github.com/MatheusJey/stremio-prehraj

## What the reference implementation does

The public project is a Stremio add-on, not a browser extension. Its flow is:

1. `src/handler.js` receives a Stremio stream request and resolves the title/episode through Cinemeta.
2. It builds title search queries and calls `search()` from `src/prehrajto.js`.
3. `parseSearchResults()` reads visible search-result HTML and extracts title, detail-page URL, size, duration, and thumbnail.
4. `getStreams()` requests each result detail page.
5. `extractSources()` parses player configuration or media elements for MP4 source URLs and labels.
6. The handler ranks candidates and returns Stremio stream objects.

## Important implementation details

- Search results are parsed with Cheerio selectors: `a.video--link`, `.video__title`, `.video__tag--size`, and `.video__tag--time`.
- The reference implementation uses a warm-up request and a process-local cookie jar.
- Its stream extraction looks for a JavaScript `sources` array, standard `<source>` elements, and finally quoted MP4 URLs.
- The README says the returned media URLs are signed and short-lived.

## How this repository differs

This repository is a passive investigation toolkit. It can inspect HTML that the researcher has lawfully saved and report:

- visible result metadata and detail-page references;
- declared iframe/player hostnames;
- visible player-library/configuration clues;
- the presence and shape of deferred-loader declarations, without calling them;
- explicit media-type hints, while hiding sensitive URL values by default.

It intentionally does not reproduce the reference project's authenticated cookie handling, automated detail-page stream resolution, signed-URL extraction, or playback delivery. A host match is evidence of a technical relationship only; it does not identify the uploader or establish permission to distribute the film.

## Current target page

- Page: https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b
- Status in this investigation: page source has not yet been supplied as a local HTML file, and an automated page fetch was not available.
- Therefore no claim is made about the actual embed host, player provider, uploader, or media storage location for this particular item.

## Next evidence step

Save the page's HTML/page source through an ordinary browser action where the site permits it, then run:

```bash
python investigator.py saved-page.html
python provider_inspector.py saved-page.html --base-url 'https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b'
python deferred_player_inspector.py saved-page.html
```

Keep the original file unchanged and retain the generated reports. Do not publish session cookies, signed URLs, or personal account data in issues or commits.
