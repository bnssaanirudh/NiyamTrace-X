# Paper-grade execution and epoch logging protocol

## One record per actual run

Preserve a unique `run_id`, exact `kind` (test, smoke, benchmark, inference, replay, training), UTC start/end, exit code, duration, code commit, Python/platform, and console output. Provide true dataset and model IDs/revisions, split, seed, prompt/parser/policy/registry versions and full input SHA-256s separately when available. A replay **must** identify the original source run/cohort.

A process with exit code zero is **not automatically a passing benchmark**. Parse task results separately. Report requested, attempted, completed, errored, timed-out and excluded sample counts with reasons. Distinguish generated fixtures from independently authored/adjudicated cases and official external benchmarks.

## Per-case authorization record

Recommended columns: `run_id,case_id,family_id,language,model_id,model_revision,parser_policy,policy_arm,expected_verdict,actual_verdict,parse_status,proposal_id,effect_before_hash,effect_after_hash,unsafe_effect,authorized_completion,latency_ms,error_type,timeout,source_cohort,source_run_id`.

Count a frozen model proposal once as inference, even if evaluated under four methods and two parser policies. Preserve per-request effect-diff evidence and group confidence intervals by independent task family when appropriate. Zero observed errors does not establish zero population risk.

## Epoch logs only for actual model training

An epoch is a full pass through the training dataset. NiyamTrace-X's authorization tests, saved-response replays and inference evaluations have **no model training epochs**. For a separate real fine-tuning run, use:

~~~csv
run_id,epoch,global_step,train_examples,val_examples,train_loss,val_loss,learning_rate,grad_norm,elapsed_seconds,checkpoint_sha256
~~~

Use actual computed loss/gradient metrics. Record checkpoint files and hashes, early stops, NaNs and completed epoch count. Never infer epochs from case counts or invent epoch-loss curves.

## Output and privacy

The `paper_log_run.py` utility writes `metadata.json`, `run.log`, and `artifacts_manifest.csv` in a uniquely named run folder, and hashes only files actually present after execution. It does not download or rerun historical archives. Review all logs for API keys, private user/ERP records and licensed sources before uploading to public GitHub. Never pass API keys in command-line parameters or publicly commit unredacted stdout.
