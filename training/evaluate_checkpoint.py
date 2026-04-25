from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES
from training.evaluate_model import mock_completion, parse_completion, score_completion, summarize
from training.make_dataset import CHALLENGE_VARIANTS, assert_prompt_has_no_hidden_answers, build_records, parse_seed_spec
from training.train_json_grpo import load_causal_model, render_prompt_for_generation

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_eval_rows(eval_seeds: str, prompt_variant: str) -> list[dict[str, Any]]:
    records = build_records("eval", parse_seed_spec(eval_seeds), prompt_variant=prompt_variant)
    rows: list[dict[str, Any]] = []
    for record in records:
        assert_prompt_has_no_hidden_answers(record)
        rows.append(
            {
                "id": record["id"],
                "family": record["family"],
                "seed": int(record["seed"]),
                "prompt_variant": record["prompt_variant"],
                "prompt": record["prompt"],
            }
        )
    return rows


def generate_model_completion(model: Any, tokenizer: Any, prompt: Any, args: argparse.Namespace) -> str:
    import torch  # type: ignore

    prompt_text = render_prompt_for_generation(tokenizer, prompt)
    device = next(model.parameters()).device
    inputs = tokenizer(prompt_text, return_tensors="pt", truncation=True, max_length=args.max_prompt_length)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    input_length = int(inputs["input_ids"].shape[-1])
    generation_kwargs = {
        "max_new_tokens": args.max_completion_length,
        "do_sample": bool(args.do_sample),
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if args.do_sample:
        generation_kwargs["temperature"] = args.temperature
        generation_kwargs["top_p"] = args.top_p
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            **generation_kwargs,
        )
    completion_ids = output_ids[0][input_length:]
    return tokenizer.decode(completion_ids, skip_special_tokens=True).strip()


def generate_model_completions(model: Any, tokenizer: Any, prompts: list[Any], args: argparse.Namespace) -> list[str]:
    import torch  # type: ignore

    prompt_texts = [render_prompt_for_generation(tokenizer, prompt) for prompt in prompts]
    device = next(model.parameters()).device
    inputs = tokenizer(
        prompt_texts,
        return_tensors="pt",
        truncation=True,
        max_length=args.max_prompt_length,
        padding=True,
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}
    input_width = int(inputs["input_ids"].shape[-1])
    generation_kwargs = {
        "max_new_tokens": args.max_completion_length,
        "do_sample": bool(args.do_sample),
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if args.do_sample:
        generation_kwargs["temperature"] = args.temperature
        generation_kwargs["top_p"] = args.top_p
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            **generation_kwargs,
        )
    completions: list[str] = []
    for row_index in range(output_ids.shape[0]):
        completion_ids = output_ids[row_index][input_width:]
        completions.append(tokenizer.decode(completion_ids, skip_special_tokens=True).strip())
    return completions


