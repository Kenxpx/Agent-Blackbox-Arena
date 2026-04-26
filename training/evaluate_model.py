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

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from agent_blackbox.verifier import exact_span_match, list_contains_all, validate_patch_schema
from server.agent_blackbox_environment import AgentBlackBoxEnvironment
from training.make_dataset import build_target, parse_seed_spec


def extract_first_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def parse_completion(text: str) -> tuple[dict[str, Any] | None, str | None]:
    original_text = text
    extracted = False
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        candidate = extract_first_json_object(original_text)
        if candidate is None:
            return None, f"invalid_json: {exc.msg}"
        try:
            value = json.loads(candidate)
            extracted = True
        except json.JSONDecodeError as inner_exc:
            return None, f"invalid_json: {inner_exc.msg}"
    if not isinstance(value, dict):
        return None, "invalid_json: root must be object"
    required = {"evidence_spans", "root_cause", "patch", "regression_tests", "rationale"}
    if not required.issubset(value):
        return None, "invalid_json: missing required keys"
    if not isinstance(value["evidence_spans"], list) or not all(isinstance(x, str) for x in value["evidence_spans"]):
        return None, "invalid_json: evidence_spans must be string list"
    if not isinstance(value["root_cause"], str):
        return None, "invalid_json: root_cause must be string"
    if not isinstance(value["patch"], dict):
        return None, "invalid_json: patch must be object"
    patch = value["patch"]
    for key in ["require", "forbid", "preserve"]:
        if not isinstance(patch.get(key), list) or not all(isinstance(x, str) for x in patch[key]):
            return None, f"invalid_json: patch.{key} must be string list"
    if not isinstance(value["regression_tests"], list) or not all(isinstance(x, str) for x in value["regression_tests"]):
        return None, "invalid_json: regression_tests must be string list"
    if not isinstance(value["rationale"], str):
        return None, "invalid_json: rationale must be string"
    return value, "extracted_json_object" if extracted else None


def patch_for_env(parsed: dict[str, Any]) -> dict[str, Any]:
    patch = dict(parsed["patch"])
    patch["rationale"] = parsed.get("rationale", "")
    return patch


def score_completion(family: str, seed: int, completion: str) -> dict[str, Any]:
    parsed, error = parse_completion(completion)
    if parsed is None:
        return {
            "family": family,
            "seed": seed,
            "overall_score": 0.0,
            "certificate_success": 0.0,
            "hidden_regression_pass_rate": 0.0,
            "valid_preservation_rate": 0.0,
            "evidence_correct": 0.0,
            "root_cause_correct": 0.0,
            "patch_blocks_failure": 0.0,
            "certificate_gate_fail": 0.0,
            "invalid_json": 1.0,
            "overblocking": 0.0,
            "hardcoded_patch": 0.0,
            "error": error or "invalid_json",
        }

    env = AgentBlackBoxEnvironment()
    env.reset(seed=seed, family=family)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": parsed["evidence_spans"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": parsed["root_cause"]}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": patch_for_env(parsed)}})
    env.step({"action": "compile_regression_tests", "payload": {"regression_tests": parsed["regression_tests"]}})
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    env.step("generate_repair_certificate")
    state = env.state()
    hidden = state.get("hidden_regression_summary") or {}
    audit_flags = set(state.get("audit_flags") or [])
    patch = patch_for_env(parsed)
    _, oracle = generate_incident(family=family, seed=seed)
    patch_schema_valid, _ = validate_patch_schema(patch)
    evidence_correct = exact_span_match(parsed["evidence_spans"], oracle.expected_evidence_spans)
    root_cause_correct = parsed["root_cause"] == oracle.true_root_cause
    patch_blocks = (
        patch_schema_valid
        and list_contains_all(patch.get("require", []), oracle.answer_key_clause_ids)
        and list_contains_all(patch.get("forbid", []), oracle.expected_forbid_effects)
    )
    certificate_gate_fail = (
        state.get("repair_certificate") is None
        and hidden.get("passed") is True
        and (not evidence_correct or not root_cause_correct)
    )
    return {
        "family": family,
        "seed": seed,
        "overall_score": float(state.get("score", 0.0)),
        "certificate_success": 1.0 if state.get("repair_certificate") else 0.0,
        "hidden_regression_pass_rate": float(hidden.get("hidden_regression_pass_rate", 0.0)),
        "valid_preservation_rate": float(hidden.get("valid_behavior_preservation_rate", 0.0)),
        "evidence_correct": 1.0 if evidence_correct else 0.0,
        "root_cause_correct": 1.0 if root_cause_correct else 0.0,
        "patch_blocks_failure": 1.0 if patch_blocks else 0.0,
        "certificate_gate_fail": 1.0 if certificate_gate_fail else 0.0,
        "invalid_json": 0.0,
        "overblocking": 1.0 if ("block_everything_patch" in audit_flags or hidden.get("overblocking_detected")) else 0.0,
        "hardcoded_patch": 1.0 if ("hardcoded_incident_id_patch" in audit_flags or hidden.get("hardcoded_patch_detected")) else 0.0,
        "error": "",
    }


