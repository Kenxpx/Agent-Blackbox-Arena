from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.make_dataset import build_records, parse_seed_spec

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def prompt_char_count(prompt: object) -> int:
    return len(json.dumps(prompt, ensure_ascii=False)) if not isinstance(prompt, str) else len(prompt)


def run_smoke(args: argparse.Namespace) -> None:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.dataset:
        records = load_jsonl(args.dataset)
    else:
        records = build_records("train", parse_seed_spec("0"))
    preview_path = args.output_dir / "sft_samples.jsonl"
    with preview_path.open("w", encoding="utf-8") as handle:
        for record in records[:3]:
            handle.write(
                json.dumps(
                    {
                        "id": record["id"],
                        "prompt_chars": prompt_char_count(record["prompt"]),
                        "target": record["target_json"],
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
        "when_to_use": (
            "Use SFT warmstart only if the base model cannot reliably emit strict JSON; "
            "it is formatting scaffolding, not the final RL evidence."
        ),
    }
    (args.output_dir / "sft_smoke_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"train_sft_warmstart: smoke wrote {preview_path}")
    print(f"train_sft_warmstart: smoke wrote {args.output_dir / 'sft_smoke_summary.json'}")
    print("train_sft_warmstart: full SFT not run in smoke mode")


def run_full_sft_scaffold(args: argparse.Namespace) -> None:
    # Use this only when invalid JSON is high enough to block GRPO reward learning.
    # Keep the dataset small and focused on schema/format; do not claim SFT as RL improvement.
    from trl import SFTTrainer  # type: ignore

    if args.use_unsloth:
        import unsloth  # type: ignore  # noqa: F401

    _ = SFTTrainer
    raise RuntimeError(
        "Gate 4 intentionally does not run full SFT. Use --smoke now; enable this path only if GRPO needs format warmup."
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lightweight SFT warmstart scaffold for JSON repair formatting.")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "sft")
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--use-unsloth", action="store_true")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    if args.smoke:
        run_smoke(args)
        return 0
    run_full_sft_scaffold(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
