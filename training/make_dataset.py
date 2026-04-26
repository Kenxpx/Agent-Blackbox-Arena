from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_blackbox.incidents import IMPLEMENTED_FAMILIES, generate_incident
from agent_blackbox.models import ALLOWED_FORBID_EFFECTS, ALLOWED_PRESERVE_CLAUSES, ALLOWED_REQUIRE_CLAUSES

DEFAULT_TRAIN_SEEDS = "0-59"
DEFAULT_EVAL_SEEDS = "1000-1014"
CHALLENGE_VARIANTS = [
    "standard",
    "shuffled_spans",
    "surface_reworded",
    "blind_family",
    "surface_reworded_blind_family",
    "shuffled_surface_blind",
    "combined_blind_shuffle",
]

LABEL_GLOSSARY = {
    "fresh_context_check": "verify retrieved context freshness before a final action",
    "verify_before_irreversible_action": "verify information before irreversible or high-impact action",
    "role_tool_scope_match": "check that user role, task, and tool permission scope match",
    "include_constraints_in_handoff": "carry constraints through an agent handoff",
    "retry_budget_cap": "limit repeated retries",
    "final_action_check": "gate the final action with the relevant safety control",
    "act_on_stale_context": "final action taken from expired or stale context",
    "irreversible_action_without_verification": "irreversible action taken from unverified information",
    "out_of_scope_tool_call": "tool call outside the user role or task permission scope",
    "constraint_dropped_in_handoff": "handoff loses task constraints",
    "unbounded_retry_loop": "agent retries without a bounded stop rule",
    "final_action_without_check": "final action happens without the required check",
    "valid_fresh_context_flow": "preserve actions where context was refreshed before use",
    "verified_action_flow": "preserve actions where verification happened before action",
    "authorized_tool_flow": "preserve actions where the selected tool is authorized",
    "valid_handoff_flow": "preserve handoffs that retain required constraints",
}

FAMILY_CANDIDATE_LABELS = {
    "stale_retrieval": {
        "require": ["fresh_context_check", "final_action_check", "verify_before_irreversible_action"],
        "forbid": ["act_on_stale_context", "irreversible_action_without_verification", "out_of_scope_tool_call"],
        "preserve": ["valid_fresh_context_flow", "verified_action_flow", "authorized_tool_flow"],
    },
    "missing_verification": {
        "require": ["verify_before_irreversible_action", "final_action_check", "fresh_context_check"],
        "forbid": ["irreversible_action_without_verification", "act_on_stale_context", "out_of_scope_tool_call"],
        "preserve": ["verified_action_flow", "valid_fresh_context_flow", "authorized_tool_flow"],
    },
    "permission_scope": {
        "require": ["role_tool_scope_match", "final_action_check", "verify_before_irreversible_action"],
        "forbid": ["out_of_scope_tool_call", "irreversible_action_without_verification", "act_on_stale_context"],
        "preserve": ["authorized_tool_flow", "verified_action_flow", "valid_fresh_context_flow"],
    },
}


def parse_seed_spec(spec: str) -> list[int]:
    seeds: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            seeds.extend(range(int(start), int(end) + 1))
        else:
            seeds.append(int(part))
    return sorted(dict.fromkeys(seeds))


def strict_json_instruction() -> str:
    return (
        "Return ONLY valid JSON. No markdown. No prose. No commentary. English only. "
        "Do not mention incident IDs. Do not invent labels. "
        "Start with { and end with }. Use exactly these top-level keys: "
        "evidence_spans, root_cause, patch, regression_tests, rationale. The patch object "
        "must contain require, forbid, and preserve arrays."
    )


def system_prompt() -> str:
    return (
        "You are Agent BlackBox JSON Repair Planner. "
        "You output one strict JSON object for an agent reliability repair plan."
    )


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def stable_shuffle(items: list[str], *, family: str, seed: int, prompt_variant: str, field: str) -> list[str]:
    """Deterministically permute public candidates so order cannot become a label shortcut."""
    shuffled = list(items)
    digest = hashlib.sha256(f"{family}:{seed}:{prompt_variant}:{field}".encode("utf-8")).digest()
    random.Random(int.from_bytes(digest[:8], "big")).shuffle(shuffled)
    if len(shuffled) > 1 and shuffled == list(items):
        offset = 1 + (int.from_bytes(digest[8:10], "big") % (len(shuffled) - 1))
        shuffled = shuffled[offset:] + shuffled[:offset]
    return shuffled


