# Final Execution Log

Project: **Agent BlackBox Arena**  
Category: **Agent Reliability CI**  
Tagline: **Replay. Repair. Regress. Certify.**

This log records the final build, hardening, training, deployment, and evidence-packaging run. It is written so the project can be checked without guessing which result is final.

## 1. Final Status

Final technical status: **CONDITIONAL GO**, with `BLOG.md` ready and pending any separate video/slides link if required by the submission form.

The codebase, OpenEnv-style environment, deterministic verifier, training scripts, evidence package, notebook guide, and Hugging Face Space are ready. The selected trained result is **Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200** from real Hugging Face Jobs logs, job `69edcef7d70108f37acdfeb3`. The 0.5B challenge-curriculum SFT result is retained as historical fallback evidence. The 1.5B and Qwen2.5-3B attempts are not claimed.

## 2. Project Identity

Agent BlackBox Arena is not an observability dashboard. Observability shows what happened. Agent BlackBox trains agents to replay, repair, regress, and certify what should happen next.

Core loop:

```text
failed trace -> replay -> evidence -> root cause -> patch -> hidden regressions -> certificate
```

MVP failure families:

- `stale_retrieval`
- `missing_verification`
- `permission_scope`

The environment is CPU-runnable and exposes OpenEnv-style `reset`, `step`, and `state` behavior. Rewards are verifier-scored and deterministic; no LLM-as-judge is used for core reward.

## 3. What Was Built

Implemented environment capabilities:

- Public failed trace observation.
- Hidden state and hidden regressions.
- Multi-step action loop.
- Evidence-span selection.
- Root-cause submission.
- Repair patch DSL.
- Visible replay.
- Hidden regression checks.
- Valid behavior preservation.
- Anti-overblocking checks.
- Anti-hardcoding checks.
- Strict repair certificate gating.
- Baseline evaluation.
- TRL/SFT/GRPO training scaffold.
- HF Jobs training scripts.
- TensorBoard-compatible tracking artifacts.
- Submission evidence packaging.
- HF Space deployment.

Patch DSL:

```json
{
  "require": [],
  "forbid": [],
  "preserve": [],
  "rationale": ""
}
```

## 4. Local Verification

Latest local verification before final packaging:

```text
python scripts/self_check.py
python scripts/generalization_audit.py
python scripts/package_submission_evidence.py
python -m pytest
```

Observed final local state:

- `scripts/self_check.py`: PASS
- `scripts/generalization_audit.py`: PASS
- `python -m pytest`: `59 passed`
- `scripts/package_submission_evidence.py`: wrote `submission_evidence/` and `submission_evidence.zip`
- Evidence package manifest: `included=44`, `missing=14`, `skipped=0`

Note: local smoke outputs under `outputs/sft_smoke/` and `outputs/training_smoke/` may be dirty because smoke checks regenerate them. They are not final model evidence and were not used as headline metrics.

## 5. Important Commits

- `fb1f224 Harden challenge evidence curriculum`
  - Added the challenge-curriculum fix after evidence grounding failed under shuffled/blinded prompts.
- `25b8d4c Add TensorBoard tracking for training evidence`
  - Added CSV/JSON plus TensorBoard-compatible tracking under `outputs/tracking/`.
- `637a210 Add extracted TensorBoard tracking artifacts`
  - Added extracted final tracking artifacts and plots from the real 0.5B challenge-curriculum run.

## 6. HF Jobs Timeline

