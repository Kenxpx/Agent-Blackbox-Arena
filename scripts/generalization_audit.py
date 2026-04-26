from __future__ import annotations

from collections import Counter
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.evaluate_checkpoint import run_mock_eval, write_outputs
from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from training.make_dataset import (
    CHALLENGE_VARIANTS,
    assert_prompt_has_no_hidden_answers,
    build_records,
    compact_json,
    ordered_candidates_for_prompt,
    parse_seed_spec,
)

OUTPUT_DIR = ROOT / "outputs" / "generalization_audit"
AUDIT_MD = ROOT / "GENERALIZATION_AND_CLAIM_AUDIT.md"
SFT_MODEL_DIR = ROOT / "outputs" / "sft_qwen25_05b_json" / "model"
GRPO_MODEL_DIR = ROOT / "outputs" / "grpo_tiny_hf" / "model"

SFT_TRAIN_SEEDS = "0-5"
GRPO_TRAIN_SEEDS = "0-2"
LARGE_EVAL_SEEDS = "1000-1049"
CHALLENGE_VARIANT = "shuffled_surface_blind"
HARD_CHALLENGE_VARIANT = "combined_blind_shuffle"
AUDIT_POSITION_SLICES = {
    "sft_train_standard": (SFT_TRAIN_SEEDS, "standard"),
    "standard_eval": (LARGE_EVAL_SEEDS, "standard"),
    "shuffled_surface_blind_eval": ("1000-1019", CHALLENGE_VARIANT),
    "combined_blind_shuffle_eval": ("1000-1019", HARD_CHALLENGE_VARIANT),
}

HF_EVAL_COMMAND = """hf jobs run \\
  --flavor t4-small \\
  --timeout 90m \\
  python:3.11 \\
  -- \\
  bash \\
  -lc \\
  "apt-get update && apt-get install -y git && git clone https://github.com/Kenxpx/Agent-Blackbox-Arena.git && cd Agent-Blackbox-Arena && pip install -e '.[training]' && python scripts/self_check.py && python training/evaluate_checkpoint.py --model Qwen/Qwen2.5-0.5B-Instruct --model-label base_0_5b --eval-seeds 1000-1019 --output-dir outputs/model_eval/base_0_5b_standard && python training/train_sft_warmstart.py --confirm-real-training --model Qwen/Qwen2.5-0.5B-Instruct --max-steps 30 --train-seeds 0-5 --eval-seeds 1000-1002 --output-dir outputs/sft_qwen25_05b_json --per-device-train-batch-size 1 --gradient-accumulation-steps 1 --learning-rate 1e-5 --max-completion-length 160 --save-steps 30 && python training/evaluate_checkpoint.py --model outputs/sft_qwen25_05b_json/model --model-label sft_0_5b --eval-seeds 1000-1019 --output-dir outputs/model_eval/sft_0_5b_standard && python training/evaluate_checkpoint.py --model outputs/sft_qwen25_05b_json/model --model-label sft_0_5b_shuffled_surface_blind --eval-seeds 1000-1019 --prompt-variant shuffled_surface_blind --output-dir outputs/model_eval/sft_0_5b_shuffled_surface_blind && python training/evaluate_checkpoint.py --model outputs/sft_qwen25_05b_json/model --model-label sft_0_5b_combined_blind_shuffle --eval-seeds 1000-1019 --prompt-variant combined_blind_shuffle --output-dir outputs/model_eval/sft_0_5b_combined_blind_shuffle && python training/train_json_grpo.py --confirm-real-training --model outputs/sft_qwen25_05b_json/model --max-steps 10 --train-seeds 0-2 --eval-seeds 1000 --eval-prompt-variant combined_blind_shuffle --output-dir outputs/grpo_tiny_hf --num-generations 2 --per-device-train-batch-size 2 --gradient-accumulation-steps 1 --learning-rate 5e-6 --max-completion-length 160 --format-reward-weight 0.2 --save-steps 10 && python training/evaluate_checkpoint.py --model outputs/grpo_tiny_hf/model --model-label sft_grpo_0_5b --eval-seeds 1000-1019 --output-dir outputs/model_eval/sft_grpo_0_5b_standard && python training/evaluate_checkpoint.py --model outputs/grpo_tiny_hf/model --model-label sft_grpo_0_5b_shuffled_surface_blind --eval-seeds 1000-1019 --prompt-variant shuffled_surface_blind --output-dir outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind && python training/evaluate_checkpoint.py --model outputs/grpo_tiny_hf/model --model-label sft_grpo_0_5b_combined_blind_shuffle --eval-seeds 1000-1019 --prompt-variant combined_blind_shuffle --output-dir outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle && python scripts/plot_model_eval.py --summary base=outputs/model_eval/base_0_5b_standard/summary.json --summary sft=outputs/model_eval/sft_0_5b_standard/summary.json --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_standard/summary.json --output-dir outputs/model_eval && python scripts/plot_model_eval.py --summary sft=outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json --output-dir outputs/model_eval/combined_blind_shuffle && echo '=== BASE SUMMARY ===' && cat outputs/model_eval/base_0_5b_standard/summary.json && echo '=== SFT STANDARD SUMMARY ===' && cat outputs/model_eval/sft_0_5b_standard/summary.json && echo '=== SFT SHUFFLED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_0_5b_shuffled_surface_blind/summary.json && echo '=== SFT COMBINED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json && echo '=== SFT+GRPO STANDARD SUMMARY ===' && cat outputs/model_eval/sft_grpo_0_5b_standard/summary.json && echo '=== SFT+GRPO SHUFFLED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind/summary.json && echo '=== SFT+GRPO COMBINED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json"
"""


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


