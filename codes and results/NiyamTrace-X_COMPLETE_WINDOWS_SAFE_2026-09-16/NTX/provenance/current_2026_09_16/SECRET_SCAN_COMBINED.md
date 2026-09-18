# Secret scan summary

- Baseline 2026-09-14 research-history scan: **PASS**. The retained baseline report records zero remaining secret hits and notes two historical metadata entries that were sanitized before release.
- Newly added 2026-09-16 assets scan: **PASS** for common OpenAI, OpenRouter, Groq, Google/Gemini, Hugging Face, and GitHub token-prefix patterns across direct text files and readable text members of newly added ZIPs.
- Historical notebooks may still contain *code patterns* that interpolate a runtime key into generated files; this is a code-safety concern even when no literal credential is present. Review such cells before running with real credentials.
- Rotate any credential that was ever pasted into a chat/notebook/output, regardless of this archive scan.

Machine-readable reports:
- `../SECRET_SCAN_REPORT.json` (baseline)
- `SECRET_SCAN_NEW_ASSETS.json` (newly added assets)