| Job ID | Hardware | Status | Outcome |
|---|---:|---|---|
| `69ed0befd2c8bd8662bce36c` | `cpu-basic` | COMPLETED | Early CPU smoke passed after dependency fixes. |
| `69ed0cebd2c8bd8662bce388` | `t4-small` | ERROR | Failed because `generation_batch_size (1)` was not divisible by `num_generations (2)`. |
| `69ed0f55d2c8bd8662bce3d6` | `t4-small` | COMPLETED | Corrected batch size, but invalid JSON collapse: reward stayed unusable. |
| `69ed12abd70108f37acdedc6` | `cpu-basic` | COMPLETED | CPU smoke after JSON prompt hardening passed. |
| `69ed130dd2c8bd8662bce45b` | `t4-small` | COMPLETED | 0.5B GRPO-only attempt failed quality stop-loss due invalid JSON. |
| `69ed1880d2c8bd8662bce4e5` | `cpu-basic` | COMPLETED | Fresh HF runtime smoke passed. |
| `69ed18e7d2c8bd8662bce4f2` | `t4-small` | COMPLETED | Tiny 0.5B SFT format warmstart succeeded on small held-out eval. |
| `69ed1a3ed2c8bd8662bce516` | `t4-small` | COMPLETED | 0.5B SFT plus GRPO validation succeeded on small held-out eval. |
| `69ed520cd2c8bd8662bcea54` | `t4-small` | CANCELED | Larger eval attempt canceled intentionally because it was too slow/quiet for the budget. |
| `69ed549bd70108f37acdf273` | `t4-small` | COMPLETED | Pre-hardening larger 0.5B eval passed standard/challenge, but challenge was later judged too easy. |
| `69ed986cd70108f37acdf8ba` | `t4-small` | COMPLETED | Post-hardening 0.5B run exposed challenge evidence-grounding failure. |
| `69eda5a4d70108f37acdfa48` | `t4-small` | COMPLETED | Challenge-curriculum 0.5B run succeeded and became historical fallback evidence. |
| `69edaafcd70108f37acdfadb` | `l4x1` | CANCELED | 1.5B stopped after SFT quality gate printed `STOP`; no 1.5B result claimed. |
| `69edc9b8d2c8bd8662bcf937` | `h200` | COMPLETED | Qwen2.5-3B completed but SFT gate stopped; no 3B result claimed. |
| `69edcb91d70108f37acdfe5a` | `h200` | COMPLETED | Qwen2.5-3B r2 completed but SFT gate stopped; no 3B result claimed. |
| `69edc9c3d2c8bd8662bcf93c` | `h200` | ERROR | Qwen3-4B intermediate errored during GRPO evaluation; not final. |
| `69edcb9ad70108f37acdfe5e` | `h200` | COMPLETED | Qwen3-4B fast r2 passed but was weaker than final. |
| `69edcef7d70108f37acdfeb3` | `h200` | COMPLETED | Final selected Qwen3-4B SFT+GRPO result. |

## 7. Failed And Canceled Runs Were Kept

The failed and canceled runs are part of the audit story:

- The first T4 run failed due a TRL batch-size/config issue.
- The next 0.5B GRPO-only attempt failed due invalid JSON collapse.
- A later post-hardening run exposed evidence-grounding failure under challenge prompts.
- The 1.5B attempt was canceled when quality gate signaled `STOP`.
- Qwen2.5-3B H200 attempts failed or were STOP-gated and are not claimed.
- Intermediate Qwen3-4B H200 attempts are recorded but only job `69edcef7d70108f37acdfeb3` is selected.

These runs are not hidden and are not used as positive claims. They drove the curriculum, prompt, and stop-loss improvements.

## 8. Challenge Failure Diagnosis

Post-hardening job `69ed986cd70108f37acdf8ba` completed and printed `POST_HARDENING_0_5B_COMPLETE`, but it was a **NO-GO** for 1.5B.

Key diagnosis:

- The model learned strict JSON.
- The model often selected the correct root cause.
- Challenge prompts destroyed evidence grounding.
- `evidence_correct_rate` became `0.0` under challenge variants.
- Strict certificate gating correctly blocked certificate success when evidence was wrong.

Post-hardening metrics that triggered the fix:

| Stage | Variant | Overall | Certificate | Evidence | Invalid JSON | Overblocking |
|---|---|---:|---:|---:|---:|---:|
| SFT 0.5B | standard | 0.8353 | 0.6500 | 1.0000 | 0.0000 | not headline |
| SFT 0.5B | shuffled_surface_blind | 0.2680 | 0.0000 | 0.0000 | 0.0333 | 0.1000 |
| SFT 0.5B | combined_blind_shuffle | 0.4050 | 0.0000 | 0.0000 | 0.0000 | 0.0333 |
| SFT+GRPO 0.5B | standard | 0.7727 | 0.5167 | 1.0000 | 0.0000 | not headline |
| SFT+GRPO 0.5B | shuffled_surface_blind | 0.2970 | 0.0000 | 0.0000 | 0.0333 | 0.1167 |
| SFT+GRPO 0.5B | combined_blind_shuffle | 0.3850 | 0.0000 | 0.0000 | 0.0000 | 0.0333 |

GRPO stop-loss for that run reported `STOP`, including nonzero overblocking and zero certificate success on held-out/challenge paths.

## 9. Fix Applied After Evidence-Grounding Failure

The fix did not loosen the verifier or certificate gate. It improved training curriculum and prompt grounding:

- Added challenge-aware SFT data.
- Mixed `standard`, `shuffled_surface_blind`, and `combined_blind_shuffle` variants.
- Added variant-specific public span aliases.
- Added public span metadata and clearer evidence-selection instructions.
- Required evidence IDs to come from visible span IDs in the current prompt.
- Kept hidden oracle fields out of prompts.
- Kept candidate order shuffled.
- Added diagnostic metrics:
  - `evidence_correct_rate`
  - `root_cause_correct_rate`
  - `patch_blocks_rate`
  - `certificate_gate_fail_rate`
- Added `scripts/diagnose_challenge_failures.py`.
- Added locked HF scripts for 0.5B, 1.5B, and 4B stages.

## 10. Final Selected Training Evidence

The selected trained evidence comes from HF job:

```text
69edcef7d70108f37acdfeb3
```

Status:

- Job status: COMPLETED
- Marker: `POST_FINAL_QWEN3_4B_H200_COMPLETE`
- Model: `Qwen/Qwen3-4B-Instruct-2507`
- Stage selected: SFT+GRPO final H200
- Hardware: `h200`
- Output root: `outputs/larger_models/qwen3_4b_2507_final_h200/`
- Log file: `logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt`

### Qwen3-4B Final Standard

```text
overall_score = 1.0000
certificate_success_rate = 1.0000
evidence_correct_rate = 1.0
hidden_regression_pass_rate = 1.0
valid_preservation_rate = 1.0
invalid_json_rate = 0.0
overblocking_rate = 0.0
hardcoded_patch_rate = 0.0
```

### Qwen3-4B Final Shuffled Surface Blind

```text
overall_score = 0.9557
certificate_success_rate = 0.8833
evidence_correct_rate = 0.8833
hidden_regression_pass_rate = 1.0
valid_preservation_rate = 1.0
invalid_json_rate = 0.0
overblocking_rate = 0.0
hardcoded_patch_rate = 0.0
```

### Qwen3-4B Final Combined Blind Shuffle

```text
overall_score = 0.9367
certificate_success_rate = 0.8333
evidence_correct_rate = 0.8333
hidden_regression_pass_rate = 1.0
valid_preservation_rate = 1.0
invalid_json_rate = 0.0
overblocking_rate = 0.0
hardcoded_patch_rate = 0.0
```

Interpretation:

- Qwen3-4B final H200 SFT+GRPO is the selected final model.
- It beats the 0.5B historical fallback on challenge evidence and certificate rates.
- Invalid JSON, overblocking, and hardcoded patch rates are all `0.0`.
- The claim is limited to synthetic MVP families, prompt variants, and eval seeds `1000-1019`.

## 11. 1.5B Attempt And Stop-Loss

HF job:

```text
69edaafcd70108f37acdfadb
```

Status:

- Hardware: `l4x1`
- Status: CANCELED
- Reason: 1.5B SFT printed `quality_status=STOP`
- Action: canceled before GRPO to avoid wasting credit and creating misleading reward curves