def stable_trace_order(spans: list[dict[str, Any]], *, family: str, seed: int, prompt_variant: str) -> list[dict[str, Any]]:
    """Shuffle visible spans without using answer membership as a sort key."""
    ordered = list(spans)
    digest = hashlib.sha256(f"{family}:{seed}:{prompt_variant}:trace_order".encode("utf-8")).digest()
    random.Random(int.from_bytes(digest[:8], "big")).shuffle(ordered)
    return ordered


def uses_public_span_aliases(prompt_variant: str) -> bool:
    return prompt_variant in {"shuffled_spans", "shuffled_surface_blind", "combined_blind_shuffle"}


def public_span_id_map(family: str, seed: int, prompt_variant: str = "standard") -> dict[str, str]:
    """Map canonical trace span IDs to the IDs visible in a prompt variant."""
    prompt_variant = normalize_prompt_variant(prompt_variant)
    incident, _ = generate_incident(family=family, seed=seed)
    public_spans = incident.public_trace()
    if variant_has(prompt_variant, "shuffle"):
        public_spans = stable_trace_order(public_spans, family=incident.family, seed=seed, prompt_variant=prompt_variant)
    if not uses_public_span_aliases(prompt_variant):
        return {span["span_id"]: span["span_id"] for span in public_spans}
    return {span["span_id"]: f"v{index + 1}" for index, span in enumerate(public_spans)}


def public_to_canonical_span_id_map(family: str, seed: int, prompt_variant: str = "standard") -> dict[str, str]:
    canonical_to_public = public_span_id_map(family, seed, prompt_variant=prompt_variant)
    return {public: canonical for canonical, public in canonical_to_public.items()}


def public_evidence_spans(family: str, seed: int, canonical_spans: list[str], prompt_variant: str = "standard") -> list[str]:
    canonical_to_public = public_span_id_map(family, seed, prompt_variant=prompt_variant)
    return [canonical_to_public[span_id] for span_id in canonical_spans]


def canonicalize_public_evidence_spans(family: str, seed: int, public_spans: list[str], prompt_variant: str = "standard") -> list[str]:
    public_to_canonical = public_to_canonical_span_id_map(family, seed, prompt_variant=prompt_variant)
    return [public_to_canonical.get(span_id, f"invalid_public_span:{span_id}") for span_id in public_spans]


def ordered_candidates_for_prompt(family: str, seed: int, prompt_variant: str = "standard") -> dict[str, list[str]]:
    prompt_variant = normalize_prompt_variant(prompt_variant)
    incident, _ = generate_incident(family=family, seed=seed)
    labels = candidate_labels_for_family(incident.family)
    return {
        "root_cause": stable_shuffle(
            list(incident.candidate_root_causes),
            family=incident.family,
            seed=seed,
            prompt_variant=prompt_variant,
            field="root_cause",
        ),
        "require": stable_shuffle(
            labels["require"],
            family=incident.family,
            seed=seed,
            prompt_variant=prompt_variant,
            field="require",
        ),
        "forbid": stable_shuffle(
            labels["forbid"],
            family=incident.family,
            seed=seed,
            prompt_variant=prompt_variant,
            field="forbid",
        ),
        "preserve": stable_shuffle(
            labels["preserve"],
            family=incident.family,
            seed=seed,
            prompt_variant=prompt_variant,
            field="preserve",
        ),
    }


def surface_rewrite(text: str) -> str:
    replacements = [
        ("User", "Requester"),
        ("user", "requester"),
        ("Agent", "Automation worker"),
        ("agent", "automation worker"),
        ("policy", "rules package"),
        ("account", "workspace"),
        ("message", "handoff note"),
        ("tool", "capability"),
        ("administrative", "privileged"),
        ("action", "operation"),
        ("requested", "asked for"),
        ("selected", "chose"),
        ("called", "invoked"),
    ]
    rewritten = text
    for old, new in replacements:
        rewritten = rewritten.replace(old, new)
    return rewritten


