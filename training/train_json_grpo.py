from __future__ import annotations

import argparse
import csv
import inspect
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.evaluate_model import extract_first_json_object, mock_completion, parse_completion, score_completion, summarize
from training.make_dataset import (
    CHALLENGE_VARIANTS,
    assert_prompt_has_no_hidden_answers,
    build_mixed_records,
    build_records,
    parse_prompt_variants,
    parse_seed_spec,
)
from training.quality_gate import build_stoploss_report, fail_on_quality_errors, validate_grpo_args, write_json
from training.tracking import trainer_log_history, tracking_run_dir, write_training_tracking

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

METRIC_FIELDNAMES = [
    "step",
    "reward_call",
    "sample_index",
    "prompt_id",
    "family",
    "seed",
    "prompt_variant",
    "reward",
    "format_reward",
    "training_reward",
    "overall_score",
    "certificate_success",
    "hidden_regression_pass_rate",
    "valid_preservation_rate",
    "evidence_correct",
    "root_cause_correct",
    "patch_blocks_failure",
    "certificate_gate_fail",
    "invalid_json",
    "overblocking",
    "hardcoded_patch",
    "parse_error",
]


def verifier_reward(family: str, seed: int, completion: str) -> float:
    return float(score_completion(family, seed, completion)["overall_score"])


def json_format_score(completion: str) -> float:
    """Small training-only shaping signal for strict JSON before verifier reward is reachable."""
    parsed, _ = parse_completion(completion)
    if parsed is not None:
        return 1.0

    text = completion.strip()
    if not text:
        return 0.0

    score = 0.0
    if text.startswith("{"):
        score += 0.10
    if text.endswith("}"):
        score += 0.05
    if "```" not in text:
        score += 0.05

    candidate = extract_first_json_object(text)
    if candidate is not None:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            value = None
        if isinstance(value, dict):
            score += 0.20
            required_keys = ["evidence_spans", "root_cause", "patch", "regression_tests", "rationale"]
            score += 0.05 * sum(1 for key in required_keys if key in value)
            patch = value.get("patch")
            if isinstance(patch, dict):
                score += 0.05 * sum(1 for key in ["require", "forbid", "preserve"] if key in patch)

    return round(min(score, 0.95), 4)


def run_smoke(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = build_records("train", parse_seed_spec("0"))
    sampled_path = args.output_dir / "sampled_generations.jsonl"
    metrics_path = args.output_dir / "metrics.csv"
    summary_path = args.output_dir / "smoke_summary.json"

    samples: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    completion_modes = ["oracle", "invalid_json", "wrapped_json", "block_everything", "hardcoded"]

    for step, record in enumerate(records[:3]):
        family = record["family"]
        seed = int(record["seed"])
        for mode in completion_modes:
            completion = mock_completion(family, seed, mode)
            parsed, error = parse_completion(completion)
            metrics = score_completion(family, seed, completion)
            format_reward = json_format_score(completion)
            training_reward = float(metrics["overall_score"]) + args.format_reward_weight * format_reward
            samples.append(
                {
                    "step": step,
                    "family": family,
                    "seed": seed,
                    "mode": mode,
                    "prompt_id": record["id"],
                    "completion": completion,
                    "parse_ok": parsed is not None,
                    "parse_error": error,
                    "reward": metrics["overall_score"],
                    "format_reward": format_reward,
                    "training_reward": training_reward,
                    "overall_score": metrics["overall_score"],
                }
            )
            metric_rows.append(
                {
                    "step": step,
                    "family": family,
                    "seed": seed,
                    "mode": mode,
                    "reward": metrics["overall_score"],
                    "format_reward": format_reward,
                    "training_reward": training_reward,
                    "overall_score": metrics["overall_score"],
                    "invalid_json": metrics["invalid_json"],
                    "certificate_success": metrics["certificate_success"],
                    "hidden_regression_pass_rate": metrics["hidden_regression_pass_rate"],
                    "valid_preservation_rate": metrics["valid_preservation_rate"],
                    "evidence_correct": metrics["evidence_correct"],
                    "root_cause_correct": metrics["root_cause_correct"],
                    "patch_blocks_failure": metrics["patch_blocks_failure"],
                    "certificate_gate_fail": metrics["certificate_gate_fail"],
                    "overblocking": metrics["overblocking"],
                    "hardcoded_patch": metrics["hardcoded_patch"],
                    "parse_error": error or metrics.get("error", ""),
                }
            )

    with sampled_path.open("w", encoding="utf-8") as handle:
        for sample in samples:
            handle.write(json.dumps(sample, sort_keys=True) + "\n")
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metric_rows[0].keys()))
        writer.writeheader()
        writer.writerows(metric_rows)
    invalid_json_rate = sum(row["invalid_json"] for row in metric_rows) / len(metric_rows)
    wrapped_rows = [row for row in metric_rows if row["mode"] == "wrapped_json"]
    if not wrapped_rows or any(row["invalid_json"] for row in wrapped_rows):
        raise AssertionError("Smoke parser failed to extract wrapped valid JSON completions.")
    summary = {
        "mode": "smoke",
        "model": args.model,
        "samples": len(samples),
        "invalid_json_rate": round(invalid_json_rate, 4),
        "max_steps": args.max_steps,
        "num_generations": args.num_generations,
        "full_grpo_ran": False,
        "note": "Smoke mode tests parser, verifier reward, and JSON-format shaping only. It does not run TRL training.",
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"train_json_grpo: smoke wrote {metrics_path}")
    print(f"train_json_grpo: smoke wrote {sampled_path}")
    print(f"train_json_grpo: smoke invalid_json_rate={invalid_json_rate:.4f}")
    print("train_json_grpo: full GRPO not run in smoke mode")


