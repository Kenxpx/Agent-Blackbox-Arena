from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from statistics import mean
from typing import Any

RANDOM_PATCH_BASELINE = 0.144


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return round(sum(_as_float(row.get(key)) for row in rows) / len(rows), 4)


def validate_grpo_args(args: Namespace) -> list[str]:
    """Return paid-run blockers that should be fixed before model loading."""
    errors: list[str] = []
    num_generations = int(getattr(args, "num_generations", 0))
    batch_size = int(getattr(args, "per_device_train_batch_size", 0))
    max_steps = int(getattr(args, "max_steps", 0))
    max_completion_length = int(getattr(args, "max_completion_length", 0))
    format_reward_weight = _as_float(getattr(args, "format_reward_weight", 0.0))

    if max_steps <= 0:
        errors.append("--max-steps must be positive for real training.")
    if num_generations < 2 and not bool(getattr(args, "allow_single_generation", False)):
        errors.append("--num-generations must be at least 2 for GRPO reward variance.")
    if batch_size <= 0:
        errors.append("--per-device-train-batch-size must be positive.")
    elif num_generations > 0 and batch_size % num_generations != 0:
        errors.append(
            "--per-device-train-batch-size must be divisible by --num-generations "
            f"(got batch_size={batch_size}, num_generations={num_generations})."
        )
    if max_completion_length < 80:
        errors.append("--max-completion-length is too short for the required repair-plan JSON.")
    if format_reward_weight < 0.0 or format_reward_weight > 0.5:
        errors.append("--format-reward-weight must stay between 0.0 and 0.5.")
    return errors


def validate_sft_args(args: Namespace) -> list[str]:
    errors: list[str] = []
    if int(getattr(args, "max_steps", 0)) <= 0:
        errors.append("--max-steps must be positive for real SFT.")
    if int(getattr(args, "per_device_train_batch_size", 0)) <= 0:
        errors.append("--per-device-train-batch-size must be positive.")
    if int(getattr(args, "max_completion_length", 0)) < 80:
        errors.append("--max-completion-length is too short for the required repair-plan JSON.")
    if int(getattr(args, "max_length", 0)) < 512:
        errors.append("--max-length is too short for the prompt-completion training records.")
    return errors


def fail_on_quality_errors(errors: list[str], label: str) -> None:
    if not errors:
        return
    formatted = "\n".join(f"- {error}" for error in errors)
    raise ValueError(f"{label} quality gate failed before paid-capable training:\n{formatted}")


