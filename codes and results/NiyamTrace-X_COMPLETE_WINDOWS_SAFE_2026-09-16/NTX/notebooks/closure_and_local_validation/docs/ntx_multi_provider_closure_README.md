# NiyamTrace-X Multi-Provider Closure Package

## Notebook 1
`NTX_01_PROVIDER_PREFLIGHT_OPENAI_GEMINI_GROQ.ipynb`

Prompts securely for OpenAI, Gemini and Groq API keys and checks chat + tool calling.

## Notebook 2
`NTX_02_MULTI_PROVIDER_PAPER_CLOSURE_FINAL.ipynb`

Prompts for the same three keys again and runs BFCL-v4, AgentDojo and tau3 using the three working independent model families.

Important:
- Keys are entered with hidden input and are never written to the output archives.
- If OpenAI API quota is unavailable, Gemini + Groq Qwen + Groq Llama/GPT-OSS can still provide three independent model families.
- ChatGPT subscription access and OpenAI API billing are separate.
- Run CLOSURE mode first; use FULL only after CLOSURE succeeds.