def completion_to_text(completion: Any) -> str:
    if isinstance(completion, str):
        return completion.strip()
    if isinstance(completion, dict):
        if "content" in completion:
            return str(completion["content"]).strip()
        return json.dumps(completion, sort_keys=True)
    if isinstance(completion, list):
        if completion and isinstance(completion[-1], dict) and "content" in completion[-1]:
            return str(completion[-1]["content"]).strip()
        return "".join(completion_to_text(item) for item in completion).strip()
    return str(completion).strip()


def as_batch(value: Any, expected_len: int, name: str) -> list[Any]:
    if isinstance(value, list):
        if len(value) != expected_len:
            raise ValueError(f"reward batch field {name} length {len(value)} != completions length {expected_len}")
        return value
    if value is None:
        raise ValueError(f"reward batch missing required field: {name}")
    return [value for _ in range(expected_len)]


def build_grpo_rows(
    split: str,
    seeds: list[int],
    prompt_variant: str = "standard",
    prompt_variants: list[str] | None = None,
) -> list[dict[str, Any]]:
    records = build_mixed_records(split, seeds, prompt_variants) if prompt_variants else build_records(split, seeds, prompt_variant=prompt_variant)
    rows: list[dict[str, Any]] = []
    for record in records:
        assert_prompt_has_no_hidden_answers(record)
        rows.append(
            {
                "prompt": record["prompt"],
                "family": record["family"],
                "seed": int(record["seed"]),
                "id": record["id"],
                "prompt_variant": record["prompt_variant"],
            }
        )
    return rows


