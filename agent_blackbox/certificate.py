from __future__ import annotations

from typing import Any, Dict

from agent_blackbox.models import EpisodeRuntime
from agent_blackbox.verifier import exact_span_match


BOUNDED_DISCLAIMER = (
    "This certificate is bounded to the generated finite incident family, visible trace, "
    "hidden regression variants, and verification horizon. It is not a global safety proof."
)


def can_generate_certificate(episode: EpisodeRuntime) -> bool:
    visible = episode.visible_replay_report or {}
    hidden = episode.hidden_regression_summary or {}
    return (
        visible.get("passed") is True
        and hidden.get("passed") is True
        and episode.submitted_patch is not None
        and episode.submitted_root_cause == episode.hidden_oracle.true_root_cause
        and exact_span_match(episode.selected_evidence_spans, episode.hidden_oracle.expected_evidence_spans)
    )


def generate_certificate(episode: EpisodeRuntime) -> Dict[str, Any]:
    hidden = episode.hidden_regression_summary or {}
    return {
        "certificate_id": f"cert_{episode.incident.incident_id}",
        "incident_id": episode.incident.incident_id,
        "family": episode.incident.family,
        "root_cause": episode.submitted_root_cause,
        "evidence_spans": list(episode.selected_evidence_spans),
        "repair_patch": episode.submitted_patch,
        "visible_replay_passed": bool((episode.visible_replay_report or {}).get("passed")),
        "hidden_regression_pass_rate": hidden.get("hidden_regression_pass_rate", 0.0),
        "valid_behavior_preservation_rate": hidden.get("valid_behavior_preservation_rate", 0.0),
        "overblocking_detected": bool(hidden.get("overblocking_detected")),
        "hardcoded_patch_detected": bool(hidden.get("hardcoded_patch_detected")),
        "repair_score": int(round(episode.score * 100)),
        "recommendation": "redeploy_with_patch_under_bounded_coverage",
        "bounded_disclaimer": BOUNDED_DISCLAIMER,
    }
