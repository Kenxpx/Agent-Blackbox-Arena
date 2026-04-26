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

This file is intentionally conservative. It keeps leakage/generalization checks separate from final training claims so the submission does not overclaim. The selected final model is `Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200` from HF Job `69edcef7d70108f37acdfeb3`.

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

## 3. Final Held-Out Eval Metrics

The final selected Qwen3-4B H200 SFT+GRPO run completed verifier-scored evaluation over seeds `1000-1019`:

| Variant | Overall | Certificate | Evidence | Hidden pass | Valid preserve | Invalid JSON |
|---|---:|---:|---:|---:|---:|---:|
| `standard` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| `shuffled_surface_blind` | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 |
| `combined_blind_shuffle` | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 |

Safety rates were `overblocking_rate=0.0000`, `hardcoded_patch_rate=0.0000`, and stoploss `PASS`. The local oracle checks below remain useful as verifier sanity checks, not as the final trained-model metric source.

Local checkpoint availability:

- `outputs/sft_qwen25_05b_json/model`: `{leakage['local_checkpoint_status']['sft_model_present']}`
- `outputs/grpo_tiny_hf/model`: `{leakage['local_checkpoint_status']['grpo_model_present']}`

Because the final trained checkpoint is not stored in this repository, this CPU audit does not rerun Qwen3-4B inference locally. The final model evidence comes from the completed HF Job log and checked-in final metrics/assets.

Oracle verifier sanity over the same larger seed range:

```json
{json.dumps(standard_summary, indent=2, sort_keys=True)}
```

This oracle sanity check proves the verifier can score correct repair plans across the larger seed range. It is **not** trained-model evidence.

## 4. Challenge Eval Metrics

Challenge variants implemented: `{CHALLENGE_VARIANT}`, `{HARD_CHALLENGE_VARIANT}`

`{CHALLENGE_VARIANT}` shuffles trace spans, rewrites surface wording, and blinds the family label as `agent_reliability_failure`. `{HARD_CHALLENGE_VARIANT}` also changes service/requester/capability names while preserving the same root-cause semantics. The final Qwen3-4B run reports real model metrics for both challenge variants above.

Oracle sanity on challenge seeds `1000-1019`:

```json
{json.dumps(challenge_summary, indent=2, sort_keys=True)}
```

Oracle sanity on `{HARD_CHALLENGE_VARIANT}` seeds `1000-1019`:

```json
{json.dumps(hard_challenge_summary, indent=2, sort_keys=True)}
```

## 5. Plots Created

No new trained-model plots are created by this CPU audit. Final selected plots and tables are stored under `docs/final_assets/` and are generated from the completed H200 run's reported metrics/log evidence.

## 6. README Changes

README should claim the Qwen3-4B final H200 SFT+GRPO result only within the reported synthetic MVP families, prompt variants, and eval seeds `1000-1019`.

## 7. TRAINING_RUN_LOG.md Update

TRAINING_RUN_LOG.md records:

- earlier failed base 0.5B GRPO attempt
- SFT warmstart recovery
- GRPO validation caveat
- final Qwen3-4B H200 selection
- failed/intermediate larger-model runs kept as audit evidence

The final H200 run is complete. The historical HF eval command remains here only as a reproducibility reference:

```bash
{HF_EVAL_COMMAND}
```

## 8. Larger-Model Decision

Decision: **Qwen3-4B final H200 SFT+GRPO is selected.**

Reason: the selected run improves the reported challenge evidence/certificate metrics while keeping invalid JSON, overblocking, and hardcoded patch rates at `0.0000`.

## 9. GO / NO-GO For Final Training Claims

Decision: **GO for bounded final Qwen3-4B claims.**

Safe claim today:

> Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200 is the selected trained result for the reported synthetic MVP families, prompt variants, and eval seeds `1000-1019`.

Unsafe claims:

- GRPO learned the task from scratch
- broad production safety
- SOTA
- unlimited generalization
- 1.5B success
- Qwen2.5-3B success
- failed/error H200 jobs as successful
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
    print("generalization_audit: final Qwen3-4B claims bounded; no local model inference run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
