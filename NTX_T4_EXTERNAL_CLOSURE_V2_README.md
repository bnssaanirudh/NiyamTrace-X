# NiyamTrace-X T4 External Closure V2

This version is based on the actual failed T4 result archive.

Main fixes:
- removes unsupported vLLM 0.29 `--swap-space`;
- replaces stale `--disable-log-requests` with runtime-detected `--no-enable-log-requests`;
- checks vLLM API-server `--help` before model serving;
- moves required Mistral validation to the BF16 Ministral-3-3B checkpoint;
- updates xLAM 3B to `Salesforce/xLAM-2-3b-fc-r`;
- uses Granite 3.3 2B, which explicitly supports function-calling tasks;
- makes Granite + Qwen + Mistral the three required T4 closure families;
- retries prior ERROR/PARTIAL model checkpoints.

Use a fresh Colab T4 runtime and Run all.