def entity_rewrite(text: str, *, family: str, seed: int) -> str:
    """Rename surface entities while preserving the underlying repair semantics."""
    service_names = ["AtlasDesk", "NimbusOps", "LedgerFlow", "HelioCRM", "VectorCare"]
    requester_names = ["Mira", "Devon", "Ishan", "Rowan", "Tala"]
    capability_names = ["policy_check", "workspace_update", "scope_admin", "approval_commit", "read_snapshot"]
    digest = hashlib.sha256(f"{family}:{seed}:entity_rewrite".encode("utf-8")).digest()
    service = service_names[digest[0] % len(service_names)]
    requester = requester_names[digest[1] % len(requester_names)]
    capability = capability_names[digest[2] % len(capability_names)]
    replacements = [
        ("User", requester),
        ("user", "requester"),
        ("Agent", "Automation worker"),
        ("agent", "automation worker"),
        ("policy document", f"{service} rules artifact"),
        ("policy snapshot", f"{service} rules snapshot"),
        ("policy", f"{service} rule set"),
        ("rules package", f"{service} rules package"),
        ("account", f"{service} workspace"),
        ("workspace", f"{service} workspace"),
        ("message", f"{service} approval note"),
        ("handoff note", f"{service} approval note"),
        ("tool", "capability"),
        ("capability", f"{service} capability"),
        ("administrative", "privileged"),
        ("action", "operation"),
        ("requested", "asked for"),
        ("selected", "chose"),
        ("called", f"invoked {capability} through"),
    ]
    rewritten = text
    for old, new in replacements:
        rewritten = rewritten.replace(old, new)
    return rewritten


def normalize_prompt_variant(prompt_variant: str) -> str:
    if prompt_variant not in CHALLENGE_VARIANTS:
        raise ValueError(f"unknown prompt variant: {prompt_variant}; expected one of {', '.join(CHALLENGE_VARIANTS)}")
    return prompt_variant


def variant_has(prompt_variant: str, feature: str) -> bool:
    if prompt_variant == "standard":
        return False
    if feature == "shuffle":
        return prompt_variant in {"shuffled_spans", "shuffled_surface_blind", "combined_blind_shuffle"}
    if feature == "rewrite":
        return prompt_variant in {"surface_reworded", "surface_reworded_blind_family", "shuffled_surface_blind", "combined_blind_shuffle"}
    if feature == "blind_family":
        return prompt_variant in {"blind_family", "surface_reworded_blind_family", "shuffled_surface_blind", "combined_blind_shuffle"}
    if feature == "rename_entities":
        return prompt_variant == "combined_blind_shuffle"
    return False


def candidate_labels_for_family(family: str) -> dict[str, list[str]]:
    if family not in FAMILY_CANDIDATE_LABELS:
        raise ValueError(f"unknown family for candidate labels: {family}")
    labels = FAMILY_CANDIDATE_LABELS[family]
    if any(label not in ALLOWED_REQUIRE_CLAUSES for label in labels["require"]):
        raise AssertionError("candidate require label is not allowed")
    if any(label not in ALLOWED_FORBID_EFFECTS for label in labels["forbid"]):
        raise AssertionError("candidate forbid label is not allowed")
    if any(label not in ALLOWED_PRESERVE_CLAUSES for label in labels["preserve"]):
        raise AssertionError("candidate preserve label is not allowed")
    return {key: list(value) for key, value in labels.items()}


def glossary_for(labels: dict[str, list[str]]) -> dict[str, str]:
    selected = sorted({label for values in labels.values() for label in values})
    return {label: LABEL_GLOSSARY[label] for label in selected}


