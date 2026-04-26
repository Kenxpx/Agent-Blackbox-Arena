from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def numeric_points(rows: list[dict[str, str]], metric: str, step_key: str = "step") -> list[tuple[int, float]]:
    points: list[tuple[int, float]] = []
    for index, row in enumerate(rows):
        raw_value = row.get(metric)
        if raw_value in (None, ""):
            continue
        try:
            value = float(raw_value)
        except ValueError:
            continue
        raw_step = row.get(step_key, row.get("epoch", index))
        try:
            step = int(float(raw_step))
        except (TypeError, ValueError):
            step = index
        points.append((step, value))
    return points


def draw_line(points: list[tuple[int, float]], title: str, y_label: str, output_path: Path) -> bool:
    if len(points) < 2:
        return False
    width, height = 1100, 650
    margin_left, margin_right = 100, 40
    margin_top, margin_bottom = 95, 120
    chart_left, chart_top = margin_left, margin_top
    chart_right, chart_bottom = width - margin_right, height - margin_bottom
    chart_width = chart_right - chart_left
    chart_height = chart_bottom - chart_top

    min_step, max_step = min(step for step, _ in points), max(step for step, _ in points)
    min_val, max_val = min(value for _, value in points), max(value for _, value in points)
    if min_val == max_val:
        min_val -= 0.05
        max_val += 0.05

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((margin_left, 32), title, font=font, fill="#111111")
    draw.text((margin_left, 55), "Generated from real CSV/TensorBoard-compatible training logs.", font=font, fill="#444444")
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#222222", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#222222", width=2)
    for tick in range(0, 6):
        value = min_val + (max_val - min_val) * tick / 5
        y = chart_bottom - int(((value - min_val) / (max_val - min_val)) * chart_height)
        draw.line((chart_left, y, chart_right, y), fill="#dddddd", width=1)
        draw.text((chart_left - 72, y - 6), f"{value:.2f}", font=font, fill="#333333")

    coords: list[tuple[int, int]] = []
    for step, value in points:
        x = chart_left + int(((step - min_step) / max(1, max_step - min_step)) * chart_width)
        y = chart_bottom - int(((value - min_val) / (max_val - min_val)) * chart_height)
        coords.append((x, y))
    draw.line(coords, fill="#3366aa", width=3)
    for x, y in coords:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#3366aa")
    draw.text((margin_left, height - 72), "training step", font=font, fill="#111111")
    draw.text((18, chart_top + chart_height // 2 - 16), y_label, font=font, fill="#111111")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")
    return True


def collect_trainer_rows(tracking_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(tracking_dir.glob("**/trainer_log_history.csv")):
        rows.extend(read_csv(path))
    return rows


def collect_reward_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.extend(read_csv(path))
    return rows


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create real loss/reward plots from training tracking logs.")
    parser.add_argument("--tracking-dir", type=Path, default=ROOT / "outputs" / "tracking")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "final_plots")
    parser.add_argument(
        "--reward-csv",
        action="append",
        type=Path,
        default=[],
        help="CSV containing verifier reward rows, e.g. outputs/grpo_x/metrics.csv.",
    )
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    tracking_dir = args.tracking_dir if args.tracking_dir.is_absolute() else ROOT / args.tracking_dir
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir

    trainer_rows = collect_trainer_rows(tracking_dir)
    loss_written = draw_line(
        numeric_points(trainer_rows, "loss"),
        "Agent BlackBox real training loss",
        "loss",
        output_dir / "training_loss_curve.png",
    )
    if loss_written:
        print(f"plot_training_tracking: wrote {output_dir / 'training_loss_curve.png'}")
    else:
        print("plot_training_tracking: skipped loss plot; no real loss series found")

    reward_paths = [path if path.is_absolute() else ROOT / path for path in args.reward_csv]
    if not reward_paths:
        reward_paths = sorted((ROOT / "outputs").glob("grpo*/metrics.csv")) + [ROOT / "outputs" / "training_metrics.csv"]
    reward_rows = collect_reward_rows(reward_paths)
    reward_written = draw_line(
        numeric_points(reward_rows, "reward"),
        "Agent BlackBox real verifier reward",
        "verifier reward",
        output_dir / "training_reward_curve.png",
    )
    if reward_written:
        print(f"plot_training_tracking: wrote {output_dir / 'training_reward_curve.png'}")
    else:
        print("plot_training_tracking: skipped reward plot; no real reward series found")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
