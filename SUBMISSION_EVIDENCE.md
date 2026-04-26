# Submission Evidence

This evidence ledger keeps the final submission claim tied to concrete artifacts. Metrics, plots, notebooks, and logs listed here come from repo files or saved HF job output.

The selected evidence is **Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200**, HF Job `69edcef7d70108f37acdfeb3`, output root `outputs/larger_models/qwen3_4b_2507_final_h200/`. The result is scoped to the reported synthetic MVP families, prompt variants, and eval seeds `1000-1019`.

## Execution Method

Training and evaluation have been run through Hugging Face Jobs CLI and repository scripts. No notebook was used; training was run via HF Jobs CLI and repo scripts.

## Known Hugging Face Jobs

| Job ID | Hardware | Status | Role |
|---|---|---|---|
| `69ed0befd2c8bd8662bce36c` | `cpu-basic` | completed | Early CPU smoke after dependency fixes. |
| `69ed0cebd2c8bd8662bce388` | `t4-small` | error | Failed because `generation_batch_size (1)` was not divisible by `num_generations (2)`. |
| `69ed0f55d2c8bd8662bce3d6` | `t4-small` | completed | Corrected batch size but invalid JSON collapse. |
| `69ed12abd70108f37acdedc6` | `cpu-basic` | completed | CPU smoke after JSON prompt hardening. |
| `69ed130dd2c8bd8662bce45b` | `t4-small` | completed | 0.5B GRPO attempt completed but failed quality stop-loss. |
| `69ed1880d2c8bd8662bce4e5` | `cpu-basic` | completed | Fresh HF runtime passed GRPO smoke, SFT smoke, self_check, Space smoke, and pytest. |
| `69ed18e7d2c8bd8662bce4f2` | `t4-small` | completed | Tiny 0.5B SFT format warmstart succeeded on reported small held-out eval. |
| `69ed1a3ed2c8bd8662bce516` | `t4-small` | completed | Tiny SFT warmstart plus 0.5B GRPO validation succeeded on reported small held-out eval. |
| `69ed520cd2c8bd8662bcea54` | `t4-small` | canceled | Larger-eval attempt canceled intentionally. |
| `69ed549bd70108f37acdf273` | `t4-small` | completed | Pre-hardening larger 0.5B standard and shuffled challenge evaluation. |
| `69eda5a4d70108f37acdfa48` | `t4-small` | completed | 0.5B challenge-curriculum SFT historical fallback baseline. |
| `69edaafcd70108f37acdfadb` | `t4-small` | canceled | 1.5B canceled by stoploss; no 1.5B result claimed. |
| `69edc89ed2c8bd8662bcf90c` | `h200` | error | Qwen2.5-3B fast r1 failed on H200 CUDA/BF16 initialization; not claimed. |
| `69edc8a5d70108f37acdfe18` | `h200` | error | Qwen3-4B fast r1 failed on H200 CUDA/BF16 initialization; not claimed. |
| `69edc9b8d2c8bd8662bcf937` | `h200` | completed | Qwen2.5-3B fast retry completed but SFT gate stopped; no 3B success claim. |
| `69edcb91d70108f37acdfe5a` | `h200` | completed | Qwen2.5-3B fast r2 completed but SFT gate stopped; no 3B success claim. |
| `69edc9c3d2c8bd8662bcf93c` | `h200` | error | Qwen3-4B fast retry produced useful SFT signal but errored during GRPO evaluation; not final. |
| `69edcb9ad70108f37acdfe5e` | `h200` | completed | Qwen3-4B fast r2 passed but was intermediate and weaker than final. |
| `69edcef7d70108f37acdfeb3` | `h200` | completed | Final selected Qwen3-4B SFT+GRPO H200 result. |

Post-hardening 0.5B job `69ed986cd70108f37acdf8ba` completed and printed `POST_HARDENING_0_5B_COMPLETE`. It is not final improvement evidence: challenge variants exposed evidence-grounding failure and GRPO stoploss reported `STOP`. The next evidence step is a 0.5B challenge-curriculum run, not 1.5B.

## Commands And Scripts

Primary local checks:

```bash
python scripts/self_check.py
python scripts/generalization_audit.py
python -m pytest
```

Hardened 0.5B HF run script:

```bash
bash scripts/hf_run_05b_hardened.sh
```

Evidence package command:

```bash
python scripts/package_submission_evidence.py
```

## Models And Hardware

| Stage | Model | Hardware | Notes |
|---|---|---|---|
| Base eval | `Qwen/Qwen2.5-0.5B-Instruct` | `t4-small` | Used as zero-shot comparison. |
| SFT warmstart | `Qwen/Qwen2.5-0.5B-Instruct` | `t4-small` | Format/action warmstart, not a standalone safety claim. |
| GRPO validation | SFT checkpoint | `t4-small` | Verifier-scored validation after SFT. |
| Final selected | `Qwen/Qwen3-4B-Instruct-2507` | `h200` | SFT+GRPO final H200, job `69edcef7d70108f37acdfeb3`. |

The 1.5B and Qwen2.5-3B attempts are not final claims. 1.5B was canceled by stoploss. Qwen2.5-3B H200 attempts failed or were STOP-gated. Qwen3-4B final H200 is the selected model.

## Seeds And Prompt Variants

Training seeds:

- SFT: `0-5`
- GRPO: `0-2`

Evaluation seeds:

- Small held-out checks: `1000-1002`
- Larger held-out checks: `1000-1019`
- Audit target range: `1000-1049`

Prompt variants:

- `standard`
- `shuffled_surface_blind`
- `combined_blind_shuffle`

## Metrics Summary

