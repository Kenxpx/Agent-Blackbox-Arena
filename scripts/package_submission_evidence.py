from __future__ import annotations

import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "submission_evidence"
ZIP_PATH = ROOT / "submission_evidence.zip"
MAX_FILE_BYTES = 25 * 1024 * 1024

REQUIRED_EXACT_FILES = [
    "README.md",
    "BLOG.md",
    "BENCHMARK_SPEC.md",
    "TRAINING.md",
    "TRAINING_RUN_LOG.md",
    "SUBMISSION_EVIDENCE.md",
    "FINAL_SUBMISSION_AUDIT.md",
    "FINAL_FORM_SUBMISSION_CHECKLIST.md",
    "FINAL_EXECUTION_LOG.md",
    "FINAL_RECENT_H200_RUNS_REPORT.md",
    "GENERALIZATION_AND_CLAIM_AUDIT.md",
    "SAFETY.md",
    "openenv.yaml",
    "Dockerfile",
    "pyproject.toml",
    "requirements.txt",
    "logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt",
]

OPTIONAL_EXACT_FILES = [
    "outputs/results.csv",
    "outputs/baseline_summary.json",
    "outputs/baseline_scores.png",
    "outputs/certificate_success_rate.png",
    "outputs/hidden_regression_pass_rate.png",
    "outputs/valid_preservation_rate.png",
    "outputs/grpo_tiny_hf/run_config.json",
    "outputs/grpo_tiny_hf/summary.json",
    "outputs/grpo_tiny_hf/metrics.csv",
    "outputs/grpo_tiny_hf/stoploss_report.json",
    "outputs/grpo_tiny_hf/sampled_generations.jsonl",
    "outputs/grpo_tiny_hf/heldout_eval_summary.json",
    "outputs/sft_qwen25_05b_json/run_config.json",
    "outputs/sft_qwen25_05b_json/sft_summary.json",
    "outputs/sft_qwen25_05b_json/heldout_eval_summary.json",
    "outputs/sft_qwen25_05b_json/sft_quality_report.json",
]

REQUIRED_GLOB_PATTERNS = [
    "docs/final_assets/**/*.json",
    "docs/final_assets/**/*.csv",
    "docs/final_assets/**/*.md",
    "docs/final_assets/**/*.png",
    "agent_blackbox/*.py",
    "server/*.py",
    "training/*.py",
    "scripts/*.py",
    "scripts/*.sh",
    "tests/*.py",
    "notebooks/*.ipynb",
]

OPTIONAL_GLOB_PATTERNS = [
    "outputs/model_eval/**/summary.json",
    "outputs/model_eval/**/*.csv",
    "outputs/model_eval/**/*.json",
    "outputs/model_eval/**/*.jsonl",
    "outputs/model_eval/**/*.png",
    "outputs/tracking/**/*.csv",
    "outputs/tracking/**/*.json",
    "outputs/tracking/**/events.out.tfevents*",
    "outputs/final_plots/**/*.png",
    "outputs/larger_models/qwen3_4b_2507_final_h200/plots/**/*.png",
    "outputs/larger_models/qwen3_4b_2507_final_h200/tracking/**/*.csv",
    "outputs/larger_models/qwen3_4b_2507_final_h200/tracking/**/*.json",
    "outputs/larger_models/qwen3_4b_2507_final_h200/tracking/**/events.out.tfevents*",
    "notebooks/*.md",
]

FORBIDDEN_PARTS = {
    ".git",
    ".cache",
    ".pytest_cache",
    "__pycache__",
    "wandb",
    "runs",
    "model",
}

FORBIDDEN_SUFFIXES = {
    ".token",
    ".env",
    ".bin",
    ".safetensors",
    ".pt",
    ".pth",
    ".ckpt",
}

SECRET_PATTERNS = [
    re.compile(r"hf_[A-Za-z0-9]{20,}"),
    re.compile(r"HF_TOKEN\s*="),
    re.compile(r"HUGGING_FACE_HUB_TOKEN\s*="),
]


def rel(path: Path) -> Path:
    return path.resolve().relative_to(ROOT.resolve())


def should_skip(path: Path) -> tuple[bool, str]:
    relative = rel(path)
    lower_parts = {part.lower() for part in relative.parts}
    lower_name = path.name.lower()
    if lower_parts & FORBIDDEN_PARTS:
        return True, "forbidden path component"
    if lower_name == ".env" or lower_name.startswith("hf_token"):
        return True, "possible secret/token file"
    if "token" in lower_name and lower_name.endswith(".txt"):
        return True, "possible secret/token file"
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True, "forbidden file suffix"
    if path.stat().st_size > MAX_FILE_BYTES:
        return True, f"file exceeds {MAX_FILE_BYTES} byte limit"
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        text = ""
    if any(pattern.search(text) for pattern in SECRET_PATTERNS):
        return True, "possible secret/token content"
    return False, ""