Decision:

- **NO-GO** for 1.5B headline result.
- No 1.5B metric is claimed as a final result.
- The later Qwen3-4B H200 final run superseded the 0.5B fallback with real verifier-scored evidence.

## 12. Real Plots And Tracking Artifacts

Real plots generated from extracted HF logs:

- `outputs/final_plots/hf_05b_challenge_curriculum_training_loss_curve.png`
- `outputs/final_plots/hf_05b_challenge_curriculum_verifier_reward_comparison.png`
- `outputs/final_plots/hf_15b_challenge_curriculum_canceled_training_loss_curve.png`

Primary final H200 plot paths for claims:

- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_model_eval/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_training/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_model_eval/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_training/`

TensorBoard-compatible tracking artifacts:

- `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/sft_warmstart_sft_qwen3_4b_2507_final_h200_challenge_curriculum/`
- `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/grpo_grpo_qwen3_4b_2507_final_h200_challenge_curriculum/`

CSV/JSON logs remain the underlying record.

## 13. Hugging Face Space

Space URL:

```text
https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena
```

Verified behavior:

- Space runtime: RUNNING
- `/` metadata endpoint loads
- `/reset` works
- `/step` works
- `/state` works
- Local `scripts/space_smoke.py` is covered through `scripts/self_check.py`

Space configuration:

- Docker Space
- CPU-runnable
- no model checkpoint required
- no secrets required
- environment server only, not GPU training

## 14. Evidence Package

Evidence package command:

```bash
python scripts/package_submission_evidence.py
```

Latest observed output:

```text
package_submission_evidence: wrote submission_evidence/
package_submission_evidence: wrote submission_evidence.zip
package_submission_evidence: included=97 missing=18 skipped=0
```

Evidence package:

- `submission_evidence/`
- `submission_evidence.zip`
- `submission_evidence/MANIFEST.json`

The packager excludes:

- `.env`
- tokens
- cache folders
- checkpoint/model folders
- large model weights

## 15. Notebook Status

Notebook path:

```text
notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb
```

Notebook role:

- Lightweight rerun guide.
- Shows setup, smoke checks, tiny training flow, real summaries, and real plots.
- Main training was run via HF Jobs CLI and repo scripts, not by faking notebook outputs.

## 16. Allowed Final Claims

Safe claims:

- Agent BlackBox Arena is an OpenEnv-style repair environment for agent reliability CI.
- The environment trains replay, evidence selection, root-cause diagnosis, patching, hidden regression checks, and certificate generation.
- Base 0.5B failed strict JSON on the reported standard evaluation.
- Challenge-curriculum SFT fixed JSON validity on the reported evaluation.
- Challenge-curriculum SFT recovered nonzero challenge evidence/certificate success after a failure case exposed by stricter evaluation.
- Qwen3-4B final H200 SFT+GRPO is the selected final trained model over eval seeds `1000-1019`.
- Hidden regression and valid-preservation metrics are deterministic verifier metrics.
- The repair certificate is bounded to this symbolic benchmark.

## 17. Not Claimed

The submission does not claim:

- SOTA.
- Production safety.
- Global safety proof.
- Unlimited generalization.
- GRPO learned the task from scratch.
- 1.5B success.
- Qwen2.5-3B success.
- Failed/error H200 runs as successful.
- Final trained improvement from the canceled 1.5B run.
- Any metric not present in the real logs.

## 18. Remaining Submission Tasks

Still required before final administrative submission:

1. Add a video/slides URL if the submission form requires one beyond `BLOG.md`.
2. Add that link to `README.md`.
3. Regenerate `submission_evidence.zip` after adding any external link.
4. Team leader submits the final repository, HF Space, evidence package, and blog/video/slides link.

## 19. Final Decision

Final submission decision:

```text
CONDITIONAL GO
```

The repo, environment, training evidence, Space, notebook guide, `BLOG.md`, and audit trail are ready. The only remaining administrative blocker is a separate external video/slides URL if required by the submission process.

