# Evidence Report: Ali G – Gdo bít já? (2026) CZ DABING

**Status:** provisional / source-derived; not independently re-parsed in this commit  
**Prepared:** 2026-11-16  
**Target page:** https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b

## 1. Scope and method

This report records the metadata and technical references supplied in the conversation as an extraction from the page's HTML/player configuration. The original complete HTML payload is not present as a file in this repository operation, so the values below are **not represented as independently reproduced by the repository parser**.

No player endpoint was called, no session or cookie was replayed, no signed media URL was tested, and no media was downloaded. Signed paths, query credentials, and JWT values are intentionally omitted.

## 2. Media item metadata (reported from supplied HTML extraction)

| Field | Reported value | Evidence status |
|---|---|---|
| Title | #Ali G - Gdo bít já (2026) CZ DABING | Supplied extraction; source HTML not re-parsed here |
| Platform file ID | 30639124 | Supplied extraction; source HTML not re-parsed here |
| Page/hash identifier | a6b13b0b09ce302b | Also present in target page URL |
| Duration | 5,486 seconds (01:31:26) | Supplied extraction |
| Reported source container | MKV | Supplied extraction; distinguish from delivered renditions |
| Reported source resolution | 1920 × 1080 | Supplied extraction |
| Upload timestamp | 2026-10-30 16:52:21 | Supplied extraction; uploader identity not established |

**Format distinction:** the reported MKV value appears to describe the uploaded/original file, while the player configuration reportedly references MP4 renditions. These are not inherently contradictory: a platform may transcode an uploaded source into playback renditions. The original file itself has not been inspected.

## 3. Reported playback references (redacted)

The supplied extraction reports two MP4 renditions:

| Rendition | Host | Path / credentials |
|---|---|---|
| 1080p MP4 | `pf-storage5.premiumcdn.net` | Hidden; signed query parameters reported |
| 720p MP4 | `pf-storage1.premiumcdn.net` | Hidden; signed query parameters reported |

The supplied extraction also reports two WebVTT subtitle tracks:

| Track label | Track ID | Host | Path / credentials |
|---|---:|---|---|
| CZE (default, as reported) | 13781981 | `pf-storage5.premiumcdn.net` | Hidden; signed query parameters reported |
| CZE1 | 13781982 | `pf-storage3.premiumcdn.net` | Hidden; signed query parameters reported |

The exact media paths, tokens, signatures, and expiry query values are deliberately excluded. The hostnames and file extensions are technical routing clues only; they do not establish the legal operator, content owner, uploader, or licence.

## 4. Player and application signals

The supplied extraction describes a player configuration containing Video.js / JW Player references and Nette-related configuration. The precise library versions, which player actually selected the active source, and the exact HTML element/configuration locations have not been independently verified in this report.

The extraction names three application JWT fields:

- `videoStartedToken`
- `videoCommissionToken`
- `videoViewProgressNotifyToken`

Only the field names are recorded. Token contents, claims, signatures, and encoded values are excluded because they may function as session- or event-specific credentials.

## 5. Attribution and rights assessment

| Question | Finding |
|---|---|
| Is the hosting platform identifiable? | The target page is on Přehraj.to. |
| Is a CDN/storage hostname reported? | Yes: three `pf-storage*.premiumcdn.net` hostnames are reported above. |
| Is the individual uploader identified? | **No evidence supplied in this extraction identifies a natural person or account as uploader.** |
| Is the copyright owner identified? | No. |
| Is permission/licensing to distribute established? | No. |
| Does the upload timestamp prove who uploaded it? | No. |
| Does the CDN hostname prove who owns the video? | No. |

A platform operator, CDN/network provider, account uploader, and copyright holder are distinct roles. A technical host match cannot be used as proof of authorship, ownership, or authorization.

## 6. Confidence and limitations

- **High confidence:** the target page identifier is embedded in the supplied target URL.
- **Reported, not independently verified here:** title, file ID, duration, upload timestamp, source container/resolution, rendition hosts, subtitle IDs, and player/token field names.
- **Not established:** exact current DNS/IP mapping for each storage hostname, the identity of the uploader, the copyright owner, and distribution authorization.
- The signed URLs were not tested. Their current validity or expiry status is therefore unknown.
- This report is a structured record of the supplied extraction, not a forensic certification of the original HTML.

## 7. Reproduction checklist

To upgrade this report from provisional to parser-verified evidence:

1. Preserve the exact original HTML file as an evidence artifact, without editing it.
2. Record its SHA-256 hash, file size, capture date/time, and the page URL from which it was obtained.
3. Run the repository's offline parser against that local file, for example:

   ```bash
   python analyze_page.py evidence/ali-g-gdo-bit-ja-2026.html \
     --base-url "https://prehraj.to/ali-g-gdo-bit-ja-2026-cz-dabing/a6b13b0b09ce302b" \
     --json reports/ali-g-gdo-bit-ja-2026-parser-output.json
   ```

4. Compare parser output with this report. Record discrepancies rather than silently overwriting them.
5. Keep any unredacted source HTML and credentials out of public commits. Publish only the redacted report and, if appropriate, a hash of the locally preserved source file.

## 8. Conclusion

The supplied extraction indicates that the Přehraj.to page's player configuration referenced MP4 playback renditions and VTT subtitle files on `pf-storage*.premiumcdn.net` hosts, alongside player/application configuration fields. This supports a **technical hosting-path lead**. It does not identify the uploader or prove that the upload was authorized. The case should remain marked **provisional** until the original HTML is preserved, hashed, and independently processed by the repository's offline parser.
