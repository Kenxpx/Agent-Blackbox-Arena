from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Tuple

from agent_blackbox.models import (
    ALLOWED_FORBID_EFFECTS,
    ALLOWED_PRESERVE_CLAUSES,
    ALLOWED_REQUIRE_CLAUSES,
    EpisodeRuntime,
    append_flag,
)


def normalize_list(value: Any) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def extract_patch(payload: Dict[str, Any]) -> Dict[str, Any]:
    patch = payload.get("patch", payload)
    if not isinstance(patch, dict):
        return {}
    return {
        "require": normalize_list(patch.get("require")),
        "forbid": normalize_list(patch.get("forbid")),
        "preserve": normalize_list(patch.get("preserve")),
        "rationale": patch.get("rationale", "") if isinstance(patch.get("rationale", ""), str) else "",
    }


def validate_patch_schema(patch: Dict[str, Any]) -> Tuple[bool, List[str]]:
    flags: List[str] = []
    if not isinstance(patch, dict) or not {"require", "forbid", "preserve", "rationale"}.issubset(patch):
        flags.append("invalid_json")
        return False, flags

    for clause in normalize_list(patch.get("require")):
        if clause not in ALLOWED_REQUIRE_CLAUSES:
            flags.append("unknown_clause_id")
    for effect in normalize_list(patch.get("forbid")):
        if effect not in ALLOWED_FORBID_EFFECTS:
            flags.append("unknown_clause_id")
    for clause in normalize_list(patch.get("preserve")):
        if clause not in ALLOWED_PRESERVE_CLAUSES:
            flags.append("unknown_clause_id")
    return "unknown_clause_id" not in flags, flags


def list_contains_all(items: Iterable[str], expected: Iterable[str]) -> bool:
    item_set = set(items)
    return all(item in item_set for item in expected)


def exact_span_match(actual: List[str], expected: List[str]) -> bool:
    return set(actual) == set(expected)


def is_block_everything_patch(patch: Dict[str, Any]) -> bool:
    require = set(normalize_list(patch.get("require")))
    forbid = set(normalize_list(patch.get("forbid")))
    preserve = set(normalize_list(patch.get("preserve")))
    if "block_all_actions" in forbid or "disable_agent" in forbid:
        return True
    if forbid == set(ALLOWED_FORBID_EFFECTS):
        return True
    if len(forbid) >= 4 and not preserve:
        return True
    if require == set(ALLOWED_REQUIRE_CLAUSES) and not preserve:
        return True
    if forbid and "valid_fresh_context_flow" not in preserve and "act_on_stale_context" in forbid:
        return True
    return False


def is_hardcoded_patch(patch: Dict[str, Any], episode: EpisodeRuntime) -> bool:
    encoded = json.dumps(patch, sort_keys=True).lower()
    hardcoded_terms = [episode.incident.incident_id.lower(), *episode.hidden_oracle.hardcoded_solution_keys]
    if any(str(term).lower() in encoded for term in hardcoded_terms):
        return True
    if "incident_id" in patch or "expected_patch" in patch or "hidden_regression_variants" in patch:
        return True
    return False


def patch_blocks_failure(patch: Dict[str, Any], episode: EpisodeRuntime) -> bool:
    require = normalize_list(patch.get("require"))
    forbid = normalize_list(patch.get("forbid"))
    return (
        list_contains_all(require, episode.hidden_oracle.answer_key_clause_ids)
        and list_contains_all(forbid, episode.hidden_oracle.expected_forbid_effects)
    )


def patch_preserves_valid_flow(patch: Dict[str, Any], episode: EpisodeRuntime) -> bool:
    preserve = normalize_list(patch.get("preserve"))
    if is_block_everything_patch(patch):
        return False
    return list_contains_all(preserve, episode.hidden_oracle.expected_preserve_clauses)


def run_visible_replay_check(episode: EpisodeRuntime) -> Dict[str, Any]:
    patch = episode.submitted_patch or {}
    schema_valid, _ = validate_patch_schema(patch)
    blocks_failure = schema_valid and patch_blocks_failure(patch, episode)
    preserves_valid = schema_valid and patch_preserves_valid_flow(patch, episode)
    passed = blocks_failure and preserves_valid and not is_hardcoded_patch(patch, episode)
    return {
        "visible_failed_trace_blocked": blocks_failure,
        "visible_valid_trace_preserved": preserves_valid,
        "passed": passed,
        "reason": (
            f"{episode.incident.family} failure is blocked and valid behavior is preserved"
            if passed
            else "patch did not both block stale behavior and preserve valid behavior"
        ),
    }


def run_hidden_regression_check(episode: EpisodeRuntime) -> Dict[str, Any]:
    patch = episode.submitted_patch or {}
    schema_valid, _ = validate_patch_schema(patch)
    blocks_failure = schema_valid and patch_blocks_failure(patch, episode)
    preserves_valid = schema_valid and patch_preserves_valid_flow(patch, episode)
    hardcoded = is_hardcoded_patch(patch, episode)
    overblocking = is_block_everything_patch(patch)

    failed_total = len(episode.hidden_oracle.hidden_regression_variants)
    valid_total = len(episode.hidden_oracle.hidden_valid_variants)
    failed_blocked = failed_total if blocks_failure and not hardcoded else 0
    valid_preserved = valid_total if preserves_valid and not overblocking and not hardcoded else 0
    total = failed_total + valid_total
    pass_count = failed_blocked + valid_preserved
    pass_rate = pass_count / total if total else 0.0
    valid_preservation_rate = valid_preserved / valid_total if valid_total else 0.0
    return {
        "hidden_failed_variants_blocked": failed_blocked,
        "hidden_failed_variant_count": failed_total,
        "hidden_valid_variants_preserved": valid_preserved,
        "hidden_valid_variant_count": valid_total,
        "hidden_regression_pass_rate": round(pass_rate, 4),
        "valid_behavior_preservation_rate": round(valid_preservation_rate, 4),
        "overblocking_detected": bool(overblocking),
        "hardcoded_patch_detected": bool(hardcoded),
        "passed": pass_rate == 1.0 and valid_preservation_rate == 1.0 and not hardcoded,
    }


def apply_patch_audit_flags(episode: EpisodeRuntime) -> None:
    patch = episode.submitted_patch
    if not patch:
        return
    schema_valid, flags = validate_patch_schema(patch)
    for flag in flags:
        append_flag(episode.audit_flags, flag)
    if not schema_valid:
        return
    if episode.selected_evidence_spans and not exact_span_match(
        episode.selected_evidence_spans, episode.hidden_oracle.expected_evidence_spans
    ):
        append_flag(episode.audit_flags, "patch_without_evidence")
    if not episode.selected_evidence_spans:
        append_flag(episode.audit_flags, "patch_without_evidence")
    if is_block_everything_patch(patch):
        append_flag(episode.audit_flags, "block_everything_patch")
        append_flag(episode.audit_flags, "overblocking_valid_flow")
    if is_hardcoded_patch(patch, episode):
        append_flag(episode.audit_flags, "hardcoded_incident_id_patch")
