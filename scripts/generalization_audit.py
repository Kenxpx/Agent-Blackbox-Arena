from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.evaluate_checkpoint import run_mock_eval, write_outputs
from training.make_dataset import CHALLENGE_VARIANTS, assert_prompt_has_no_hidden_answers, build_records, compact_json, parse_seed_spec

OUTPUT_DIR = ROOT / "outputs" / "generalization_audit"
AUDIT_MD = ROOT / "GENERALIZATION_AND_CLAIM_AUDIT.md"

SFT_TRAIN_SEEDS = "0-5"
GRPO_TRAIN_SEEDS = "0-2"
LARGE_EVAL_SEEDS = "1000-1049"
CHALLENGE_VARIANT = "shuffled_surface_blind"


def prompt_text(record: dict[str, Any]) -> str:
    return json.dumps(record["prompt"], ensure_ascii=False, sort_keys=True)


def check_target_not_in_prompt(record: dict[str, Any]) -> list[str]:
    prompt = prompt_text(record)
    target = record["target_json"]
    issues: list[str] = []
    target_forms = [
        json.dumps(target, ensure_ascii=False, sort_keys=True),
        compact_json(target),
    ]
    for target_form in target_forms:
        if target_form in prompt:
            issues.append(f"target JSON appears verbatim in prompt for {record['id']}")
    incident_id = f"{record['family']}_{int(record['seed']):03d}"
    if incident_id in prompt:
        issues.append(f"incident id appears in prompt for {record['id']}")
    return issues


def run_leakage_audit() -> dict[str, Any]:
    sft_train = set(parse_seed_spec(SFT_TRAIN_SEEDS))
    grpo_train = set(parse_seed_spec(GRPO_TRAIN_SEEDS))
    eval_seeds = set(parse_seed_spec(LARGE_EVAL_SEEDS))
    overlap = sorted((sft_train | grpo_train) & eval_seeds)

    issues: list[str] = []
    checked_records = 0
    for variant in CHALLENGE_VARIANTS:
        for record in build_records("eval", sorted(eval_seeds), prompt_variant=variant):
            checked_records += 1
            assert_prompt_has_no_hidden_answers(record)
            issues.extend(check_target_not_in_prompt(record))

    train_records = build_records("train", sorted(sft_train), prompt_variant="standard")
    eval_records = build_records("eval", sorted(eval_seeds), prompt_variant="standard")
    train_ids = {record["id"] for record in train_records}
    eval_ids = {record["id"] for record in eval_records}

    family_label_note = (
        "Standard prompts expose the failure family because the OpenEnv state exposes family. "
        "This is treated as public metadata, not hidden oracle data. To stress-test label dependence, "
        "the challenge suite includes blind-family prompts that replace the family name with "
        "`agent_reliability_failure` while keeping only public trace spans and allowed candidate labels."
    )

    return {
        "status": "PASS" if not overlap and not issues else "FAIL",
        "sft_train_seeds": sorted(sft_train),
        "grpo_train_seeds": sorted(grpo_train),
        "large_eval_seeds": [min(eval_seeds), max(eval_seeds)],
        "train_eval_seed_overlap": overlap,
        "train_eval_record_id_overlap": sorted(train_ids & eval_ids),
        "records_checked_across_variants": checked_records,
        "prompt_target_leakage_issues": issues,
        "hidden_answer_leakage": "passed" if not issues else "failed",
        "family_label_note": family_label_note,
    }


