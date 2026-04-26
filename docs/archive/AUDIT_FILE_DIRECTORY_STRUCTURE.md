# Audit File And Directory Structure

This file is a judge/audit map for the repository. Comments explain what each file or folder contains and why it matters.

Importance key:

- `CRITICAL`: needed to verify the final selected result, Space behavior, environment contract, or claims.
- `HIGH`: important supporting evidence, tests, or training code.
- `MEDIUM`: useful for reproduction or debugging.
- `LOW`: historical, generated, or auxiliary material.

## Fast Audit Path

```text
README.md                                      # CRITICAL: public project overview, final selected Qwen3-4B H200 SFT+GRPO metrics, Space link, evidence instructions, bounded claims.
FINAL_SUBMISSION_AUDIT.md                      # CRITICAL: final submission checklist, selected model, readiness status, remaining video/blog TODO.
SUBMISSION_EVIDENCE.md                         # CRITICAL: source-of-truth evidence ledger, final job ID, allowed/forbidden claims, plot/tracking/log paths.
TRAINING_RUN_LOG.md                            # CRITICAL: full training chronology, failed/canceled runs, stoploss decisions, final H200 metrics.
FINAL_RECENT_H200_RUNS_REPORT.md               # CRITICAL: five recent H200 runs with job IDs, statuses, summaries, stoploss, plots, tracking, final decision.
server/ui.py                                   # CRITICAL: Hugging Face Space homepage UI and visible metric cards.
server/app.py                                  # CRITICAL: FastAPI app exposing `/`, `/metadata`, `/reset`, `/step`, `/state`.
agent_blackbox/                                # CRITICAL: core benchmark environment logic, incidents, verifier, reward, certificate.
scripts/package_submission_evidence.py         # CRITICAL: creates `submission_evidence/` and `submission_evidence.zip` while excluding secrets/checkpoints.
submission_evidence.zip                        # CRITICAL: generated evidence package for submission review.
notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb # HIGH: rerun guide/notebook artifact for judges.
```

## Root Files

```text
.
├── README.md                                  # CRITICAL: main public readme; includes project identity, final selected Qwen3-4B metrics, HF Space URL, notebook link, evidence instructions, and bounded claim language.
├── BENCHMARK_SPEC.md                          # HIGH: benchmark/environment specification; explains OpenEnv-style contract, actions, scoring, and expected behavior.
├── TRAINING.md                                # HIGH: training methodology and commands; useful for reproducing SFT/GRPO pipeline design.
├── TRAINING_RUN_LOG.md                        # CRITICAL: real HF Jobs training history; includes failures, stoploss, 0.5B fallback, Qwen3-4B final H200 metrics.
├── SUBMISSION_EVIDENCE.md                     # CRITICAL: evidence ledger with final job ID `69edcef7d70108f37acdfeb3`, final metrics, plot paths, tracking paths, and claim boundaries.
├── FINAL_SUBMISSION_AUDIT.md                  # CRITICAL: final readiness checklist; confirms Space/API/training evidence/tracking/notebook status.
├── FINAL_EXECUTION_LOG.md                     # HIGH: consolidated build/training/deployment narrative; good for audit chronology.
├── FINAL_RECENT_H200_RUNS_REPORT.md           # CRITICAL: recent H200 run report; distinguishes final Qwen3-4B success from failed/intermediate 3B/4B attempts.
├── FINAL_SAFE_BASELINE.md                     # HIGH: documents preserved 0.5B fallback/historical baseline and append-only larger-model policy.
├── GENERALIZATION_AND_CLAIM_AUDIT.md          # HIGH: leakage/generalization audit output; confirms prompt/seed separation and bounded claims.
├── CHALLENGE_FAILURE_ANALYSIS.md              # MEDIUM: analysis of challenge prompt/evidence grounding failures and fixes.
├── POST_HARDENING_05B_RESULTS_FOR_REVIEW.md   # MEDIUM: historical 0.5B post-hardening review before final larger-model result.
├── PRE_TRAINING_AUDIT.md                      # MEDIUM: early training readiness audit and safety checks.
├── HF_HARDENED_05B_RERUN_READY.md             # LOW: historical go/no-go note for hardened 0.5B rerun.
├── FINAL_HF_TRAINING_GO.md                    # LOW: historical plan for HF training before final result.
├── SUBMISSION_READY.md                        # MEDIUM: submission preparation notes.
├── UI_FINAL_AUDIT.md                          # MEDIUM: Space UI audit notes.
├── SAFETY.md                                  # HIGH: safety scope; synthetic traces only, no real credentials/live APIs/offensive tooling.
├── openenv.yaml                               # CRITICAL: OpenEnv-style metadata/manifest for the environment.
├── Dockerfile                                 # HIGH: Hugging Face Space container/runtime definition.
├── pyproject.toml                             # HIGH: Python package metadata, dependencies, pytest/config entry points.
├── requirements.txt                           # HIGH: runtime dependencies for local/Space execution.
└── AUDIT_FILE_DIRECTORY_STRUCTURE.md          # HIGH: this file; audit map of repository contents and importance.
```

