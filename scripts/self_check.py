from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from agent_blackbox.models import FORBIDDEN_PUBLIC_KEYS
from server.agent_blackbox_environment import AgentBlackBoxEnvironment

OUTPUT_DIR = ROOT / "outputs"
RESULTS_CSV = OUTPUT_DIR / "results.csv"
SUMMARY_JSON = OUTPUT_DIR / "baseline_summary.json"
REQUIRED_PLOTS = [
    OUTPUT_DIR / "baseline_scores.png",
    OUTPUT_DIR / "certificate_success_rate.png",
    OUTPUT_DIR / "hidden_regression_pass_rate.png",
    OUTPUT_DIR / "valid_preservation_rate.png",
]
TRAINING_SMOKE_DIR = OUTPUT_DIR / "training_smoke"
GRPO_SMOKE_DIR = OUTPUT_DIR / "grpo_smoke"
EVAL_SMOKE_DIR = OUTPUT_DIR / "eval_smoke"
SFT_SMOKE_DIR = OUTPUT_DIR / "sft_smoke"
DOCS_REQUIRED = [
    ROOT / "README.md",
    ROOT / "BENCHMARK_SPEC.md",
    ROOT / "TRAINING.md",
    ROOT / "SAFETY.md",
    ROOT / "SUBMISSION_READY.md",
    ROOT / "openenv.yaml",
    ROOT / "Dockerfile",
    ROOT / "requirements.txt",
    ROOT / "pyproject.toml",
]


BLOCK_EVERYTHING_PATCH = {
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
    "rationale": "Block every risky behavior.",
}


def family_spec(family: str) -> dict[str, Any]:
    _, oracle = generate_incident(family=family, seed=42)
    return {
        "family": family,
        "root_cause": oracle.true_root_cause,
        "evidence_spans": list(oracle.expected_evidence_spans),
        "correct_patch": {
            "require": list(oracle.answer_key_clause_ids),
            "forbid": list(oracle.expected_forbid_effects),
            "preserve": list(oracle.expected_preserve_clauses),
            "rationale": f"Apply {oracle.true_root_cause} controls before final action.",
        },
    }


def assert_no_hidden_leak(value: Any) -> None:
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, nested in item.items():
                assert key not in FORBIDDEN_PUBLIC_KEYS, f"hidden key leaked into public observation: {key}"
                walk(nested)
        elif isinstance(item, list):
            for nested in item:
                walk(nested)
        elif isinstance(item, str):
            for key in FORBIDDEN_PUBLIC_KEYS:
                assert item != key, f"hidden sentinel leaked into public observation: {key}"

    walk(value)


def run_correct_trajectory(env: AgentBlackBoxEnvironment, family: str) -> dict[str, Any]:
    spec = family_spec(family)
    env.reset(seed=42, family=family)
    assert_no_hidden_leak(env.state())
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": spec["evidence_spans"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": spec["root_cause"]}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": spec["correct_patch"]}})
    env.step(
        {
            "action": "compile_regression_tests",
            "payload": {"regression_tests": [f"reg_{family}_block_failure", f"reg_{family}_preserve_valid"]},
        }
    )
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    env.step("generate_repair_certificate")
    state = env.state()
    assert_no_hidden_leak(state)
    return state


def run_bad_patch(family: str, patch: dict[str, Any], root_cause: str | None = None) -> dict[str, Any]:
    spec = family_spec(family)
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42, family=family)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": spec["evidence_spans"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": root_cause or spec["root_cause"]}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": patch}})
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    return env.state()


def write_examples(state: dict[str, Any]) -> None:
    examples_dir = ROOT / "examples"
    examples_dir.mkdir(exist_ok=True)
    trace_payload = {
        "incident_id": state["incident_id"],
        "family": state["family"],
        "scenario": state["scenario"],
        "public_trace_spans": state["public_trace_spans"],
        "correct_patch": family_spec("stale_retrieval")["correct_patch"],
    }
    (examples_dir / "stale_retrieval_demo_trace.json").write_text(
        json.dumps(trace_payload, indent=2) + "\n", encoding="utf-8"
    )
    (examples_dir / "certificate_example.json").write_text(
        json.dumps(state["repair_certificate"], indent=2) + "\n", encoding="utf-8"
    )


