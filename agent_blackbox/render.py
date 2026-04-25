from __future__ import annotations

from agent_blackbox.models import Observation


def render_observation(observation: Observation) -> str:
    lines = [
        f"Episode: {observation.episode_id}",
        f"Incident: {observation.incident_id}",
        f"Family: {observation.family}",
        f"Score: {observation.score:.4f}",
        "Trace:",
    ]
    for span in observation.public_trace_spans:
        lines.append(f"- {span['span_id']} [{span['span_type']}]: {span['summary']}")
    return "\n".join(lines)