def prompt_text_for_incident(family: str, seed: int, prompt_variant: str = "standard") -> str:
    prompt_variant = normalize_prompt_variant(prompt_variant)
    incident, _ = generate_incident(family=family, seed=seed)
    candidates = ordered_candidates_for_prompt(incident.family, seed, prompt_variant=prompt_variant)
    public_spans = incident.public_trace()
    if variant_has(prompt_variant, "shuffle"):
        public_spans = stable_trace_order(public_spans, family=incident.family, seed=seed, prompt_variant=prompt_variant)
    span_id_map = public_span_id_map(incident.family, seed, prompt_variant=prompt_variant)
    trace_lines = []
    for span in public_spans:
        visible_span_id = span_id_map[span["span_id"]]
        span_type = surface_rewrite(span["span_type"]) if variant_has(prompt_variant, "rewrite") else span["span_type"]
        summary = surface_rewrite(span["summary"]) if variant_has(prompt_variant, "rewrite") else span["summary"]
        if variant_has(prompt_variant, "rename_entities"):
            span_type = entity_rewrite(span_type, family=incident.family, seed=seed)
            summary = entity_rewrite(summary, family=incident.family, seed=seed)
        visible_tags = compact_json(span.get("visible_tags", []))
        trace_lines.append(f"- {visible_span_id} | event_type={span_type} | tags={visible_tags} | text={summary}")
    scenario = surface_rewrite(incident.scenario) if variant_has(prompt_variant, "rewrite") else incident.scenario
    if variant_has(prompt_variant, "rename_entities"):
        scenario = entity_rewrite(scenario, family=incident.family, seed=seed)
    family_line = "agent_reliability_failure" if variant_has(prompt_variant, "blind_family") else incident.family
    return f"""{strict_json_instruction()}

Episode:
family: {family_line}
prompt_variant: {prompt_variant}
scenario: {scenario}

trace:
{chr(10).join(trace_lines)}

visible_span_ids: {compact_json([span_id_map[span["span_id"]] for span in public_spans])}

Choose only from these candidates:
root_cause: {compact_json(candidates["root_cause"])}
require: {compact_json(candidates["require"])}
forbid: {compact_json(candidates["forbid"])}
preserve: {compact_json(candidates["preserve"])}
label_glossary: {compact_json(glossary_for({key: candidates[key] for key in ["require", "forbid", "preserve"]}))}

Output requirements:
- evidence_spans: choose from visible_span_ids only
- evidence_spans must identify both the failed final action and the earlier missing/unsafe control source
- do not assume span IDs from prior examples; use the IDs printed in this current trace
- if trace order or wording changes, re-read the visible span text and select evidence from this prompt
- root_cause: exactly one candidate root cause
- patch.require, patch.forbid, patch.preserve: allowed labels only
- regression_tests: short test names for blocking the failure and preserving valid behavior
- rationale: one short English sentence based on evidence spans

Now return the JSON object only.
"""


def build_prompt(family: str, seed: int, prompt_variant: str = "standard") -> list[dict[str, str]]:
    # TRL supports conversational prompt records. For Qwen Instruct models this
    # lets the trainer apply the model's chat template instead of treating the
    # instruction as raw pretraining text. The content contains only public trace
    # information and allowed labels, never hidden variants or answer keys.
    return [
        {"role": "system", "content": system_prompt()},
        {"role": "user", "content": prompt_text_for_incident(family, seed, prompt_variant=prompt_variant)},
    ]


def build_target(family: str, seed: int, prompt_variant: str = "standard") -> dict[str, Any]:
    _, oracle = generate_incident(family=family, seed=seed)
    return {
        "evidence_spans": public_evidence_spans(family, seed, list(oracle.expected_evidence_spans), prompt_variant=prompt_variant),
        "root_cause": oracle.true_root_cause,
        "patch": {
            "require": list(oracle.answer_key_clause_ids),
            "forbid": list(oracle.expected_forbid_effects),
            "preserve": list(oracle.expected_preserve_clauses),
        },
        "regression_tests": [f"reg_{family}_block_failure", f"reg_{family}_preserve_valid"],
        "rationale": "The selected evidence shows the missing control before final action.",
    }


def build_records(split: str, seeds: Iterable[int], prompt_variant: str = "standard") -> list[dict[str, Any]]:
    prompt_variant = normalize_prompt_variant(prompt_variant)
    records: list[dict[str, Any]] = []
    for family in IMPLEMENTED_FAMILIES:
        for seed in seeds:
            suffix = f"_{prompt_variant}" if prompt_variant != "standard" else ""
            records.append(
                {
                    "id": f"{split}_{family}_{seed:04d}{suffix}",
                    "split": split,
                    "family": family,
                    "seed": seed,
                    "prompt_variant": prompt_variant,
                    "prompt": build_prompt(family, seed, prompt_variant=prompt_variant),
                    "target_json": build_target(family, seed, prompt_variant=prompt_variant),
                }
            )
    return records


