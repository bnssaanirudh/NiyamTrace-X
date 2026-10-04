# NiyamTrace Annotation Guidelines

## Overview
These guidelines are used by human reviewers to validate the "gold" ActionContract extraction for each scenario in the 320-scenario benchmark.

## Rules
1. **Language Neutrality**: The final ActionContract MUST look identical for semantically equivalent utterances regardless of the input language (English, Hinglish, Telugu, Romanized Telugu).
2. **Intent Classification**: Use only the approved intent schemas (e.g., `invoice.archive`, `access.grant`). Do not invent new intents.
3. **Protected Spans**: Identify and extract exact protected values (like `VENDOR_ID`). Do not translate or modify these values during extraction.
4. **Scope Resolution**: Ensure temporal and spatial scopes are accurately captured. For example, "March invoices" should explicitly map to `{"MONTH": 3}`.
5. **Ambiguity Handling**: If an utterance is overly broad or ambiguous, it MUST be assigned an intent of `unknown` or flagged for `CLARIFY`. Do not guess the user's implicit meaning.
