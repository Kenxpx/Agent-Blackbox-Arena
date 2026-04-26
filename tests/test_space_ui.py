from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from server.app import app


client = TestClient(app)


def test_root_returns_polished_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Agent BlackBox Arena" in response.text
    assert "Replay. Repair. Regress. Certify." in response.text
    assert "OpenEnv-style environment" in response.text
    assert "Live Repair Episode" in response.text
    assert "Mini benchmark scoreboard" in response.text
    assert "POST_CHALLENGE_CURRICULUM_0_5B_COMPLETE" not in response.text


def test_space_resource_links_are_stable_public_urls():
    response = client.get("/")
    html = response.text
    repo = "https://github.com/Kenxpx/Agent-Blackbox-Arena"
    expected_links = [
        repo,
        f"{repo}#readme",
        f"{repo}/blob/main/BENCHMARK_SPEC.md",
        f"{repo}/blob/main/notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb",
        f"{repo}/blob/main/SUBMISSION_EVIDENCE.md",
        f"{repo}/blob/main/FINAL_SUBMISSION_AUDIT.md",
        f"{repo}/blob/main/TRAINING_RUN_LOG.md",
        f"{repo}/blob/main/openenv.yaml",
        f"{repo}/tree/main/training",
        "/metadata",
    ]
    for link in expected_links:
        assert f'href="{link}"' in html
    assert 'href="#"' not in html
    assert f'href="{repo}#agent-blackbox-arena"' not in html
    assert "Video / Blog" in html
    assert "link pending before final submission" in html


def test_metadata_endpoint_keeps_json_metadata():
    response = client.get("/metadata")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "agent-blackbox-arena"
    assert payload["tagline"] == "Replay. Repair. Regress. Certify."
    assert "stale_retrieval" in payload["implemented_families"]

    alias = client.get("/api/metadata")
    assert alias.status_code == 200
    assert alias.json() == payload


def test_openenv_api_endpoints_still_work_from_space_app():
    reset = client.post("/reset", json={"seed": 42, "family": "stale_retrieval"})
    assert reset.status_code == 200
    assert reset.json()["family"] == "stale_retrieval"

    step = client.post("/step", json={"action": "inspect_trace", "payload": {}})
    assert step.status_code == 200
    assert step.json()["reward"] > 0

    state = client.get("/state")
    assert state.status_code == 200
    assert state.json()["last_action_summary"] == "public trace inspected"


def test_final_plot_asset_loads_when_present():
    plot = Path("outputs/final_plots/hf_05b_challenge_curriculum_training_loss_curve.png")
    if not plot.exists():
        return
    response = client.get("/assets/final_plots/hf_05b_challenge_curriculum_training_loss_curve.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
