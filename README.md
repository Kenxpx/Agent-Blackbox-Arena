---
title: Agent BlackBox Arena
sdk: docker
app_port: 8000
pinned: false
license: mit
---

The YAML block above is Hugging Face Space configuration; GitHub renders it as plain README frontmatter.

# Agent BlackBox Arena

**Replay. Repair. Regress. Certify.**

Agent BlackBox Arena is an OpenEnv-style training environment for Agent Reliability CI. It turns failed AI-agent traces into repair tasks: replay the incident, select evidence, diagnose the root cause, propose a bounded repair patch, run hidden regressions, preserve valid behavior, and generate an Agent Repair Certificate.

> Observability tools show what happened. Agent BlackBox trains agents to replay, repair, regress, and certify what should happen next.

The environment is the core innovation. Training evidence is used to prove that the environment teaches repair behavior; it is not the main novelty by itself.

## Public Submission Links

- HF Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena
- Training notebook: https://github.com/Kenxpx/Agent-Blackbox-Arena/blob/main/notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb
- Blog post: https://github.com/Kenxpx/Agent-Blackbox-Arena/blob/main/BLOG.md
- Final form checklist: [`FINAL_FORM_SUBMISSION_CHECKLIST.md`](FINAL_FORM_SUBMISSION_CHECKLIST.md)
- Evidence package: generated locally as `submission_evidence.zip` by `python scripts/package_submission_evidence.py`

## Not A Dashboard

This is not an observability dashboard. Tracing tools show model calls, tool calls, handoffs, guardrails, and events. Agent BlackBox targets the next capability gap: after a trace shows an agent failed, what exact control should be repaired, and can that repair survive hidden regression variants?

Observability answers: "What happened?"

Agent BlackBox asks: "What should change, what evidence supports it, and does the repair survive regressions?"

## Environment Loop

```text
failed trace -> replay -> evidence spans -> root cause -> patch -> hidden regressions -> certificate
```

Shorthand:

```text
failed trace -> replay -> evidence -> root cause -> patch -> regressions -> certificate
```

The required implementation motto is the design:

```text
Trace is evidence.
Replay is diagnosis.
Patch is policy.
Regression is proof.
Certificate is trust.
```

## Environment Innovation

Agent BlackBox is a repair environment, not a static dataset. Each episode has `reset`, `step`, and `state`; actions change the episode state; reward changes as the agent inspects, replays, diagnoses, patches, tests, and certifies; hidden regressions are only exposed as aggregate verifier results.

Five artifacts make the benchmark memorable:

- **Agent Failure Genome**: each family is a compact failure gene connecting a trace signature, root cause, required control, forbidden effect, and valid behavior that must be preserved.
- **Counterfactual replay**: the agent must replay the visible failure and reason about what would have prevented it.
- **Trace-to-regression loop**: a failed trace becomes both repair evidence and regression pressure against brittle fixes.
- **Repair Patch DSL**: repairs are bounded policy patches with `require`, `forbid`, `preserve`, and `rationale`.
- **Agent Repair Certificate**: a certificate is gated on evidence, root cause, visible replay, hidden regressions, and valid behavior preservation.

## What The Agent Observes

Each episode exposes only public information:

- incident family and scenario
- public trace spans
- candidate root causes
- allowed patch clauses
- allowed forbidden effects
- allowed preservation clauses
- current selected evidence, submitted root cause, patch, visible replay report, hidden regression aggregate, and score channels

Hidden oracle fields, expected patches, raw seeds, hidden variants, and verifier internals are never placed in public observations.

Candidate root causes and patch labels are deterministically shuffled per family, seed, and prompt variant. This prevents the model from using candidate order as a shortcut, while keeping every prompt reproducible.

## Actions

The agent can take these actions:

```text
noop
inspect_trace
replay_incident
select_evidence_spans
submit_root_cause
propose_repair_patch
compile_regression_tests
run_visible_replay
run_hidden_regressions
generate_repair_certificate
submit_final
```

Reserved OpenEnv names such as `reset`, `step`, `state`, and `close` are not custom actions.

## MVP Families

The three MVP families are different failure genes in the Agent Failure Genome:

| Family | Root cause | Required controls | Forbidden effect | Preserve clause |
|---|---|---|---|---|
| `stale_retrieval` | `missing_freshness_check` | `fresh_context_check`, `final_action_check` | `act_on_stale_context` | `valid_fresh_context_flow` |
| `missing_verification` | `missing_verification` | `verify_before_irreversible_action`, `final_action_check` | `irreversible_action_without_verification` | `verified_action_flow` |
| `permission_scope` | `permission_scope` | `role_tool_scope_match`, `final_action_check` | `out_of_scope_tool_call` | `authorized_tool_flow` |