def run_mock_eval(eval_rows: list[dict[str, Any]], mode: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    completions: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    for row in eval_rows:
        completion = mock_completion(row["family"], int(row["seed"]), mode)
        parsed, parse_error = parse_completion(completion)
        scored = score_completion(row["family"], int(row["seed"]), completion)
        metric_row = {
            "model_label": "mock_" + mode,
            "prompt_id": row["id"],
            "family": row["family"],
            "seed": int(row["seed"]),
            "prompt_variant": row["prompt_variant"],
            **{key: scored[key] for key in [
                "overall_score",
                "certificate_success",
                "hidden_regression_pass_rate",
                "valid_preservation_rate",
                "invalid_json",
                "overblocking",
                "hardcoded_patch",
            ]},
            "parse_error": parse_error or scored.get("error", ""),
        }
        metrics.append(metric_row)
        completions.append({**metric_row, "parse_ok": parsed is not None, "completion": completion})
    return completions, metrics


def run_model_eval(eval_rows: list[dict[str, Any]], args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from transformers import AutoTokenizer  # type: ignore

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True, padding_side="left")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = load_causal_model(args.model, args)
    if tokenizer.pad_token_id is not None:
        model.config.pad_token_id = tokenizer.pad_token_id
    model.eval()

    completions: list[dict[str, Any]] = []
    metrics: list[dict[str, Any]] = []
    batch_size = max(1, int(args.batch_size))
    total = len(eval_rows)
    for start in range(0, total, batch_size):
        batch = eval_rows[start : start + batch_size]
        batch_completions = generate_model_completions(model, tokenizer, [row["prompt"] for row in batch], args)
        for row, completion in zip(batch, batch_completions):
            parsed, parse_error = parse_completion(completion)
            scored = score_completion(row["family"], int(row["seed"]), completion)
            metric_row = {
                "model_label": args.model_label,
                "prompt_id": row["id"],
                "family": row["family"],
                "seed": int(row["seed"]),
                "prompt_variant": row["prompt_variant"],
                **{key: scored[key] for key in [
                    "overall_score",
                    "certificate_success",
                    "hidden_regression_pass_rate",
                    "valid_preservation_rate",
                    "invalid_json",
                    "overblocking",
                    "hardcoded_patch",
                ]},
                "parse_error": parse_error or scored.get("error", ""),
            }
            metrics.append(metric_row)
            completions.append({**metric_row, "parse_ok": parsed is not None, "completion": completion})
        print(
            "evaluate_checkpoint: "
            f"label={args.model_label} variant={args.prompt_variant} progress={min(start + len(batch), total)}/{total}",
            flush=True,
        )
    return completions, metrics


def write_outputs(output_dir: Path, completions: list[dict[str, Any]], metrics: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    completion_path = output_dir / "completions.jsonl"
    with completion_path.open("w", encoding="utf-8") as handle:
        for row in completions:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    write_csv(output_dir / "metrics.csv", metrics)
    summary = summarize(metrics)
    summary.update(
        {
            "mode": "mock" if args.mock_policy else "model",
            "model": args.model,
            "model_label": args.model_label if not args.mock_policy else "mock_" + args.mock_policy,
            "eval_seeds": args.eval_seeds,
            "prompt_variant": args.prompt_variant,
            "families": list(IMPLEMENTED_FAMILIES),
            "note": "Verifier-scored held-out model completions." if not args.mock_policy else "CPU mock/oracle sanity check, not trained model evidence.",
        }
    )
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a base, SFT, or GRPO checkpoint on held-out Agent BlackBox prompts.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-label", default="model")
    parser.add_argument("--eval-seeds", default="1000-1019")
    parser.add_argument("--prompt-variant", choices=CHALLENGE_VARIANTS, default="standard")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "model_eval")
    parser.add_argument("--mock-policy", choices=["oracle", "invalid_json", "wrapped_json", "block_everything", "hardcoded"], default=None)
    parser.add_argument("--max-prompt-length", type=int, default=1024)
    parser.add_argument("--max-completion-length", type=int, default=160)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--torch-dtype", choices=["auto", "float16", "bfloat16", "float32", "none"], default="auto")
    parser.add_argument("--do-sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top-p", type=float, default=0.9)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    eval_rows = build_eval_rows(args.eval_seeds, args.prompt_variant)
    if args.mock_policy:
        completions, metrics = run_mock_eval(eval_rows, args.mock_policy)
    else:
        completions, metrics = run_model_eval(eval_rows, args)
    summary = write_outputs(args.output_dir, completions, metrics, args)
    print(f"evaluate_checkpoint: wrote {args.output_dir / 'metrics.csv'}")
    print(f"evaluate_checkpoint: wrote {args.output_dir / 'summary.json'}")
    print(
        "evaluate_checkpoint: "
        f"label={summary['model_label']} variant={summary['prompt_variant']} "
        f"score={summary['overall_score']:.4f} cert={summary['certificate_success_rate']:.4f} "
        f"hidden={summary['hidden_regression_pass_rate']:.4f} invalid_json={summary['invalid_json_rate']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
