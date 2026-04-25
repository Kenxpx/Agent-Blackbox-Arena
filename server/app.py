from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI

from agent_blackbox.models import Action
from server.agent_blackbox_environment import AgentBlackBoxEnvironment

app = FastAPI(title="Agent BlackBox Arena", version="0.1.0")
env = AgentBlackBoxEnvironment()


@app.get("/")
def root() -> Dict[str, Any]:
    return env.metadata()


@app.post("/reset")
def reset(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    payload = payload or {}
    return env.reset(seed=int(payload.get("seed", 42)), family=str(payload.get("family", "stale_retrieval")))


@app.post("/step")
def step(payload: Dict[str, Any]) -> Dict[str, Any]:
    return env.step(Action.from_any(payload))


@app.get("/state")
def state() -> Dict[str, Any]:
    return env.state()
