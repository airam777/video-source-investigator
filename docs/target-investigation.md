# Target investigation: Ali G: Gdo bít já?

Last checked: 2026-11-16

## Target

- Detail page: https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b
- Item identifier: `a6b13b0b09ce302b`
- Search terms checked: exact item identifier and detail-page slug.
- Retrieval status: automated page retrieval failed; exact identifier/slug search returned no indexed result.
- Local evidence status: no saved HTML source for this exact detail page has been supplied yet.

## Confirmed platform context

Přehraj.to's own FAQ describes the service as cloud storage where users upload audiovisual content. It says the operator does not create or upload the content itself and that content is supplied by users:
- https://prehraj.to/faq

Its public “Jak na to” page says users can upload files and earn based on how often their videos are downloaded:
- https://prehrajto.cz/jak-na-to

This makes the uploader account a relevant lead for a specific item. It does not identify the account for this film and does not establish that any uploader has distribution rights.

## Availability of the title

The official Prime Video title page lists *Ali G: Gdo bít já?* as a 2026 title and lists Amazon MGM Studios:
- https://www.primevideo.com/-/cs/detail/0RQIMJGXQRO3TJ5YMC2X1Y0UJ9

This is evidence of an official commercial listing, not evidence about the provenance or licensing status of the specific Přehraj.to upload.

## Findings not yet established

- the actual player/embed host on this specific item page;
- the actual storage/CDN host for its media;
- the public uploader account, if displayed;
- whether that uploader is authorized to distribute the film.

## Next evidence required

Provide the saved HTML source of the exact Přehraj.to detail page as a file attachment. Run:

```bash
python analyze_page.py saved-page.html --base-url 'https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b' --json ali-g-report.json
```

The report checks static page references, player/provider clues, and explicit uploader attribution. It hides media paths and query credentials and does not call hidden endpoints or resolve playable stream URLs.
