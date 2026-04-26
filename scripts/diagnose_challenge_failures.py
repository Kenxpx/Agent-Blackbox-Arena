from __future__ import annotations

from collections import Counter, defaultdict
import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.evaluate_model import parse_completion, score_completion
from training.make_dataset import build_records, build_target, parse_seed_spec


DEFAULT_GLOBS = [
    "outputs/model_eval/**/completions.jsonl",
    "outputs/grpo_tiny_hf/heldout_eval_completions.jsonl",
    "outputs/grpo_tiny_hf/sampled_generations.jsonl",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def infer_prompt_variant(row: dict[str, Any], path: Path) -> str:
    if row.get("prompt_variant"):
        return str(row["prompt_variant"])
    text = " ".join(str(value) for value in [row.get("prompt_id", ""), row.get("id", ""), path.as_posix()])
    for variant in ["combined_blind_shuffle", "shuffled_surface_blind", "surface_reworded_blind_family", "blind_family", "surface_reworded", "shuffled_spans"]:
        if variant in text:
            return variant
    return "standard"


def expected_visible_ids(family: str, seed: int, prompt_variant: str) -> list[str]:
    return list(build_target(family, seed, prompt_variant=prompt_variant)["evidence_spans"])


def gate_failure_reasons(metrics: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if metrics["invalid_json"]:
        reasons.append("invalid_json")
    if not metrics["evidence_correct"]:
        reasons.append("wrong_evidence")
    if not metrics["root_cause_correct"]:
        reasons.append("wrong_root_cause")
    if not metrics["patch_blocks_failure"]:
        reasons.append("patch_does_not_block_failure")
    if metrics["valid_preservation_rate"] < 1.0:
        reasons.append("valid_preservation_incomplete")
    if metrics["overblocking"]:
        reasons.append("overblocking")
    if metrics["hardcoded_patch"]:
        reasons.append("hardcoded_patch")
    if not reasons and not metrics["certificate_success"]:
        reasons.append("certificate_gate_unmet")
    return reasons


def discover_files(patterns: list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(dict.fromkeys(paths))


def analyze_files(paths: list[Path]) -> dict[str, Any]:
    by_family: Counter[str] = Counter()
    by_variant: Counter[str] = Counter()
    wrong_evidence_by_family: Counter[str] = Counter()
    wrong_evidence_by_variant: Counter[str] = Counter()
    gate_reasons: Counter[str] = Counter()
    repeated_wrong_evidence: Counter[str] = Counter()
    repeated_wrong_clauses: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    overblocking_examples: list[dict[str, Any]] = []
    copied_standard_ids = 0
    rows_seen = 0

    for path in paths:
        for row in load_jsonl(path):
            if "completion" not in row or "family" not in row or "seed" not in row:
                continue
            family = str(row["family"])
            seed = int(row["seed"])
            prompt_variant = infer_prompt_variant(row, path)
            completion = str(row["completion"])
            parsed, parse_error = parse_completion(completion)
            metrics = score_completion(family, seed, completion, prompt_variant=prompt_variant)
            expected = expected_visible_ids(family, seed, prompt_variant)
            predicted = list(parsed["evidence_spans"]) if parsed else []
            rows_seen += 1
            by_family[family] += 1
            by_variant[prompt_variant] += 1
            for reason in gate_failure_reasons(metrics):
                gate_reasons[reason] += 1

            if metrics["evidence_correct"] == 0.0:
                wrong_evidence_by_family[family] += 1
                wrong_evidence_by_variant[prompt_variant] += 1
                repeated_wrong_evidence[json.dumps(predicted, sort_keys=True)] += 1
                if set(predicted) == {"s2", "s4"}:
                    copied_standard_ids += 1
                if len(examples) < 20:
                    patch = parsed.get("patch", {}) if parsed else {}
                    examples.append(
                        {
                            "source": path.as_posix(),
                            "prompt_id": row.get("prompt_id") or row.get("id", ""),
                            "family": family,
                            "seed": seed,
                            "prompt_variant": prompt_variant,
                            "expected_evidence": expected,
                            "predicted_evidence": predicted,
                            "root_cause": parsed.get("root_cause") if parsed else None,
                            "require": patch.get("require") if isinstance(patch, dict) else None,
                            "forbid": patch.get("forbid") if isinstance(patch, dict) else None,
                            "preserve": patch.get("preserve") if isinstance(patch, dict) else None,
                            "parse_error": parse_error,
                            "metrics": metrics,
                            "gate_failure_reasons": gate_failure_reasons(metrics),
                        }
                    )

            if metrics["overblocking"]:
                if len(overblocking_examples) < 20:
                    overblocking_examples.append(
                        {
                            "source": path.as_posix(),
                            "prompt_id": row.get("prompt_id") or row.get("id", ""),
                            "family": family,
                            "seed": seed,
                            "prompt_variant": prompt_variant,
                            "completion": completion[:1000],
                            "metrics": metrics,
                        }
                    )

            if parsed and isinstance(parsed.get("patch"), dict):
                patch = parsed["patch"]
                for field in ["require", "forbid", "preserve"]:
                    values = patch.get(field, [])
                    if isinstance(values, list):
                        for value in values:
                            repeated_wrong_clauses[f"{field}:{value}"] += 1

    return {
        "files": [path.as_posix() for path in paths],
        "rows_seen": rows_seen,
        "by_family": dict(by_family),
        "by_prompt_variant": dict(by_variant),
        "wrong_evidence_by_family": dict(wrong_evidence_by_family),
        "wrong_evidence_by_prompt_variant": dict(wrong_evidence_by_variant),
        "certificate_gate_failure_reasons": dict(gate_reasons),
        "top_wrong_evidence_patterns": dict(repeated_wrong_evidence.most_common(10)),
        "top_clause_patterns": dict(repeated_wrong_clauses.most_common(20)),
        "copied_standard_s2_s4_count": copied_standard_ids,
        "wrong_evidence_examples": examples,
        "overblocking_examples": overblocking_examples,
    }


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Challenge Failure Diagnosis Output",
        "",
        f"Rows seen: `{report['rows_seen']}`",
        "",
        "## Files",
    ]
    if report["files"]:
        lines.extend(f"- `{item}`" for item in report["files"])
    else:
        lines.append("No completion artifacts were found. Expected files from a future HF run include `outputs/model_eval/**/completions.jsonl` and `outputs/grpo_tiny_hf/heldout_eval_completions.jsonl`.")
    lines.extend(
        [
            "",
            "## Summary JSON",
            "",
            "```json",
            json.dumps(report, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose challenge evidence and certificate failures from model completion artifacts.")
    parser.add_argument("--glob", action="append", default=None, help="Completion JSONL glob relative to repo root.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "challenge_failure_diagnosis")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    patterns = args.glob or DEFAULT_GLOBS
    paths = discover_files(patterns)
    report = analyze_files(paths)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "diagnosis.json"
    md_path = args.output_dir / "diagnosis.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(md_path, report)
    print(f"diagnose_challenge_failures: files={len(paths)} rows={report['rows_seen']}")
    print(f"diagnose_challenge_failures: wrote {json_path}")
    print(f"diagnose_challenge_failures: wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