def make_verifier_reward_func(sampled_path: Path, metric_rows: list[dict[str, Any]], format_reward_weight: float):
    reward_call = 0

    def reward_func(*reward_args: Any, **kwargs: Any) -> list[float]:
        nonlocal reward_call
        if "completions" in kwargs:
            completions = kwargs.pop("completions")
        elif len(reward_args) == 1:
            completions = reward_args[0]
        elif len(reward_args) >= 2:
            completions = reward_args[1]
        else:
            raise ValueError("reward function did not receive completions")
        if not isinstance(completions, list):
            completions = [completions]
        families = as_batch(kwargs.get("family"), len(completions), "family")
        seeds = as_batch(kwargs.get("seed"), len(completions), "seed")
        prompt_ids = as_batch(kwargs.get("id"), len(completions), "id")
        prompt_variants = as_batch(kwargs.get("prompt_variant"), len(completions), "prompt_variant")

        rewards: list[float] = []
        with sampled_path.open("a", encoding="utf-8") as handle:
            for sample_index, raw_completion in enumerate(completions):
                family = str(families[sample_index])
                seed = int(seeds[sample_index])
                prompt_variant = str(prompt_variants[sample_index])
                completion = completion_to_text(raw_completion)
                parsed, parse_error = parse_completion(completion)
                metrics = score_completion(family, seed, completion, prompt_variant=prompt_variant)
                verifier_score = float(metrics["overall_score"])
                format_reward = json_format_score(completion)
                training_reward = verifier_score + format_reward_weight * format_reward
                rewards.append(training_reward)
                row = {
                    "step": reward_call,
                    "reward_call": reward_call,
                    "sample_index": sample_index,
                    "prompt_id": str(prompt_ids[sample_index]),
                    "family": family,
                    "seed": seed,
                    "prompt_variant": prompt_variant,
                    "reward": verifier_score,
                    "format_reward": format_reward,
                    "training_reward": training_reward,
                    "overall_score": verifier_score,
                    "certificate_success": metrics["certificate_success"],
                    "hidden_regression_pass_rate": metrics["hidden_regression_pass_rate"],
                    "valid_preservation_rate": metrics["valid_preservation_rate"],
                    "evidence_correct": metrics["evidence_correct"],
                    "root_cause_correct": metrics["root_cause_correct"],
                    "patch_blocks_failure": metrics["patch_blocks_failure"],
                    "certificate_gate_fail": metrics["certificate_gate_fail"],
                    "invalid_json": metrics["invalid_json"],
                    "overblocking": metrics["overblocking"],
                    "hardcoded_patch": metrics["hardcoded_patch"],
                    "parse_error": parse_error or metrics.get("error", ""),
                }
                metric_rows.append(row)
                handle.write(
                    json.dumps(
                        {
                            **row,
                            "parse_ok": parsed is not None,
                            "completion": completion,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
        reward_call += 1
        return rewards

    return reward_func


def render_prompt_for_generation(tokenizer: Any, prompt: Any) -> str:
    if isinstance(prompt, list):
        try:
            return tokenizer.apply_chat_template(prompt, tokenize=False, add_generation_prompt=True)
        except Exception:
            lines: list[str] = []
            for message in prompt:
                if isinstance(message, dict):
                    lines.append(f"{message.get('role', 'user')}: {message.get('content', '')}")
                else:
                    lines.append(str(message))
            return "\n".join(lines) + "\nassistant:"
    return str(prompt)


def write_training_metrics(
    output_dir: Path,
    metric_rows: list[dict[str, Any]],
    trainer_metrics: dict[str, Any],
    trainer_history: list[dict[str, Any]] | None = None,
) -> None:
    metrics_path = output_dir / "metrics.csv"
    summary_path = output_dir / "summary.json"
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDNAMES)
        writer.writeheader()
        writer.writerows(metric_rows)

    eval_like_rows = [
        {
            "overall_score": row["overall_score"],
            "certificate_success": row["certificate_success"],
            "hidden_regression_pass_rate": row["hidden_regression_pass_rate"],
            "valid_preservation_rate": row["valid_preservation_rate"],
            "evidence_correct": row["evidence_correct"],
            "root_cause_correct": row["root_cause_correct"],
            "patch_blocks_failure": row["patch_blocks_failure"],
            "certificate_gate_fail": row["certificate_gate_fail"],
            "invalid_json": row["invalid_json"],
            "overblocking": row["overblocking"],
            "hardcoded_patch": row["hardcoded_patch"],
        }
        for row in metric_rows
    ]
    verifier_summary = summarize(eval_like_rows) if eval_like_rows else {}
    summary = {
        "mode": "real_grpo",
        "samples_scored": len(metric_rows),
        "verifier_summary": verifier_summary,
        "trainer_metrics": trainer_metrics,
        "quality_gate_note": (
            "See stoploss_report.json for pass/stop decision, held-out checks, "
            "and GRPO saturation caveats."
        ),
        "note": "Generated from real model completions scored by the deterministic verifier.",
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # scripts/make_plots.py reads this file to create real training plots.
    mirror_path = ROOT / "outputs" / "training_metrics.csv"
    mirror_path.parent.mkdir(parents=True, exist_ok=True)
    with mirror_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDNAMES)
        writer.writeheader()
        writer.writerows(metric_rows)

    if trainer_history:
        history_path = output_dir / "trainer_log_history.csv"
        history_fields = sorted({key for row in trainer_history for key in row})
        with history_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=history_fields)
            writer.writeheader()
            writer.writerows(trainer_history)


def build_grpo_config(GRPOConfig: Any, args: argparse.Namespace) -> Any:
    tracking_dir = tracking_run_dir(args.output_dir, "grpo") / "trainer"
    config_kwargs = {
        "output_dir": str(args.output_dir),
        "learning_rate": args.learning_rate,
        "max_steps": args.max_steps,
        "num_generations": args.num_generations,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "gradient_checkpointing": args.gradient_checkpointing,
        "max_prompt_length": args.max_prompt_length,
        "max_completion_length": args.max_completion_length,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "top_k": args.top_k,
        "repetition_penalty": args.repetition_penalty,
        "logging_steps": args.logging_steps,
        "save_steps": args.save_steps,
        "bf16": args.bf16,
        "report_to": ["tensorboard"],
        "logging_dir": str(tracking_dir),
        "remove_unused_columns": False,
    }
    accepted = set(inspect.signature(GRPOConfig).parameters)
    return GRPOConfig(**{key: value for key, value in config_kwargs.items() if key in accepted})


def maybe_apply_lora(model: Any, args: argparse.Namespace) -> Any:
    if not args.use_lora:
        return model
    from peft import LoraConfig, TaskType, get_peft_model  # type: ignore

    target_modules = [module.strip() for module in args.lora_target_modules.split(",") if module.strip()]
    config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules or None,
    )
    peft_model = get_peft_model(model, config)
    peft_model.print_trainable_parameters()
    return peft_model


