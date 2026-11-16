# Open Web Forensics Lab — Architecture Proposal

**Status:** Draft 0.1 — architecture review requested  
**Repository:** `airam777/video-source-investigator`  
**Direction:** Hybrid evolution; preserve the existing video-analysis core.

## 1. Mission and non-goals

Open Web Forensics Lab (OWFL) is a local-first, passive analysis framework for documenting technical structures in HTML documents that the operator is authorized to inspect.

It records observable facts, clearly labels interpretations, preserves provenance, and exports redacted reports.

Non-goals:
- fetching pages or calling endpoints;
- executing JavaScript or deobfuscating runtime code;
- replaying browser sessions, cookies, or authorization material;
- bypassing access controls or extracting protected/playable streams;
- identifying private people from infrastructure clues;
- making legal conclusions about ownership or distribution rights.

All platform fixtures must be synthetic, public-domain, or otherwise explicitly authorized and sanitized before entering the repository.

## 2. Inventory of the existing codebase

| Existing file/module | Current responsibility | Proposed destination |
|---|---|---|
| `investigator.py` | HTML title, metadata, iframe/source/media/track references, host-level observations | `core/html_inspector.py` (compatibility wrapper initially) |
| `provider_inspector.py` | Player signatures, host clues, media type hints | `inspectors/player_inspector.py` |
| `deferred_player_inspector.py` | Static inspection of script blocks and declared AJAX configuration | `inspectors/script_inspector.py` |
| `provenance_inspector.py` | Explicit page-author/uploader labels from supplied HTML | `inspectors/attribution_inspector.py` |
| `authorized_stream_extractor.py` | Static recognition of explicitly declared media references; host-only output | `inspectors/media_reference_inspector.py` |
| `prehraj_catalog.py` | Přehraj.to-specific catalog parsing | `adapters/prehraj.py` |
| `evidence_schema_mapping.py` | Evidence field categories and caveats | `evidence/schema.py` |
| `evidence_validator.py` | Provenance, classification, and sensitive-reference validation | `evidence/validator.py` |
| `report_exporter.py` | Recursive sanitization and JSON/Markdown export | `reporting/exporter.py` |
| `analyze_page.py` | Current orchestration of all inspectors | `application/pipeline.py` (after compatibility phase) |

The current implementation is function-oriented and has no common platform-adapter contract or graph data model. The existing CLI and JSON report shape should remain compatible during the first migration steps.

## 3. Target architecture

```text
Local HTML input
      |
      v
Input + Provenance (bytes, SHA-256, filename, capture context)
      |
      v
Passive Core Inspectors
  | HTML | Script | Player | Media/Track | Attribution |
      |
      v
Platform Adapter Registry
  | Prehraj | YouTube | Vimeo | Dailymotion | Generic |
      |
      v
Normalized Observations
      |
      v
Evidence Engine
  | schema validation | confidence/status | provenance links |
      |
      v
Evidence Graph
      |
      v
Redaction boundary
      |
      v
JSON / Markdown / HTML report
```

Core inspectors extract platform-neutral observations. Adapters add platform-specific interpretation and normalized observations. The generic adapter is always available as a fallback. A platform adapter must never suppress generic observations.

## 4. Platform adapter contract

Use a small, dependency-free Python interface. Prefer `typing.Protocol` for the initial contract so existing function-based inspectors can be wrapped without a large rewrite.

Conceptual contract:

```python
class PlatformAdapter(Protocol):
    adapter_id: str
    version: str

    def detect(self, document: DocumentContext) -> Detection:
        """Return match status, score, and explainable signals."""

    def analyze(self, document: DocumentContext) -> list[Observation]:
        """Return normalized observations; never perform network I/O."""
```

### DocumentContext
- immutable input bytes/text (or a read-only view);
- source filename and SHA-256 digest;
- optional declared base URL, treated as untrusted input;
- parser/capture metadata;
- no cookies, browser profile, credentials, or network client.

### Detection
- `matched: bool`;
- `score: float` in [0, 1], explicitly heuristic rather than probability;
- `signals: list[str]` containing explainable detector reasons.

### Observation
Every observation has:
- stable observation ID;
- `kind` from a controlled vocabulary;
- normalized, already-safe value;
- source locator (HTML line/column when available, otherwise script block/attribute locator);
- `evidence_status`: `fact`, `derived`, or `unknown`;
- adapter ID/version and source document digest;
- optional caveat and relation hints.

Adapters must not return raw signed media URLs, cookies, tokens, credentials, or arbitrary script values. Sensitive values are discarded or replaced at extraction time, not merely hidden at final rendering.

### Registry and selection
1. Run generic core inspectors once.
2. Run all adapters in deterministic registry order.
3. Keep each adapter's detection signals in the report.
4. Deduplicate observations by stable semantic key, retaining all source references.
5. Never treat a detector score as proof of platform ownership or operator identity.

## 5. Evidence Graph model

The graph is a provenance-aware record of observations and claims, not a social or ownership graph.

### Node types
- `document`
- `html_element`
- `metadata`
- `script_config`
- `player`
- `host`
- `media_reference`
- `track_reference`
- `attribution`
- `claim`

