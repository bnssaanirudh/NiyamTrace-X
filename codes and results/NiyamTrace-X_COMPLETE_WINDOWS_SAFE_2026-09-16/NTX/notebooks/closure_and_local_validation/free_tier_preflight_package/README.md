# NiyamTrace-X Free-Tier Preflight — Two Cells

Files:
- `NTX_FREE_TIER_PREFLIGHT_2_CELLS.ipynb`
- `NTX_FREE_TIER_PREFLIGHT_2_CELLS.py`

Requirements:
- `GEMINI_API_KEY` already set in the notebook/runtime.
- `GROQ_API_KEY` already set in the notebook/runtime.
- `openai` Python package available.

The notebook:
1. retries Gemini with fallbacks,
2. verifies Groq Qwen 3.8 and GPT-OSS,
3. saves preflight CSV,
4. builds the final Gemini + Qwen + GPT-OSS three-family matrix.
