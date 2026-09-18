# NiyamTrace-X 3.0 — MI300X Experiment Bundle

Target: Ubuntu 24.04, AMD Instinct MI300X 192 GB HBM, ROCm 7.2.4.

The bundle uses the official vLLM ROCm Docker image so it does **not** replace the host PyTorch/ROCm environment. The model API is published on `127.0.0.1:8000` only.

## Fast start

```bash
unzip niyamtrace_x3_mi300x_bundle.zip
cd niyamtrace_x3_mi300x_bundle

bash scripts/00_preflight.sh
bash scripts/01_bootstrap.sh

# Optional but recommended for Hugging Face downloads
export HF_TOKEN='...'

# Do this BEFORE starting your 3-hour experiment timer.
bash scripts/02_stage_assets.sh core

bash scripts/03_test_bundle.sh

# Primary model
bash scripts/04_start_model.sh qwen35_122b
bash scripts/05_smoke.sh qwen35_122b

source .venv/bin/activate
python -m niyamx3.benchgen --out data/niyamtrace_bench3.jsonl --n 10000

python -m niyamx3.runner   --dataset data/niyamtrace_bench3.jsonl   --base-url http://127.0.0.1:8000/v1   --model Qwen/Qwen3.5-122B-A10B-FP8   --out results/qwen35_122b   --concurrency 64   --max-cases 5000

python -m niyamx3.system_tests --out results/system_tests.json
python -m niyamx3.aggregate results
```

For the staged multi-model campaign:

```bash
bash scripts/06_run_campaign.sh
```

Read `RUNBOOK.md` and `EXTERNAL_BENCHMARKS.md` before the final run.