## Core Benchmark Package

```text
agent_blackbox/
├── __init__.py                                # LOW: package marker/import surface.
├── models.py                                  # CRITICAL: action/data models used by environment and API.
├── incidents.py                               # CRITICAL: synthetic incident families, trace data, hidden/visible scenario definitions.
├── verifier.py                                # CRITICAL: deterministic verifier logic; checks evidence, root cause, patch, regressions, overblocking, hardcoding.
├── reward.py                                  # CRITICAL: reward computation and score channels for benchmark episodes.
├── certificate.py                             # CRITICAL: Agent Repair Certificate generation/gating.
├── client.py                                  # MEDIUM: client helpers for interacting with environment/API.
└── render.py                                  # MEDIUM: rendering helpers for observations/traces.
```

Why important: this folder is the benchmark itself. Audit this to verify that final metrics come from deterministic symbolic checks, not from an LLM judge or hand-written claims.

## Space And API Server

```text
server/
├── app.py                                     # CRITICAL: FastAPI entrypoint; exposes homepage, metadata, reset, step, and state routes.
├── ui.py                                      # CRITICAL: HTML/CSS/JS homepage for HF Space; displays final Qwen3-4B metrics and bounded disclaimers.
└── agent_blackbox_environment.py              # CRITICAL: OpenEnv-style environment wrapper around core benchmark state transitions.
```

Why important: this is what judges see and what the HF Space runs. `/reset`, `/step`, `/state`, and `/metadata` must remain working.

## Training Code

```text
training/
├── make_dataset.py                            # HIGH: creates SFT/GRPO datasets across standard and challenge prompt variants.
├── train_sft_warmstart.py                     # HIGH: real SFT training path; writes summaries, checkpoints, tracking, held-out evals.
├── train_json_grpo.py                         # HIGH: real GRPO training path; writes sampled generations, metrics, stoploss reports.
├── evaluate_checkpoint.py                     # HIGH: evaluates trained/base checkpoints on standard/challenge variants and writes verifier summaries.
├── evaluate_model.py                          # MEDIUM: smoke/model evaluation helper.
├── quality_gate.py                            # HIGH: stoploss and quality-gate logic; prevents bad runs from being claimed.
└── tracking.py                                # HIGH: CSV/JSON/TensorBoard-compatible tracking writer; supports output-root overrides.
```

Why important: this folder proves the training/evaluation pipeline exists and records real metrics. For final claims, the key output is the final Qwen3-4B H200 job, not a local checkpoint folder.

## Scripts

