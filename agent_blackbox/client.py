from __future__ import annotations

import json
from typing import Any, Dict
from urllib import request


class AgentBlackBoxClient:
    """Small HTTP client that does not import server internals."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000") -> None:
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def _get(self, path: str) -> Dict[str, Any]:
        with request.urlopen(f"{self.base_url}{path}", timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def reset(self, seed: int = 42) -> Dict[str, Any]:
        return self._post("/reset", {"seed": seed})

    def step(self, action: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self._post("/step", {"action": action, "payload": payload or {}})

    def state(self) -> Dict[str, Any]:
        return self._get("/state")
