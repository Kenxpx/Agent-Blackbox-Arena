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

from training.make_dataset import assert_prompt_has_no_hidden_answers, build_records, parse_seed_spec
from training.quality_gate import build_stoploss_report, fail_on_quality_errors, validate_sft_args, write_json
from training.train_json_grpo import namespace_to_jsonable, run_heldout_generation_eval

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def prompt_char_count(prompt: object) -> int:
    return len(json.dumps(prompt, ensure_ascii=False)) if not isinstance(prompt, str) else len(prompt)


def sft_completion_for_record(record: dict[str, Any]) -> list[dict[str, str]]:
    return [{"role": "assistant", "content": compact_json(record["target_json"])}]


def build_sft_records(split: str, seeds: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in build_records(split, seeds):
        assert_prompt_has_no_hidden_answers(record)
        rows.append(
            {
                "id": record["id"],
                "family": record["family"],
                "seed": int(record["seed"]),
                "prompt": record["prompt"],
                "completion": sft_completion_for_record(record),
            }
        )
    return rows


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def load_csv_rows(path: Path) -> list[dict[str, Any]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_smoke(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.dataset:
        source_records = load_jsonl(args.dataset)
        records = [
            {
                "id": record["id"],
                "family": record["family"],
                "seed": int(record["seed"]),
                "prompt": record["prompt"],
                "completion": sft_completion_for_record(record),
            }
            for record in source_records
        ]
    else:
        records = build_sft_records("train", parse_seed_spec("0"))

    preview_path = args.output_dir / "sft_samples.jsonl"
    with preview_path.open("w", encoding="utf-8") as handle:
        for record in records[:3]:
            handle.write(
                json.dumps(
                    {
                        "id": record["id"],
                        "prompt_chars": prompt_char_count(record["prompt"]),
                        "completion": record["completion"],
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    summary = {
        "mode": "smoke",
        "model": args.model,
        "records_seen": len(records),
        "max_steps": args.max_steps,
        "full_sft_ran": False,
        "dataset_format": "conversational_prompt_completion",
        "when_to_use": (
            "Use SFT warmstart only if the base model cannot reliably emit strict JSON; "
            "it is formatting warmup, not final RL evidence."
        ),
    }
    (args.output_dir / "sft_smoke_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"train_sft_warmstart: smoke wrote {preview_path}")
    print(f"train_sft_warmstart: smoke wrote {args.output_dir / 'sft_smoke_summary.json'}")
    print("train_sft_warmstart: full SFT not run in smoke mode")


def build_sft_config(SFTConfig: Any, args: argparse.Namespace) -> Any:
    config_kwargs = {
        "output_dir": str(args.output_dir),
        "learning_rate": args.learning_rate,
        "max_steps": args.max_steps,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "gradient_checkpointing": args.gradient_checkpointing,
        "max_length": args.max_length,
        "logging_steps": args.logging_steps,
        "save_steps": args.save_steps,
        "completion_only_loss": True,
        "packing": False,
        "report_to": [],
    }
    accepted = set(inspect.signature(SFTConfig).parameters)
    return SFTConfig(**{key: value for key, value in config_kwargs.items() if key in accepted})


def maybe_lora_config(args: argparse.Namespace) -> Any | None:
    if not args.use_lora:
        return None
    from peft import LoraConfig, TaskType  # type: ignore

    target_modules = [module.strip() for module in args.lora_target_modules.split(",") if module.strip()]
    return LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules or None,
    )


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


def make_sft_trainer(SFTTrainer: Any, model: Any, tokenizer: Any, config: Any, train_dataset: Any, eval_dataset: Any, peft_config: Any) -> Any:
    trainer_kwargs = {
        "model": model,
        "args": config,
        "train_dataset": train_dataset,
        "eval_dataset": eval_dataset,
        "peft_config": peft_config,
    }
    try:
        return SFTTrainer(**trainer_kwargs, processing_class=tokenizer)
    except TypeError:
        return SFTTrainer(**trainer_kwargs, tokenizer=tokenizer)


def run_full_sft(args: argparse.Namespace) -> None:
    fail_on_quality_errors(validate_sft_args(args), "SFT")
    if not args.confirm_real_training:
        raise RuntimeError(
            "Refusing to start paid-capable SFT without --confirm-real-training. "
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

    from datasets import Dataset  # type: ignore
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    from trl import SFTConfig, SFTTrainer  # type: ignore

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        args.output_dir / "run_config.json",
        {
            "mode": "real_sft_warmstart",
            "args": namespace_to_jsonable(args),
            "quality_gate": "passed_before_model_load",
            "source": "training/train_sft_warmstart.py",
        },
    )
    train_rows = build_sft_records("train", parse_seed_spec(args.train_seeds))
    eval_rows = build_sft_records("eval", parse_seed_spec(args.eval_seeds))
    write_jsonl(args.output_dir / "train_sft.jsonl", train_rows)
    write_jsonl(args.output_dir / "eval_sft.jsonl", eval_rows)

    train_dataset = Dataset.from_list([{"prompt": row["prompt"], "completion": row["completion"]} for row in train_rows])
    eval_dataset = Dataset.from_list([{"prompt": row["prompt"], "completion": row["completion"]} for row in eval_rows])

    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model_kwargs = {"trust_remote_code": True, "device_map": "auto"}
    if args.torch_dtype != "none":
        model_kwargs["torch_dtype"] = torch_dtype_arg(args.torch_dtype)
    model = AutoModelForCausalLM.from_pretrained(args.model, **model_kwargs)
    if tokenizer.pad_token_id is not None:
        model.config.pad_token_id = tokenizer.pad_token_id

    config = build_sft_config(SFTConfig, args)
    trainer = make_sft_trainer(
        SFTTrainer,
        model,
        tokenizer,
        config,
        train_dataset,
        eval_dataset,
        maybe_lora_config(args),
    )
    train_result = trainer.train()
    trainer_metrics = dict(getattr(train_result, "metrics", {}) or {})
    trainer.save_model(str(args.output_dir / "model"))
    tokenizer.save_pretrained(str(args.output_dir / "model"))

    summary = {
        "mode": "real_sft_warmstart",
        "model": args.model,
        "train_records": len(train_rows),
        "eval_records": len(eval_rows),
        "max_steps": args.max_steps,
        "use_lora": bool(args.use_lora),
        "trainer_metrics": trainer_metrics,
        "note": "SFT warmstart teaches strict JSON format only; final claims require verifier-scored GRPO or held-out verifier metrics.",
    }
    (args.output_dir / "sft_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    eval_generation_rows = [
        {"prompt": row["prompt"], "family": row["family"], "seed": int(row["seed"]), "id": row["id"]}
        for row in eval_rows
    ]
    generation_args = argparse.Namespace(
        output_dir=args.output_dir,
        max_prompt_length=args.max_prompt_length,
        max_completion_length=args.max_completion_length,
    )
    heldout_summary = run_heldout_generation_eval(trainer.model, tokenizer, eval_generation_rows, generation_args)
    heldout_rows = load_csv_rows(args.output_dir / "heldout_eval_metrics.csv")
    quality_report = build_stoploss_report(
        heldout_rows,
        heldout_summary=heldout_summary,
        trainer_metrics=trainer_metrics,
        mode="sft_warmstart",
    )
    quality_report["sft_claim_boundary"] = (
        "SFT is a strict-JSON warmstart. Treat PASS as formatting readiness, not final RL improvement."
    )
    write_json(args.output_dir / "sft_quality_report.json", quality_report)

    print(f"train_sft_warmstart: real SFT wrote {args.output_dir / 'sft_summary.json'}")
    print(f"train_sft_warmstart: real SFT wrote {args.output_dir / 'model'}")
    print(f"train_sft_warmstart: held-out verifier summary {args.output_dir / 'heldout_eval_summary.json'}")
    print(f"train_sft_warmstart: quality_status={quality_report['status']}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lightweight SFT warmstart for strict JSON repair formatting.")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--confirm-real-training", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "sft")
    parser.add_argument("--max-steps", type=int, default=20)
    parser.add_argument("--train-seeds", default="0-5")
    parser.add_argument("--eval-seeds", default="1000-1002")
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument("--torch-dtype", choices=["auto", "float16", "bfloat16", "float32", "none"], default="auto")
    parser.add_argument("--max-length", type=int, default=1400)
    parser.add_argument("--max-prompt-length", type=int, default=1024)
    parser.add_argument("--max-completion-length", type=int, default=160)
    parser.add_argument("--logging-steps", type=int, default=1)
    parser.add_argument("--save-steps", type=int, default=20)
    parser.add_argument("--use-lora", action="store_true")
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-target-modules", default="q_proj,k_proj,v_proj,o_proj")
    parser.add_argument("--use-unsloth", action="store_true")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.smoke:
        run_smoke(args)
        return 0
    run_full_sft(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