```text
scripts/
├── self_check.py                              # CRITICAL: end-to-end local verification; runs environment, baselines, training smoke, Space smoke, audit.
├── space_smoke.py                             # CRITICAL: verifies FastAPI import, homepage, metadata, reset/step/state, certificate path.
├── package_submission_evidence.py             # CRITICAL: builds `submission_evidence/` and zip; excludes secrets, caches, model folders, token files.
├── generalization_audit.py                    # HIGH: audits leakage, prompt safety, seed separation, and claim boundaries.
├── training_preflight.py                      # HIGH: validates training config and prompt/verifier safety before real training spend.
├── evaluate_baselines.py                      # HIGH: computes deterministic baseline policy metrics.
├── make_plots.py                              # MEDIUM: creates baseline plots.
├── plot_model_eval.py                         # HIGH: creates model-evaluation plots from real summary files.
├── plot_training_tracking.py                  # HIGH: creates loss/reward plots from tracking logs.
├── diagnose_challenge_failures.py             # MEDIUM: analyzes challenge evidence/root-cause failures.
├── extract_hf_job_evidence.py                 # MEDIUM: extracts HF job evidence into local structured artifacts.
├── hf_run_05b_hardened.sh                     # LOW: historical 0.5B hardened HF run script.
├── hf_run_05b_challenge_curriculum.sh         # HIGH: historical 0.5B challenge-curriculum run script/fallback evidence path.
├── hf_run_15b_challenge_curriculum.sh         # MEDIUM: locked/cautious 1.5B script; resulted in stoploss/cancel, not claimed.
├── hf_run_4b_stretch.sh                       # LOW: older 4B stretch script, superseded by final Qwen3 H200 flow.
├── hf_run_larger_model_stretch.sh             # MEDIUM: generic larger-model stretch script.
└── hf_run_larger_model_fast_stretch.sh        # HIGH: fast larger-model script used during H200 iteration; includes SFT gate and optional GRPO.
```

Why important: scripts show reproducibility and guardrails. The package script and checks are most important for final submission integrity.

## Tests

```text
tests/
├── test_reset_step_state.py                    # CRITICAL: verifies OpenEnv-style reset/step/state behavior.
├── test_certificate.py                         # CRITICAL: verifies certificate gating.
├── test_reward_anti_hacking.py                 # CRITICAL: verifies anti-overblocking, hardcoding, and reward-hacking resistance.
├── test_hidden_leakage.py                      # CRITICAL: verifies hidden fields do not leak into observations/prompts.
├── test_space_ui.py                            # HIGH: verifies Space UI content and routing expectations.
├── test_training_dataset.py                    # HIGH: verifies dataset generation and challenge prompt safety.
├── test_training_quality_gate.py               # HIGH: verifies quality gate / stoploss logic.
├── test_stale_retrieval.py                     # HIGH: family-specific environment behavior test.
├── test_missing_verification.py                # HIGH: family-specific environment behavior test.
└── test_permission_scope.py                    # HIGH: family-specific environment behavior test.
```

Why important: final local validation passed with `64 passed`. These tests support the claim that the API and verifier logic are intact after final UI/doc updates.

## Notebook

```text
notebooks/
└── Agent_BlackBox_Arena_Training_Rerun.ipynb   # HIGH: judge-facing rerun guide; explains setup, smoke checks, training/eval scaffold, and evidence review.
```

Why important: the notebook is a reproducibility artifact. It is not used to fake metrics; main training evidence comes from HF Jobs logs and summaries.

## Outputs And Evidence Artifacts

```text
outputs/
├── results.csv                                 # HIGH: baseline policy metrics table.
├── baseline_summary.json                       # HIGH: baseline summary.
├── baseline_scores.png                         # MEDIUM: baseline score plot.
├── certificate_success_rate.png                # MEDIUM: baseline certificate plot.
├── hidden_regression_pass_rate.png             # MEDIUM: baseline hidden-regression plot.
├── valid_preservation_rate.png                 # MEDIUM: baseline valid-preservation plot.
├── final_plots/                                # MEDIUM: historical 0.5B/canceled 1.5B plot artifacts.
│   ├── hf_05b_challenge_curriculum_training_loss_curve.png       # MEDIUM: historical 0.5B fallback training loss plot.
│   ├── hf_05b_challenge_curriculum_verifier_reward_comparison.png # MEDIUM: historical 0.5B fallback verifier comparison plot.
│   └── hf_15b_challenge_curriculum_canceled_training_loss_curve.png # LOW: canceled 1.5B stoploss context plot.
├── model_eval/                                 # HIGH: extracted/evaluation summaries used for historical model comparisons.
├── tracking/                                   # HIGH: historical TensorBoard-compatible extracted tracking artifacts.
├── training_smoke/                             # LOW: generated by smoke/self-check; not final model evidence.
├── grpo_smoke/                                 # LOW: generated by smoke/self-check; not final model evidence.
├── eval_smoke/                                 # LOW: generated by smoke/self-check; not final model evidence.
├── sft_smoke/                                  # LOW: generated by smoke/self-check; not final model evidence.
├── generalization_audit/                       # HIGH: leakage/generalization audit outputs.
└── larger_models/                              # CRITICAL if present: append-only larger-model outputs; final Qwen3 path is `qwen3_4b_2507_final_h200/`.
```