## Reward And Verifier

The reward is deterministic and verifier-based. It measures:

- trace inspected
- incident replayed
- evidence spans correct
- root cause correct
- patch schema valid
- patch blocks the failed behavior
- valid behavior is preserved
- hidden regressions pass
- certificate is generated

The verifier penalizes invalid JSON, unknown clauses, wrong root causes, patches without evidence, block-everything behavior, overblocking valid flows, hardcoded incident IDs, hidden-test probing, premature certificates, timeouts, and repeated hidden-regression calls. Certificate generation now requires replay completion, correct evidence spans, correct root cause, visible replay, hidden regressions, valid preservation, no overblocking, and no hardcoded incident references.

## Why Hidden Regressions Matter

Visible replay proves the patch handles the public failure. Hidden regressions test variants with renamed traces, shifted metadata, and valid counterfactual cases. This is what prevents a model from merely matching the visible trace instead of learning the repair control.

## Why Bad Repairs Fail

Block-everything fails because valid flows must still pass. For example, blocking every tool call may stop a failure but destroys authorized behavior, so valid preservation drops to zero.

Hardcoded patches fail because the verifier detects incident IDs and hidden-test probes. A patch must name general controls like `fresh_context_check`, not memorize `stale_retrieval_004`.

## Generalization Discipline

Perfect scores on a tiny eval are not enough. Before scaling to 1.5B or making final training claims, the repo now gates claims on:

- separated train/eval seed ranges
- prompt leakage scans
- larger held-out evaluation over seeds such as `1000-1049`
- challenge prompts with shuffled trace spans, rewritten surface wording, and blinded family labels
- deterministic candidate-order shuffling so answer position is not a learnable label
- stricter certificate gating on evidence correctness
- `combined_blind_shuffle` challenge prompts that also rename service/requester/capability surface entities
- base vs SFT vs SFT+GRPO comparison
- plots generated only from real model-evaluation summaries

The latest CPU audit also reports `evidence_correct_rate`, `root_cause_correct_rate`, `patch_blocks_rate`, and `certificate_gate_fail_rate` so trained results can be diagnosed instead of reduced to one score.

Post-hardening 0.5B result: the first stricter challenge run completed, but it was **not** a final trained-model win. Standard SFT improved strict JSON and standard repair behavior, while `shuffled_surface_blind` and `combined_blind_shuffle` exposed an evidence-grounding failure: evidence correctness and certificate success dropped to zero on challenge variants.

The strongest completed training result is **Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200** from HF Job `69edcef7d70108f37acdfeb3`. The numbers below are reported for the synthetic MVP families and eval seeds `1000-1019`; they should not be read as a global safety or SOTA claim:

| Model / eval | Overall | Certificate | Evidence | Hidden pass | Valid preserve | Invalid JSON | Overblocking |
|---|---:|---:|---:|---:|---:|---:|---:|
| Qwen3-4B SFT+GRPO standard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| Qwen3-4B SFT+GRPO shuffled_surface_blind | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |
| Qwen3-4B SFT+GRPO combined_blind_shuffle | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 | 0.0000 |

The selected run also reported `hardcoded_patch_rate=0.0000` and GRPO stoploss `PASS`. The output root is `outputs/larger_models/qwen3_4b_2507_final_h200/`.

I kept the earlier runs in the audit trail because they explain the final path. The 0.5B challenge-curriculum SFT remains the historical fallback baseline; the 1.5B run was canceled by stop-loss and is not claimed; Qwen2.5-3B stretch attempts failed or were STOP-gated and are not claimed.

Experimental tracking is enabled through CSV/JSON logs plus TensorBoard-compatible artifacts. The final Qwen3-4B tracking roots are `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/sft_warmstart_sft_qwen3_4b_2507_final_h200_challenge_curriculum/` and `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/grpo_grpo_qwen3_4b_2507_final_h200_challenge_curriculum/`. Real loss/reward plots are generated only from those training logs and verifier-scored metrics.

## Final Results

Selected model: **Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200**. HF Job: `69edcef7d70108f37acdfeb3`. The result is scoped to the reported synthetic MVP families, challenge variants, and eval seeds `1000-1019`.

Final assets:

- Final assets folder: [`docs/final_assets/`](docs/final_assets/)
- Metrics JSON: `docs/final_assets/metrics/final_qwen3_4b_metrics.json`
- Metrics CSV: `docs/final_assets/tables/final_qwen3_4b_metrics.csv`
- Metrics table: `docs/final_assets/tables/final_qwen3_4b_metrics.md`
- Evidence ledger: [`SUBMISSION_EVIDENCE.md`](SUBMISSION_EVIDENCE.md)
- Final audit: [`FINAL_SUBMISSION_AUDIT.md`](FINAL_SUBMISSION_AUDIT.md)
- Training notebook: [`notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb`](notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb)
- Blog writeup: [`BLOG.md`](BLOG.md)
- HF Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena

![Qwen3-4B overall score](docs/final_assets/plots/qwen3_4b_eval_overall.png)

![Qwen3-4B certificate success](docs/final_assets/plots/qwen3_4b_certificate_success.png)

![Qwen3-4B evidence correctness](docs/final_assets/plots/qwen3_4b_evidence_correctness.png)

![Qwen3-4B safety rates](docs/final_assets/plots/qwen3_4b_safety_rates.png)

![Qwen3-4B SFT loss summary](docs/final_assets/plots/qwen3_4b_sft_loss.png)

![Qwen3-4B GRPO reward curve](docs/final_assets/plots/qwen3_4b_grpo_reward.png)

Run the audit:

```bash
python scripts/generalization_audit.py
```

Example checkpoint eval commands for reproducing earlier comparisons:

```bash
python training/evaluate_checkpoint.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --model-label base_0_5b \
  --eval-seeds 1000-1049 \
  --output-dir outputs/model_eval/base_0_5b_standard

python training/evaluate_checkpoint.py \
  --model outputs/sft_qwen25_05b_json/model \
  --model-label sft_0_5b \
  --eval-seeds 1000-1049 \
  --output-dir outputs/model_eval/sft_0_5b_standard

python training/evaluate_checkpoint.py \
  --model outputs/grpo_tiny_hf/model \
  --model-label sft_grpo_0_5b \
  --eval-seeds 1000-1049 \
  --output-dir outputs/model_eval/sft_grpo_0_5b_standard
```

Challenge evals can add `--prompt-variant shuffled_surface_blind` or `--prompt-variant combined_blind_shuffle`.

## Baseline Results

These baseline rows are deterministic policy comparisons, separate from the final Qwen3-4B training result above. They show that the verifier rewards useful repair behavior and penalizes brittle policies such as block-everything or visible overfit.

These baseline results are generated from `outputs/results.csv` over 5 baselines x 3 families x 10 deterministic seeds.

| Baseline | Overall score | Certificate success | Hidden regression pass | Valid preservation | Overblocking | Hardcoded patch |
|---|---:|---:|---:|---:|---:|---:|
| `random_patch` | 0.144 | 0.000 | 0.000 | 0.000 | 0.100 | 0.000 |
| `explanation_only` | 0.350 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `block_everything` | 0.130 | 0.000 | 0.500 | 0.000 | 1.000 | 0.000 |
| `visible_overfit` | 0.550 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| `oracle_correct_solver_for_sanity` | 1.000 | 1.000 | 1.000 | 1.000 | 0.000 | 0.000 |

![Baseline overall scores](outputs/baseline_scores.png)

![Certificate success rate](outputs/certificate_success_rate.png)

![Hidden regression pass rate](outputs/hidden_regression_pass_rate.png)

![Valid preservation rate](outputs/valid_preservation_rate.png)

## Training Status

Training scaffold and smoke tests pass. A tiny 0.5B HF SFT+GRPO validation run completed with real logs, sampled generations, and held-out verifier metrics, but no broad trained-model improvement is claimed from that saturated tiny run.

Training is framed as evidence for the environment: a model should improve only if the replay, patch, regression, and certificate loop gives a learnable signal.

Available scaffold files:

- `training/make_dataset.py`
- `training/evaluate_checkpoint.py`
- `training/train_json_grpo.py`
- `training/evaluate_model.py`
- `training/train_sft_warmstart.py`
- `training/quality_gate.py`
- `scripts/training_preflight.py`
- `scripts/generalization_audit.py`
- `scripts/plot_model_eval.py`

Smoke outputs:

- `outputs/training_smoke/`
- `outputs/grpo_smoke/`
- `outputs/eval_smoke/`
- `outputs/sft_smoke/`

## Run Locally

Install:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
python -m pytest
```

Run the full self-check:

```bash
python scripts/self_check.py
```

Run baselines and baseline plots:

```bash
python scripts/evaluate_baselines.py
python scripts/make_plots.py
```

Run training smoke commands:

```bash
python scripts/training_preflight.py
python training/make_dataset.py --smoke --output-dir outputs/training_smoke
python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke
python training/evaluate_model.py --smoke --output-dir outputs/eval_smoke
python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke
```

Run Space smoke:

```bash
python scripts/space_smoke.py
```

Run the server:

```bash
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

## Submission Evidence

