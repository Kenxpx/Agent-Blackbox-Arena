from __future__ import annotations

import csv
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, ROOT_CAUSES, generate_incident
from agent_blackbox.models import ALLOWED_FORBID_EFFECTS, ALLOWED_PRESERVE_CLAUSES, ALLOWED_REQUIRE_CLAUSES
from server.agent_blackbox_environment import AgentBlackBoxEnvironment

SEEDS = list(range(10))
OUTPUT_DIR = ROOT / "outputs"
RESULTS_CSV = OUTPUT_DIR / "results.csv"
SUMMARY_JSON = OUTPUT_DIR / "baseline_summary.json"


def family_spec(family: str, seed: int) -> dict[str, Any]:
    _, oracle = generate_incident(family=family, seed=seed)
    return {
        "root_cause": oracle.true_root_cause,
        "wrong_root_cause": next(root for root in ROOT_CAUSES if root != oracle.true_root_cause),
        "evidence_spans": list(oracle.expected_evidence_spans),
        "correct_patch": {
            "require": list(oracle.answer_key_clause_ids),
            "forbid": list(oracle.expected_forbid_effects),
            "preserve": list(oracle.expected_preserve_clauses),
            "rationale": f"Apply {oracle.true_root_cause} controls before final action.",
        },
        "incident_id": f"{family}_{seed:03d}",
    }


def block_everything_patch() -> dict[str, Any]:
    return {
        "require": list(ALLOWED_REQUIRE_CLAUSES),
        "forbid": list(ALLOWED_FORBID_EFFECTS),
        "preserve": [],
        "rationale": "Block every risky behavior instead of preserving valid flows.",
    }


def deterministic_random_patch(family: str, seed: int) -> tuple[str, dict[str, Any]]:
    spec = family_spec(family, seed)
    rng = random.Random(f"{family}:{seed}:random_patch")
    wrong_roots = [root for root in ROOT_CAUSES if root != spec["root_cause"]]
    require = rng.sample(ALLOWED_REQUIRE_CLAUSES, k=2)
    forbid = rng.sample(ALLOWED_FORBID_EFFECTS, k=1)
    preserve = rng.sample(ALLOWED_PRESERVE_CLAUSES, k=1)
    # Keep this baseline weak even if random sampling accidentally touched one correct clause.
    if set(require) == set(spec["correct_patch"]["require"]):
        require = ["retry_budget_cap", "final_action_check"]
    if forbid == spec["correct_patch"]["forbid"]:
        forbid = ["unbounded_retry_loop"]
    if preserve == spec["correct_patch"]["preserve"]:
        preserve = ["valid_handoff_flow"]
    return rng.choice(wrong_roots), {
        "require": require,
        "forbid": forbid,
        "preserve": preserve,
        "rationale": "Deterministic pseudo-random weak repair policy.",
    }


def visible_overfit_patch(family: str, seed: int) -> tuple[str, dict[str, Any]]:
    spec = family_spec(family, seed)
    patch = dict(spec["correct_patch"])
    patch["rationale"] = (
        f"Overfit to visible incident {spec['incident_id']} instead of learning a general repair rule."
    )
    return spec["root_cause"], patch


def run_repair_policy(
    family: str,
    seed: int,
    root_cause: str,
    patch: dict[str, Any] | None,
    evidence_spans: list[str],
    run_verifiers: bool = True,
    try_certificate: bool = True,
) -> dict[str, Any]:
    env = AgentBlackBoxEnvironment()
    env.reset(seed=seed, family=family)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": evidence_spans}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": root_cause}})
    if patch is not None:
        env.step({"action": "propose_repair_patch", "payload": {"patch": patch}})
        env.step(
            {
                "action": "compile_regression_tests",
                "payload": {"regression_tests": [f"reg_{family}_block_failure", f"reg_{family}_preserve_valid"]},
            }
        )
        if run_verifiers:
            env.step("run_visible_replay")
            env.step("run_hidden_regressions")
    if try_certificate:
        env.step("generate_repair_certificate")
    return env.state()


def run_explanation_only(family: str, seed: int) -> dict[str, Any]:
    spec = family_spec(family, seed)
    return run_repair_policy(
        family=family,
        seed=seed,
        root_cause=spec["root_cause"],
        patch=None,
        evidence_spans=spec["evidence_spans"],
        run_verifiers=False,
        try_certificate=False,
    )


def run_random_patch(family: str, seed: int) -> dict[str, Any]:
    spec = family_spec(family, seed)
    root_cause, patch = deterministic_random_patch(family, seed)
    return run_repair_policy(family, seed, root_cause, patch, spec["evidence_spans"])


def run_block_everything(family: str, seed: int) -> dict[str, Any]:
    spec = family_spec(family, seed)
    return run_repair_policy(family, seed, spec["root_cause"], block_everything_patch(), spec["evidence_spans"])


def run_visible_overfit(family: str, seed: int) -> dict[str, Any]:
    spec = family_spec(family, seed)
    root_cause, patch = visible_overfit_patch(family, seed)
    return run_repair_policy(family, seed, root_cause, patch, spec["evidence_spans"])


def run_oracle_correct_solver(family: str, seed: int) -> dict[str, Any]:
    spec = family_spec(family, seed)
    return run_repair_policy(family, seed, spec["root_cause"], spec["correct_patch"], spec["evidence_spans"])


