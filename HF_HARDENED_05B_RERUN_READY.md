# Agent BlackBox Arena - Hardened 0.5B Rerun Ready

Status: **GO for post-hardening 0.5B HF rerun**

Important lock: **NO-GO for 1.5B** until the post-hardening 0.5B `standard`, `shuffled_surface_blind`, and `combined_blind_shuffle` summaries are inspected.

## 1. self_check Output

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
training_preflight: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_preflight_report.json
training_preflight: status=PASS records=6 families=missing_verification,permission_scope,stale_retrieval
training_preflight: bad GRPO batch/num_generations config rejected
training_preflight: prompt leakage and verifier targets ok
make_dataset: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_smoke\train.jsonl
make_dataset: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_smoke\eval.jsonl
make_dataset: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\training_smoke\dataset_summary.json
make_dataset: train_records=6 eval_records=3 families=stale_retrieval,missing_verification,permission_scope prompt_variant=standard
train_json_grpo: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\grpo_smoke\metrics.csv
train_json_grpo: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\grpo_smoke\sampled_generations.jsonl
train_json_grpo: smoke invalid_json_rate=0.2000
train_json_grpo: full GRPO not run in smoke mode
evaluate_model: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\eval_smoke\metrics.csv
evaluate_model: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\eval_smoke\summary.json
evaluate_model: score=0.5360 cert=0.4000 hidden=0.5000 invalid_json=0.2000
train_sft_warmstart: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\sft_smoke\sft_samples.jsonl
train_sft_warmstart: smoke wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\sft_smoke\sft_smoke_summary.json
train_sft_warmstart: full SFT not run in smoke mode
space_smoke: FastAPI app import ok
space_smoke: environment metadata ok
space_smoke: reset/step/state ok
space_smoke: stale_retrieval certificate path ok
generalization_audit: leakage_status=PASS
generalization_audit: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\generalization_audit\leakage_audit.json
generalization_audit: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\GENERALIZATION_AND_CLAIM_AUDIT.md
generalization_audit: model larger held-out eval pending; no trained plots created
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
self_check: generalization audit ok
```

## 2. generalization_audit Output

```text
generalization_audit: leakage_status=PASS
generalization_audit: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\outputs\generalization_audit\leakage_audit.json
generalization_audit: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\GENERALIZATION_AND_CLAIM_AUDIT.md
generalization_audit: model larger held-out eval pending; no trained plots created
```

## 3. package_submission_evidence Output

```text
package_submission_evidence: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\submission_evidence
package_submission_evidence: wrote C:\Users\sanji\Music\Metax\agent-blackbox-arena\submission_evidence.zip
package_submission_evidence: included=19 missing=16 skipped=0
```

Evidence package:

```text
C:\Users\sanji\Music\Metax\agent-blackbox-arena\submission_evidence.zip
```

Manifest summary:

```text
included=19 missing=16 skipped=0
zip_exists=True
```

Missing files are expected before the post-hardening HF rerun because fresh `outputs/model_eval/*`, `outputs/grpo_tiny_hf/*`, and `outputs/sft_qwen25_05b_json/*` artifacts do not exist locally yet.

## 4. pytest Output

```text
.....................................................                    [100%]
53 passed in 0.13s
```

## 5. Exact HF Command

Run this from the local repo after confirming HF CLI is authenticated:

```powershell
hf jobs run `
  --flavor t4-small `
  --timeout 120m `
  python:3.11 `
  -- `
  bash `
  -lc `
  "apt-get update && apt-get install -y git && git clone https://github.com/Kenxpx/Agent-Blackbox-Arena.git && cd Agent-Blackbox-Arena && pip install -e '.[training]' && bash scripts/hf_run_05b_hardened.sh"
```

This runs only the hardened 0.5B sequence. It does **not** run 1.5B or 4B.

## 6. GO / NO-GO

**GO** for one controlled post-hardening 0.5B HF rerun.

**NO-GO** for 1.5B until the post-hardening 0.5B standard, `shuffled_surface_blind`, and `combined_blind_shuffle` summaries are inspected.

**NO-GO** for final trained-model claims until the fresh post-hardening model-eval summaries and plots exist.

## Notes

- No GPU was used during local checks.
- No fake plots or metrics were created.
- Local Windows shell did not have `bash`, so only the Python checks were executed locally. The HF job uses a Linux `python:3.11` runtime and executes the script through `bash -lc`.
- Latest pushed commit containing the run script and evidence packager: `569bd94 Add hardened HF run and submission evidence packaging`.
