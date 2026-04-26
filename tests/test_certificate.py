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


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_certificate_cannot_be_generated_before_verifier(family):
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42, family=family)
    result = env.step("generate_repair_certificate")
    obs = result["observation"]

    assert obs["repair_certificate"] is None
    assert obs["last_error"] == "certificate requires visible replay and hidden regressions to pass"
    assert "certificate_before_verifier" in obs["audit_flags"]


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_certificate_has_bounded_disclaimer_after_verifier(family):
    spec = family_spec(family)
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42, family=family)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": spec["evidence_spans"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": spec["root_cause"]}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": spec["patch"]}})
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    obs = env.step("generate_repair_certificate")["observation"]
    certificate = obs["repair_certificate"]

    assert certificate["visible_replay_passed"] is True
    assert certificate["family"] == family
    assert certificate["root_cause"] == spec["root_cause"]
    assert certificate["hidden_regression_pass_rate"] == 1.0
    assert certificate["valid_behavior_preservation_rate"] == 1.0
    assert certificate["recommendation"] == "redeploy_with_patch_under_bounded_coverage"
    assert "not a global safety proof" in certificate["bounded_disclaimer"]


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_certificate_requires_correct_evidence_not_only_patch_success(family):
    spec = family_spec(family)
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42, family=family)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": ["s1", "s4"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": spec["root_cause"]}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": spec["patch"]}})
    env.step("run_visible_replay")
    hidden_obs = env.step("run_hidden_regressions")["observation"]
    obs = env.step("generate_repair_certificate")["observation"]

    assert hidden_obs["hidden_regression_summary"]["passed"] is True
    assert obs["repair_certificate"] is None
    assert obs["score_channels"]["evidence_spans_correct"] == 0.0
    assert "certificate_before_verifier" in obs["audit_flags"]
