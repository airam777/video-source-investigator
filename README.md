# Video Source Investigator

A small, local-first research tool for inspecting HTML that you are authorized to examine.

## What it does

- Reads a saved HTML page or page-source file.
- Extracts publicly present video-related metadata and URLs: `<video>`, `<source>`, `<iframe>`, Open Graph video tags, canonical URL, and relevant script/link references.
- Groups discovered URLs by host so you can see which service appears to provide an embed.
- Produces a JSON report that can be saved for research notes.

## What it does not do

This tool does not bypass access controls, DRM, paywalls, anti-copy protections, signed URL restrictions, or authentication. It does not call hidden AJAX endpoints, enumerate private APIs, download streams, or identify private uploaders. A visible embed or hosting domain does not prove that a video is authorized.

## Requirements

Python 3.10 or newer. No third-party packages are required.

## Usage

```bash
python investigator.py path/to/saved-page.html
python investigator.py path/to/saved-page.html --json report.json
```

Save the page source using your browser's normal page-source or save-page feature, then inspect the local copy. Treat signed or tokenized URLs as sensitive; do not publish reports containing them.

## Responsible research

Only inspect pages and files you have permission to access. If you need to establish whether a video is licensed, use the hosting service's official reporting/contact process or obtain confirmation from the rights holder.
