from server.agent_blackbox_environment import AgentBlackBoxEnvironment


FAMILY = "permission_scope"
CORRECT_PATCH = {
    "require": ["role_tool_scope_match", "final_action_check"],
    "forbid": ["out_of_scope_tool_call"],
    "preserve": ["authorized_tool_flow"],
    "rationale": "Tool calls must match the user's role and task scope before final action.",
}


def run_correct_path():
    env = AgentBlackBoxEnvironment()
    obs = env.reset(seed=42, family=FAMILY)
    assert obs["family"] == FAMILY
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": ["s2", "s4"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": "permission_scope"}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": CORRECT_PATCH}})
    env.step("compile_regression_tests")
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    env.step("generate_repair_certificate")
    return env


def test_permission_scope_correct_path_scores_high():
    env = run_correct_path()
    state = env.state()

    assert state["score"] >= 0.90
    assert state["visible_replay_report"]["passed"] is True
    assert state["hidden_regression_summary"]["passed"] is True
    assert state["repair_certificate"]["root_cause"] == "permission_scope"
    assert state["repair_certificate"]["valid_behavior_preservation_rate"] == 1.0


def test_permission_scope_wrong_root_cause_scores_low():
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42, family=FAMILY)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": ["s2", "s4"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": "missing_verification"}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": CORRECT_PATCH}})
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    env.step("generate_repair_certificate")
    state = env.state()

    assert state["score"] <= 0.55
    assert "wrong_root_cause" in state["audit_flags"]
    assert state["repair_certificate"] is None