def run_oracle_sanity() -> tuple[dict[str, Any], dict[str, Any]]:
    standard_rows = [
        {
            "id": record["id"],
            "family": record["family"],
            "seed": int(record["seed"]),
            "prompt_variant": record["prompt_variant"],
            "prompt": record["prompt"],
        }
        for record in build_records("eval", parse_seed_spec(LARGE_EVAL_SEEDS), prompt_variant="standard")
    ]
    challenge_rows = [
        {
            "id": record["id"],
            "family": record["family"],
            "seed": int(record["seed"]),
            "prompt_variant": record["prompt_variant"],
            "prompt": record["prompt"],
        }
        for record in build_records("eval", parse_seed_spec("1000-1019"), prompt_variant=CHALLENGE_VARIANT)
    ]

    class Args:
        model = "oracle_correct_solver_for_sanity"
        model_label = "oracle_correct_solver_for_sanity"
        eval_seeds = LARGE_EVAL_SEEDS
        prompt_variant = "standard"
        mock_policy = "oracle"

    completions, metrics = run_mock_eval(standard_rows, "oracle")
    standard_summary = write_outputs(OUTPUT_DIR / "oracle_large_eval", completions, metrics, Args())

    class ChallengeArgs:
        model = "oracle_correct_solver_for_sanity"
        model_label = "oracle_correct_solver_for_sanity"
        eval_seeds = "1000-1019"
        prompt_variant = CHALLENGE_VARIANT
        mock_policy = "oracle"

    challenge_completions, challenge_metrics = run_mock_eval(challenge_rows, "oracle")
    challenge_summary = write_outputs(OUTPUT_DIR / "oracle_challenge_eval", challenge_completions, challenge_metrics, ChallengeArgs())
    return standard_summary, challenge_summary


def write_audit_md(leakage: dict[str, Any], standard_summary: dict[str, Any], challenge_summary: dict[str, Any]) -> None:
    content = f"""# Generalization And Claim Audit

This file is intentionally conservative. It separates real completed 0.5B evidence from pending larger held-out model evaluation so the submission does not overclaim.

## 1. Leakage Audit Result

Result: **{leakage['status']}**

- Hidden prompt leakage: `{leakage['hidden_answer_leakage']}`
- Records checked across standard and challenge variants: `{leakage['records_checked_across_variants']}`
- Target JSON appears verbatim in eval prompts: `{bool(leakage['prompt_target_leakage_issues'])}`
- Incident IDs usable for hardcoding in prompts: `False`
- Family-specific labels: public metadata in standard OpenEnv prompts; blind-family challenge prompts are available to test dependence on that metadata.

## 2. Train/Eval Separation Result

- SFT train seeds: `{SFT_TRAIN_SEEDS}`
- GRPO train seeds: `{GRPO_TRAIN_SEEDS}`
- Larger eval seeds prepared: `{LARGE_EVAL_SEEDS}`
- Train/eval seed overlap: `{leakage['train_eval_seed_overlap']}`
- Train/eval record ID overlap: `{leakage['train_eval_record_id_overlap']}`

## 3. Larger Held-Out Eval Metrics

Real 0.5B larger held-out model evaluation is **pending** until the next HF job is approved. The repo now includes `training/evaluate_checkpoint.py` to evaluate base, SFT, and SFT+GRPO checkpoints over seeds `{LARGE_EVAL_SEEDS}`.

Oracle verifier sanity over the same larger seed range:

```json
{json.dumps(standard_summary, indent=2, sort_keys=True)}
```

This oracle sanity check proves the verifier can score correct repair plans across the larger seed range. It is **not** trained-model evidence.

## 4. Challenge Eval Metrics

Challenge variant implemented: `{CHALLENGE_VARIANT}`

The variant shuffles trace spans, rewrites surface wording, and blinds the family label as `agent_reliability_failure`. Real model challenge evaluation is pending.

Oracle sanity on challenge seeds `1000-1019`:

```json
{json.dumps(challenge_summary, indent=2, sort_keys=True)}
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
"""
    AUDIT_MD.write_text(content, encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    leakage = run_leakage_audit()
    standard_summary, challenge_summary = run_oracle_sanity()
    (OUTPUT_DIR / "leakage_audit.json").write_text(json.dumps(leakage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_audit_md(leakage, standard_summary, challenge_summary)
    print(f"generalization_audit: leakage_status={leakage['status']}")
    print(f"generalization_audit: wrote {OUTPUT_DIR / 'leakage_audit.json'}")
    print(f"generalization_audit: wrote {AUDIT_MD}")
    print("generalization_audit: model larger held-out eval pending; no trained plots created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