def parse_prompt_variants(value: str) -> list[str]:
    variants = [part.strip() for part in value.split(",") if part.strip()]
    if not variants:
        raise ValueError("at least one prompt variant is required")
    for variant in variants:
        normalize_prompt_variant(variant)
    return list(dict.fromkeys(variants))


def build_mixed_records(split: str, seeds: Iterable[int], prompt_variants: Iterable[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for prompt_variant in prompt_variants:
        rows.extend(build_records(split, seeds, prompt_variant=prompt_variant))
    return rows


def assert_prompt_has_no_hidden_answers(record: dict[str, Any]) -> None:
    prompt = json.dumps(record["prompt"], ensure_ascii=False)
    forbidden_terms = [
        "hidden_regression_variants",
        "hidden_valid_variants",
        "answer_key_clause_ids",
        "expected_patch",
        "oracle_score_details",
        "raw_seed",
        "hidden_span_labels",
    ]
    for term in forbidden_terms:
        if term in prompt:
            raise AssertionError(f"Prompt leaked hidden term: {term}")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def make_dataset(
    output_dir: Path,
    train_seeds: list[int],
    eval_seeds: list[int],
    prompt_variant: str = "standard",
    prompt_variants: list[str] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    train_prompt_variants = prompt_variants or [prompt_variant]
    train_records = build_mixed_records("train", train_seeds, train_prompt_variants)
    eval_records = build_records("eval", eval_seeds, prompt_variant=prompt_variant)
    for record in [*train_records, *eval_records]:
        assert_prompt_has_no_hidden_answers(record)
    write_jsonl(output_dir / "train.jsonl", train_records)
    write_jsonl(output_dir / "eval.jsonl", eval_records)
    summary = {
        "schema": "agent_blackbox_single_turn_json_dataset_v1",
        "families": list(IMPLEMENTED_FAMILIES),
        "train_seeds": train_seeds,
        "eval_seeds": eval_seeds,
        "train_records": len(train_records),
        "eval_records": len(eval_records),
        "prompt_variant": prompt_variant,
        "train_prompt_variants": train_prompt_variants,
        "challenge_variants": list(CHALLENGE_VARIANTS),
        "prompt_leakage_check": "passed",
    }
    (output_dir / "dataset_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate Agent BlackBox single-turn JSON repair-plan datasets.")
    parser.add_argument("--smoke", action="store_true", help="Generate a tiny CPU-only smoke dataset.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "training_dataset")
    parser.add_argument("--train-seeds", default=DEFAULT_TRAIN_SEEDS)
    parser.add_argument("--eval-seeds", default=DEFAULT_EVAL_SEEDS)
    parser.add_argument("--prompt-variant", choices=CHALLENGE_VARIANTS, default="standard")
    parser.add_argument(
        "--prompt-variants",
        default=None,
        help="Comma-separated train prompt variants. Defaults to --prompt-variant for backward compatibility.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    train_seeds = parse_seed_spec("0-1" if args.smoke else args.train_seeds)
    eval_seeds = parse_seed_spec("1000" if args.smoke else args.eval_seeds)
    prompt_variants = parse_prompt_variants(args.prompt_variants) if args.prompt_variants else None
    summary = make_dataset(args.output_dir, train_seeds, eval_seeds, prompt_variant=args.prompt_variant, prompt_variants=prompt_variants)
    print(f"make_dataset: wrote {args.output_dir / 'train.jsonl'}")
    print(f"make_dataset: wrote {args.output_dir / 'eval.jsonl'}")
    print(f"make_dataset: wrote {args.output_dir / 'dataset_summary.json'}")
    print(
        "make_dataset: "
        f"train_records={summary['train_records']} eval_records={summary['eval_records']} "
        f"families={','.join(summary['families'])} prompt_variant={summary['prompt_variant']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