Baseline metrics are in `outputs/results.csv` and `outputs/baseline_summary.json`.

Known pre-hardening evidence:

- Base 0.5B zero-shot emitted invalid JSON on reported larger eval.
- SFT 0.5B fixed strict repair-plan JSON generation on reported held-out seeds.
- SFT+GRPO 0.5B passed reported standard hidden-regression and certificate metrics after SFT.
- Pre-hardening `shuffled_surface_blind` challenge did not collapse, but `overall_score` was `0.78`, which motivated stricter anti-leakage hardening.

Post-hardening evidence status:

- standard eval completed for the selected Qwen3-4B run
- `shuffled_surface_blind` eval completed for the selected Qwen3-4B run
- `combined_blind_shuffle` eval completed for the selected Qwen3-4B run
- clean final plots and tables are stored under `docs/final_assets/`

Post-curriculum evidence now available:

- HF job `69eda5a4d70108f37acdfa48` completed and printed `POST_CHALLENGE_CURRICULUM_0_5B_COMPLETE`.
- Extracted summaries are under `outputs/model_eval/extracted_hf/hf_05b_challenge_curriculum/`.
- Real plots are under `outputs/final_plots/`.
- The 1.5B attempt `69edaafcd70108f37acdfadb` was canceled after `quality_status=STOP`; no 1.5B result is claimed.

Final Qwen3-4B H200 evidence now available:

- HF job `69edcef7d70108f37acdfeb3` completed and printed `POST_FINAL_QWEN3_4B_H200_COMPLETE`.
- Final selected model: `Qwen/Qwen3-4B-Instruct-2507`.
- Final selected checkpoint: `SFT+GRPO`.
- Output root: `outputs/larger_models/qwen3_4b_2507_final_h200/`.
- Log file: `logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt`.
- Recent run report: `FINAL_RECENT_H200_RUNS_REPORT.md`.

Final metrics over eval seeds `1000-1019`:

| Variant | Overall | Certificate | Evidence | Hidden pass | Valid preserve | Invalid JSON | Overblocking | Hardcoded patch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `standard` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| `shuffled_surface_blind` | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| `combined_blind_shuffle` | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |

Final plot paths:

- Clean final assets:
  - `docs/final_assets/plots/qwen3_4b_sft_loss.png`
  - `docs/final_assets/plots/qwen3_4b_grpo_reward.png`
  - `docs/final_assets/plots/qwen3_4b_eval_overall.png`
  - `docs/final_assets/plots/qwen3_4b_certificate_success.png`
  - `docs/final_assets/plots/qwen3_4b_evidence_correctness.png`
  - `docs/final_assets/plots/qwen3_4b_safety_rates.png`
- Clean metrics assets:
  - `docs/final_assets/metrics/final_qwen3_4b_metrics.json`
  - `docs/final_assets/tables/final_qwen3_4b_metrics.csv`
  - `docs/final_assets/tables/final_qwen3_4b_metrics.md`
- Loss/reward provenance:
  - `qwen3_4b_sft_loss.png` and `qwen3_4b_grpo_reward.png` are derived from real final H200 log/tracking evidence, not invented curves.
  - The final GRPO reward rows are visible in `logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt`.
- Remote H200 output paths recorded in the final log:
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_model_eval/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_training/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_model_eval/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_training/`

Final tracking paths:

- `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/sft_warmstart_sft_qwen3_4b_2507_final_h200_challenge_curriculum/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/grpo_grpo_qwen3_4b_2507_final_h200_challenge_curriculum/`

Training status:

- final training is complete
- no additional 1.5B, 3B, 4B, or H200 job is needed for the submission package
- historical scripts remain in `scripts/` for audit/reproducibility, not as active next steps

Experimental tracking:

- CSV/JSON logs remain the underlying record.
- TensorBoard-compatible artifacts are written under `outputs/tracking/` during real SFT/GRPO runs.
- Lightweight loss/reward plots are written under `outputs/final_plots/` only when real tracking or verifier reward rows exist.

## Stop-Loss Decisions

All training is stopped. Final selected model is Qwen3-4B H200 SFT+GRPO. No further model runs are needed for this submission package.

Stop if any post-hardening 0.5B run shows:

- missing `summary.json`, `metrics.csv`, or sampled generations
- `invalid_json_rate > 0.10` for SFT or SFT+GRPO
- certificate success high while evidence/root-cause/patch diagnostics are weak
- hidden regression collapse
- valid preservation collapse
- overblocking or hardcoded-patch behavior
- no real model-eval logs

## Claim Boundaries

Supported by the evidence above:

- Agent BlackBox Arena is an OpenEnv-style repair environment with hidden regressions and certificate gating.
- Baseline policies score low while the oracle sanity solver scores high.
- The first 0.5B GRPO-only attempt exposed an invalid-JSON formatting bottleneck.
- A small SFT warmstart fixed strict repair-plan generation on the reported held-out seeds.
- Qwen3-4B final H200 SFT+GRPO is the final selected model based on real HF Job `69edcef7d70108f37acdfeb3`.
- The selected result passed standard, `shuffled_surface_blind`, and `combined_blind_shuffle` verifier-scored eval over seeds `1000-1019`.
- The selected result had `invalid_json_rate=0.0000`, `overblocking_rate=0.0000`, `hardcoded_patch_rate=0.0000`, and stoploss `PASS`.

## Not Claimed

The submission does not claim:

- broad production safety
- SOTA
- GRPO learned from scratch
- 1.5B success
- Qwen2.5-3B success
- failed/error H200 jobs as successful
- unlimited generalization
- trained improvement from fake or placeholder plots
- certificate as a global safety proof
