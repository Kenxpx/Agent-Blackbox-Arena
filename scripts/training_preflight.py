from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.evaluate_model import parse_completion, score_completion
from training.make_dataset import assert_prompt_has_no_hidden_answers, build_records
from training.quality_gate import build_stoploss_report, validate_grpo_args, write_json

REPORT_PATH = ROOT / "outputs" / "training_preflight_report.json"


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _grpo_args(**overrides: Any) -> Namespace:
    defaults = {
        "max_steps": 10,
        "num_generations": 2,
        "per_device_train_batch_size": 2,
        "max_completion_length": 160,
        "format_reward_weight": 0.2,
        "allow_single_generation": False,
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def run_preflight() -> dict[str, Any]:
    train_records = build_records("train", [0])
    eval_records = build_records("eval", [1000])
    all_records = [*train_records, *eval_records]

    for record in all_records:
        assert_prompt_has_no_hidden_answers(record)

    prompt_text = _json_text([record["prompt"] for record in all_records])
    hidden_terms = [
        "incident_id",
        "hidden_regression_variants",
        "hidden_valid_variants",
        "answer_key_clause_ids",
        "expected_patch",
        "oracle_score_details",
        "raw_seed",
        "hidden_span_labels",
    ]
    leaked_terms = [term for term in hidden_terms if term in prompt_text]
    if leaked_terms:
        raise AssertionError(f"training prompts leak hidden terms: {leaked_terms}")

    target_metrics = []
    challenge_records = build_records("train", [0], prompt_variant="combined_blind_shuffle")
    for record in [*train_records, *challenge_records]:
        completion = json.dumps(record["target_json"], sort_keys=True)
        parsed, parse_error = parse_completion(completion)
        if parsed is None:
            raise AssertionError(f"SFT target is not parseable JSON: {parse_error}")
        metrics = score_completion(record["family"], int(record["seed"]), completion, prompt_variant=record["prompt_variant"])
        target_metrics.append(metrics)
        if metrics["overall_score"] < 1.0 or metrics["certificate_success"] != 1.0:
            raise AssertionError(f"SFT target does not pass verifier: {record['id']} {metrics}")

    bad_config_errors = validate_grpo_args(_grpo_args(per_device_train_batch_size=1, num_generations=2))
    if not any("divisible" in error for error in bad_config_errors):
        raise AssertionError("bad GRPO batch/generation config was not rejected")

    good_config_errors = validate_grpo_args(_grpo_args(per_device_train_batch_size=2, num_generations=2))
    if good_config_errors:
        raise AssertionError(f"known-good GRPO config was rejected: {good_config_errors}")

    invalid_rows = [
        {
            "overall_score": 0.0,
            "certificate_success": 0.0,
            "hidden_regression_pass_rate": 0.0,
            "valid_preservation_rate": 0.0,
            "invalid_json": 1.0,
            "overblocking": 0.0,
            "hardcoded_patch": 0.0,
        }
        for _ in range(3)
    ]
    invalid_report = build_stoploss_report(invalid_rows, mode="preflight_invalid_fixture")
    if invalid_report["status"] != "STOP":
        raise AssertionError("invalid-json stop-loss fixture did not stop")

    perfect_report = build_stoploss_report(
        target_metrics,
        trainer_metrics={"reward_std": 0.0, "frac_reward_zero_std": 1.0, "train_loss": 0.0},
        mode="preflight_perfect_fixture",
    )
    if perfect_report["status"] != "PASS":
        raise AssertionError("perfect verifier fixture should pass")
    if not perfect_report["warnings"]:
        raise AssertionError("perfect saturated fixture should produce a GRPO caveat")

    report = {
        "status": "PASS",
        "records_checked": len(all_records),
        "challenge_target_records_checked": len(challenge_records),
        "families_checked": sorted({record["family"] for record in all_records}),
        "prompt_schema": "conversational_prompt_with_public_trace_only",
        "hidden_prompt_leakage": "passed",
        "target_json_verifier": "passed",
        "bad_grpo_config_rejected": bad_config_errors,
        "good_grpo_config": "passed",
        "invalid_json_stoploss": invalid_report["status"],
        "saturated_grpo_caveat_detected": perfect_report["warnings"],
        "report_path": str(REPORT_PATH),
    }
    write_json(REPORT_PATH, report)
    return report


def main() -> int:
    report = run_preflight()
    print(f"training_preflight: wrote {REPORT_PATH}")
    print(
        "training_preflight: "
        f"status={report['status']} records={report['records_checked']} "
        f"families={','.join(report['families_checked'])}"
    )
    print("training_preflight: bad GRPO batch/num_generations config rejected")
    print("training_preflight: prompt leakage and verifier targets ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