def collect_candidates() -> tuple[dict[Path, str], list[dict[str, str]], list[dict[str, str]]]:
    candidates: dict[Path, str] = {}
    missing_required: list[dict[str, str]] = []
    missing_optional: list[dict[str, str]] = []

    for item in REQUIRED_EXACT_FILES:
        path = ROOT / item
        if path.exists() and path.is_file():
            candidates[path.resolve()] = "required_exact"
        else:
            missing_required.append({"path": item, "reason": "not present"})

    for item in OPTIONAL_EXACT_FILES:
        path = ROOT / item
        if path.exists() and path.is_file():
            candidates[path.resolve()] = "optional_exact"
        else:
            missing_optional.append({"path": item, "reason": "optional historical artifact not present"})

    for pattern in REQUIRED_GLOB_PATTERNS:
        matches = sorted(path for path in ROOT.glob(pattern) if path.is_file())
        if not matches:
            missing_required.append({"path": pattern, "reason": "no matches"})
            continue
        for path in matches:
            candidates[path.resolve()] = f"required_glob:{pattern}"

    for pattern in OPTIONAL_GLOB_PATTERNS:
        matches = sorted(path for path in ROOT.glob(pattern) if path.is_file())
        if not matches:
            missing_optional.append({"path": pattern, "reason": "optional historical artifact not present"})
            continue
        for path in matches:
            candidates[path.resolve()] = f"optional_glob:{pattern}"

    return candidates, missing_required, missing_optional


def prepare_output_dir() -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()


def write_manifest_note(
    included: list[dict[str, Any]],
    missing_required: list[dict[str, str]],
    missing_optional: list[dict[str, str]],
    skipped: list[dict[str, str]],
) -> None:
    note = f"""# Submission Evidence Manifest

Canonical final evidence is stored in:

- `docs/final_assets/` for final Qwen3-4B metrics, tables, and plots
- `logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt` for the final H200 log
- `SUBMISSION_EVIDENCE.md`, `FINAL_SUBMISSION_AUDIT.md`, and `FINAL_FORM_SUBMISSION_CHECKLIST.md` for claim boundaries and form links

`missing_required_count` must be `0` for a complete package. `optional_missing_count` can be nonzero because historical or remote H200 output folders are not required when their canonical final metrics/log evidence is present in `docs/final_assets/` and `logs/final/`.

- Included files: {len(included)}
- Missing required files: {len(missing_required)}
- Missing optional historical artifacts: {len(missing_optional)}
- Skipped unsafe/large files: {len(skipped)}
"""
    (PACKAGE_DIR / "MANIFEST.md").write_text(note, encoding="utf-8")


def copy_files(
    candidates: dict[Path, str],
    missing_required: list[dict[str, str]],
    missing_optional: list[dict[str, str]],
) -> dict[str, Any]:
    included: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []

    for source, source_kind in sorted(candidates.items(), key=lambda item: str(rel(item[0])).lower()):
        skip, reason = should_skip(source)
        relative = rel(source)
        if skip:
            skipped.append({"path": relative.as_posix(), "reason": reason})
            continue
        destination = PACKAGE_DIR / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        included.append(
            {
                "path": relative.as_posix(),
                "bytes": source.stat().st_size,
                "source": source_kind,
            }
        )

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": ".",
        "package_dir": PACKAGE_DIR.name,
        "zip_path": ZIP_PATH.name,
        "included_count": len(included),
        "missing_required_count": len(missing_required),
        "optional_missing_count": len(missing_optional),
        "skipped_count": len(skipped),
        "included": included,
        "missing_required": missing_required,
        "optional_missing": missing_optional,
        "skipped": skipped,
        "safety": {
            "secrets_excluded": True,
            "model_weight_folders_excluded": True,
            "cache_folders_excluded": True,
            "max_file_bytes": MAX_FILE_BYTES,
        },
    }
    write_manifest_note(included, missing_required, missing_optional, skipped)
    manifest_path = PACKAGE_DIR / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def write_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(PACKAGE_DIR).as_posix())


def main() -> int:
    candidates, missing_required, missing_optional = collect_candidates()
    prepare_output_dir()
    manifest = copy_files(candidates, missing_required, missing_optional)
    write_zip()
    print(f"package_submission_evidence: wrote {PACKAGE_DIR}")
    print(f"package_submission_evidence: wrote {ZIP_PATH}")
    print(
        "package_submission_evidence: "
        f"included={manifest['included_count']} "
        f"missing_required={manifest['missing_required_count']} "
        f"optional_missing={manifest['optional_missing_count']} "
        f"skipped={manifest['skipped_count']}"
    )
    return 1 if manifest["missing_required_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