def torch_dtype_arg(value: str) -> Any:
    if value == "none":
        return None
    if value == "auto":
        return "auto"
    import torch  # type: ignore

    return {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }[value]


def load_causal_model(model_id: str, args: argparse.Namespace) -> Any:
    from transformers import AutoModelForCausalLM  # type: ignore

    model_kwargs = {"trust_remote_code": True, "device_map": "auto"}
    if args.torch_dtype != "none":
        model_kwargs["torch_dtype"] = torch_dtype_arg(args.torch_dtype)

    model_path = Path(model_id)
    adapter_config_path = model_path / "adapter_config.json"
    if adapter_config_path.exists():
        from peft import PeftConfig, PeftModel  # type: ignore

        peft_config = PeftConfig.from_pretrained(str(model_path))
        base_model = AutoModelForCausalLM.from_pretrained(
            peft_config.base_model_name_or_path,
            **model_kwargs,
        )
        return PeftModel.from_pretrained(base_model, str(model_path), is_trainable=True)

    return AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)


def make_trainer(GRPOTrainer: Any, model: Any, tokenizer: Any, reward_func: Any, config: Any, train_dataset: Any, eval_dataset: Any) -> Any:
    trainer_kwargs = {
        "model": model,
        "reward_funcs": [reward_func],
        "args": config,
        "train_dataset": train_dataset,
        "eval_dataset": eval_dataset,
    }
    try:
        return GRPOTrainer(**trainer_kwargs, processing_class=tokenizer)
    except TypeError:
        return GRPOTrainer(**trainer_kwargs, tokenizer=tokenizer)