BASELINES: dict[str, Callable[[str, int], dict[str, Any]]] = {
    "random_patch": run_random_patch,
    "explanation_only": run_explanation_only,
    "block_everything": run_block_everything,
    "visible_overfit": run_visible_overfit,
    "oracle_correct_solver_for_sanity": run_oracle_correct_solver,
}


def metrics_from_state(state: dict[str, Any]) -> dict[str, Any]:
    hidden = state.get("hidden_regression_summary") or {}
    audit_flags = set(state.get("audit_flags") or [])
    certificate = state.get("repair_certificate")
    return {
        "overall_score": float(state.get("score", 0.0)),
        "certificate_success": 1.0 if certificate else 0.0,
        "hidden_regression_pass_rate": float(hidden.get("hidden_regression_pass_rate", 0.0)),
        "valid_preservation_rate": float(hidden.get("valid_behavior_preservation_rate", 0.0)),
        "overblocking": 1.0 if ("block_everything_patch" in audit_flags or hidden.get("overblocking_detected")) else 0.0,
        "hardcoded_patch": 1.0 if ("hardcoded_incident_id_patch" in audit_flags or hidden.get("hardcoded_patch_detected")) else 0.0,
        "invalid_json": 1.0 if "invalid_json" in audit_flags else 0.0,
        "audit_flags": ";".join(sorted(audit_flags)),
    }


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["baseline"]].append(row)

    summary: dict[str, Any] = {
        "schema": "agent_blackbox_baseline_summary_v1",
        "families": list(IMPLEMENTED_FAMILIES),
        "seeds": SEEDS,
        "baselines": {},
    }
    metric_keys = [
        "overall_score",
        "certificate_success",
        "hidden_regression_pass_rate",
        "valid_preservation_rate",
        "overblocking",
        "hardcoded_patch",
        "invalid_json",
    ]
    for baseline, baseline_rows in grouped.items():
        summary["baselines"][baseline] = {
            "episodes": len(baseline_rows),
            "overall_score": round(sum(float(row["overall_score"]) for row in baseline_rows) / len(baseline_rows), 4),
            "certificate_success_rate": round(
                sum(float(row["certificate_success"]) for row in baseline_rows) / len(baseline_rows), 4
            ),
            "hidden_regression_pass_rate": round(
                sum(float(row["hidden_regression_pass_rate"]) for row in baseline_rows) / len(baseline_rows), 4
            ),
            "valid_preservation_rate": round(
                sum(float(row["valid_preservation_rate"]) for row in baseline_rows) / len(baseline_rows), 4
            ),
            "overblocking_rate": round(sum(float(row["overblocking"]) for row in baseline_rows) / len(baseline_rows), 4),
            "hardcoded_patch_rate": round(
                sum(float(row["hardcoded_patch"]) for row in baseline_rows) / len(baseline_rows), 4
            ),
            "invalid_json_rate": round(sum(float(row["invalid_json"]) for row in baseline_rows) / len(baseline_rows), 4),
        }
        for key in metric_keys:
            assert key in baseline_rows[0]
    return summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    fieldnames = [
        "baseline",
        "family",
        "seed",
        "overall_score",
        "certificate_success",
        "hidden_regression_pass_rate",
        "valid_preservation_rate",
        "overblocking",
        "hardcoded_patch",
        "invalid_json",
        "audit_flags",
    ]
    with RESULTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def assert_expected_behavior(summary: dict[str, Any]) -> None:
    baselines = summary["baselines"]
    assert baselines["oracle_correct_solver_for_sanity"]["overall_score"] >= 0.9
    assert baselines["oracle_correct_solver_for_sanity"]["certificate_success_rate"] == 1.0
    assert baselines["random_patch"]["overall_score"] < 0.5
    assert baselines["explanation_only"]["overall_score"] <= 0.35
    assert baselines["explanation_only"]["certificate_success_rate"] == 0.0
    assert baselines["block_everything"]["overall_score"] <= 0.55
    assert baselines["block_everything"]["overblocking_rate"] == 1.0
    assert baselines["visible_overfit"]["hardcoded_patch_rate"] == 1.0
    assert baselines["visible_overfit"]["hidden_regression_pass_rate"] == 0.0


def main() -> int:
    rows: list[dict[str, Any]] = []
    for baseline_name, runner in BASELINES.items():
        for family in IMPLEMENTED_FAMILIES:
            for seed in SEEDS:
                state = runner(family, seed)
                row = {
                    "baseline": baseline_name,
                    "family": family,
                    "seed": seed,
                    **metrics_from_state(state),
                }
                rows.append(row)

    summary = aggregate(rows)
    assert_expected_behavior(summary)
    write_outputs(rows, summary)

    print(f"evaluate_baselines: wrote {RESULTS_CSV.relative_to(ROOT)}")
    print(f"evaluate_baselines: wrote {SUMMARY_JSON.relative_to(ROOT)}")
    for baseline, metrics in summary["baselines"].items():
        print(
            "evaluate_baselines: "
            f"{baseline} score={metrics['overall_score']:.4f} "
            f"cert={metrics['certificate_success_rate']:.4f} "
            f"hidden={metrics['hidden_regression_pass_rate']:.4f} "
            f"valid={metrics['valid_preservation_rate']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
