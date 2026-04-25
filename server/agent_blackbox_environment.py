from __future__ import annotations

from typing import Any, Dict, Optional

from agent_blackbox.certificate import can_generate_certificate, generate_certificate
from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from agent_blackbox.models import ACTION_NAMES, RESERVED_TOOL_NAMES, Action, EpisodeRuntime, append_flag
from agent_blackbox.reward import compute_score
from agent_blackbox.verifier import (
    apply_patch_audit_flags,
    extract_patch,
    run_hidden_regression_check,
    run_visible_replay_check,
    validate_patch_schema,
)


class AgentBlackBoxEnvironment:
    """Gate 2 OpenEnv-style environment for three MVP repair families."""

    def __init__(self, max_steps: int = 10) -> None:
        self.max_steps = max_steps
        self._episode: Optional[EpisodeRuntime] = None

    def metadata(self) -> Dict[str, Any]:
        return {
            "name": "agent-blackbox-arena",
            "category": "Agent Reliability CI",
            "tagline": "Replay. Repair. Regress. Certify.",
            "implemented_families": list(IMPLEMENTED_FAMILIES),
            "actions": list(ACTION_NAMES),
            "reserved_tool_names": sorted(RESERVED_TOOL_NAMES),
            "motto": "Trace is evidence. Replay is diagnosis. Patch is policy. Regression is proof. Certificate is trust.",
        }

    def reset(self, seed: int = 42, family: str = "stale_retrieval") -> Dict[str, Any]:
        incident, hidden = generate_incident(family=family, seed=seed)
        self._episode = EpisodeRuntime(
            episode_id=f"ep_{seed:05d}",
            incident=incident,
            hidden_oracle=hidden,
            steps_remaining=self.max_steps,
            last_action_summary="episode reset",
        )
        compute_score(self._episode)
        return self.state()

    def state(self) -> Dict[str, Any]:
        if self._episode is None:
            return self.reset()
        return self._episode.public_observation().to_dict()

    def step(self, action: Action | Dict[str, Any] | str) -> Dict[str, Any]:
        if self._episode is None:
            self.reset()
        assert self._episode is not None
        episode = self._episode
        previous_score = episode.score
        parsed = Action.from_any(action)

        episode.last_error = None
        if episode.done:
            episode.last_error = "episode already done"
            return {
                "observation": self.state(),
                "reward": 0.0,
                "done": True,
                "info": {"score": episode.score, "error": episode.last_error},
            }

        if parsed.action not in ACTION_NAMES:
            episode.last_error = f"unknown action: {parsed.action}"
            append_flag(episode.audit_flags, "invalid_action")
        else:
            self._apply_action(parsed)

        episode.steps_remaining -= 1
        if episode.steps_remaining <= 0 and not episode.done:
            append_flag(episode.audit_flags, "timeout")
            episode.done = True
            episode.last_action_summary = "episode timed out"

        compute_score(episode)
        reward = round(episode.score - previous_score, 4)
        return {
            "observation": self.state(),
            "reward": reward,
            "done": episode.done,
            "info": {"score": episode.score, "audit_flags": list(episode.audit_flags)},
        }

    def _apply_action(self, action: Action) -> None:
        assert self._episode is not None
        episode = self._episode
        payload = action.payload

        if _payload_probes_hidden(payload):
            append_flag(episode.audit_flags, "hidden_test_probe_attempt")

        if action.action == "noop":
            episode.last_action_summary = "noop"
            return

        if action.action == "inspect_trace":
            episode.trace_inspected = True
            episode.last_action_summary = "public trace inspected"
            return

        if action.action == "replay_incident":
            episode.incident_replayed = True
            episode.last_action_summary = "incident replayed"
            return

        if action.action == "select_evidence_spans":
            spans = payload.get("evidence_spans", payload.get("spans", []))
            if not isinstance(spans, list) or not all(isinstance(span, str) for span in spans):
                episode.last_error = "evidence_spans must be a list of span ids"
                append_flag(episode.audit_flags, "invalid_json")
                return
            episode.selected_evidence_spans = spans
            episode.last_action_summary = "evidence spans selected"
            return

        if action.action == "submit_root_cause":
            root_cause = payload.get("root_cause")
            if not isinstance(root_cause, str):
                episode.last_error = "root_cause must be a string"
                append_flag(episode.audit_flags, "invalid_json")
                return
            episode.submitted_root_cause = root_cause
            episode.last_action_summary = "root cause submitted"
            return

        if action.action == "propose_repair_patch":
            patch = extract_patch(payload)
            schema_valid, flags = validate_patch_schema(patch)
            for flag in flags:
                append_flag(episode.audit_flags, flag)
            episode.submitted_patch = patch if patch else {}
            if not schema_valid:
                episode.last_error = "repair patch failed schema validation"
            apply_patch_audit_flags(episode)
            episode.last_action_summary = "repair patch proposed"
            return

        if action.action == "compile_regression_tests":
            tests = payload.get("regression_tests")
            if tests is None:
                tests = [
                    f"reg_{episode.incident.family}_block_failure",
                    f"reg_{episode.incident.family}_preserve_valid",
                ]
            if not isinstance(tests, list) or not all(isinstance(item, str) for item in tests):
                episode.last_error = "regression_tests must be a list of ids"
                append_flag(episode.audit_flags, "invalid_json")
                return
            episode.compiled_regression_tests = tests
            episode.last_action_summary = "regression tests compiled"
            return

        if action.action == "run_visible_replay":
            if not episode.submitted_patch:
                episode.last_error = "repair patch required before visible replay"
                append_flag(episode.audit_flags, "patch_without_evidence")
                return
            episode.visible_replay_report = run_visible_replay_check(episode)
            episode.last_action_summary = "visible replay verifier completed"
            return

        if action.action == "run_hidden_regressions":
            episode.hidden_regression_call_count += 1
            if episode.hidden_regression_call_count > 1:
                append_flag(episode.audit_flags, "repeated_hidden_regression_call")
            if not episode.visible_replay_report:
                episode.last_error = "visible replay required before hidden regressions"
                return
            episode.hidden_regression_summary = run_hidden_regression_check(episode)
            episode.last_action_summary = "hidden regression verifier completed"
            return

        if action.action == "generate_repair_certificate":
            if not can_generate_certificate(episode):
                episode.last_error = "certificate requires visible replay and hidden regressions to pass"
                append_flag(episode.audit_flags, "certificate_before_verifier")
                episode.last_action_summary = "certificate blocked"
                return
            compute_score(episode)
            episode.repair_certificate = generate_certificate(episode)
            episode.last_action_summary = "repair certificate generated"
            return

        if action.action == "submit_final":
            episode.done = True
            episode.last_action_summary = "final submitted"


def _payload_probes_hidden(payload: Dict[str, Any]) -> bool:
    encoded = str(payload).lower()
    probe_terms = [
        "hidden_regression_variants",
        "hidden_valid_variants",
        "oracle_score_details",
        "answer_key_clause_ids",
        "expected_patch",
        "raw_seed",
    ]
    return any(term in encoded for term in probe_terms)
