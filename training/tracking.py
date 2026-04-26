from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_TRACKING_ROOT_ENV = os.environ.get("AGENT_BLACKBOX_TRACKING_ROOT")
TRACKING_ROOT = Path(_TRACKING_ROOT_ENV) if _TRACKING_ROOT_ENV else ROOT / "outputs" / "tracking"
if not TRACKING_ROOT.is_absolute():
    TRACKING_ROOT = ROOT / TRACKING_ROOT


def tracking_run_dir(output_dir: Path, run_type: str) -> Path:
    name = output_dir.name or run_type
    return TRACKING_ROOT / f"{run_type}_{name}"


def flatten_scalars(prefix: str, payload: dict[str, Any]) -> dict[str, float]:
    scalars: dict[str, float] = {}
    for key, value in payload.items():
        name = f"{prefix}/{key}" if prefix else key
        if isinstance(value, bool):
            scalars[name] = float(value)
        elif isinstance(value, (int, float)):
            scalars[name] = float(value)
        elif isinstance(value, dict):
            scalars.update(flatten_scalars(name, value))
    return scalars


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def trainer_log_history(trainer: Any) -> list[dict[str, Any]]:
    state = getattr(trainer, "state", None)
    history = getattr(state, "log_history", None)
    if not isinstance(history, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in history:
        if isinstance(item, dict):
            rows.append(dict(item))
    return rows


def write_tensorboard_scalars(run_dir: Path, rows: list[dict[str, Any]], *, step_key: str = "step", prefix: str = "") -> bool:
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        from torch.utils.tensorboard import SummaryWriter  # type: ignore
    except Exception as exc:
        (run_dir / "tensorboard_unavailable.json").write_text(
            json.dumps({"available": False, "error": str(exc)}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return False

    writer = SummaryWriter(log_dir=str(run_dir))
    try:
        for index, row in enumerate(rows):
            raw_step = row.get(step_key, index)
            try:
                step = int(float(raw_step))
            except (TypeError, ValueError):
                step = index
            for key, value in row.items():
                if key == step_key or value in (None, ""):
                    continue
                if isinstance(value, bool):
                    scalar = float(value)
                elif isinstance(value, (int, float)):
                    scalar = float(value)
                else:
                    try:
                        scalar = float(value)
                    except (TypeError, ValueError):
                        continue
                tag = f"{prefix}/{key}" if prefix else key
                writer.add_scalar(tag, scalar, step)
    finally:
        writer.flush()
        writer.close()
    return True


def write_summary_tracking(run_dir: Path, payloads: dict[str, dict[str, Any]]) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    scalars: dict[str, float] = {}
    for prefix, payload in payloads.items():
        scalars.update(flatten_scalars(prefix, payload))
    rows = [{"step": 0, **scalars}] if scalars else []
    if rows:
        write_tensorboard_scalars(run_dir / "summary", rows)
    summary_path = run_dir / "summary_scalars.json"
    summary_path.write_text(json.dumps(scalars, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary_path


def write_training_tracking(
    output_dir: Path,
    run_type: str,
    *,
    trainer_history: list[dict[str, Any]] | None = None,
    verifier_rows: list[dict[str, Any]] | None = None,
    summaries: dict[str, dict[str, Any]] | None = None,
) -> Path:
    run_dir = tracking_run_dir(output_dir, run_type)
    run_dir.mkdir(parents=True, exist_ok=True)
    if trainer_history:
        write_csv(run_dir / "trainer_log_history.csv", trainer_history)
        write_tensorboard_scalars(run_dir / "trainer", trainer_history, prefix="trainer")
    if verifier_rows:
        write_csv(run_dir / "verifier_metrics.csv", verifier_rows)
        write_tensorboard_scalars(run_dir / "verifier", verifier_rows, step_key="step", prefix="verifier")
    if summaries:
        write_summary_tracking(run_dir, summaries)
    (run_dir / "tracking_status.json").write_text(
        json.dumps(
            {
                "tracking_enabled": True,
                "format": "csv/json plus TensorBoard event files when tensorboard is installed",
                "run_type": run_type,
                "output_dir": str(output_dir),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir
