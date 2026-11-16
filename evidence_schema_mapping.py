"""Evidence classification rules for offline video-page investigations.

The schema separates what the supplied HTML literally declares from
interpretations and claims that require independent evidence.
"""

EVIDENCE_VALIDATION_RULES = {
    "direct_html": [
        "video_id",
        "video_hash",
        "title",
        "duration_meta",
        "resolution_meta",
        "uploader_string",
        "active_player",
        "cdn_storage_hosts",
        "subtitle_ids",
        "streaming_variants_mp4",
        "ajax_endpoints",
    ],
    "derived_or_transcoded": [
        "transcoding_interpretation",
        "storage_offload_interpretation",
    ],
    "reported_external": [
        "original_file_format",
        "original_file_size_bytes",
        "uploader_identity",
        "rights_holder",
        "licensing_status",
    ],
    "security_and_actions": [
        "url_tokens_present",
        "signed_url_parameters_present",
        "ajax_action_names",
    ],
}

# Literal declarations can be directly observed, while their meaning may remain
# uncertain. Keep these caveats machine-readable for reports and tests.
EVIDENCE_CAVEATS = {
    "streaming_variants_mp4": (
        "MP4 variants are directly declared in the supplied HTML; "
        "their generation/transcoding history is not proven by that fact alone."
    ),
    "cdn_storage_hosts": (
        "Hostnames are directly visible in the supplied HTML; their infrastructure "
        "role (for example, storage offload) is an interpretation."
    ),
    "uploader_string": (
        "A displayed uploader/software label does not identify a natural person "
        "or establish who uploaded the file."
    ),
    "original_file_format": (
        "The original uploaded file format must be supported by a separate source; "
        "do not infer it from transcoded player variants."
    ),
}
