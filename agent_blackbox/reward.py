from __future__ import annotations

from typing import Dict

from agent_blackbox.models import EpisodeRuntime, append_flag
from agent_blackbox.verifier import (
    exact_span_match,
    patch_blocks_failure,
    patch_preserves_valid_flow,
    validate_patch_schema,
)


POSITIVE_WEIGHTS = {
    "trace_inspected": 0.05,
    "incident_replayed": 0.08,
    "evidence_spans_correct": 0.14,
    "root_cause_correct": 0.16,
    "repair_patch_valid_schema": 0.07,
    "repair_patch_blocks_failure": 0.16,
    "valid_behavior_preserved": 0.14,
    "hidden_regressions_passed": 0.14,
    "certificate_generated": 0.06,
}

PENALTIES = {
    "invalid_json": -0.06,
    "unknown_clause_id": -0.05,
    "wrong_root_cause": -0.08,
    "patch_without_evidence": -0.08,
    "block_everything_patch": -0.25,
    "overblocking_valid_flow": -0.18,
    "hardcoded_incident_id_patch": -0.15,
    "hidden_test_probe_attempt": -0.12,
    "certificate_before_verifier": -0.10,
    "timeout": -0.05,
    "repeated_hidden_regression_call": -0.08,
}


def compute_score(episode: EpisodeRuntime) -> float:
    channels: Dict[str, float] = {}
    channels["trace_inspected"] = POSITIVE_WEIGHTS["trace_inspected"] if episode.trace_inspected else 0.0
    channels["incident_replayed"] = POSITIVE_WEIGHTS["incident_replayed"] if episode.incident_replayed else 0.0
    channels["evidence_spans_correct"] = (
        POSITIVE_WEIGHTS["evidence_spans_correct"]
        if exact_span_match(episode.selected_evidence_spans, episode.hidden_oracle.expected_evidence_spans)
        else 0.0
    )
    root_correct = episode.submitted_root_cause == episode.hidden_oracle.true_root_cause
    channels["root_cause_correct"] = POSITIVE_WEIGHTS["root_cause_correct"] if root_correct else 0.0
    if episode.submitted_root_cause and not root_correct:
        append_flag(episode.audit_flags, "wrong_root_cause")

    patch = episode.submitted_patch
    schema_valid = False
    if patch:
        schema_valid, _ = validate_patch_schema(patch)
    channels["repair_patch_valid_schema"] = POSITIVE_WEIGHTS["repair_patch_valid_schema"] if schema_valid else 0.0
    channels["repair_patch_blocks_failure"] = (
        POSITIVE_WEIGHTS["repair_patch_blocks_failure"]
        if patch and schema_valid and patch_blocks_failure(patch, episode)
        else 0.0
    )
    channels["valid_behavior_preserved"] = (
        POSITIVE_WEIGHTS["valid_behavior_preserved"]
        if patch and schema_valid and patch_preserves_valid_flow(patch, episode)
        else 0.0
    )
    channels["hidden_regressions_passed"] = (
        POSITIVE_WEIGHTS["hidden_regressions_passed"]
        if episode.hidden_regression_summary and episode.hidden_regression_summary.get("passed") is True
        else 0.0
    )
    channels["certificate_generated"] = (
        POSITIVE_WEIGHTS["certificate_generated"] if episode.repair_certificate is not None else 0.0
    )

    positive = sum(channels.values())
    penalty_total = sum(PENALTIES[flag] for flag in set(episode.audit_flags) if flag in PENALTIES)
    score = max(0.0, min(1.0, positive + penalty_total))

    # Score caps make explanation-only and incomplete repair behavior visibly insufficient.
    if not patch and score > 0.35:
        score = 0.35
    if episode.incident_replayed and not patch and score > 0.45:
        score = 0.45
    if patch and not episode.hidden_regression_summary and score > 0.70:
        score = 0.70
    if episode.repair_certificate and channels["valid_behavior_preserved"] == 0.0 and score > 0.75:
        score = 0.75
    if "wrong_root_cause" in episode.audit_flags and score > 0.55:
        score = 0.55

    episode.score_channels = channels
    episode.score = round(score, 4)
    return episode.score
