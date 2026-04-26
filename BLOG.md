# Agent BlackBox Arena: Replay. Repair. Regress. Certify.

Agent BlackBox Arena is my OpenEnv-style repair environment for agent reliability CI. It starts from failed synthetic AI-agent traces and asks a model to do the work a reliability engineer would expect: inspect the trace, find evidence, diagnose the root cause, propose a bounded repair, run regressions, and generate a gated repair certificate.

## Problem

Observability shows what happened. It does not train agents to repair behavior after the failure is found.

Agent BlackBox Arena turns failed AI-agent traces into verifier-scored repair episodes. The point is not another dashboard. The point is a training environment where a model must move from trace evidence to a repair that survives hidden regression checks.

## Environment

Each episode follows the same repair loop:

```text
failed trace -> evidence -> root cause -> repair patch -> visible replay -> hidden regressions -> bounded certificate
```

The model sees only public episode state: trace spans, candidate root causes, allowed patch clauses, allowed forbidden effects, and preservation clauses. Hidden oracle fields and hidden regression variants are not exposed. The environment is stepped through `/reset`, `/step`, `/state`, and `/metadata`, so it behaves like a small OpenEnv-style API rather than a static benchmark file.

## Failure Genome

The MVP covers three compact failure families:

- `stale_retrieval`: the agent acts on expired context.
- `missing_verification`: the agent takes an irreversible action without checking the needed condition.
- `permission_scope`: the agent calls a tool outside its allowed role or task scope.

Each family connects a trace signature, root cause, required control, forbidden behavior, and valid behavior that must still be preserved.

## Actions

The action set makes the repair process explicit:

```text
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

An agent cannot jump straight to a certificate. It has to build the repair chain first.

## Reward / Verifier

The reward is deterministic and verifier-scored. There is no LLM judge.

The verifier checks evidence correctness, root-cause correctness, patch quality, hidden regression pass rate, valid behavior preservation, overblocking, and hardcoded-patch behavior. Invalid JSON is rejected. Hardcoded incident IDs and brittle patches are rejected. A certificate only counts after the visible replay, hidden regressions, and preservation checks pass.

## Training

The training story is intentionally honest.

The base model first failed the strict JSON/action format. A 0.5B iteration fixed format behavior but exposed a challenge-evidence weakness when prompts were shuffled and blinded. A challenge curriculum improved grounding. Larger-model stretch runs then tested whether the repair loop was learnable at a more competitive scale.

The selected final run is:

- Model: `Qwen/Qwen3-4B-Instruct-2507`
- Checkpoint/result: `SFT+GRPO final H200`
- HF Job: `69edcef7d70108f37acdfeb3`
- Output root: `outputs/larger_models/qwen3_4b_2507_final_h200/`
- Eval seeds: `1000-1019`
- Stoploss: `PASS`

Qwen2.5-3B and earlier 1.5B attempts were not claimed because stop-loss or quality gates rejected them. Failed and intermediate runs remain in the evidence trail, but they are not promoted into final results.

## Final Results

| variant | overall | cert | evidence | hidden | valid | invalid_json |
|---|---:|---:|---:|---:|---:|---:|
| standard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| shuffled_surface_blind | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 |
| combined_blind_shuffle | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 |

Safety rates:

- `overblocking_rate = 0.0000`
- `hardcoded_patch_rate = 0.0000`
- `stoploss = PASS`

## Evidence Links

- HF Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena
- Training notebook: [notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb](notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb)
- README: [README.md](README.md)
- Submission evidence: [SUBMISSION_EVIDENCE.md](SUBMISSION_EVIDENCE.md)
- Final audit: [FINAL_SUBMISSION_AUDIT.md](FINAL_SUBMISSION_AUDIT.md)
- Recent H200 report: [FINAL_RECENT_H200_RUNS_REPORT.md](FINAL_RECENT_H200_RUNS_REPORT.md)
- Final assets: [docs/final_assets/](docs/final_assets/)
- Final H200 log: [logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt](logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt)

## Boundaries

The Agent Repair Certificate is bounded to synthetic incident families, prompt variants, hidden regressions, and eval seeds. It is not a global safety proof, production certification, SOTA claim, or claim of unlimited generalization.
