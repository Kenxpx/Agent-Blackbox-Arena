from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


ACTION_NAMES = [
    "noop",
    "inspect_trace",
    "replay_incident",
    "select_evidence_spans",
    "submit_root_cause",
    "propose_repair_patch",
    "compile_regression_tests",
    "run_visible_replay",
    "run_hidden_regressions",
    "generate_repair_certificate",
    "submit_final",
]

RESERVED_TOOL_NAMES = {"reset", "step", "state", "close"}

ALLOWED_REQUIRE_CLAUSES = [
    "fresh_context_check",
    "verify_before_irreversible_action",
    "role_tool_scope_match",
    "include_constraints_in_handoff",
    "retry_budget_cap",
    "final_action_check",
]

ALLOWED_FORBID_EFFECTS = [
    "act_on_stale_context",
    "irreversible_action_without_verification",
    "out_of_scope_tool_call",
    "constraint_dropped_in_handoff",
    "unbounded_retry_loop",
    "final_action_without_check",
]

ALLOWED_PRESERVE_CLAUSES = [
    "valid_fresh_context_flow",
    "verified_action_flow",
    "authorized_tool_flow",
    "valid_handoff_flow",
]

FORBIDDEN_PUBLIC_KEYS = [
    "true_root_cause",
    "answer_key_clause_ids",
    "hidden_regression_variants",
    "hidden_valid_variants",
    "oracle_score_details",
    "raw_seed",
    "expected_patch",
    "hardcoded_solution_keys",
    "hidden_span_labels",
    "full_verifier_decision_tree",
]


@dataclass(frozen=True)
class TraceSpan:
    span_id: str
    span_type: str
    summary: str
    visible_tags: List[str]

    def public_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Incident:
    incident_id: str
    family: str
    difficulty: str
    scenario: str
    trace_spans: List[TraceSpan]
    visible_failure_outcome: str
    candidate_root_causes: List[str]
    candidate_patch_clauses: List[str]

    def public_trace(self) -> List[Dict[str, Any]]:
        return [span.public_dict() for span in self.trace_spans]


@dataclass(frozen=True)
class HiddenVariant:
    variant_id: str
    should_block: bool
    condition: str


@dataclass
class HiddenOracle:
    true_root_cause: str
    answer_key_clause_ids: List[str]
    expected_forbid_effects: List[str]
    expected_preserve_clauses: List[str]
    expected_evidence_spans: List[str]
    hidden_regression_variants: List[HiddenVariant]
    hidden_valid_variants: List[HiddenVariant]
    raw_seed: int
    expected_patch: Dict[str, Any]
    hardcoded_solution_keys: List[str]
    hidden_span_labels: Dict[str, str]
    oracle_score_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    action: str
    payload: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_any(cls, value: "Action | Dict[str, Any] | str") -> "Action":
        if isinstance(value, Action):
            return value
        if isinstance(value, str):
            return cls(action=value, payload={})
        if not isinstance(value, dict):
            raise TypeError("Action must be an Action, dict, or string.")
        action = value.get("action")
        if not isinstance(action, str):
            raise ValueError("Action dict requires string field 'action'.")
        payload = value.get("payload", {})
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise ValueError("Action payload must be an object.")
        return cls(action=action, payload=payload)


@dataclass
class Observation:
    episode_id: str
    incident_id: str
    family: str
    difficulty: str
    scenario: str
    public_trace_spans: List[Dict[str, Any]]
    allowed_patch_clauses: List[str]
    allowed_forbid_effects: List[str]
    allowed_preserve_clauses: List[str]
    available_actions: List[str]
    selected_evidence_spans: List[str] = field(default_factory=list)
    submitted_root_cause: Optional[str] = None
    submitted_patch: Optional[Dict[str, Any]] = None
    compiled_regression_tests: List[str] = field(default_factory=list)
    visible_replay_report: Optional[Dict[str, Any]] = None
    hidden_regression_summary: Optional[Dict[str, Any]] = None
    repair_certificate: Optional[Dict[str, Any]] = None
    score_channels: Dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    audit_flags: List[str] = field(default_factory=list)
    steps_remaining: int = 10
    last_action_summary: str = ""
    last_error: Optional[str] = None
    done: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EpisodeRuntime:
    episode_id: str
    incident: Incident
    hidden_oracle: HiddenOracle
    selected_evidence_spans: List[str] = field(default_factory=list)
    submitted_root_cause: Optional[str] = None
    submitted_patch: Optional[Dict[str, Any]] = None
    compiled_regression_tests: List[str] = field(default_factory=list)
    visible_replay_report: Optional[Dict[str, Any]] = None
    hidden_regression_summary: Optional[Dict[str, Any]] = None
    repair_certificate: Optional[Dict[str, Any]] = None
    score_channels: Dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    audit_flags: List[str] = field(default_factory=list)
    steps_remaining: int = 10
    last_action_summary: str = ""
    last_error: Optional[str] = None
    done: bool = False
    trace_inspected: bool = False
    incident_replayed: bool = False
    hidden_regression_call_count: int = 0

    def public_observation(self) -> Observation:
        return Observation(
            episode_id=self.episode_id,
            incident_id=self.incident.incident_id,
            family=self.incident.family,
            difficulty=self.incident.difficulty,
            scenario=self.incident.scenario,
            public_trace_spans=self.incident.public_trace(),
            allowed_patch_clauses=list(ALLOWED_REQUIRE_CLAUSES),
            allowed_forbid_effects=list(ALLOWED_FORBID_EFFECTS),
            allowed_preserve_clauses=list(ALLOWED_PRESERVE_CLAUSES),
            available_actions=list(ACTION_NAMES),
            selected_evidence_spans=list(self.selected_evidence_spans),
            submitted_root_cause=self.submitted_root_cause,
            submitted_patch=self.submitted_patch,
            compiled_regression_tests=list(self.compiled_regression_tests),
            visible_replay_report=self.visible_replay_report,
            hidden_regression_summary=self.hidden_regression_summary,
            repair_certificate=self.repair_certificate,
            score_channels=dict(self.score_channels),
            score=self.score,
            audit_flags=list(self.audit_flags),
            steps_remaining=self.steps_remaining,
            last_action_summary=self.last_action_summary,
            last_error=self.last_error,
            done=self.done,
        )


def append_flag(flags: List[str], flag: str) -> None:
    if flag not in flags:
        flags.append(flag)
