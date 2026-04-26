from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent_blackbox.models import Action
from server.agent_blackbox_environment import AgentBlackBoxEnvironment
from server.ui import render_homepage

app = FastAPI(title="Agent BlackBox Arena", version="0.1.0")
env = AgentBlackBoxEnvironment()
ROOT = Path(__file__).resolve().parents[1]
FINAL_PLOTS_DIR = ROOT / "outputs" / "final_plots"

if FINAL_PLOTS_DIR.exists():
    app.mount("/assets/final_plots", StaticFiles(directory=str(FINAL_PLOTS_DIR)), name="final_plots")


@app.get("/", response_class=HTMLResponse)
def root() -> HTMLResponse:
    return HTMLResponse(render_homepage())


@app.get("/metadata")
def metadata() -> Dict[str, Any]:
    return env.metadata()


@app.get("/api/metadata")
def api_metadata() -> Dict[str, Any]:
    return env.metadata()


@app.post("/reset")
def reset(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = payload or {}
    return env.reset(seed=int(payload.get("seed", 42)), family=str(payload.get("family", "stale_retrieval")))


@app.get("/reset")
def reset_get(seed: int = 42, family: str = "stale_retrieval") -> Dict[str, Any]:
    return env.reset(seed=seed, family=family)


@app.post("/step")
def step(payload: Dict[str, Any]) -> Dict[str, Any]:
    return env.step(Action.from_any(payload))


@app.get("/step")
def step_get(action: str = "inspect_trace") -> Dict[str, Any]:
    return env.step(action)


@app.get("/state")
def state() -> Dict[str, Any]:
    return env.state()