def answer_position_distribution(seeds: list[int], prompt_variant: str) -> dict[str, dict[str, Any]]:
    distribution: dict[str, dict[str, Any]] = {}
    for family in IMPLEMENTED_FAMILIES:
        _, oracle = generate_incident(family=family, seed=42)
        field_positions = {
            "root_cause": [],
            "require_first_clause": [],
            "forbid": [],
            "preserve": [],
        }
        for seed in seeds:
            candidates = ordered_candidates_for_prompt(family, seed, prompt_variant=prompt_variant)
            field_positions["root_cause"].append(candidates["root_cause"].index(oracle.true_root_cause))
            field_positions["require_first_clause"].append(candidates["require"].index(oracle.answer_key_clause_ids[0]))
            field_positions["forbid"].append(candidates["forbid"].index(oracle.expected_forbid_effects[0]))
            field_positions["preserve"].append(candidates["preserve"].index(oracle.expected_preserve_clauses[0]))
        distribution[family] = {}
        for field, positions in field_positions.items():
            counts = Counter(positions)
            distribution[family][field] = {
                "positions_seen": sorted(counts),
                "counts": {str(position): count for position, count in sorted(counts.items())},
                "always_first": set(positions) == {0},
                "single_position": len(set(positions)) == 1,
            }
    return distribution


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
    candidate_position_audit = {
        name: answer_position_distribution(parse_seed_spec(seed_spec), variant)
        for name, (seed_spec, variant) in AUDIT_POSITION_SLICES.items()
    }
    candidate_position_issue = any(
        field_payload["always_first"] or field_payload["single_position"]
        for slice_payload in candidate_position_audit.values()
        for family_payload in slice_payload.values()
        for field_payload in family_payload.values()
    )

    family_label_note = (
        "Standard prompts expose the failure family because the OpenEnv state exposes family. "
        "This is treated as public metadata, not hidden oracle data. To stress-test label dependence, "
        "the challenge suite includes blind-family prompts that replace the family name with "
        "`agent_reliability_failure` while keeping only public trace spans and allowed candidate labels."
    )

    return {
        "status": "PASS" if not overlap and not issues and not candidate_position_issue else "FAIL",
        "sft_train_seeds": sorted(sft_train),
        "grpo_train_seeds": sorted(grpo_train),
        "large_eval_seeds": [min(eval_seeds), max(eval_seeds)],
        "train_eval_seed_overlap": overlap,
        "train_eval_record_id_overlap": sorted(train_ids & eval_ids),
        "records_checked_across_variants": checked_records,
        "prompt_target_leakage_issues": issues,
        "candidate_position_audit": candidate_position_audit,
        "candidate_position_issue": candidate_position_issue,
        "hidden_answer_leakage": "passed" if not issues else "failed",
        "family_label_note": family_label_note,
        "local_checkpoint_status": {
            "sft_model_present": SFT_MODEL_DIR.exists(),
            "grpo_model_present": GRPO_MODEL_DIR.exists(),
            "sft_model_path": str(SFT_MODEL_DIR),
            "grpo_model_path": str(GRPO_MODEL_DIR),
        },
    }


