# Sanitization log

Before creating the GitHub package, a recursive credential scan was run over normal files and nested ZIP archives.

The scan detected a historical OpenRouter-style credential string inside `results/external_validation/MASTER_RUN_CONFIGURED_RESULTS.zip`. The value appeared in two JSON metadata files and was replaced with `<REDACTED_SECRET>` without removing the surrounding experiment metadata.

Sanitized entries:
- `results/external_validation/MASTER_RUN_CONFIGURED_RESULTS.zip::MASTER_MANIFEST.json`
- `results/external_validation/MASTER_RUN_CONFIGURED_RESULTS.zip::master00_working_models_redacted.json`

No credential value is reproduced in this log.
