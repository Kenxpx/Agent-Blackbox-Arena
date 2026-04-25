from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from agent_blackbox.models import ALLOWED_FORBID_EFFECTS, ALLOWED_PRESERVE_CLAUSES, ALLOWED_REQUIRE_CLAUSES

DEFAULT_TRAIN_SEEDS = "0-59"
DEFAULT_EVAL_SEEDS = "1000-1014"


def parse_seed_spec(spec: str) -> list[int]:
    seeds: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            seeds.extend(range(int(start), int(end) + 1))
        else:
            seeds.append(int(part))
    return sorted(dict.fromkeys(seeds))


def strict_json_instruction() -> str:
    return (
        "Return only strict JSON with keys: evidence_spans, root_cause, patch, "
        "regression_tests, rationale. Do not include markdown. The patch object must "
        "contain require, forbid, and preserve arrays."
    )


def build_prompt(family: str, seed: int) -> str:
    incident, _ = generate_incident(family=family, seed=seed)
    public_payload = {
        "task": "Repair this failed agent trace with a bounded policy patch.",
        "family": incident.family,
        "incident_id": incident.incident_id,
        "scenario": incident.scenario,
        "public_trace_spans": incident.public_trace(),
        "candidate_root_causes": incident.candidate_root_causes,
        "allowed_patch_clauses": list(ALLOWED_REQUIRE_CLAUSES),
        "allowed_forbid_effects": list(ALLOWED_FORBID_EFFECTS),
        "allowed_preserve_clauses": list(ALLOWED_PRESERVE_CLAUSES),
        "instruction": strict_json_instruction(),
    }
    # This prompt intentionally contains only public trace information and allowed labels.
    # It does not include oracle fields, hidden variants, expected patches, or answer keys.
    return json.dumps(public_payload, indent=2, sort_keys=True)


def build_target(family: str, seed: int) -> dict[str, Any]:
    _, oracle = generate_incident(family=family, seed=seed)
    return {
        "evidence_spans": list(oracle.expected_evidence_spans),
        "root_cause": oracle.true_root_cause,
        "patch": {
            "require": list(oracle.answer_key_clause_ids),
            "forbid": list(oracle.expected_forbid_effects),
            "preserve": list(oracle.expected_preserve_clauses),
        },
        "regression_tests": [f"reg_{family}_block_failure", f"reg_{family}_preserve_valid"],
        "rationale": "The selected evidence shows the missing control before final action.",
    }


def build_records(split: str, seeds: Iterable[int]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for family in IMPLEMENTED_FAMILIES:
        for seed in seeds:
            records.append(
                {
                    "id": f"{split}_{family}_{seed:04d}",
                    "split": split,
                    "family": family,
                    "seed": seed,
                    "prompt": build_prompt(family, seed),
                    "target_json": build_target(family, seed),
                }
            )
    return records


def assert_prompt_has_no_hidden_answers(record: dict[str, Any]) -> None:
    prompt = record["prompt"]
    forbidden_terms = [
        "hidden_regression_variants",
        "hidden_valid_variants",
        "answer_key_clause_ids",
        "expected_patch",
        "oracle_score_details",
        "raw_seed",
        "hidden_span_labels",
    ]
    for term in forbidden_terms:
        if term in prompt:
            raise AssertionError(f"Prompt leaked hidden term: {term}")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def make_dataset(output_dir: Path, train_seeds: list[int], eval_seeds: list[int]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    train_records = build_records("train", train_seeds)
    eval_records = build_records("eval", eval_seeds)
    for record in [*train_records, *eval_records]:
        assert_prompt_has_no_hidden_answers(record)
    write_jsonl(output_dir / "train.jsonl", train_records)
    write_jsonl(output_dir / "eval.jsonl", eval_records)
    summary = {
        "schema": "agent_blackbox_single_turn_json_dataset_v1",
        "families": list(IMPLEMENTED_FAMILIES),
        "train_seeds": train_seeds,
        "eval_seeds": eval_seeds,
        "train_records": len(train_records),
        "eval_records": len(eval_records),
        "prompt_leakage_check": "passed",
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Agent BlackBox single-turn JSON repair-plan datasets.")
    parser.add_argument("--smoke", action="store_true", help="Generate a tiny CPU-only smoke dataset.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "training_dataset")
    parser.add_argument("--train-seeds", default=DEFAULT_TRAIN_SEEDS)
    parser.add_argument("--eval-seeds", default=DEFAULT_EVAL_SEEDS)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    train_seeds = parse_seed_spec("0-1" if args.smoke else args.train_seeds)
    eval_seeds = parse_seed_spec("1000" if args.smoke else args.eval_seeds)
    summary = make_dataset(args.output_dir, train_seeds, eval_seeds)
    print(f"make_dataset: wrote {args.output_dir / 'train.jsonl'}")
    print(f"make_dataset: wrote {args.output_dir / 'eval.jsonl'}")
    print(f"make_dataset: wrote {args.output_dir / 'dataset_summary.json'}")
    print(
        "make_dataset: "
        f"train_records={summary['train_records']} eval_records={summary['eval_records']} "
        f"families={','.join(summary['families'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