def run_oracle_sanity() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
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
    hard_challenge_rows = [
        {
            "id": record["id"],
            "family": record["family"],
            "seed": int(record["seed"]),
            "prompt_variant": record["prompt_variant"],
            "prompt": record["prompt"],
        }
        for record in build_records("eval", parse_seed_spec("1000-1019"), prompt_variant=HARD_CHALLENGE_VARIANT)
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

    class HardChallengeArgs:
        model = "oracle_correct_solver_for_sanity"
        model_label = "oracle_correct_solver_for_sanity"
        eval_seeds = "1000-1019"
        prompt_variant = HARD_CHALLENGE_VARIANT
        mock_policy = "oracle"

    hard_challenge_completions, hard_challenge_metrics = run_mock_eval(hard_challenge_rows, "oracle")
    hard_challenge_summary = write_outputs(
        OUTPUT_DIR / "oracle_combined_blind_shuffle_eval",
        hard_challenge_completions,
        hard_challenge_metrics,
        HardChallengeArgs(),
    )
    return standard_summary, challenge_summary, hard_challenge_summary


def write_audit_md(
    leakage: dict[str, Any],
    standard_summary: dict[str, Any],
    challenge_summary: dict[str, Any],
    hard_challenge_summary: dict[str, Any],
) -> None:
    content = f"""# Generalization And Claim Audit

This file is intentionally conservative. It separates real completed 0.5B evidence from pending larger held-out model evaluation so the submission does not overclaim.

## 1. Leakage Audit Result

Result: **{leakage['status']}**

- Hidden prompt leakage: `{leakage['hidden_answer_leakage']}`
- Records checked across standard and challenge variants: `{leakage['records_checked_across_variants']}`
- Target JSON appears verbatim in eval prompts: `{bool(leakage['prompt_target_leakage_issues'])}`
- Incident IDs usable for hardcoding in prompts: `False`
- Candidate answer positions vary across train/eval/challenge slices: `{not leakage['candidate_position_issue']}`
- Family-specific labels: public metadata in standard OpenEnv prompts; blind-family challenge prompts are available to test dependence on that metadata.

Candidate answer-position distribution:

```json
{json.dumps(leakage['candidate_position_audit'], indent=2, sort_keys=True)}
```

## 2. Train/Eval Separation Result

- SFT train seeds: `{SFT_TRAIN_SEEDS}`
- GRPO train seeds: `{GRPO_TRAIN_SEEDS}`
- Larger eval seeds prepared: `{LARGE_EVAL_SEEDS}`
- Train/eval seed overlap: `{leakage['train_eval_seed_overlap']}`
- Train/eval record ID overlap: `{leakage['train_eval_record_id_overlap']}`

## 3. Larger Held-Out Eval Metrics

Post-hardening real 0.5B larger held-out model evaluation is **pending** until the next HF job is approved. A pre-hardening same-job 0.5B evaluation completed successfully, but final claims should use a fresh run because candidate-order shuffling and stricter certificate gating changed the evaluation surface. The repo includes `training/evaluate_checkpoint.py` to evaluate base, SFT, and SFT+GRPO checkpoints over seeds `{LARGE_EVAL_SEEDS}` or the budget-safe minimum range `1000-1019`.

Local checkpoint availability:

- `outputs/sft_qwen25_05b_json/model`: `{leakage['local_checkpoint_status']['sft_model_present']}`
- `outputs/grpo_tiny_hf/model`: `{leakage['local_checkpoint_status']['grpo_model_present']}`

Because the trained checkpoints are not present locally, this audit did not run real model inference. The post-hardening larger eval must run in an HF job or another runtime where the checkpoints are recreated or available.

Oracle verifier sanity over the same larger seed range:

```json
{json.dumps(standard_summary, indent=2, sort_keys=True)}
```

This oracle sanity check proves the verifier can score correct repair plans across the larger seed range. It is **not** trained-model evidence.

## 4. Challenge Eval Metrics

Challenge variants implemented: `{CHALLENGE_VARIANT}`, `{HARD_CHALLENGE_VARIANT}`

`{CHALLENGE_VARIANT}` shuffles trace spans, rewrites surface wording, and blinds the family label as `agent_reliability_failure`. `{HARD_CHALLENGE_VARIANT}` also changes service/requester/capability names while preserving the same root-cause semantics. Real model challenge evaluation is pending.

Oracle sanity on challenge seeds `1000-1019`:

```json
{json.dumps(challenge_summary, indent=2, sort_keys=True)}
```

Oracle sanity on `{HARD_CHALLENGE_VARIANT}` seeds `1000-1019`:

```json
{json.dumps(hard_challenge_summary, indent=2, sort_keys=True)}
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

Exact next HF Jobs command, when approved:

```bash
{HF_EVAL_COMMAND}
```

## 8. GO / NO-GO For 1.5B

Decision: **NO-GO until post-hardening 0.5B held-out and challenge model evaluation are inspected.**

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
    standard_summary, challenge_summary, hard_challenge_summary = run_oracle_sanity()
    (OUTPUT_DIR / "leakage_audit.json").write_text(json.dumps(leakage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_audit_md(leakage, standard_summary, challenge_summary, hard_challenge_summary)
    print(f"generalization_audit: leakage_status={leakage['status']}")
    print(f"generalization_audit: wrote {OUTPUT_DIR / 'leakage_audit.json'}")
    print(f"generalization_audit: wrote {AUDIT_MD}")
    print("generalization_audit: model larger held-out eval pending; no trained plots created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
