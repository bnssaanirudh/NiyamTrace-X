# Security and secret-handling notes

No API key is intentionally included in this repository package.

Some **historical experiment notebooks** were developed before the final
secret-handling cleanup and contain code patterns that could write a runtime
API key into a generated helper script (for example, interpolating `api_key`
into `run_bfcl.py`). These notebooks are retained only to preserve the research
history. Do not run them with a real credential without reviewing the relevant
cells.

Recommended practice:
- enter credentials at runtime with `getpass()` or environment variables;
- never write credentials into generated files, logs, notebooks, or archives;
- rotate any credential ever pasted into a chat or notebook output;
- use the later local/T4 notebooks when possible because they use a local
  `EMPTY` OpenAI-compatible key and do not require commercial provider secrets.

A recursive scan is run on this package for common OpenAI, OpenRouter, Groq,
Google/Gemini, Hugging Face, and GitHub token prefixes before release.
