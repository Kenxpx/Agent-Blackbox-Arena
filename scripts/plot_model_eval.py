from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

METRICS = {
    "overall_score": "baseline_vs_trained_score.png",
    "certificate_success_rate": "certificate_success_rate.png",
    "hidden_regression_pass_rate": "hidden_regression_pass_rate.png",
    "invalid_json_rate": "invalid_json_rate.png",
    "valid_preservation_rate": "valid_preservation_rate.png",
}
COLORS = ["#4c78a8", "#59a14f", "#f28e2b", "#e15759", "#b07aa1"]


def parse_summary_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("summary must use LABEL=PATH")
    label, path = value.split("=", 1)
    if not label.strip():
        raise argparse.ArgumentTypeError("summary label cannot be empty")
    return label.strip(), Path(path)


def load_summaries(items: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, path in items:
        full_path = path if path.is_absolute() else ROOT / path
        if not full_path.exists():
            raise FileNotFoundError(f"missing summary for {label}: {full_path}")
        payload = json.loads(full_path.read_text(encoding="utf-8"))
        rows.append({"label": label, **payload})
    return rows


def draw_bar_plot(rows: list[dict[str, Any]], metric: str, output_path: Path) -> None:
    width, height = 1100, 650
    margin_left, margin_right = 95, 40
    margin_top, margin_bottom = 95, 135
    chart_left, chart_top = margin_left, margin_top
    chart_right, chart_bottom = width - margin_right, height - margin_bottom
    chart_width = chart_right - chart_left
    chart_height = chart_bottom - chart_top
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((margin_left, 32), f"Agent BlackBox held-out {metric.replace('_', ' ')}", font=font, fill="#111111")
    draw.text((margin_left, 55), "Generated from real model-evaluation summary JSON files.", font=font, fill="#444444")
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#222222", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#222222", width=2)
    for tick in range(0, 6):
        value = tick / 5
        y = chart_bottom - int(value * chart_height)
        draw.line((chart_left, y, chart_right, y), fill="#dddddd", width=1)
        draw.text((chart_left - 42, y - 6), f"{value:.1f}", font=font, fill="#333333")
    slot_width = chart_width / len(rows)
    bar_width = int(slot_width * 0.55)
    for index, row in enumerate(rows):
        value = float(row[metric])
        center_x = int(chart_left + slot_width * index + slot_width / 2)
        bar_height = int(value * chart_height)
        y0 = chart_bottom - bar_height
        color = COLORS[index % len(COLORS)]
        draw.rectangle(
            (center_x - bar_width // 2, y0, center_x + bar_width // 2, chart_bottom),
            fill=color,
            outline="#222222",
            width=2,
        )
        draw.text((center_x - 18, max(chart_top + 4, y0 - 18)), f"{value:.2f}", font=font, fill="#111111")
        label = str(row["label"])[:18]
        draw.text((center_x - len(label) * 3, chart_bottom + 14), label, font=font, fill="#111111")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Plot base/SFT/GRPO held-out model evaluation summaries.")
    parser.add_argument(
        "--summary",
        action="append",
        type=parse_summary_arg,
        required=True,
        help="Add a summary as LABEL=PATH, e.g. base=outputs/eval_base/summary.json.",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "model_eval")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    rows = load_summaries(args.summary)
    for metric, filename in METRICS.items():
        draw_bar_plot(rows, metric, args.output_dir / filename)
        print(f"plot_model_eval: wrote {args.output_dir / filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
