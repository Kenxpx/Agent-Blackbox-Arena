# Generalization And Claim Audit

This file is intentionally conservative. It separates real completed 0.5B evidence from pending larger held-out model evaluation so the submission does not overclaim.

## 1. Leakage Audit Result

Result: **PASS**

- Hidden prompt leakage: `passed`
- Records checked across standard and challenge variants: `900`
- Target JSON appears verbatim in eval prompts: `False`
- Incident IDs usable for hardcoding in prompts: `False`
- Family-specific labels: public metadata in standard OpenEnv prompts; blind-family challenge prompts are available to test dependence on that metadata.

## 2. Train/Eval Separation Result

- SFT train seeds: `0-5`
- GRPO train seeds: `0-2`
- Larger eval seeds prepared: `1000-1049`
- Train/eval seed overlap: `[]`
- Train/eval record ID overlap: `[]`

## 3. Larger Held-Out Eval Metrics

Real 0.5B larger held-out model evaluation is **pending** until the next HF job is approved. The repo now includes `training/evaluate_checkpoint.py` to evaluate base, SFT, and SFT+GRPO checkpoints over seeds `1000-1049`.

Oracle verifier sanity over the same larger seed range:

```json
{
  "certificate_success_rate": 1.0,
  "episodes": 150,
  "eval_seeds": "1000-1049",
  "families": [
    "stale_retrieval",
    "missing_verification",
    "permission_scope"
  ],
  "hardcoded_patch_rate": 0.0,
  "hidden_regression_pass_rate": 1.0,
  "invalid_json_rate": 0.0,
  "mode": "mock",
  "model": "oracle_correct_solver_for_sanity",
  "model_label": "mock_oracle",
  "note": "CPU mock/oracle sanity check, not trained model evidence.",
  "overall_score": 1.0,
  "overblocking_rate": 0.0,
  "prompt_variant": "standard",
  "valid_preservation_rate": 1.0
}
```

This oracle sanity check proves the verifier can score correct repair plans across the larger seed range. It is **not** trained-model evidence.

## 4. Challenge Eval Metrics

Challenge variant implemented: `shuffled_surface_blind`

The variant shuffles trace spans, rewrites surface wording, and blinds the family label as `agent_reliability_failure`. Real model challenge evaluation is pending.

Oracle sanity on challenge seeds `1000-1019`:

```json
{
  "certificate_success_rate": 1.0,
  "episodes": 60,
  "eval_seeds": "1000-1019",
  "families": [
    "stale_retrieval",
    "missing_verification",
    "permission_scope"
  ],
  "hardcoded_patch_rate": 0.0,
  "hidden_regression_pass_rate": 1.0,
  "invalid_json_rate": 0.0,
  "mode": "mock",
  "model": "oracle_correct_solver_for_sanity",
  "model_label": "mock_oracle",
  "note": "CPU mock/oracle sanity check, not trained model evidence.",
  "overall_score": 1.0,
  "overblocking_rate": 0.0,
  "prompt_variant": "shuffled_surface_blind",
  "valid_preservation_rate": 1.0
}
```

## 5. Plots Created

No new trained-model plots were created in this audit because no new real model evaluation was run locally. Existing baseline plots remain valid. Future trained plots should be generated only after real `evaluate_checkpoint.py` outputs exist.

Required future plots:

- `outputs/model_eval/baseline_vs_trained_score.png`
- `outputs/model_eval/certificate_success_rate.png`
- `outputs/model_eval/hidden_regression_pass_rate.png`
- `outputs/model_eval/invalid_json_rate.png`
- `outputs/model_eval/valid_preservation_rate.png`

## 6. README Changes

README should only claim the completed 0.5B pipeline validation and should not claim broad trained-model improvement until larger held-out and challenge evaluations are run.

## 7. TRAINING_RUN_LOG.md Update

TRAINING_RUN_LOG.md records:

- earlier failed base 0.5B GRPO attempt
- SFT warmstart recovery
- GRPO validation caveat
- no broad final claim yet

This audit adds the next required evidence gate: larger held-out and challenge model evaluation before Run 2 or final claims.

## 8. GO / NO-GO For 1.5B

Decision: **NO-GO until larger 0.5B held-out and challenge model evaluation are inspected.**

Reason: the existing 0.5B result is real and useful, but it is perfect on a small eval and saturated after SFT. Elite reviewers will expect a leakage/generalization check before scaling.

## 9. GO / NO-GO For Final Training Claims

Decision: **NO-GO for final trained-vs-baseline claims. GO only for pipeline-validation claims.**

Safe claim today:

> 0.5B base GRPO collapsed into invalid JSON. A small SFT format warmstart fixed valid repair-plan generation. Verifier-scored held-out evaluation showed certificate success and hidden regression pass on the reported eval seeds, with GRPO serving as a pipeline validation after SFT saturation.

Unsafe claims:

- GRPO learned the task from scratch
- broad production safety
- SOTA
- unlimited generalization
- 1.5B or 4B results
