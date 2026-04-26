# Agent BlackBox Arena: Replay. Repair. Regress. Certify.

I built Agent BlackBox Arena for the part of agent reliability that current tooling still leaves open: after an agent fails, can another agent learn to repair the behavior, prove the repair against hidden regressions, and preserve valid behavior?

This is the benchmark I wanted to submit in a field where strong RL and ML researchers will inspect every shortcut. So I made the environment deterministic, the reward auditable, the failure modes concrete, and the final claim narrow enough to survive review.

## The Problem

Observability tools are good at answering: what happened?

Agent BlackBox Arena asks the next question: what should change?

A failed trace is not the end of the story. It should become a repair episode. The model has to inspect the evidence, identify the root cause, propose a bounded patch, run visible replay, pass hidden regressions, preserve valid behavior, and only then generate a certificate.

```text
failed trace -> evidence -> root cause -> repair patch -> visible replay -> hidden regressions -> bounded certificate
```

That loop is the core idea. It turns post-failure debugging into an OpenEnv-style training environment.

## Why This Is Hard

A cheap repair can look good on the visible trace and still be wrong.

For example, an agent can block every risky action. That stops the failure, but it also destroys valid flows. Another model can memorize incident IDs. That passes one example, but fails hidden variants. Another can write a plausible explanation without selecting the right evidence.

The benchmark is designed so those shortcuts fail.

Agent BlackBox Arena rewards a repair only when the full chain holds: evidence, root cause, patch, visible replay, hidden regressions, preservation, and certificate gating.

## Failure Genome

The MVP uses three compact reliability families:

- `stale_retrieval`: the agent acts on expired retrieved context.
- `missing_verification`: the agent takes an irreversible action without verifying the required condition.
- `permission_scope`: the agent calls a tool outside its allowed role or task scope.

Each family has a trace signature, a root cause, required controls, forbidden behavior, and a valid behavior that must still pass. This makes the task small enough to audit but structured enough to train.

## Environment Actions

The agent does not output a final answer in one shot. It has to move through the repair process:

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

The live Space exposes the same environment through `/metadata`, `/reset`, `/step`, and `/state`.

## Deterministic Reward, No LLM Judge

The reward is verifier-scored. There is no LLM judge and no subjective grading layer.

The verifier checks:

- evidence correctness
- root-cause correctness
- patch schema and patch quality
- hidden regression pass rate
- valid behavior preservation
- overblocking
- hardcoded patch rejection
- certificate gate completion
- strict JSON/action validity

This matters because a benchmark for repair should make weak fixes fail in a reproducible way.

## Training Story

The first lesson was format. The base model failed strict JSON/action output. A 0.5B SFT warmstart fixed the format bottleneck, but the harder challenge prompts exposed an evidence-grounding weakness.

The next step was a challenge curriculum. The 0.5B challenge-curriculum SFT run became a real historical baseline:

| model / eval | overall | cert | evidence | invalid_json |
|---|---:|---:|---:|---:|
| 0.5B SFT standard | 0.9492 | 0.9333 | 1.0000 | 0.0000 |
| 0.5B SFT shuffled_surface_blind | 0.6710 | 0.1833 | 0.1833 | 0.0000 |
| 0.5B SFT combined_blind_shuffle | 0.6753 | 0.2167 | 0.2167 | 0.0000 |

That was useful, but not enough for a winning submission. The challenge variants were the real test: could the model keep evidence grounding when surface wording, candidate ordering, and family labels changed?

The final selected run used `Qwen/Qwen3-4B-Instruct-2507` with SFT+GRPO on H200:

- HF Job: `69edcef7d70108f37acdfeb3`
- Output root: `outputs/larger_models/qwen3_4b_2507_final_h200/`
- Eval seeds: `1000-1019`
- Stoploss: `PASS`

## Final Result

| variant | overall | cert | evidence | hidden | valid | invalid_json |
|---|---:|---:|---:|---:|---:|---:|
| standard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| shuffled_surface_blind | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 |
| combined_blind_shuffle | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 |

Safety rates:

- `overblocking_rate = 0.0000`
- `hardcoded_patch_rate = 0.0000`
- `stoploss = PASS`

The important improvement is on the challenge variants. The historical 0.5B baseline scored `0.6710` shuffled and `0.6753` combined. The final Qwen3-4B run reached `0.9557` shuffled and `0.9367` combined while keeping invalid JSON, overblocking, and hardcoded patch rates at zero.

## What I Would Want Judges To Notice

The project is not just a model run. The environment is the main contribution.

It gives agents a concrete repair loop, hidden regressions, deterministic reward, bounded certificates, and anti-shortcut pressure. The training result matters because it shows the environment can produce a learnable signal, but the benchmark itself is what makes the work reusable.

I also kept the failed and intermediate runs in the logs. That is intentional. In a serious RL/ML setting, stop-loss discipline is part of the result: weak runs should not become marketing claims.

## Evidence

- HF Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena
- Training notebook: [notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb](notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb)
- README: [README.md](README.md)
- Submission evidence: [SUBMISSION_EVIDENCE.md](SUBMISSION_EVIDENCE.md)
- Final audit: [FINAL_SUBMISSION_AUDIT.md](FINAL_SUBMISSION_AUDIT.md)
- Recent H200 report: [FINAL_RECENT_H200_RUNS_REPORT.md](FINAL_RECENT_H200_RUNS_REPORT.md)
- Final assets: [docs/final_assets/](docs/final_assets/)
- Final H200 log: [logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt](logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt)

## Boundaries

The Agent Repair Certificate is bounded to these synthetic incident families, prompt variants, hidden regressions, and eval seeds. This is not a global safety proof, production certification, SOTA claim, or claim of unlimited generalization.
