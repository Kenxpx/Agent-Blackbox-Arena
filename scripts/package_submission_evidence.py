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

EXACT_FILES = [
    "README.md",
    "BENCHMARK_SPEC.md",
    "TRAINING.md",
    "TRAINING_RUN_LOG.md",
    "SUBMISSION_EVIDENCE.md",
    "FINAL_SUBMISSION_AUDIT.md",
    "FINAL_EXECUTION_LOG.md",
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

GLOB_PATTERNS = [
    "outputs/model_eval/**/summary.json",
    "outputs/model_eval/**/*.csv",
    "outputs/model_eval/**/*.json",
    "outputs/model_eval/**/*.jsonl",
    "outputs/model_eval/**/*.png",
    "outputs/tracking/**/*.csv",
    "outputs/tracking/**/*.json",
    "outputs/tracking/**/events.out.tfevents*",
    "outputs/final_plots/**/*.png",
    "hf_job_*_logs.txt",
    "notebooks/*.ipynb",
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


def collect_candidates() -> tuple[dict[Path, str], list[dict[str, str]]]:
    candidates: dict[Path, str] = {}
    missing: list[dict[str, str]] = []

    for item in EXACT_FILES:
        path = ROOT / item
        if path.exists() and path.is_file():
            candidates[path.resolve()] = "exact"
        else:
            missing.append({"path": item, "reason": "not present"})

    for pattern in GLOB_PATTERNS:
        matches = sorted(path for path in ROOT.glob(pattern) if path.is_file())
        if not matches:
            missing.append({"path": pattern, "reason": "no matches"})
            continue
        for path in matches:
            candidates[path.resolve()] = f"glob:{pattern}"

    return candidates, missing


def prepare_output_dir() -> None:
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()


def copy_files(candidates: dict[Path, str], missing: list[dict[str, str]]) -> dict[str, Any]:
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
        "root": str(ROOT),
        "package_dir": str(PACKAGE_DIR),
        "zip_path": str(ZIP_PATH),
        "included_count": len(included),
        "missing_count": len(missing),
        "skipped_count": len(skipped),
        "included": included,
        "missing": missing,
        "skipped": skipped,
        "safety": {
            "secrets_excluded": True,
            "model_weight_folders_excluded": True,
            "cache_folders_excluded": True,
            "max_file_bytes": MAX_FILE_BYTES,
        },
    }
    manifest_path = PACKAGE_DIR / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def write_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PACKAGE_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(PACKAGE_DIR).as_posix())


def main() -> int:
    candidates, missing = collect_candidates()
    prepare_output_dir()
    manifest = copy_files(candidates, missing)
    write_zip()
    print(f"package_submission_evidence: wrote {PACKAGE_DIR}")
    print(f"package_submission_evidence: wrote {ZIP_PATH}")
    print(
        "package_submission_evidence: "
        f"included={manifest['included_count']} missing={manifest['missing_count']} skipped={manifest['skipped_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
