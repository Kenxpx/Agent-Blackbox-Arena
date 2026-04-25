import pytest

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES
from agent_blackbox.models import FORBIDDEN_PUBLIC_KEYS, RESERVED_TOOL_NAMES
from server.agent_blackbox_environment import AgentBlackBoxEnvironment


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_reset_step_state_work_and_hide_reserved_actions(family):
    env = AgentBlackBoxEnvironment()
    obs = env.reset(seed=42, family=family)

    assert obs["episode_id"] == "ep_00042"
    assert obs["incident_id"] == f"{family}_042"
    assert obs["family"] == family
    assert obs["done"] is False
    assert "reset" not in obs["available_actions"]
    assert "step" not in obs["available_actions"]
    assert "state" not in obs["available_actions"]
    assert "close" not in obs["available_actions"]
    assert RESERVED_TOOL_NAMES.isdisjoint(set(obs["available_actions"]))

    result = env.step("inspect_trace")
    assert result["reward"] > 0
    assert result["observation"]["score_channels"]["trace_inspected"] == 0.05

    state = env.state()
    assert state["last_action_summary"] == "public trace inspected"
    encoded = str(state)
    for key in FORBIDDEN_PUBLIC_KEYS:
        assert key not in encoded


def test_unknown_action_is_safe_error():
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42)
    result = env.step({"action": "not_a_real_action", "payload": {}})
    assert result["observation"]["last_error"] == "unknown action: not_a_real_action"
    assert result["done"] is False