def summarize_metric_rows(metric_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [_as_float(row.get("overall_score", row.get("reward"))) for row in metric_rows]
    summary = {
        "samples": len(metric_rows),
        "overall_score": _mean(metric_rows, "overall_score"),
        "certificate_success_rate": _mean(metric_rows, "certificate_success"),
        "hidden_regression_pass_rate": _mean(metric_rows, "hidden_regression_pass_rate"),
        "valid_preservation_rate": _mean(metric_rows, "valid_preservation_rate"),
        "evidence_correct_rate": _mean(metric_rows, "evidence_correct"),
        "root_cause_correct_rate": _mean(metric_rows, "root_cause_correct"),
        "patch_blocks_rate": _mean(metric_rows, "patch_blocks_failure"),
        "certificate_gate_fail_rate": _mean(metric_rows, "certificate_gate_fail"),
        "invalid_json_rate": _mean(metric_rows, "invalid_json"),
        "overblocking_rate": _mean(metric_rows, "overblocking"),
        "hardcoded_patch_rate": _mean(metric_rows, "hardcoded_patch"),
    }
    if scores:
        summary["min_overall_score"] = round(min(scores), 4)
        summary["max_overall_score"] = round(max(scores), 4)
        summary["score_saturated"] = len({round(score, 6) for score in scores}) == 1
        summary["all_perfect"] = bool(scores) and all(score >= 1.0 for score in scores)
    else:
        summary["min_overall_score"] = 0.0
        summary["max_overall_score"] = 0.0
        summary["score_saturated"] = False
        summary["all_perfect"] = False
    return summary


def _trainer_metric(trainer_metrics: dict[str, Any] | None, names: list[str]) -> float | None:
    if not trainer_metrics:
        return None
    for name in names:
        if name in trainer_metrics:
            return _as_float(trainer_metrics[name])
    return None


def build_stoploss_report(
    metric_rows: list[dict[str, Any]],
    *,
    heldout_summary: dict[str, Any] | None = None,
    trainer_metrics: dict[str, Any] | None = None,
    mode: str = "grpo",
    random_baseline: float = RANDOM_PATCH_BASELINE,
) -> dict[str, Any]:
    summary = summarize_metric_rows(metric_rows)
    failures: list[str] = []
    warnings: list[str] = []

    invalid_json_rate = _as_float(summary["invalid_json_rate"])
    overall_score = _as_float(summary["overall_score"])
    certificate_rate = _as_float(summary["certificate_success_rate"])

    if summary["samples"] == 0:
        failures.append("No verifier-scored samples were written.")
    if invalid_json_rate > 0.60:
        failures.append(f"invalid_json_rate={invalid_json_rate:.4f} is above stop-loss threshold 0.60.")
    if overall_score <= random_baseline:
        failures.append(f"overall_score={overall_score:.4f} does not beat random baseline {random_baseline:.3f}.")
    if _as_float(summary["overblocking_rate"]) > 0.0:
        failures.append("overblocking_rate is nonzero.")
    if _as_float(summary["hardcoded_patch_rate"]) > 0.0:
        failures.append("hardcoded_patch_rate is nonzero.")
    if overall_score > random_baseline and certificate_rate == 0.0:
        warnings.append("Reward beat random baseline but certificate_success_rate is zero; inspect sampled generations.")

    reward_std = _trainer_metric(trainer_metrics, ["reward_std", "train_reward_std"])
    zero_std = _trainer_metric(trainer_metrics, ["frac_reward_zero_std", "train_frac_reward_zero_std"])
    train_loss = _trainer_metric(trainer_metrics, ["train_loss"])
    if summary.get("all_perfect") and (reward_std == 0.0 or zero_std == 1.0 or train_loss == 0.0):
        warnings.append(
            "Verifier rows are perfect and trainer reward variance/loss is saturated; "
            "this validates the pipeline but is not evidence of additional GRPO learning."
        )

    if heldout_summary:
        heldout_invalid = _as_float(heldout_summary.get("invalid_json_rate"))
        heldout_score = _as_float(heldout_summary.get("overall_score"))
        heldout_cert = _as_float(heldout_summary.get("certificate_success_rate"))
        if heldout_invalid > 0.60:
            failures.append(f"heldout invalid_json_rate={heldout_invalid:.4f} is above threshold 0.60.")
        if heldout_score <= random_baseline:
            failures.append(f"heldout overall_score={heldout_score:.4f} does not beat random baseline.")
        if heldout_score > random_baseline and heldout_cert == 0.0:
            warnings.append("Held-out score beats random but certificate success is zero; inspect generations.")

    return {
        "mode": mode,
        "status": "PASS" if not failures else "STOP",
        "random_patch_baseline": random_baseline,
        "summary": summary,
        "heldout_summary": heldout_summary or {},
        "trainer_metrics_focus": {
            "reward": _trainer_metric(trainer_metrics, ["reward", "train_reward"]),
            "reward_std": reward_std,
            "frac_reward_zero_std": zero_std,
            "train_loss": train_loss,
        },
        "failures": failures,
        "warnings": warnings,
        "decision_rule": (
            "Proceed only when status is PASS, invalid_json_rate <= 0.60, scores beat random, "
            "and sampled generations show real JSON without overblocking or hardcoding."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mean_metric_from_csv_rows(rows: list[dict[str, Any]], key: str) -> float:
    values = [_as_float(row.get(key)) for row in rows]
    return round(mean(values), 4) if values else 0.0
