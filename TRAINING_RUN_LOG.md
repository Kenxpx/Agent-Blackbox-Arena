# Training Run Log

Current decision: **NO-GO for Run 2 until larger 0.5B held-out and challenge evaluation are inspected**.

This log records real Hugging Face Jobs output. No fake metrics, fake plots, or trained-improvement claims are made.

## Phase 0 - Job Diagnosis

Relevant jobs inspected:

| Job ID | Flavor | Status | Diagnosis |
|---|---|---|---|
| `69ed0befd2c8bd8662bce36c` | `cpu-basic` | `COMPLETED` | CPU smoke passed after dependency fixes. |
| `69ed0cebd2c8bd8662bce388` | `t4-small` | `ERROR` | Failed with `generation_batch_size (1) must be divisible by num_generations (2)`. |
| `69ed0f55d2c8bd8662bce3d6` | `t4-small` | `COMPLETED` | Corrected batch size ran, but invalid JSON was total failure: `invalid_json_rate=1.0`, reward `0.0`. |
| `69ed12abd70108f37acdedc6` | `cpu-basic` | `COMPLETED` | CPU smoke passed after JSON prompt hardening. |
| `69ed130dd2c8bd8662bce45b` | `t4-small` | `COMPLETED` | Run 1 after JSON hardening. Completed, but failed quality stop-loss. |

## Phase 1 - JSON Format Hardening

Applied before rerunning GPU:

- Shortened the training prompt.
- Moved strict JSON requirements to the top.
- Added explicit: return only JSON, no markdown, no prose, no commentary, English only, start with `{` and end with `}`.
- Added a minimal example JSON object.
- Added tolerant first-object JSON extraction for mildly wrapped completions.
- Kept strict field validation.
- Kept deterministic verifier reward.
- Kept sampled generation logging.
- Kept invalid JSON logging.
- Added smoke coverage for wrapped valid JSON.
- Reduced default max completion length from `256` to `160`.
- Fixed run commands to use `--per-device-train-batch-size 2` with `--num-generations 2`.

Local checks passed:

```text
python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke
python scripts/self_check.py
python -m pytest
```

HF CPU smoke after hardening:

```text
Job ID: 69ed12abd70108f37acdedc6
Status: COMPLETED
pytest: 34 passed
smoke invalid_json_rate: 0.2000
self_check: passed
space smoke: passed
```

## Run 1 - 0.5B Pipeline Validation

Job ID: `69ed130dd2c8bd8662bce45b`

Hardware: `t4-small`

Model: `Qwen/Qwen2.5-0.5B-Instruct`

Command:

```bash
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
  --save-steps 10
```

Final status: `COMPLETED`

Training runtime reported by trainer:

```json
{
  "train_runtime": 82.1219,
  "train_samples_per_second": 0.244,
  "train_steps_per_second": 0.122,
  "train_loss": 0.0
}
```

## Run 1 Metrics Summary

Verifier summary:

```json
{
  "episodes": 20,
  "overall_score": 0.0,
  "certificate_success_rate": 0.0,
  "hidden_regression_pass_rate": 0.0,
  "valid_preservation_rate": 0.0,
  "invalid_json_rate": 0.9,
  "overblocking_rate": 0.05,
  "hardcoded_patch_rate": 0.0
}
```

Held-out generation summary:

