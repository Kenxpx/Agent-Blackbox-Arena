# Training Run Log

Current decision: **NO-GO for Run 2**.

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
