# Pre-Training Audit

Audit date: 2026-04-25

Decision: **GO for a tiny real Hugging Face training run**, with the explicit `--confirm-real-training` guard and tiny-run limits below.

No real training was run during this audit. No GPU was used. No Hugging Face credit was spent. No trained-model improvement is claimed.

## Audit Result

The repo is ready for the first tiny paid-capable GRPO run after installing training-only dependencies on the training runtime.

The environment server remains CPU-runnable and does not require GPU. Training dependencies are optional and are not part of the minimal Space runtime.

## Problems Found

1. The non-smoke GRPO path was still Gate-4 blocked and raised before training.
2. `README.md` and `TRAINING.md` still described real GRPO as intentionally blocked.
3. The optional TRL dependency floor was too loose for a reliable GRPOTrainer path.

## Fixes Applied

1. Implemented a guarded real TRL GRPO path in `training/train_json_grpo.py`.
2. Added `--confirm-real-training` so paid-capable training cannot start accidentally.
3. Real non-smoke reward scoring now uses `score_completion(...)`, which runs the deterministic Agent BlackBox environment and verifier.
4. Real non-smoke training strips `target_json` before constructing GRPO datasets, so GRPO receives public prompts plus routing metadata only.
5. Real generated completions are logged to `sampled_generations.jsonl`.
6. Real verifier metrics are saved to `metrics.csv`, `summary.json`, and `outputs/training_metrics.csv`.
7. Updated `README.md` and `TRAINING.md` with the guarded first-run command.
8. Updated optional training dependency floor to `trl>=0.15` and `transformers>=4.48`.

## Requirement Checks

| Check | Status | Notes |
|---|---|---|
| deterministic verifier reward used | PASS | `verifier_reward(...)` and the real reward callback call `score_completion(...)`. |
| non-smoke scores real completions | PASS | Non-smoke reward callback receives TRL completions and scores those strings. |
| smoke separate from real training | PASS | `--smoke` never imports TRL or loads a model. Real mode requires `--confirm-real-training`. |
| prompt hidden leakage | PASS | Smoke train/eval prompts passed leakage scan. |
| prompts informative enough | PASS | Prompts include public trace spans, scenario, family, candidate root causes, and allowed patch clauses. |
| strict JSON parser | PASS | Requires object root and required typed fields, while allowing ordinary whitespace. |
| invalid JSON logged | PASS | Smoke and real callback record `parse_error` and `invalid_json`. |
| overblocking penalized | PASS | Block-everything scores low and logs `overblocking=1.0`. |
| hardcoding penalized | PASS | Hardcoded incident references lose certificate and log `hardcoded_patch=1.0`. |
| CSV/JSON metrics saved | PASS | Smoke and real paths write metrics; real path also writes `summary.json`. |
| sampled generations saved | PASS | `sampled_generations.jsonl` exists in smoke and will be written in real mode. |
| future plots only from real logs | PASS | `scripts/make_plots.py` creates training plots only if `outputs/training_metrics.csv` exists. |
| README avoids trained claims | PASS | README says current results are baseline and smoke only. |
| TRAINING.md has safe commands | PASS | Tiny first-run command and stop-loss rules are documented. |
| default model | PASS | Default remains `Qwen/Qwen2.5-0.5B-Instruct`. |
| no 7B+ model required | PASS | First run uses 0.5B. Larger models are stretch only. |
| environment server GPU-free | PASS | FastAPI/OpenEnv environment is CPU-only. |
| hidden leakage in eval outputs | PASS | Smoke eval metrics and summary contain no forbidden hidden terms. |

## Exact Safe First HF Training Command

Run this only after the smoke commands are green on the HF training runtime:

```bash
pip install -e ".[training]"

python training/train_json_grpo.py \
  --confirm-real-training \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --max-steps 10 \
  --train-seeds 0-2 \
  --eval-seeds 1000 \
  --output-dir outputs/grpo_tiny_hf \
  --num-generations 2 \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 1 \
  --learning-rate 5e-6 \
  --save-steps 10
```

## Exact Stop-Loss Rules

Stop immediately if:

- dependencies fail before model training starts
- model download/startup consumes more than the planned tiny-run budget
- `outputs/grpo_tiny_hf/sampled_generations.jsonl` is missing
- `outputs/grpo_tiny_hf/metrics.csv` is missing
- invalid JSON rate remains above `0.60`
- mean reward does not beat the `random_patch` baseline score of `0.144`
- reward rises while certificate success stays flat
- overblocking rate is nonzero and increasing
- hardcoded patch rate is nonzero and increasing
- hidden regression pass improves while valid preservation collapses
- sampled generations are mostly markdown, prose-only answers, or copied incident IDs

## Expected Output Files

After a real tiny run:

- `outputs/grpo_tiny_hf/metrics.csv`
- `outputs/grpo_tiny_hf/summary.json`
- `outputs/grpo_tiny_hf/sampled_generations.jsonl`
- `outputs/grpo_tiny_hf/model/`
- `outputs/training_metrics.csv`

After plotting from real logs:

- `outputs/training_reward_curve.png`
- optional `outputs/training_loss_curve.png` if loss is present in the real metrics

## Metrics To Check After Training

