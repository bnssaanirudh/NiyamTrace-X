# NiyamTrace-X Paper Closure Notebook

Recommended:
1. Open the notebook in Colab.
2. Provide an OpenRouter key with enough credit.
3. Leave `NTX_CLOSURE_MODE=CLOSURE`.
4. Run all cells in order.
5. Send back `NTX_PAPER_CLOSURE_MASTER.zip`.

The notebook dynamically selects three viable independent LLM families, retries cheaper/alternate models inside a family, closes BFCL-v4 + AgentDojo + tau3, preserves every failed and successful raw artifact, and generates paper-ready LaTeX/CSV evidence.

For a zero-cost parser/export check, set `NTX_SELFTEST=1`. Self-test evidence is explicitly marked non-paper.