### Edge types
- `observed_in`: an observation was found in a document/source location;
- `declares`: a source element/config declares a metadata item or reference;
- `references`: one technical resource points to another;
- `derived_from`: a derived interpretation depends on one or more observations;
- `shares_infrastructure_with`: two observations share a hostname/provider clue.

The last relation is explicitly a technical similarity only. It must never imply common ownership, control, uploader identity, or legal responsibility.

### Evidence status
- `fact`: directly observable in the supplied bytes/document;
- `derived`: deterministic or heuristic interpretation based on cited facts;
- `unknown`: the source does not establish the proposition.

Do not collapse status into a numeric confidence score. If a heuristic score is needed for adapter detection, keep it separate from evidence status.

### Minimal graph record

```json
{
  "schema_version": "0.1",
  "nodes": [
    {
      "id": "node-001",
      "type": "host",
      "value": "cdn.example.test",
      "evidence_status": "fact",
      "source": {
        "document_sha256": "<64-hex-digest>",
        "locator": "script[2].config.file"
      },
      "caveats": []
    }
  ],
  "edges": [
    {
      "id": "edge-001",
      "type": "observed_in",
      "from": "node-001",
      "to": "document-001",
      "evidence_status": "fact",
      "source_observation_ids": ["obs-001"]
    }
  ]
}
```

The example is illustrative only. Real reports must not contain raw media paths or secret values.

## 6. Security and privacy architecture

- Keep the pipeline offline by construction; do not add HTTP clients to the core or adapters.
- Treat HTML and script text as untrusted data, never as instructions or executable code.
- Centralize URL and secret handling in a shared redaction module.
- Prefer allowlisted output fields and host-only references over generic recursive string cleanup.
- Never store full media/track paths, signed query values, cookies, authorization headers, or session identifiers in graph nodes, fixtures, logs, or reports.
- Redaction tests must use canary secrets and assert their absence from every output format and error path.
- Do not persist personal names/profile URLs from attribution observations by default. If a workflow needs to record a public attribution label, make the capture explicit, minimize it, and label it as a source claim rather than verified identity.
- Add size limits for input documents, script blocks, and graph nodes to reduce denial-of-service risk.
- No automatic fetching of canonical URLs, embed URLs, CDN hosts, or declared AJAX endpoints.

## 7. Migration plan

### Phase 0 — Architecture review (current)
- Confirm module inventory and target boundaries.
- Review this proposal independently before changing code.
- Decide the normalized observation vocabulary and compatibility policy.

### Phase 1 — Contracts and shared models
- Add `core/models.py` with `DocumentContext`, `Observation`, `Detection`, and provenance types.
- Add `adapters/base.py` and deterministic `AdapterRegistry`.
- Add schema tests; do not move existing modules yet.
- Wrap the current Přehraj.to-specific catalog logic as the first adapter.

### Phase 2 — Generic adapter
- Add a generic HTML adapter using current platform-neutral inspectors.
- Preserve current CLI/report outputs with compatibility tests.
- Add synthetic fixtures for common Open Graph, JSON-LD VideoObject, iframe, HTML5 video, Video.js, JW Player, and subtitle references.

### Phase 3 — Evidence Graph
- Add graph construction from normalized observations.
- Validate node/edge types, referential integrity, source locators, and evidence status.
- Export graph as a versioned section of JSON; Markdown should render a readable relationship summary.

### Phase 4 — Platform adapters
- Add YouTube, Vimeo, and Dailymotion adapters only for static, public metadata patterns in safe fixtures.
- Keep platform detection explainable and conservative.
- Do not fetch remote pages or resolve player/runtime configuration.

### Phase 5 — Reporting and CI
- Extend redaction tests to graph nodes, edges, Markdown tables, JSON, HTML, exceptions, and debug output.
- Keep Python 3.10, 3.11, and 3.12 CI.
- Add deterministic fixture-based regression tests and a documented threat model.

## 8. Acceptance criteria

1. Existing CLI commands and current tests remain passing during migration.
2. Generic observations are emitted even when no platform adapter matches.
3. Adapters perform no network I/O and do not execute JavaScript.
4. Every graph edge points to existing nodes and cites one or more source observations.
5. Every fact/derived/unknown status is traceable to source evidence or explicitly marked unknown.
6. No canary secret, signed URL value, media path, cookie, or authorization value appears in JSON, Markdown, HTML, logs, or exceptions.
7. Host sharing is never described as common ownership or identity.
8. CI passes on Python 3.10, 3.11, and 3.12.

## 9. Independent review questions

Reviewers (including Gemini) should challenge this proposal rather than merely endorse it:

1. Is `typing.Protocol` the right initial adapter contract, or would an abstract base class be safer/clearer?
2. Should generic inspectors run before adapters, or should adapters contribute parsing rules to a shared parse pass?
3. Is the proposed graph schema sufficiently expressive without making provenance cumbersome?
4. Are `fact`, `derived`, and `unknown` statuses sufficient, and how should conflicts between adapters be represented?
5. Which current modules have overlapping extraction logic that should be consolidated before adding platforms?
6. What security issues remain in current URL sanitization, attribution extraction, and report rendering?
7. What is the smallest Phase 1 change that can be merged without breaking existing users?

**Review outcome format:** list blocking issues, non-blocking improvements, suggested schema changes, and a recommended first implementation PR. Include concrete examples and tests for every claimed issue.
