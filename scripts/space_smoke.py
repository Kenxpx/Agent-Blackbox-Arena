from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from server.app import app
from server.agent_blackbox_environment import AgentBlackBoxEnvironment


CORRECT_PATCH = {
    "require": ["fresh_context_check", "final_action_check"],
    "forbid": ["act_on_stale_context"],
    "preserve": ["valid_fresh_context_flow"],
    "rationale": "The failed trace used expired retrieved context before final action.",
}


def main() -> int:
    client = TestClient(app)
    root = client.get("/")
    assert root.status_code == 200
    assert "text/html" in root.headers["content-type"]
    assert "Agent BlackBox Arena" in root.text
    metadata_response = client.get("/metadata")
    assert metadata_response.status_code == 200
    assert metadata_response.json()["name"] == "agent-blackbox-arena"

    env = AgentBlackBoxEnvironment()
    metadata = env.metadata()
    assert metadata["name"] == "agent-blackbox-arena"
    assert "stale_retrieval" in metadata["implemented_families"]

    obs = env.reset(seed=42, family="stale_retrieval")
    assert obs["family"] == "stale_retrieval"
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": ["s2", "s4"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": "missing_freshness_check"}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": CORRECT_PATCH}})
    env.step("compile_regression_tests")
    env.step("run_visible_replay")
    env.step("run_hidden_regressions")
    env.step("generate_repair_certificate")
    state = env.state()
    assert state["repair_certificate"] is not None
    assert state["score"] >= 0.9

    print("space_smoke: FastAPI app import ok")
    print("space_smoke: root HTML ok")
    print("space_smoke: metadata JSON ok")
    print("space_smoke: environment metadata ok")
    print("space_smoke: reset/step/state ok")
    print("space_smoke: stale_retrieval certificate path ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
