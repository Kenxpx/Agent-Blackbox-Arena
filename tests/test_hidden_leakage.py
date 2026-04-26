import json

import pytest

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from agent_blackbox.models import FORBIDDEN_PUBLIC_KEYS
from server.agent_blackbox_environment import AgentBlackBoxEnvironment
from training.make_dataset import ordered_candidates_for_prompt


def family_spec(family):
    _, oracle = generate_incident(family=family, seed=42)
    return {
        "root_cause": oracle.true_root_cause,
        "evidence_spans": oracle.expected_evidence_spans,
        "patch": {
            "require": oracle.answer_key_clause_ids,
            "forbid": oracle.expected_forbid_effects,
            "preserve": oracle.expected_preserve_clauses,
            "rationale": "Family-specific repair patch.",
        },
        "hidden_variant_ids": [
            *(variant.variant_id for variant in oracle.hidden_regression_variants),
            *(variant.variant_id for variant in oracle.hidden_valid_variants),
        ],
    }


def assert_no_forbidden_keys(value):
    def walk(item):
        if isinstance(item, dict):
            for key, nested in item.items():
                assert key not in FORBIDDEN_PUBLIC_KEYS
                walk(nested)
        elif isinstance(item, list):
            for nested in item:
                walk(nested)
        elif isinstance(item, str):
            for key in FORBIDDEN_PUBLIC_KEYS:
                assert item != key

    walk(value)


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_public_observation_never_leaks_hidden_state(family):
    spec = family_spec(family)
    env = AgentBlackBoxEnvironment()
    states = [env.reset(seed=42, family=family)]
    actions = [
        "inspect_trace",
        "replay_incident",
        {"action": "select_evidence_spans", "payload": {"evidence_spans": spec["evidence_spans"]}},
        {"action": "submit_root_cause", "payload": {"root_cause": spec["root_cause"]}},
        {"action": "propose_repair_patch", "payload": {"patch": spec["patch"]}},
        "run_visible_replay",
        "run_hidden_regressions",
        "generate_repair_certificate",
    ]
    for action in actions:
        states.append(env.step(action)["observation"])

    for state in states:
        assert_no_forbidden_keys(state)


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_hidden_regression_summary_is_aggregate_only(family):
    spec = family_spec(family)
    env = AgentBlackBoxEnvironment()
    env.reset(seed=42, family=family)
    env.step("inspect_trace")
    env.step("replay_incident")
    env.step({"action": "select_evidence_spans", "payload": {"evidence_spans": spec["evidence_spans"]}})
    env.step({"action": "submit_root_cause", "payload": {"root_cause": spec["root_cause"]}})
    env.step({"action": "propose_repair_patch", "payload": {"patch": spec["patch"]}})
    env.step("run_visible_replay")
    summary = env.step("run_hidden_regressions")["observation"]["hidden_regression_summary"]

    assert set(summary) == {
        "hidden_failed_variants_blocked",
        "hidden_failed_variant_count",
        "hidden_valid_variants_preserved",
        "hidden_valid_variant_count",
        "hidden_regression_pass_rate",
        "valid_behavior_preservation_rate",
        "overblocking_detected",
        "hardcoded_patch_detected",
        "passed",
    }
    encoded = json.dumps(summary, sort_keys=True)
    for variant_id in spec["hidden_variant_ids"]:
        assert variant_id not in encoded


@pytest.mark.parametrize("family", IMPLEMENTED_FAMILIES)
def test_training_prompt_candidate_order_is_not_answer_position_shortcut(family):
    _, oracle = generate_incident(family=family, seed=42)
    root_positions = []
    forbid_positions = []
    preserve_positions = []
    require_first_clause_positions = []

    for seed in range(1000, 1020):
        candidates = ordered_candidates_for_prompt(family, seed, prompt_variant="shuffled_surface_blind")
        root_positions.append(candidates["root_cause"].index(oracle.true_root_cause))
        forbid_positions.append(candidates["forbid"].index(oracle.expected_forbid_effects[0]))
        preserve_positions.append(candidates["preserve"].index(oracle.expected_preserve_clauses[0]))
        require_first_clause_positions.append(candidates["require"].index(oracle.answer_key_clause_ids[0]))

    assert len(set(root_positions)) > 1
    assert len(set(forbid_positions)) > 1
    assert len(set(preserve_positions)) > 1
    assert len(set(require_first_clause_positions)) > 1
    assert not all(position == 0 for position in root_positions)