def run_heldout_generation_eval(model: Any, tokenizer: Any, eval_rows: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    import torch  # type: ignore

    heldout_path = args.output_dir / "heldout_eval_completions.jsonl"
    metrics_path = args.output_dir / "heldout_eval_metrics.csv"
    summary_path = args.output_dir / "heldout_eval_summary.json"
    heldout_metrics: list[dict[str, Any]] = []
    model.eval()
    device = next(model.parameters()).device

    with heldout_path.open("w", encoding="utf-8") as handle:
        for row in eval_rows:
            prompt_text = render_prompt_for_generation(tokenizer, row["prompt"])
            inputs = tokenizer(prompt_text, return_tensors="pt", truncation=True, max_length=args.max_prompt_length)
            inputs = {key: value.to(device) for key, value in inputs.items()}
            input_length = int(inputs["input_ids"].shape[-1])
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=args.max_completion_length,
                    do_sample=False,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
            completion_ids = output_ids[0][input_length:]
            completion = tokenizer.decode(completion_ids, skip_special_tokens=True).strip()
            parsed, parse_error = parse_completion(completion)
            prompt_variant = str(row.get("prompt_variant", "standard"))
            metrics = score_completion(str(row["family"]), int(row["seed"]), completion, prompt_variant=prompt_variant)
            metric_row = {
                "family": row["family"],
                "seed": int(row["seed"]),
                "prompt_id": row["id"],
                "prompt_variant": prompt_variant,
                "overall_score": metrics["overall_score"],
                "certificate_success": metrics["certificate_success"],
                "hidden_regression_pass_rate": metrics["hidden_regression_pass_rate"],
                "valid_preservation_rate": metrics["valid_preservation_rate"],
                "evidence_correct": metrics["evidence_correct"],
                "root_cause_correct": metrics["root_cause_correct"],
                "patch_blocks_failure": metrics["patch_blocks_failure"],
                "certificate_gate_fail": metrics["certificate_gate_fail"],
                "invalid_json": metrics["invalid_json"],
                "overblocking": metrics["overblocking"],
                "hardcoded_patch": metrics["hardcoded_patch"],
                "parse_error": parse_error or metrics.get("error", ""),
            }
            heldout_metrics.append(metric_row)
            handle.write(
                json.dumps(
                    {
                        **metric_row,
                        "parse_ok": parsed is not None,
                        "completion": completion,
                    },
                    sort_keys=True,
                )
                + "\n"
            )

    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(heldout_metrics[0].keys()))
        writer.writeheader()
        writer.writerows(heldout_metrics)
    summary = summarize(heldout_metrics)
    summary["mode"] = "heldout_generation_eval"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def namespace_to_jsonable(args: argparse.Namespace) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in sorted(vars(args).items()):
        output[key] = str(value) if isinstance(value, Path) else value
    return output


