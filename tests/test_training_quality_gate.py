from argparse import Namespace

from training.quality_gate import build_stoploss_report, validate_grpo_args


def make_grpo_args(**overrides):
    args = {
        "max_steps": 10,
        "num_generations": 2,
        "per_device_train_batch_size": 2,
        "max_completion_length": 160,
        "format_reward_weight": 0.2,
        "allow_single_generation": False,
    }
    args.update(overrides)
    return Namespace(**args)


def test_grpo_quality_gate_rejects_old_hf_batch_error():
    errors = validate_grpo_args(make_grpo_args(per_device_train_batch_size=1, num_generations=2))
    assert any("divisible" in error for error in errors)


def test_grpo_quality_gate_accepts_corrected_tiny_run_config():
    errors = validate_grpo_args(make_grpo_args(per_device_train_batch_size=2, num_generations=2))
    assert errors == []


def test_stoploss_report_blocks_invalid_json_collapse():
    rows = [
        {
            "overall_score": 0.0,
            "certificate_success": 0.0,
            "hidden_regression_pass_rate": 0.0,
            "valid_preservation_rate": 0.0,
            "invalid_json": 1.0,
            "overblocking": 0.0,
            "hardcoded_patch": 0.0,
        }
        for _ in range(4)
    ]
    report = build_stoploss_report(rows)
    assert report["status"] == "STOP"
    assert any("invalid_json_rate" in failure for failure in report["failures"])


def test_stoploss_report_flags_saturated_perfect_grpo_as_caveat_not_failure():
    rows = [
        {
            "overall_score": 1.0,
            "certificate_success": 1.0,
            "hidden_regression_pass_rate": 1.0,
            "valid_preservation_rate": 1.0,
            "invalid_json": 0.0,
            "overblocking": 0.0,
            "hardcoded_patch": 0.0,
        }
        for _ in range(4)
    ]
    report = build_stoploss_report(rows, trainer_metrics={"reward_std": 0.0, "frac_reward_zero_std": 1.0})
    assert report["status"] == "PASS"
    assert report["warnings"]
    assert "not evidence of additional GRPO learning" in report["warnings"][0]
