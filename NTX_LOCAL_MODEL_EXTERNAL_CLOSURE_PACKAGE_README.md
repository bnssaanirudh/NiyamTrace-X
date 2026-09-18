# NiyamTrace-X Local Open-Weight External Benchmark Closure

Run the notebook on a Google Colab GPU runtime.

Recommended:
- Start with MODE = CLOSURE.
- Use "Run all".
- The notebook downloads each GPU-eligible model, serves it locally with vLLM, performs tool-call preflight, runs BFCL-v4 + AgentDojo + tau3, unloads it, then moves to the next model.
- Models that cannot load or cannot automatically call tools are skipped instead of terminating the experiment.
- On a T4-class GPU, the high-memory Mistral-7B entry is expected to be skipped automatically.
- At the end download `NTX_LOCAL_MODELS_EXTERNAL_CLOSURE_RESULTS.zip`.

Default open model queue:
1. ibm-granite/granite-3.1-2b-instruct
2. Qwen/Qwen2.5-3B-Instruct
3. Qwen/Qwen3-1.7B
4. microsoft/Phi-4-mini-instruct
5. mistralai/Ministral-3-3B-Instruct-2512
6. Qwen/Qwen2.5-7B-Instruct-AWQ
7. mistralai/Mistral-7B-Instruct-v0.3 (high-memory only)

Scientific note:
tau3 uses the currently loaded model as both agent and simulated user so only one GPU model needs to be resident. The manifest records this; do not present tau3 cross-model differences as controlled user-simulator comparisons.