- overall score
- certificate success rate
- hidden regression pass rate
- valid preservation rate
- invalid JSON rate
- overblocking rate
- hardcoded patch rate
- sampled generation quality
- baseline comparison against `random_patch`, `block_everything`, `visible_overfit`, and `oracle_correct_solver_for_sanity`

## What Not To Claim Unless Results Prove It

- Do not claim trained-model improvement unless real post-training evaluation beats pre-training baselines.
- Do not claim robust generalization unless hidden regression pass and valid preservation both improve.
- Do not claim safety certification beyond the bounded Agent Repair Certificate.
- Do not claim production readiness.
- Do not claim SOTA.
- Do not present smoke/mock results as trained-model results.

## Smoke Outputs

Dataset smoke:

```text
make_dataset: wrote outputs\training_smoke\train.jsonl
make_dataset: wrote outputs\training_smoke\eval.jsonl
make_dataset: wrote outputs\training_smoke\dataset_summary.json
make_dataset: train_records=6 eval_records=3 families=stale_retrieval,missing_verification,permission_scope
```

GRPO smoke:

```text
train_json_grpo: smoke wrote outputs\grpo_smoke\metrics.csv
train_json_grpo: smoke wrote outputs\grpo_smoke\sampled_generations.jsonl
train_json_grpo: smoke invalid_json_rate=0.2500
train_json_grpo: full GRPO not run in smoke mode
```

Evaluation smoke:

```text
evaluate_model: wrote outputs\eval_smoke\metrics.csv
evaluate_model: wrote outputs\eval_smoke\summary.json
evaluate_model: score=0.4200 cert=0.2500 hidden=0.3750 invalid_json=0.2500
```

Leakage scan:

```text
leakage_scan: checked 9 prompts and eval outputs; no forbidden hidden terms found
```

## self_check Output

```text
evaluate_baselines: wrote outputs\results.csv
evaluate_baselines: wrote outputs\baseline_summary.json
evaluate_baselines: random_patch score=0.1440 cert=0.0000 hidden=0.0000 valid=0.0000
evaluate_baselines: explanation_only score=0.3500 cert=0.0000 hidden=0.0000 valid=0.0000
evaluate_baselines: block_everything score=0.1300 cert=0.0000 hidden=0.5000 valid=0.0000
evaluate_baselines: visible_overfit score=0.5500 cert=0.0000 hidden=0.0000 valid=0.0000
evaluate_baselines: oracle_correct_solver_for_sanity score=1.0000 cert=1.0000 hidden=1.0000 valid=1.0000
make_plots: wrote outputs\baseline_scores.png
make_plots: wrote outputs\certificate_success_rate.png
make_plots: wrote outputs\hidden_regression_pass_rate.png
make_plots: wrote outputs\valid_preservation_rate.png
make_plots: no outputs/training_metrics.csv found; skipped training plots
make_dataset: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_smoke\train.jsonl
make_dataset: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_smoke\eval.jsonl
make_dataset: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_smoke\dataset_summary.json
make_dataset: train_records=6 eval_records=3 families=stale_retrieval,missing_verification,permission_scope
train_json_grpo: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\grpo_smoke\metrics.csv
train_json_grpo: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\grpo_smoke\sampled_generations.jsonl
train_json_grpo: smoke invalid_json_rate=0.2500
train_json_grpo: full GRPO not run in smoke mode
evaluate_model: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\eval_smoke\metrics.csv
evaluate_model: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\eval_smoke\summary.json
evaluate_model: score=0.4200 cert=0.2500 hidden=0.3750 invalid_json=0.2500
train_sft_warmstart: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\sft_smoke\sft_samples.jsonl
train_sft_warmstart: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\sft_smoke\sft_smoke_summary.json
train_sft_warmstart: full SFT not run in smoke mode
space_smoke: FastAPI app import ok
space_smoke: environment metadata ok
space_smoke: reset/step/state ok
space_smoke: stale_retrieval certificate path ok
self_check: stale_retrieval correct trajectory score = 1.0
self_check: stale_retrieval block-everything score = 0.23
self_check: stale_retrieval hardcoded patch rejected
self_check: missing_verification correct trajectory score = 1.0
self_check: missing_verification block-everything score = 0.23
self_check: missing_verification hardcoded patch rejected
self_check: permission_scope correct trajectory score = 1.0
self_check: permission_scope block-everything score = 0.23
self_check: permission_scope hardcoded patch rejected
self_check: reset/step/state ok
self_check: all three MVP families verified
self_check: certificate gating ok
self_check: hidden leakage scan ok
self_check: examples written
self_check: baseline evaluator ok
self_check: baseline plots ok
self_check: training scaffold smoke ok
self_check: docs readiness ok
self_check: space smoke ok
```

## pytest Output

```text
..................................                                       [100%]
34 passed in 0.11s
```

## Remaining Risks

- The real TRL path is code-audited and smoke-separated, but not locally executed with a model in this audit.
- HF runtime dependency versions can still differ; install with `pip install -e ".[training]"` and stop before training if imports fail.
- First-run outputs may be modest. That is acceptable if reported honestly as a tiny real run.
- `--use-unsloth` is intentionally not approved for the first tiny run.