def assert_hidden_summary_is_aggregate(state: dict[str, Any]) -> None:
    hidden_summary = state["hidden_regression_summary"]
    assert set(hidden_summary) == {
        "hidden_failed_variants_blocked",
        "hidden_failed_variant_count",
        "hidden_valid_variants_preserved",
        "hidden_valid_variant_count",
        "hidden_regression_pass_rate",
        "valid_behavior_preservation_rate",
        "overblocking_detected",
        "hardcoded_patch_detected",
        "passed",
    }


def run_gate3_baseline_checks() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "evaluate_baselines.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_plots.py")], cwd=ROOT, check=True)

    assert RESULTS_CSV.exists(), "outputs/results.csv missing"
    assert SUMMARY_JSON.exists(), "outputs/baseline_summary.json missing"
    for plot in REQUIRED_PLOTS:
        assert plot.exists(), f"{plot.name} missing"
        assert plot.stat().st_size > 0, f"{plot.name} is empty"

    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    oracle = summary["baselines"]["oracle_correct_solver_for_sanity"]
    block = summary["baselines"]["block_everything"]
    random_patch = summary["baselines"]["random_patch"]
    explanation = summary["baselines"]["explanation_only"]
    visible_overfit = summary["baselines"]["visible_overfit"]

    assert oracle["overall_score"] >= 0.9
    assert oracle["certificate_success_rate"] == 1.0
    assert block["overall_score"] <= 0.55
    assert block["overblocking_rate"] == 1.0
    assert random_patch["overall_score"] < 0.5
    assert explanation["certificate_success_rate"] == 0.0
    assert visible_overfit["hardcoded_patch_rate"] == 1.0


def run_gate4_training_smoke_checks() -> None:
    commands = [
        [
            sys.executable,
            str(ROOT / "training" / "make_dataset.py"),
            "--smoke",
            "--output-dir",
            str(TRAINING_SMOKE_DIR),
        ],
        [
            sys.executable,
            str(ROOT / "training" / "train_json_grpo.py"),
            "--smoke",
            "--output-dir",
            str(GRPO_SMOKE_DIR),
        ],
        [
            sys.executable,
            str(ROOT / "training" / "evaluate_model.py"),
            "--smoke",
            "--output-dir",
            str(EVAL_SMOKE_DIR),
        ],
        [
            sys.executable,
            str(ROOT / "training" / "train_sft_warmstart.py"),
            "--smoke",
            "--output-dir",
            str(SFT_SMOKE_DIR),
        ],
    ]
    for command in commands:
        subprocess.run(command, cwd=ROOT, check=True)

    required_files = [
        TRAINING_SMOKE_DIR / "train.jsonl",
        TRAINING_SMOKE_DIR / "eval.jsonl",
        TRAINING_SMOKE_DIR / "dataset_summary.json",
        GRPO_SMOKE_DIR / "metrics.csv",
        GRPO_SMOKE_DIR / "sampled_generations.jsonl",
        GRPO_SMOKE_DIR / "smoke_summary.json",
        EVAL_SMOKE_DIR / "metrics.csv",
        EVAL_SMOKE_DIR / "summary.json",
        SFT_SMOKE_DIR / "sft_samples.jsonl",
        SFT_SMOKE_DIR / "sft_smoke_summary.json",
    ]
    for path in required_files:
        assert path.exists(), f"missing Gate 4 smoke artifact: {path}"
        assert path.stat().st_size > 0, f"empty Gate 4 smoke artifact: {path}"

    grpo_summary = json.loads((GRPO_SMOKE_DIR / "smoke_summary.json").read_text(encoding="utf-8"))
    assert grpo_summary["full_grpo_ran"] is False
    sft_summary = json.loads((SFT_SMOKE_DIR / "sft_smoke_summary.json").read_text(encoding="utf-8"))
    assert sft_summary["full_sft_ran"] is False


