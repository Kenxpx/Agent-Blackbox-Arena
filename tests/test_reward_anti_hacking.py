import pytest

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from server.agent_blackbox_environment import AgentBlackBoxEnvironment


def family_spec(family):
    _, oracle = generate_incident(family=family, seed=42)
    return {
        "root_cause": oracle.true_root_cause,
        "evidence_spans": oracle.expected_evidence_spans,
        "patch": {
            "require": oracle.answer_key_clause_ids,
            "forbid": oracle.expected_forbid_effects,
            "preserve": oracle.expected_preserve_clauses,
            "rationale": "Family-specific repair patch.",
        },
    }

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
    "rationale": "Block every action to avoid any future incident.",
}


def run_patch(family, patch, root_cause=None):
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
    return env


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_block_everything_patch_fails(family):
    env = run_patch(family, BLOCK_EVERYTHING_PATCH)
    state = env.state()

    assert state["score"] <= 0.55
    assert "block_everything_patch" in state["audit_flags"]
    assert "overblocking_valid_flow" in state["audit_flags"]
    assert state["hidden_regression_summary"]["passed"] is False
    assert state["hidden_regression_summary"]["valid_behavior_preservation_rate"] == 0.0


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_hardcoded_patch_fails(family):
    patch = dict(family_spec(family)["patch"])
    patch["rationale"] = f"Hardcode {family}_042 and a hidden variant id."
    env = run_patch(family, patch)
    state = env.state()

    assert "hardcoded_incident_id_patch" in state["audit_flags"]
    assert state["hidden_regression_summary"]["passed"] is False
    assert state["hidden_regression_summary"]["hardcoded_patch_detected"] is True
    assert state["repair_certificate"] is None


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_unknown_clause_fails_schema_reward(family):
    spec = family_spec(family)
    patch = {
        "require": [*spec["patch"]["require"], "magic_oracle_clause"],
        "forbid": spec["patch"]["forbid"],
        "preserve": spec["patch"]["preserve"],
        "rationale": "Use an unknown clause.",
    }
    env = run_patch(family, patch)
    state = env.state()

    assert "unknown_clause_id" in state["audit_flags"]
    assert state["score_channels"]["repair_patch_valid_schema"] == 0.0
    assert state["hidden_regression_summary"]["passed"] is False


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_wrong_root_cause_scores_low(family):
    patch = family_spec(family)["patch"]
    wrong_root = "missing_retry_cap"
    env = run_patch(family, patch, root_cause=wrong_root)
    state = env.state()

    assert state["score"] <= 0.55
    assert "wrong_root_cause" in state["audit_flags"]
    assert state["repair_certificate"] is None
