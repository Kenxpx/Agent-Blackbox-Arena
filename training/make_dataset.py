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

LABEL_GLOSSARY = {
    "fresh_context_check": "verify retrieved context freshness before a final action",
    "verify_before_irreversible_action": "verify information before irreversible or high-impact action",
    "role_tool_scope_match": "check that user role, task, and tool permission scope match",
    "include_constraints_in_handoff": "carry constraints through an agent handoff",
    "retry_budget_cap": "limit repeated retries",
    "final_action_check": "gate the final action with the relevant safety control",
    "act_on_stale_context": "final action taken from expired or stale context",
    "irreversible_action_without_verification": "irreversible action taken from unverified information",
    "out_of_scope_tool_call": "tool call outside the user role or task permission scope",
    "constraint_dropped_in_handoff": "handoff loses task constraints",
    "unbounded_retry_loop": "agent retries without a bounded stop rule",
    "final_action_without_check": "final action happens without the required check",
    "valid_fresh_context_flow": "preserve actions where context was refreshed before use",
    "verified_action_flow": "preserve actions where verification happened before action",
    "authorized_tool_flow": "preserve actions where the selected tool is authorized",
    "valid_handoff_flow": "preserve handoffs that retain required constraints",
}

FAMILY_CANDIDATE_LABELS = {
    "stale_retrieval": {
        "require": ["fresh_context_check", "final_action_check", "verify_before_irreversible_action"],
        "forbid": ["act_on_stale_context", "irreversible_action_without_verification", "out_of_scope_tool_call"],
        "preserve": ["valid_fresh_context_flow", "verified_action_flow", "authorized_tool_flow"],
    },
    "missing_verification": {
        "require": ["verify_before_irreversible_action", "final_action_check", "fresh_context_check"],
        "forbid": ["irreversible_action_without_verification", "act_on_stale_context", "out_of_scope_tool_call"],
        "preserve": ["verified_action_flow", "valid_fresh_context_flow", "authorized_tool_flow"],
    },
    "permission_scope": {
        "require": ["role_tool_scope_match", "final_action_check", "verify_before_irreversible_action"],
        "forbid": ["out_of_scope_tool_call", "irreversible_action_without_verification", "act_on_stale_context"],
        "preserve": ["authorized_tool_flow", "verified_action_flow", "valid_fresh_context_flow"],
    },
}


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
        "Return ONLY valid JSON. No markdown. No prose. No commentary. English only. "
        "Do not mention incident IDs. Do not invent labels. "
        "Start with { and end with }. Use exactly these top-level keys: "
        "evidence_spans, root_cause, patch, regression_tests, rationale. The patch object "
        "must contain require, forbid, and preserve arrays."
    )


def system_prompt() -> str:
    return (
        "You are Agent BlackBox JSON Repair Planner. "
        "You output one strict JSON object for an agent reliability repair plan."
    )


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def candidate_labels_for_family(family: str) -> dict[str, list[str]]:
    if family not in FAMILY_CANDIDATE_LABELS:
        raise ValueError(f"unknown family for candidate labels: {family}")
    labels = FAMILY_CANDIDATE_LABELS[family]
    if any(label not in ALLOWED_REQUIRE_CLAUSES for label in labels["require"]):
        raise AssertionError("candidate require label is not allowed")
    if any(label not in ALLOWED_FORBID_EFFECTS for label in labels["forbid"]):
        raise AssertionError("candidate forbid label is not allowed")
    if any(label not in ALLOWED_PRESERVE_CLAUSES for label in labels["preserve"]):
        raise AssertionError("candidate preserve label is not allowed")
    return {key: list(value) for key, value in labels.items()}


def glossary_for(labels: dict[str, list[str]]) -> dict[str, str]:
    selected = sorted({label for values in labels.values() for label in values})
    return {label: LABEL_GLOSSARY[label] for label in selected}


def prompt_text_for_incident(family: str, seed: int) -> str:
    incident, _ = generate_incident(family=family, seed=seed)
    labels = candidate_labels_for_family(incident.family)
    trace_lines = [
        f"- {span['span_id']} {span['span_type']}: {span['summary']}"
        for span in incident.public_trace()
    ]
    return f"""{strict_json_instruction()}

Episode:
family: {incident.family}
scenario: {incident.scenario}

trace:
{chr(10).join(trace_lines)}

Choose only from these candidates:
root_cause: {compact_json(incident.candidate_root_causes)}
require: {compact_json(labels["require"])}
forbid: {compact_json(labels["forbid"])}
preserve: {compact_json(labels["preserve"])}
label_glossary: {compact_json(glossary_for(labels))}

Output requirements:
- evidence_spans: trace span IDs only
- root_cause: exactly one candidate root cause
- patch.require, patch.forbid, patch.preserve: allowed labels only
- regression_tests: short test names for blocking the failure and preserving valid behavior
- rationale: one short English sentence based on evidence spans

Now return the JSON object only.
"""


def build_prompt(family: str, seed: int) -> list[dict[str, str]]:
    # TRL supports conversational prompt records. For Qwen Instruct models this
    # lets the trainer apply the model's chat template instead of treating the
    # instruction as raw pretraining text. The content contains only public trace
    # information and allowed labels, never hidden variants or answer keys.
    return [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": prompt_text_for_incident(family, seed)},
    ]


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
    prompt = json.dumps(record["prompt"], ensure_ascii=False)
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