Important note: some final Qwen3-4B H200 outputs are recorded by HF job logs and docs rather than fully materialized locally. The final selected output root is:

```text
outputs/larger_models/qwen3_4b_2507_final_h200/ # CRITICAL: final selected output root from HF job; contains/records SFT+GRPO evals, plots, and tracking paths.
```

## Submission Evidence Package

```text
submission_evidence/                            # CRITICAL: generated unpacked evidence package.
submission_evidence.zip                         # CRITICAL: generated zip for submission/review.
```

Contains:

- key docs: README, final audits, training logs, evidence ledger
- notebook rerun guide
- baseline/model-eval summaries
- final plots and tracking artifacts available locally
- HF job logs/tail files included by package rules
- manifest: `submission_evidence/MANIFEST.json`

Safety behavior:

- excludes `.env`, token files, cache folders, checkpoint/model folders, and large model-weight suffixes
- latest observed packaging result: `included=63 missing=14 skipped=0`

## HF Job Logs And Tail Files

```text
hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt        # CRITICAL: final selected Qwen3-4B H200 SFT+GRPO log tail and summaries.
hf_job_qwen3_4b_fast_r2_h200_cuda128_69edcb9ad70108f37acdfe5e_tail.txt # HIGH: intermediate Qwen3-4B fast r2 run; weaker than final.
hf_job_qwen3_4b_fast_h200_cuda128_69edc9c3d2c8bd8662bcf93c_tail.txt    # MEDIUM: intermediate Qwen3-4B run that errored during GRPO eval.
hf_job_3b_fast_r2_h200_cuda128_69edcb91d70108f37acdfe5a_tail.txt       # MEDIUM: Qwen2.5-3B STOP-gated run; not claimed.
hf_job_3b_fast_h200_cuda128_69edc9b8d2c8bd8662bcf937_tail.txt          # MEDIUM: Qwen2.5-3B STOP-gated run; not claimed.
hf_job_3b_fast_h200_69edc89ed2c8bd8662bcf90c_tail.txt                 # LOW: failed 3B r1 H200 CUDA/BF16 attempt.
hf_job_qwen3_4b_fast_h200_69edc8a5d70108f37acdfe18_tail.txt            # LOW: failed Qwen3 r1 H200 CUDA/BF16 attempt.
hf_job_3b_h200_69edc207d70108f37acdfd6d_logs.txt                      # LOW: older 3B H200 log inspected during exploration.
```

Why important: these logs keep failed/error/STOP runs honest and prevent accidental overclaiming.

## Final Claim Source Of Truth

Use these files to verify the final selected model and metrics:

```text
README.md
FINAL_SUBMISSION_AUDIT.md
SUBMISSION_EVIDENCE.md
TRAINING_RUN_LOG.md
FINAL_EXECUTION_LOG.md
FINAL_RECENT_H200_RUNS_REPORT.md
hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt
```

Final selected model:

```text
Qwen/Qwen3-4B-Instruct-2507
SFT+GRPO final H200
HF Job: 69edcef7d70108f37acdfeb3
Eval seeds: 1000-1019
Stoploss: PASS
```

Bounded final metrics:

```text
standard: overall 1.0000, certificate 1.0000, evidence 1.0000, invalid_json 0.0000
shuffled_surface_blind: overall 0.9557, certificate 0.8833, evidence 0.8833, invalid_json 0.0000
combined_blind_shuffle: overall 0.9367, certificate 0.8333, evidence 0.8333, invalid_json 0.0000
overblocking_rate: 0.0000
hardcoded_patch_rate: 0.0000
```

Forbidden claims:

```text
Do not claim global safety.
Do not claim SOTA.
Do not claim production safety.
Do not claim 1.5B success.
Do not claim Qwen2.5-3B success.
Do not claim failed/error H200 runs as successful.
Do not claim generalization beyond reported synthetic families, prompt variants, and eval seeds.
```
