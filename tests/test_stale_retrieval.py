from server.agent_blackbox_environment import AgentBlackBoxEnvironment


CORRECT_PATCH = {
    "require": ["fresh_context_check", "final_action_check"],
    "forbid": ["act_on_stale_context"],
    "preserve": ["valid_fresh_context_flow"],
    "rationale": "The failed trace used expired retrieved context before final action.",
}


def run_correct_path():
    env = AgentBlackBoxEnvironment()
    obs = env.reset(seed=42)
    assert obs["family"] == "stale_retrieval"
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": ["s2", "s4"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": "missing_freshness_check"}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": CORRECT_PATCH}})
    env.step({"action": "compile_regression_tests", "payload": {"regression_tests": ["reg_stale_context_block"]}})
    visible = env.step("run_visible_replay")
    hidden = env.step("run_hidden_regressions")
    cert = env.step("generate_repair_certificate")
    return env, visible, hidden, cert


def test_stale_retrieval_correct_path_scores_high():
    env, visible, hidden, cert = run_correct_path()
    state = env.state()

    assert visible["observation"]["visible_replay_report"]["passed"] is True
    assert hidden["observation"]["hidden_regression_summary"]["passed"] is True
    assert cert["observation"]["repair_certificate"] is not None
    assert state["score"] >= 0.90
    assert state["score_channels"]["evidence_spans_correct"] == 0.14
    assert state["score_channels"]["root_cause_correct"] == 0.16
    assert state["score_channels"]["hidden_regressions_passed"] == 0.14
    assert state["score_channels"]["certificate_generated"] == 0.06


def test_visible_replay_requires_patch():
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42)
    result = env.step("run_visible_replay")
    assert result["observation"]["last_error"] == "repair patch required before visible replay"
    assert "patch_without_evidence" in result["observation"]["audit_flags"]