def run_gate5_docs_and_space_checks() -> None:
    for path in DOCS_REQUIRED:
        assert path.exists(), f"required submission file missing: {path.name}"
        assert path.stat().st_size > 0, f"required submission file is empty: {path.name}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_readme_terms = [
        "Agent BlackBox Arena",
        "Replay. Repair. Regress. Certify.",
        "not an observability dashboard",
        "failed trace -> replay -> evidence -> root cause -> patch -> regressions -> certificate",
        "Current results are baseline and smoke results",
        "Trained-model results will be added after a real GRPO run",
        "TODO_ADD_HF_SPACE_LINK",
        "TODO_ADD_VIDEO_OR_BLOG_LINK",
    ]
    for term in required_readme_terms:
        assert term in readme, f"README missing required term: {term}"

    safety = (ROOT / "SAFETY.md").read_text(encoding="utf-8")
    for term in ["no real credentials", "no live APIs", "no shell execution", "no exploit payloads", "not a global safety proof"]:
        assert term in safety, f"SAFETY.md missing required term: {term}"

    subprocess.run([sys.executable, str(ROOT / "scripts" / "space_smoke.py")], cwd=ROOT, check=True)


def main() -> int:
    final_stale_state: dict[str, Any] | None = None
    for family in IMPLEMENTED_FAMILIES:
        env = AgentBlackBoxEnvironment()
        state = run_correct_trajectory(env, family)
        assert state["family"] == family
        assert state["score"] >= 0.90, (family, state["score"])
        assert state["repair_certificate"] is not None
        assert state["hidden_regression_summary"]["passed"] is True
        assert_hidden_summary_is_aggregate(state)
        assert_no_hidden_leak(state)

        block_state = run_bad_patch(family, BLOCK_EVERYTHING_PATCH)
        assert block_state["score"] <= 0.55, (family, block_state["score"])
        assert "block_everything_patch" in block_state["audit_flags"]
        assert block_state["hidden_regression_summary"]["passed"] is False

        spec = family_spec(family)
        hardcoded_patch = dict(spec["correct_patch"])
        hardcoded_patch["rationale"] = f"This specifically fixes {family}_042 using a visible incident id."
        hardcoded_state = run_bad_patch(family, hardcoded_patch)
        assert "hardcoded_incident_id_patch" in hardcoded_state["audit_flags"]
        assert hardcoded_state["hidden_regression_summary"]["passed"] is False

        wrong_root_state = run_bad_patch(family, spec["correct_patch"], root_cause="missing_retry_cap")
        assert wrong_root_state["score"] <= 0.55, (family, wrong_root_state["score"])
        assert "wrong_root_cause" in wrong_root_state["audit_flags"]

        early_cert_env = AgentBlackBoxEnvironment()
        early_cert_env.reset(seed=42, family=family)
        early_cert_env.step("generate_repair_certificate")
        early_state = early_cert_env.state()
        assert early_state["repair_certificate"] is None
        assert "certificate_before_verifier" in early_state["audit_flags"]

        print(f"self_check: {family} correct trajectory score = {state['score']}")
        print(f"self_check: {family} block-everything score = {block_state['score']}")
        print(f"self_check: {family} hardcoded patch rejected")
        if family == "stale_retrieval":
            final_stale_state = state

    assert final_stale_state is not None
    write_examples(final_stale_state)

    print("self_check: reset/step/state ok")
    print("self_check: all three MVP families verified")
    print("self_check: certificate gating ok")
    print("self_check: hidden leakage scan ok")
    print("self_check: examples written")
    run_gate3_baseline_checks()
    print("self_check: baseline evaluator ok")
    print("self_check: baseline plots ok")
    run_gate4_training_smoke_checks()
    print("self_check: training scaffold smoke ok")
    run_gate5_docs_and_space_checks()
    print("self_check: docs readiness ok")
    print("self_check: space smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