```json
{
  "episodes": 3,
  "overall_score": 0.0,
  "certificate_success_rate": 0.0,
  "hidden_regression_pass_rate": 0.0,
  "valid_preservation_rate": 0.0,
  "invalid_json_rate": 1.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

## Sample Generation Diagnosis

The hardening helped slightly: the model sometimes emitted JSON-like objects and the tolerant parser extracted a few first JSON objects. However, the run is still not valid evidence of learning.

Observed issues:

- Most completions are still prose, markdown, or mixed text.
- Some completions start with `{ }` and then continue with prose.
- Some completions produce JSON missing required keys.
- Some completions use invalid clause IDs such as `require_sufficient_permissions`, `context_not_fresh`, or placeholder labels.
- Some completions include non-English text.
- Some completions are truncated before closing valid JSON.
- Reward remained `0.0`.
- Certificate success remained `0.0`.
- Held-out invalid JSON remained `1.0`.

This is a real negative result. It should not be presented as trained improvement.

## Run 2 Decision

Run 2 is **not approved**.

Reason:

- `invalid_json_rate=0.90` on training samples.
- `heldout invalid_json_rate=1.00`.
- `overall_score=0.0`.
- `certificate_success_rate=0.0`.
- `hidden_regression_pass_rate=0.0`.
- `valid_preservation_rate=0.0`.
- Mean reward did not beat the `random_patch` baseline score `0.144`.

## Next Recommendation

Do not run 1.5B or 4B yet.

Recommended next step is a CPU-only training-format fix:

1. Add a real SFT warmstart path, or use a supervised formatting warmup before GRPO.
2. Alternatively, change GRPO prompts to a chat-template format that Qwen Instruct follows more reliably.
3. Add a pre-GRPO zero-shot evaluation command to measure valid JSON rate before paid training.
4. Only rerun 0.5B after zero-shot/sample outputs contain valid JSON at a usable rate.

## Post-Run Research And Patch

Official TRL documentation says `GRPOTrainer` datasets must include a `prompt` column and can use either plain text or conversational message format. The same docs show custom reward functions and format rewards can be used with GRPO. That explains the failure pattern:

- The Qwen Instruct model was being trained from raw plain-text prompts instead of structured chat messages.
- The verifier reward stayed at zero because most generations were invalid JSON, so GRPO had no useful relative ranking signal.
- Trainer loss stayed at `0.0`, consistent with all sampled rewards being equal or unusable.
- Completion samples were often prose, markdown, non-English text, malformed JSON, or truncated JSON.

Patch applied after this diagnosis:

- Convert training prompts to conversational messages so TRL can apply the model chat template.
- Render held-out generation prompts with the same chat template.
- Add a small training-only JSON-format shaping reward to escape the all-invalid cold start.
- Keep the deterministic verifier and benchmark metrics unchanged.
- Keep invalid JSON, certificate success, hidden regression, valid preservation, overblocking, and hardcoding logged separately.

Deeper patch after reviewing the first fix:

- Remove incident IDs from model prompts to reduce hardcoded-patch behavior.
- Replace global patch-label lists with compact family-specific candidate labels and semantic glosses.
- Remove placeholder example labels that small models may copy as invalid clause IDs.
- Add real guarded TRL SFT warmstart support using conversational prompt-completion records.
- Keep SFT framed as format warmup only; final claims still require verifier-scored GRPO or held-out verifier metrics.

Next GPU action should be a tiny 0.5B SFT format warmstart or a patched 0.5B GRPO rerun only. Run 2 is still blocked until the patched 0.5B path produces valid JSON, nonzero verifier reward, and held-out metrics.

## README Claim Decision

GO for README claim:

- "HF T4 0.5B Run 1 completed and exposed a formatting bottleneck."
- "Real logs show current GRPO outputs are not yet valid repair plans."
- "No trained improvement is claimed."

NO-GO for README claim:

- Any trained-model improvement.
- Any baseline-vs-trained improvement.
- Any certificate improvement.
- Any robust generalization improvement.
- Any 1.5B or 4B result.

## Patched 0.5B Rerun

Current decision: **0.5B rerun succeeded; Run 2 is unblocked but not started**.

Relevant new jobs:

| Job ID | Flavor | Status | Diagnosis |
|---|---|---|---|
| `69ed1880d2c8bd8662bce4e5` | `cpu-basic` | `COMPLETED` | Fresh HF runtime passed GRPO smoke, SFT smoke, self_check, Space smoke, and `36 passed`. |
| `69ed18e7d2c8bd8662bce4f2` | `t4-small` | `COMPLETED` | Tiny 0.5B SFT format warmstart succeeded; held-out verifier metrics were perfect on 9 eval episodes. |
| `69ed1a3ed2c8bd8662bce516` | `t4-small` | `COMPLETED` | Combined tiny SFT warmstart followed by 0.5B GRPO validation succeeded. |

### CPU Smoke

Fresh HF runtime command passed:

```text
python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke
python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke
python scripts/self_check.py
python -m pytest
```

Result:

```text
pytest: 36 passed
GRPO smoke invalid_json_rate: 0.2000
self_check: passed
space_smoke: passed
```

### 0.5B SFT Format Warmstart

Model: `Qwen/Qwen2.5-0.5B-Instruct`

Hardware: `t4-small`

Train records: `18`

Eval records: `9`

Max steps: `30`

Trainer metrics:

```json
{
  "train_loss": 0.19936987646312143,
  "train_runtime": 34.4061,
  "train_samples_per_second": 0.872,
  "train_steps_per_second": 0.872
}
```

Held-out verifier summary:

```json
{
  "episodes": 9,
  "overall_score": 1.0,
  "certificate_success_rate": 1.0,
  "hidden_regression_pass_rate": 1.0,
  "valid_preservation_rate": 1.0,
  "invalid_json_rate": 0.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

Diagnosis:

- The SFT warmstart fixed the invalid JSON failure.
- The model emitted strict JSON on held-out eval seeds.
- The outputs used correct family-specific controls.
- No hardcoded incident IDs appeared in the reported held-out completions.
- This is valid formatting/training evidence, but SFT alone is not the final RL claim.

### 0.5B GRPO After SFT

Model: `outputs/sft_qwen25_05b_json/model`

Hardware: `t4-small`

Max steps: `10`

Train seeds: `0-2`

Eval seed: `1000`

Samples scored: `20`

Verifier summary:

```json
{
  "episodes": 20,
  "overall_score": 1.0,
  "certificate_success_rate": 1.0,
  "hidden_regression_pass_rate": 1.0,
  "valid_preservation_rate": 1.0,
  "invalid_json_rate": 0.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

Held-out verifier summary:

```json
{
  "episodes": 3,
  "overall_score": 1.0,
  "certificate_success_rate": 1.0,
  "hidden_regression_pass_rate": 1.0,
  "valid_preservation_rate": 1.0,
  "invalid_json_rate": 0.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

Trainer metrics:

```json
{
  "train_loss": 0.0,
  "train_runtime": 50.4753,
  "train_samples_per_second": 0.396,
  "train_steps_per_second": 0.198
}
```

Important caveat:

- GRPO reward was already saturated from the SFT checkpoint: `reward=1.2`, `reward_std=0`, and `frac_reward_zero_std=1`.
- This means the GRPO stage validates real model completions, deterministic verifier scoring, metric writing, sampled generation logging, and held-out evaluation.
- It does **not** prove additional GRPO learning beyond the SFT warmstart, because the warmstarted model was already producing verifier-perfect completions.

### Updated README Claim Decision

GO for README claim:

- "The first unassisted 0.5B GRPO attempt failed due to invalid JSON collapse."
- "A guarded 0.5B SFT format warmstart fixed the JSON bottleneck."
- "A verifier-scored 0.5B GRPO validation run produced strict JSON repair plans with `overall_score=1.0`, `certificate_success_rate=1.0`, `hidden_regression_pass_rate=1.0`, and `invalid_json_rate=0.0` on the reported held-out eval."
- "GRPO did not add measurable improvement after SFT because reward was saturated."

NO-GO for README claim:

- Do not claim GRPO alone solved the task from the base model.
- Do not claim 1.5B or 4B results.
- Do not claim broad generalization beyond the reported hidden-regression/eval seeds.
- Do not hide the earlier failed 0.5B attempt.

## Generalization And Leakage Audit Gate

After the successful 0.5B SFT+GRPO validation, the next risk is not raw pipeline failure. The next risk is overclaiming from a tiny held-out set or from prompts that are too easy.

Added safeguards before Run 2:

- `scripts/generalization_audit.py`
- `training/evaluate_checkpoint.py`
- `scripts/plot_model_eval.py`
- challenge prompt variants in `training/make_dataset.py`
- tests that challenge prompts do not leak hidden answers or incident IDs

The new challenge variant `shuffled_surface_blind`:

- shuffles visible trace span order
- rewrites surface wording
- replaces the family name with `agent_reliability_failure`
- keeps the same root-cause candidates and allowed patch labels
- keeps hidden variants and answer keys out of the prompt

Run 2 remains blocked until base 0.5B, SFT warmstart, and SFT+GRPO checkpoints are compared on a larger held-out seed range such as `1000-1049`, plus at least one challenge variant.

Formal local audit result:

- Leakage audit: PASS.
- Standard and challenge prompt records checked: 900.
- SFT train seeds `0-5` and GRPO train seeds `0-2` do not overlap larger eval seeds `1000-1049`.
- Target JSON does not appear verbatim in eval prompts.
- Hidden oracle fields do not appear in prompts.
- Incident IDs are not present in prompts and are not usable for hardcoding.
- Local trained checkpoints are not present at `outputs/sft_qwen25_05b_json/model` or `outputs/grpo_tiny_hf/model`, so larger real model evaluation must run in an HF job or another runtime where the checkpoints are recreated or available.

First larger-eval HF attempt:

- Job ID: `69ed520cd2c8bd8662bcea54`
- Flavor: `t4-small`
- Status: canceled intentionally.
- Reason: the 150-episode base eval over seeds `1000-1049` was not cheap enough and produced no summary after setup plus a long quiet generation window.
- Follow-up fix: `training/evaluate_checkpoint.py` now supports batched generation and progress logging.
- Next run should use the minimum allowed eval range `1000-1019` before any 1.5B spend.

## Controlled 0.5B Larger Eval Job

Job ID: `69ed549bd70108f37acdf273`

Flavor: `t4-small`

Status: `COMPLETED`

Commit used in job: `f86f38f`

Purpose:

- recreate the 0.5B SFT checkpoint inside the same job
- evaluate SFT on held-out seeds `1000-1019`
- run 0.5B GRPO validation from the SFT checkpoint
- evaluate SFT+GRPO on held-out seeds `1000-1019`
- evaluate SFT+GRPO on `shuffled_surface_blind` challenge prompts
- create plots only from real model-eval summaries

Base 0.5B zero-shot summary:

```json
{
  "episodes": 60,
  "overall_score": 0.0,
  "certificate_success_rate": 0.0,
  "hidden_regression_pass_rate": 0.0,
  "valid_preservation_rate": 0.0,
  "invalid_json_rate": 1.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

SFT larger held-out summary:

```json
{
  "episodes": 60,
  "overall_score": 1.0,
  "certificate_success_rate": 1.0,
  "hidden_regression_pass_rate": 1.0,
  "valid_preservation_rate": 1.0,
  "invalid_json_rate": 0.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

SFT+GRPO larger held-out summary:

```json
{
  "episodes": 60,
  "overall_score": 1.0,
  "certificate_success_rate": 1.0,
  "hidden_regression_pass_rate": 1.0,
  "valid_preservation_rate": 1.0,
  "invalid_json_rate": 0.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

SFT+GRPO challenge summary:

```json
{
  "episodes": 60,
  "prompt_variant": "shuffled_surface_blind",
  "overall_score": 0.78,
  "certificate_success_rate": 1.0,
  "hidden_regression_pass_rate": 1.0,
  "valid_preservation_rate": 1.0,
  "invalid_json_rate": 0.0,
  "overblocking_rate": 0.0,
  "hardcoded_patch_rate": 0.0
}
```

Plots created inside the HF job:

- `outputs/model_eval/baseline_vs_trained_score.png`
- `outputs/model_eval/certificate_success_rate.png`
- `outputs/model_eval/hidden_regression_pass_rate.png`
- `outputs/model_eval/invalid_json_rate.png`
- `outputs/model_eval/valid_preservation_rate.png`
- `outputs/model_eval/challenge/baseline_vs_trained_score.png`
- `outputs/model_eval/challenge/certificate_success_rate.png`
- `outputs/model_eval/challenge/hidden_regression_pass_rate.png`
- `outputs/model_eval/challenge/invalid_json_rate.png`
- `outputs/model_eval/challenge/valid_preservation_rate.png`

Interpretation:

- The base 0.5B model fails the task by emitting invalid JSON.
- The small SFT warmstart fixes strict repair-plan generation on the reported held-out seeds.
- The GRPO validation remains saturated after SFT: verifier reward is already perfect, with `reward_std=0` and `frac_reward_zero_std=1`.
- The challenge eval does not collapse: certificate success, hidden regression pass, valid preservation, invalid JSON, overblocking, and hardcoding are all healthy.
- The challenge eval overall score is `0.78`, so it reveals a useful harder surface-generalization gap even though the final certificate path succeeds.

Run 2 decision after this job:

- **GO for a cautious 1.5B run only if the next objective is stronger challenge/generalization performance.**
- **NO-GO for claiming GRPO learned from scratch.**
- **GO for claiming 0.5B SFT fixed the invalid JSON bottleneck on reported held-out seeds.**
- **GO for claiming the SFT+GRPO checkpoint passed reported hidden regression/certificate metrics, including the challenge variant, with bounded caveats.**

Safe next evidence claim, if the larger eval passes:

- "Base 0.5B collapsed into invalid JSON."
- "SFT warmstart fixed strict JSON repair-plan generation."
- "Verifier-scored held-out eval passed on the reported standard and challenge seeds."

Unsafe claim even if the larger eval passes:

- "GRPO learned the task from scratch."
- "The benchmark proves production safety."
- "The result generalizes beyond reported seeds and challenge variants."

## Rank-1 Hardening Pass Before 1.5B

Status: `COMPLETED LOCALLY`

Purpose:

- remove candidate-order shortcuts before scaling
- make certificate success stricter
- add richer diagnostics for model-eval claims
- keep the environment identity and reward weights unchanged

Changes:

- Root-cause, require, forbid, and preserve candidates are deterministically shuffled by family, seed, and prompt variant.
- `generate_repair_certificate` now requires correct evidence spans in addition to correct root cause, visible replay, hidden regressions, and valid preservation.
- Model-eval metrics now include:
  - `evidence_correct_rate`
  - `root_cause_correct_rate`
  - `patch_blocks_rate`
  - `certificate_gate_fail_rate`
- `scripts/generalization_audit.py` now audits candidate answer positions across challenge seeds.
- `scripts/plot_model_eval.py` can plot the new diagnostic metrics when fresh model-eval summaries contain them.

Local verification:

- `python training/make_dataset.py --smoke --output-dir outputs/training_smoke`: passed
- `python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke`: passed
- `python training/evaluate_model.py --smoke --output-dir outputs/eval_smoke`: passed
- `python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke`: passed
- `python scripts/generalization_audit.py`: `leakage_status=PASS`
- `python scripts/self_check.py`: passed
- `python -m pytest`: `47 passed`

Decision after hardening:

- The previous 0.5B same-job result remains valid historical evidence for the pre-hardening pipeline.
- Final claims should use a fresh post-hardening 0.5B same-job evaluation.
- 1.5B remains approved only after the post-hardening 0.5B evaluation does not collapse on challenge prompts.

## Rank-1 Anti-Leakage Challenge Patch

Status: `COMPLETED LOCALLY`

Purpose:

- add a harder challenge surface before any 1.5B spend
- audit candidate answer positions across train, standard eval, and challenge eval
- make the certificate gate match the full repair chain
- avoid presenting saturated GRPO as learning

Additional changes:

- Added `combined_blind_shuffle`, which combines shuffled spans, blinded family label, rewritten surface wording, shuffled candidates, and renamed service/requester/capability entities.
- Candidate answer-position audit now reports distributions for:
  - `sft_train_standard`
  - `standard_eval`
  - `shuffled_surface_blind_eval`
  - `combined_blind_shuffle_eval`
- Certificate generation now also requires replay completion and explicit no-overblocking/no-hardcoding hidden regression flags.
- Tests increased to `53 passed`.

Local verification:

- `python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke`: passed
- `python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke`: passed
- `python training/evaluate_model.py --smoke --output-dir outputs/eval_smoke`: passed
- `python scripts/self_check.py`: passed
- `python -m pytest`: `53 passed`

Decision:

- **GO** for one controlled post-hardening 0.5B rerun.
- **NO-GO** for 1.5B until the post-hardening 0.5B standard, `shuffled_surface_blind`, and `combined_blind_shuffle` summaries are inspected.

## Post-Hardening 0.5B Challenge Result

Job ID: `69ed986cd70108f37acdf8ba`

Status: `COMPLETED`

Marker: `POST_HARDENING_0_5B_COMPLETE`

Decision: **NO-GO for 1.5B, NO-GO for 4B, NO-GO for final trained-model improvement claims.**

Key result:

- Base 0.5B standard emitted invalid JSON: `overall_score=0.0`, `invalid_json_rate=1.0`.
- SFT 0.5B standard became useful: `overall_score=0.8353`, `certificate_success_rate=0.65`, `evidence_correct_rate=1.0`, `invalid_json_rate=0.0`.
- SFT challenge prompts failed evidence grounding:
  - `shuffled_surface_blind`: `overall_score=0.268`, `certificate_success_rate=0.0`, `evidence_correct_rate=0.0`, `overblocking_rate=0.1`.
  - `combined_blind_shuffle`: `overall_score=0.405`, `certificate_success_rate=0.0`, `evidence_correct_rate=0.0`, `overblocking_rate=0.0333`.
- SFT+GRPO standard did not improve over SFT: `overall_score=0.7727`, `certificate_success_rate=0.5167`.
- SFT+GRPO challenge prompts still failed evidence grounding:
  - `shuffled_surface_blind`: `overall_score=0.297`, `certificate_success_rate=0.0`, `evidence_correct_rate=0.0`, `overblocking_rate=0.1167`.
  - `combined_blind_shuffle`: `overall_score=0.385`, `certificate_success_rate=0.0`, `evidence_correct_rate=0.0`, `overblocking_rate=0.0333`.
- GRPO stoploss: `STOP`, failure `overblocking_rate is nonzero`, warning that held-out score beat random but certificate success was zero.

Diagnosis:

- The model can emit valid JSON.
- The model often predicts root cause correctly.
- The failure is evidence grounding under shuffled/blinded challenge prompts.
- Strict certificate gating is working as intended because it blocks certificates when evidence is wrong.
- This is a curriculum/prompt-grounding issue, not a reason to jump to 1.5B, 4B, or H200.

Patch after diagnosis:

- Challenge prompts now use variant-specific public span aliases such as `v1` through `v4`; old standard IDs like `s2` and `s4` are invalid in aliased challenge prompts.
- Prompt text now includes public span metadata and explicit evidence-selection instructions.
- SFT and GRPO now support mixed challenge curriculum through `--prompt-variants`.
- Added `scripts/diagnose_challenge_failures.py`.
- Added `scripts/hf_run_05b_challenge_curriculum.sh`.

Next gate:

- Run one 0.5B challenge-curriculum HF job.
- Do not run 1.5B until challenge evidence correctness and certificate success improve without invalid JSON, overblocking, or hardcoding.

## Challenge-Curriculum Script Lock

Status: `PREPARED LOCALLY`

Scripts:

- `scripts/hf_run_05b_challenge_curriculum.sh`: unlocked next run. Uses 0.5B mixed standard + challenge SFT, challenge eval, real plots, and optional GRPO disabled by default.
- `scripts/hf_run_15b_challenge_curriculum.sh`: locked. Exits unless `CONFIRM_15B_CHALLENGE_PASSED=1` is set after the 0.5B challenge-curriculum run passes.
- `scripts/hf_run_4b_stretch.sh`: locked. Exits unless `CONFIRM_4B_AFTER_15B_PASSED=1` is set after the 1.5B run passes.

Hardware decision:

- T4-small remains the next appropriate machine for 0.5B curriculum validation.
- L4/A10G is appropriate for 1.5B only after 0.5B challenge evidence recovers.
- A100/H200 is not justified for prompt or curriculum debugging; it is reserved only for optional final stretch/ablation after smaller gates pass.
