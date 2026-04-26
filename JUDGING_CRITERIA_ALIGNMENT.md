# Judging Criteria Alignment

This file maps Agent BlackBox Arena directly to the OpenEnv Hackathon judging guide.

## TL;DR

Agent BlackBox Arena is an OpenEnv-style repair environment for agent reliability CI. It is designed to teach an LLM a capability that current observability tools do not teach: after an agent fails, identify the evidence, diagnose the root cause, propose a bounded repair, run visible replay, pass hidden regressions, preserve valid behavior, and generate a bounded certificate.

The selected trained result is `Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200`, HF Job `69edcef7d70108f37acdfeb3`.

## Minimum Requirements

| Requirement | Status | Evidence |
|---|---|---|
| OpenEnv-style hosted environment | Ready | HF Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena and live app: https://kenxpx-agent-blackbox-arena.hf.space/ |
| Standard environment API | Ready | `/metadata`, `/reset`, `/step`, `/state`; see `server/app.py`, `server/ui.py`, and `scripts/space_smoke.py` |
| Valid manifest | Ready | `openenv.yaml` |
| Training script using HF TRL / RL framework | Ready | `training/train_json_grpo.py`, `training/train_sft_warmstart.py`, `scripts/hf_run_larger_model_fast_stretch.sh` |
| Rerunnable notebook / guide | Ready | `notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb` |
| Mini-blog or video | Ready | `BLOG.md` |
| Real training evidence | Ready | `docs/final_assets/`, `logs/final/`, `TRAINING_RUN_LOG.md`, `SUBMISSION_EVIDENCE.md` |
| No huge video/checkpoint files in Space | Ready | Space upload excludes logs, evidence zip, caches, tokens, and `outputs/**/model/*` |

## 1. Environment Innovation - 40%

Agent BlackBox Arena is not a grid-world clone or a static dataset. It is an interactive repair environment where a failed agent trace becomes a stateful episode.

What makes it novel:

- **Trace-to-repair loop**: failure trace -> evidence -> root cause -> patch -> replay -> hidden regressions -> certificate.
- **Agent Failure Genome**: each synthetic family has a trace signature, root cause, required controls, forbidden behavior, and valid behavior that must be preserved.
- **Repair Patch DSL**: repairs are bounded policy patches with `require`, `forbid`, `preserve`, and `rationale`.
- **Hidden regressions**: the agent cannot pass by only fixing the visible trace.
- **Bounded certificate**: a certificate is gated on evidence, root cause, visible replay, hidden regressions, valid preservation, no overblocking, and no hardcoded incident references.
- **Anti-shortcut design**: block-everything repairs, incident-ID memorization, invalid JSON, hidden-test probing, and premature certificates are penalized.

The environment targets Theme #3.1 Professional Tasks / World Modeling and Theme #5 Wild Card. It asks the model to maintain state, update beliefs from trace outcomes, and orchestrate a multi-step repair workflow.

## 2. Storytelling & Presentation - 30%

The submission is designed so a judge can understand it quickly:

- `README.md` starts with public links, judge quick links, final metrics, and the live app.
- `BLOG.md` tells the story: problem, environment, why shortcuts fail, training, final result, and boundaries.
- The Space homepage gives an interactive live demo and a results overview.
- `FINAL_FORM_SUBMISSION_CHECKLIST.md` contains exact form URLs and final values.
- `TRAINING_RUN_LOG.md` now starts with a "Start Here For Judges" block pointing to the final H200 section.

The one-sentence story:

> Observability shows what happened; Agent BlackBox trains an agent to decide what should change and prove the repair survives regressions.

## 3. Showing Improvement In Rewards - 20%

The final result shows measurable improvement over the historical 0.5B challenge-curriculum SFT baseline.

| Model / eval | Overall | Certificate | Evidence | Invalid JSON |
|---|---:|---:|---:|---:|
| 0.5B SFT standard | 0.9492 | 0.9333 | 1.0000 | 0.0000 |
| 0.5B SFT shuffled_surface_blind | 0.6710 | 0.1833 | 0.1833 | 0.0000 |
| 0.5B SFT combined_blind_shuffle | 0.6753 | 0.2167 | 0.2167 | 0.0000 |
| Qwen3-4B SFT+GRPO standard | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| Qwen3-4B SFT+GRPO shuffled_surface_blind | 0.9557 | 0.8833 | 0.8833 | 0.0000 |
| Qwen3-4B SFT+GRPO combined_blind_shuffle | 0.9367 | 0.8333 | 0.8333 | 0.0000 |

Safety rates for the selected Qwen3-4B run:

- `overblocking_rate = 0.0000`
- `hardcoded_patch_rate = 0.0000`
- stoploss `PASS`

Plots and metrics:

- `docs/final_assets/plots/qwen3_4b_sft_loss.png`
- `docs/final_assets/plots/qwen3_4b_grpo_reward.png`
- `docs/final_assets/plots/qwen3_4b_eval_overall.png`
- `docs/final_assets/plots/qwen3_4b_certificate_success.png`
- `docs/final_assets/plots/qwen3_4b_evidence_correctness.png`
- `docs/final_assets/plots/qwen3_4b_safety_rates.png`
- `docs/final_assets/metrics/final_qwen3_4b_metrics.json`

## 4. Reward & Training Pipeline - 10%

The reward is deterministic and verifier-scored. There is no LLM judge.

Reward channels include:

- evidence correctness
- root-cause correctness
- patch schema and patch quality
- visible replay success
- hidden regression pass
- valid preservation
- certificate generation
- invalid JSON penalty
- overblocking penalty
- hardcoded patch rejection

Training pipeline evidence:

- SFT warmstart: `training/train_sft_warmstart.py`
- GRPO training: `training/train_json_grpo.py`
- quality gates: `training/quality_gate.py`
- dataset/eval generation: `training/make_dataset.py`, `training/evaluate_checkpoint.py`, `training/evaluate_model.py`
- final H200 run evidence: `logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt`
- run ledger: `TRAINING_RUN_LOG.md`

## Engineering Cleanliness

- Client/server separation is preserved through FastAPI endpoints.
- The public API uses `/metadata`, `/reset`, `/step`, and `/state`.
- Reserved OpenEnv names are not custom actions.
- `openenv.yaml` is present.
- `scripts/self_check.py`, `scripts/space_smoke.py`, `scripts/generalization_audit.py`, and `pytest` pass locally.
- The Space runs without GPU and without live external APIs.

## Claim Boundaries

The selected Qwen3-4B result is bounded to the reported synthetic MVP families, prompt variants, and eval seeds `1000-1019`. The submission does not claim global safety, production safety, SOTA, unlimited generalization, 1.5B success, or Qwen2.5-3B success.