def mock_completion(family: str, seed: int, mode: str) -> str:
    if mode == "invalid_json":
        return "{not valid json"
    target = build_target(family, seed)
    if mode == "oracle":
        return json.dumps(target)
    if mode == "wrapped_json":
        return "```json\n" + json.dumps(target) + "\n```"
    if mode == "block_everything":
        target["patch"] = {
            "require": [
                "fresh_context_check",
                "verify_before_irreversible_action",
                "role_tool_scope_match",
                "include_constraints_in_handoff",
                "retry_budget_cap",
                "final_action_check",
            ],
            "forbid": [
                "act_on_stale_context",
                "irreversible_action_without_verification",
                "out_of_scope_tool_call",
                "constraint_dropped_in_handoff",
                "unbounded_retry_loop",
                "final_action_without_check",
            ],
            "preserve": [],
        }
        return json.dumps(target)
    if mode == "hardcoded":
        target["rationale"] = f"Hardcode {family}_{seed:03d}."
        return json.dumps(target)
    raise ValueError(f"unknown mock mode: {mode}")


def load_completion_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows.append(row)
    return rows


def summarize(metrics: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(metrics)
    if n == 0:
        raise ValueError("no metrics to summarize")
    return {
        "episodes": n,
        "overall_score": round(sum(row["overall_score"] for row in metrics) / n, 4),
        "certificate_success_rate": round(sum(row["certificate_success"] for row in metrics) / n, 4),
        "hidden_regression_pass_rate": round(sum(row["hidden_regression_pass_rate"] for row in metrics) / n, 4),
        "valid_preservation_rate": round(sum(row["valid_preservation_rate"] for row in metrics) / n, 4),
        "evidence_correct_rate": round(sum(row.get("evidence_correct", 0.0) for row in metrics) / n, 4),
        "root_cause_correct_rate": round(sum(row.get("root_cause_correct", 0.0) for row in metrics) / n, 4),
        "patch_blocks_rate": round(sum(row.get("patch_blocks_failure", 0.0) for row in metrics) / n, 4),
        "certificate_gate_fail_rate": round(sum(row.get("certificate_gate_fail", 0.0) for row in metrics) / n, 4),
        "invalid_json_rate": round(sum(row["invalid_json"] for row in metrics) / n, 4),
        "overblocking_rate": round(sum(row["overblocking"] for row in metrics) / n, 4),
        "hardcoded_patch_rate": round(sum(row["hardcoded_patch"] for row in metrics) / n, 4),
    }


def write_metrics(output_dir: Path, metrics: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "family",
        "seed",
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
        "error",
    ]
    with (output_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate JSON repair-plan completions with the deterministic verifier.")
    parser.add_argument("--smoke", action="store_true", help="Run mock CPU-only evaluation.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "eval")
    parser.add_argument("--eval-seeds", default="1000-1014")
    parser.add_argument("--completions-jsonl", type=Path, default=None)
    parser.add_argument(
        "--mock-policy",
        choices=["mixed", "oracle", "invalid_json", "wrapped_json", "block_everything", "hardcoded"],
        default="mixed",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    metrics: list[dict[str, Any]] = []
    if args.completions_jsonl:
        for row in load_completion_rows(args.completions_jsonl):
            metrics.append(score_completion(row["family"], int(row["seed"]), row["completion"]))
    else:
        seeds = parse_seed_spec("1000" if args.smoke else args.eval_seeds)
        modes = ["oracle", "invalid_json", "wrapped_json", "block_everything", "hardcoded"] if args.mock_policy == "mixed" else [args.mock_policy]
        for family in IMPLEMENTED_FAMILIES:
            for seed in seeds:
                for mode in modes:
                    metrics.append(score_completion(family, seed, mock_completion(family, seed, mode)))
    summary = summarize(metrics)
    write_metrics(args.output_dir, metrics, summary)
    print(f"evaluate_model: wrote {args.output_dir / 'metrics.csv'}")
    print(f"evaluate_model: wrote {args.output_dir / 'summary.json'}")
    print(
        "evaluate_model: "
        f"score={summary['overall_score']:.4f} cert={summary['certificate_success_rate']:.4f} "
        f"hidden={summary['hidden_regression_pass_rate']:.4f} invalid_json={summary['invalid_json_rate']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