def run_full_grpo(args: argparse.Namespace) -> None:
    fail_on_quality_errors(validate_grpo_args(args), "GRPO")
    if not args.confirm_real_training:
        raise RuntimeError(
            "Refusing to start paid-capable training without --confirm-real-training. "
            "Run smoke checks first, then pass the confirmation flag intentionally."
        )
    if args.use_unsloth:
        try:
            import unsloth  # type: ignore  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "--use-unsloth was requested, but unsloth is not installed in this runtime. "
                "Use plain TRL first, or install/audit Unsloth before a stretch run."
            ) from exc

    # Stop-loss rules before any real HF spend:
    # - run scripts/self_check.py first
    # - keep max_steps tiny for the first paid run
    # - stop if invalid JSON remains above 60 percent
    # - stop if reward rises while certificate success does not
    # - stop if block-everything or hardcoded behavior appears
    from datasets import Dataset  # type: ignore
    from transformers import AutoTokenizer  # type: ignore
    from trl import GRPOConfig, GRPOTrainer  # type: ignore

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output_dir / "run_config.json",
        {
            "mode": "real_grpo",
            "args": namespace_to_jsonable(args),
            "quality_gate": "passed_before_model_load",
            "source": "training/train_json_grpo.py",
        },
    )
    sampled_path = args.output_dir / "sampled_generations.jsonl"
    sampled_path.write_text("", encoding="utf-8")
    metric_rows: list[dict[str, Any]] = []

    train_prompt_variants = parse_prompt_variants(args.prompt_variants) if args.prompt_variants else None
    train_rows = build_grpo_rows(
        "train",
        parse_seed_spec(args.train_seeds),
        prompt_variant=args.prompt_variant,
        prompt_variants=train_prompt_variants,
    )
    eval_rows = build_grpo_rows("eval", parse_seed_spec(args.eval_seeds), prompt_variant=args.eval_prompt_variant)
    train_dataset = Dataset.from_list(train_rows)
    eval_dataset = Dataset.from_list(eval_rows)

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = load_causal_model(args.model, args)
    if tokenizer.pad_token_id is not None:
        model.config.pad_token_id = tokenizer.pad_token_id
    model = maybe_apply_lora(model, args)

    reward_func = make_verifier_reward_func(sampled_path, metric_rows, args.format_reward_weight)
    config = build_grpo_config(GRPOConfig, args)
    trainer = make_trainer(GRPOTrainer, model, tokenizer, reward_func, config, train_dataset, eval_dataset)
    train_result = trainer.train()
    trainer_metrics = dict(getattr(train_result, "metrics", {}) or {})
    trainer_history = trainer_log_history(trainer)
    trainer.save_model(str(args.output_dir / "model"))
    tokenizer.save_pretrained(str(args.output_dir / "model"))
    write_training_metrics(args.output_dir, metric_rows, trainer_metrics, trainer_history)
    heldout_summary = run_heldout_generation_eval(model, tokenizer, eval_rows, args)
    stoploss_report = build_stoploss_report(
        metric_rows,
        heldout_summary=heldout_summary,
        trainer_metrics=trainer_metrics,
        mode="grpo",
    )
    write_json(args.output_dir / "stoploss_report.json", stoploss_report)
    tracking_dir = write_training_tracking(
        args.output_dir,
        "grpo",
        trainer_history=trainer_history,
        verifier_rows=metric_rows,
        summaries={
            "trainer": trainer_metrics,
            "heldout": heldout_summary,
            "stoploss": {"status_pass": 1.0 if stoploss_report["status"] == "PASS" else 0.0},
        },
    )

    print(f"train_json_grpo: real GRPO wrote {args.output_dir / 'metrics.csv'}")
    print(f"train_json_grpo: real GRPO wrote {sampled_path}")
    print(f"train_json_grpo: real GRPO wrote {args.output_dir / 'summary.json'}")
    print(f"train_json_grpo: real GRPO wrote {args.output_dir / 'heldout_eval_summary.json'}")
    print(f"train_json_grpo: tracking wrote {tracking_dir}")
    print(f"train_json_grpo: real GRPO stoploss_status={stoploss_report['status']}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TRL/GRPO scaffold for JSON repair-plan training.")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--confirm-real-training", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--train-seeds", default="0-59")
    parser.add_argument("--eval-seeds", default="1000-1014")
    parser.add_argument("--prompt-variant", choices=CHALLENGE_VARIANTS, default="standard")
    parser.add_argument(
        "--prompt-variants",
        default=None,
        help="Comma-separated train prompt variants for mixed challenge curriculum.",
    )
    parser.add_argument("--eval-prompt-variant", choices=CHALLENGE_VARIANTS, default="standard")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "grpo")
    parser.add_argument("--num-generations", type=int, default=4)
    parser.add_argument(
        "--allow-single-generation",
        action="store_true",
        help="Emergency OOM override only. Single-generation GRPO has no group variance and is not preferred evidence.",
    )
    parser.add_argument("--use-unsloth", action="store_true")
    parser.add_argument("--learning-rate", type=float, default=5e-6)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument("--torch-dtype", choices=["auto", "float16", "bfloat16", "float32", "none"], default="auto")
    parser.add_argument("--max-prompt-length", type=int, default=1024)
    parser.add_argument("--max-completion-length", type=int, default=160)
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--repetition-penalty", type=float, default=1.05)
    parser.add_argument(
        "--format-reward-weight",
        type=float,
        default=0.2,
        help=(
            "Training-only JSON-format shaping weight. Core verifier metrics still use overall_score, "
            "certificate success, hidden regression, and valid preservation."
        ),
    )
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--save-steps", type=int, default=20)
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--use-lora", action="store_true")
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-target-modules", default="q_proj,k_proj,v_proj,o_proj")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.smoke:
        run_smoke(args)
        return 0
    run_full_grpo(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