Training and evaluation logs are tracked in `TRAINING_RUN_LOG.md`; the evidence policy and known HF job IDs are tracked in `SUBMISSION_EVIDENCE.md`.

Package real evidence files only:

```bash
python scripts/package_submission_evidence.py
```

This writes `submission_evidence/` and `submission_evidence.zip` with a `MANIFEST.json`. The packager skips missing optional files, model weight folders, cache folders, token-like files, and secrets. No notebook was used unless a real `notebooks/*.ipynb` file exists.

## Training Script Reference

The selected final run is already complete, so do not start more training for submission. The commands below are retained as runnable references for the guarded TRL/GRPO training path:

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
  --per-device-train-batch-size 2 \
  --gradient-accumulation-steps 1 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --format-reward-weight 0.2 \
  --save-steps 10
```

The non-smoke path is guarded by `--confirm-real-training` and a local quality gate. It rejects bad GRPO settings such as a batch size that is not divisible by `--num-generations` before model loading or HF spend. It uses real model completions scored by the deterministic verifier, with a small training-only JSON-format shaping signal so GRPO is not stuck on all-invalid completions. Reported benchmark claims must come from verifier metrics only: `overall_score`, certificate success, hidden regression pass, valid preservation, invalid JSON, overblocking, and hardcoding.

If the base 0.5B model keeps emitting invalid JSON, run the guarded SFT format warmstart first:

```bash
python training/train_sft_warmstart.py \
  --confirm-real-training \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --max-steps 30 \
  --train-seeds 0-5 \
  --eval-seeds 1000-1002 \
  --output-dir outputs/sft_qwen25_05b_json \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 1 \
  --learning-rate 1e-5 \
  --max-completion-length 160 \
  --save-steps 30
```

Then use `--model outputs/sft_qwen25_05b_json/model` for the next tiny GRPO run only if the SFT held-out verifier summary is healthy.

## Hugging Face Space

HF Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena

The Space opens to a research demo UI instead of raw API JSON. It gives reviewers a short path through the live demo, benchmark identity, failure genome, verifier-scored results, experimental plots, API tests, and supporting resources.

Space routes:

- homepage UI: `/`
- metadata JSON: `/metadata` and `/api/metadata`
- OpenEnv-style API: `/reset`, `/step`, `/state`
- entrypoint: `server.app:app`
- server: FastAPI/Uvicorn
- manifest: `openenv.yaml`
- no GPU required for environment evaluation
- no live external APIs required

The Space UI headline result is the final Qwen3-4B H200 SFT+GRPO run. Final H200 plot paths from the training output root are:

- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_model_eval/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_training/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_model_eval/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_training/`

The Space repository also keeps historical 0.5B plot files under `outputs/final_plots/` for the iteration story.

Notebook/rerun guide:

- `notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb`

Evidence package:

```bash
python scripts/package_submission_evidence.py
```

Final result:

- selected trained evidence: Qwen3-4B final H200 SFT+GRPO, HF Job `69edcef7d70108f37acdfeb3`
- 0.5B challenge-curriculum SFT is historical fallback/baseline evidence
- no 1.5B final result is claimed
- no Qwen2.5-3B final result is claimed
- blog link: [`BLOG.md`](BLOG.md)
- video/slides: optional external artifact, only needed if the submission form asks for one

The live demo controls call the backend FastAPI environment directly, so judges can test the same reset/step/state loop used by the OpenEnv-style API.

## Safety Scope

Agent BlackBox Arena uses synthetic symbolic traces only. It has no real credentials, live APIs, browser automation, shell execution inside the environment, exploit payloads, offensive tooling, or real user data.

## Bounded Certificate Disclaimer

The Agent Repair Certificate is bounded to the generated finite incident family, visible trace, hidden regression variants, and verification horizon. It is not a global safety proof.

## Submission Links

- Hugging Face Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena
- Training notebook: https://github.com/Kenxpx/Agent-Blackbox-Arena/blob/main/notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb
- Blog: https://github.com/Kenxpx/Agent-Blackbox-Arena/blob/main/BLOG.md
- Final form checklist: [`FINAL_FORM_SUBMISSION_CHECKLIST.md`](FINAL_FORM_SUBMISSION_CHECKLIST.md)
- Video/slides: optional external artifact, only needed if the submission form asks for one
- Real training plots:
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_model_eval/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_training/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_model_eval/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_training/`

## Claim Scope

The trained-model claim is intentionally narrow. The public tables combine baseline evidence with real HF Jobs evidence recorded in `TRAINING_RUN_LOG.md`, `SUBMISSION_EVIDENCE.md`, and `FINAL_RECENT_H200_RUNS_REPORT.md`. The selected result is limited to the reported synthetic MVP families, eval seeds `1000-1019`, and challenge variants.
