from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = ROOT / "outputs"
RESULTS_CSV = OUTPUT_DIR / "results.csv"
SUMMARY_JSON = OUTPUT_DIR / "baseline_summary.json"
FUTURE_TRAINING_METRICS = OUTPUT_DIR / "training_metrics.csv"

PLOTS = {
    "overall_score": OUTPUT_DIR / "baseline_scores.png",
    "certificate_success_rate": OUTPUT_DIR / "certificate_success_rate.png",
    "hidden_regression_pass_rate": OUTPUT_DIR / "hidden_regression_pass_rate.png",
    "valid_preservation_rate": OUTPUT_DIR / "valid_preservation_rate.png",
}

BASELINE_ORDER = [
    "random_patch",
    "explanation_only",
    "block_everything",
    "visible_overfit",
    "oracle_correct_solver_for_sanity",
]
BASELINE_LABELS = ["random", "explain", "block-all", "overfit", "oracle"]
BAR_COLORS = ["#8da0cb", "#66c2a5", "#fc8d62", "#e78ac3", "#a6d854"]


def load_inputs() -> tuple[list[dict[str, str]], dict[str, Any]]:
    if not RESULTS_CSV.exists():
        raise FileNotFoundError(f"Missing {RESULTS_CSV}; run scripts/evaluate_baselines.py first.")
    if not SUMMARY_JSON.exists():
        raise FileNotFoundError(f"Missing {SUMMARY_JSON}; run scripts/evaluate_baselines.py first.")
    with RESULTS_CSV.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    summary = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
    if not rows:
        raise ValueError("results.csv has no rows.")
    return rows, summary


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, fill: str) -> None:
    width, _ = text_size(draw, text, font)
    draw.text((xy[0] - width // 2, xy[1]), text, font=font, fill=fill)


def plot_metric(summary: dict[str, Any], metric: str, output_path: Path) -> None:
    width, height = 1100, 650
    margin_left, margin_right = 100, 40
    margin_top, margin_bottom = 95, 135
    chart_left, chart_top = margin_left, margin_top
    chart_right, chart_bottom = width - margin_right, height - margin_bottom
    chart_width = chart_right - chart_left
    chart_height = chart_bottom - chart_top

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    title_font = ImageFont.load_default()

    title = f"Agent BlackBox baseline-only {metric.replace('_', ' ')}"
    draw.text((margin_left, 32), title, font=title_font, fill="#111111")
    draw.text(
        (margin_left, 55),
        "Generated from outputs/results.csv and outputs/baseline_summary.json. No trained model rows.",
        font=font,
        fill="#444444",
    )

    # Axes and horizontal grid.
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#222222", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#222222", width=2)
    for tick in range(0, 6):
        value = tick / 5
        y = chart_bottom - int(value * chart_height)
        draw.line((chart_left, y, chart_right, y), fill="#dddddd", width=1)
        draw.text((chart_left - 42, y - 6), f"{value:.1f}", font=font, fill="#333333")

    values = [float(summary["baselines"][baseline][metric]) for baseline in BASELINE_ORDER]
    slot_width = chart_width / len(BASELINE_ORDER)
    bar_width = int(slot_width * 0.58)
    for idx, (label, value, color) in enumerate(zip(BASELINE_LABELS, values, BAR_COLORS)):
        center_x = int(chart_left + slot_width * idx + slot_width / 2)
        bar_height = int(value * chart_height)
        x0 = center_x - bar_width // 2
        x1 = center_x + bar_width // 2
        y0 = chart_bottom - bar_height
        y1 = chart_bottom
        draw.rectangle((x0, y0, x1, y1), fill=hex_to_rgb(color), outline="#222222", width=2)
        draw_centered(draw, (center_x, max(chart_top + 4, y0 - 18)), f"{value:.2f}", font, "#111111")
        draw_centered(draw, (center_x, chart_bottom + 14), label, font, "#111111")

    draw.text((margin_left, height - 80), "pre-training baseline policy", font=font, fill="#111111")
    draw.text((18, chart_top + chart_height // 2 - 16), metric.replace("_", " "), font=font, fill="#111111")
    image.save(output_path, format="PNG")


def plot_training_metric(rows: list[dict[str, str]], metric: str, output_path: Path) -> None:
    points = [(int(row["step"]), float(row[metric])) for row in rows if row.get(metric) not in (None, "")]
    if len(points) < 2:
        return

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
    draw.text((margin_left, 32), f"Agent BlackBox real training {metric}", font=font, fill="#111111")
    draw.text((margin_left, 55), "Generated only when outputs/training_metrics.csv exists.", font=font, fill="#444444")
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#222222", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#222222", width=2)

    coords: list[tuple[int, int]] = []
    for step, value in points:
        x = chart_left + int(((step - min_step) / max(1, max_step - min_step)) * chart_width)
        y = chart_bottom - int(((value - min_val) / (max_val - min_val)) * chart_height)
        coords.append((x, y))
    if len(coords) >= 2:
        draw.line(coords, fill="#3366aa", width=3)
    for x, y in coords:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#3366aa")
    draw.text((margin_left, height - 72), "training step", font=font, fill="#111111")
    draw.text((18, chart_top + chart_height // 2 - 16), metric, font=font, fill="#111111")
    image.save(output_path, format="PNG")


def maybe_plot_future_training_metrics() -> None:
    if not FUTURE_TRAINING_METRICS.exists():
        print("make_plots: no outputs/training_metrics.csv found; skipped training plots")
        return
    with FUTURE_TRAINING_METRICS.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        print("make_plots: outputs/training_metrics.csv is empty; skipped training plots")
        return
    if "reward" in rows[0]:
        plot_training_metric(rows, "reward", OUTPUT_DIR / "training_reward_curve.png")
        print("make_plots: wrote outputs\\training_reward_curve.png")
    if "loss" in rows[0]:
        plot_training_metric(rows, "loss", OUTPUT_DIR / "training_loss_curve.png")
        print("make_plots: wrote outputs\\training_loss_curve.png")


def main() -> int:
    rows, summary = load_inputs()
    if len(rows) != 150:
        raise ValueError(f"Expected 150 baseline rows, found {len(rows)}.")
    for metric, output_path in PLOTS.items():
        plot_metric(summary, metric, output_path)
        print(f"make_plots: wrote {output_path.relative_to(ROOT)}")
    maybe_plot_future_training_metrics()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
