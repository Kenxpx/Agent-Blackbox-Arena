from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

SUMMARY_LABELS = {
    "BASE 0.5B STANDARD SUMMARY": "base_0_5b_standard",
    "SFT CHALLENGE CURRICULUM TRAIN SUMMARY": "sft_0_5b_train",
    "SFT CHALLENGE CURRICULUM HELDOUT SUMMARY": "sft_0_5b_heldout",
    "SFT CHALLENGE CURRICULUM STANDARD SUMMARY": "sft_0_5b_standard",
    "SFT CHALLENGE CURRICULUM SHUFFLED_SURFACE_BLIND SUMMARY": "sft_0_5b_shuffled_surface_blind",
    "SFT CHALLENGE CURRICULUM COMBINED_BLIND_SHUFFLE SUMMARY": "sft_0_5b_combined_blind_shuffle",
    "BASE 1.5B STANDARD SUMMARY": "base_1_5b_standard",
    "1.5B SFT TRAIN SUMMARY": "sft_1_5b_train",
    "1.5B SFT HELDOUT SUMMARY": "sft_1_5b_heldout",
    "1.5B SFT STANDARD SUMMARY": "sft_1_5b_standard",
    "1.5B SFT SHUFFLED_SURFACE_BLIND SUMMARY": "sft_1_5b_shuffled_surface_blind",
    "1.5B SFT COMBINED_BLIND_SHUFFLE SUMMARY": "sft_1_5b_combined_blind_shuffle",
}


def read_log(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16", errors="replace")
    return raw.decode("utf-8", errors="replace")


def extract_json_after(text: str, label: str) -> dict[str, Any] | None:
    marker = f"=== {label} ==="
    marker_index = text.find(marker)
    if marker_index < 0:
        return None
    start = text.find("{", marker_index)
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text[start:], start):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : index + 1])
    return None


def extract_loss_rows(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    pattern = re.compile(r"\{[^{}]*'loss':\s*'[^']+'[^{}]*\}")
    for step, match in enumerate(pattern.finditer(text)):
        try:
            payload = ast.literal_eval(match.group(0))
        except (SyntaxError, ValueError):
            continue
        row: dict[str, Any] = {"step": step}
        for key in ["loss", "grad_norm", "learning_rate", "entropy", "num_tokens", "mean_token_accuracy", "epoch"]:
            if key in payload:
                try:
                    row[key] = float(payload[key])
                except (TypeError, ValueError):
                    row[key] = payload[key]
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def draw_line(points: list[tuple[int, float]], title: str, output_path: Path) -> bool:
    if len(points) < 2:
        return False
    width, height = 1100, 650
    margin_left, margin_right = 100, 40
    margin_top, margin_bottom = 95, 120
    chart_left, chart_top = margin_left, margin_top
    chart_right, chart_bottom = width - margin_right, height - margin_bottom
    chart_width, chart_height = chart_right - chart_left, chart_bottom - chart_top
    min_step, max_step = min(step for step, _ in points), max(step for step, _ in points)
    min_val, max_val = min(value for _, value in points), max(value for _, value in points)
    if min_val == max_val:
        min_val -= 0.05
        max_val += 0.05
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((margin_left, 32), title, font=font, fill="#111111")
    draw.text((margin_left, 55), "Generated from real saved HF job logs.", font=font, fill="#444444")
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#222222", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#222222", width=2)
    coords = []
    for step, value in points:
        x = chart_left + int(((step - min_step) / max(1, max_step - min_step)) * chart_width)
        y = chart_bottom - int(((value - min_val) / (max_val - min_val)) * chart_height)
        coords.append((x, y))
    draw.line(coords, fill="#3366aa", width=3)
    for x, y in coords:
        draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#3366aa")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return True


def draw_reward_bars(summaries: dict[str, dict[str, Any]], output_path: Path) -> bool:
    rows = [
        (label, payload["overall_score"])
        for label, payload in summaries.items()
        if isinstance(payload.get("overall_score"), (int, float))
    ]
    if not rows:
        return False
    width, height = 1200, 700
    margin_left, margin_right = 100, 40
    margin_top, margin_bottom = 95, 170
    chart_left, chart_top = margin_left, margin_top
    chart_right, chart_bottom = width - margin_right, height - margin_bottom
    chart_width, chart_height = chart_right - chart_left, chart_bottom - chart_top
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((margin_left, 32), "Agent BlackBox verifier reward comparison", font=font, fill="#111111")
    draw.text((margin_left, 55), "overall_score from real HF model-evaluation summaries.", font=font, fill="#444444")
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#222222", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#222222", width=2)
    slot = chart_width / len(rows)
    bar_width = int(slot * 0.55)
    for idx, (label, value) in enumerate(rows):
        center = int(chart_left + slot * idx + slot / 2)
        top = chart_bottom - int(float(value) * chart_height)
        draw.rectangle((center - bar_width // 2, top, center + bar_width // 2, chart_bottom), fill="#4c78a8", outline="#222222")
        draw.text((center - 18, max(chart_top + 4, top - 18)), f"{float(value):.2f}", font=font, fill="#111111")
        short = label.replace("sft_0_5b_", "sft_").replace("_challenge_curriculum", "")[:22]
        draw.text((center - len(short) * 3, chart_bottom + 12), short, font=font, fill="#111111")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return True


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract auditable summaries/plots from saved HF job logs.")
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "outputs" / "model_eval" / "extracted_hf")
    parser.add_argument("--plot-dir", type=Path, default=ROOT / "outputs" / "final_plots")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    text = read_log(args.log)
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir
    plot_dir = args.plot_dir if args.plot_dir.is_absolute() else ROOT / args.plot_dir
    output_dir = output_dir / args.run_label
    summaries: dict[str, dict[str, Any]] = {}
    for label, filename in SUMMARY_LABELS.items():
        payload = extract_json_after(text, label)
        if payload is None:
            continue
        summary_path = output_dir / f"{filename}_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summaries[filename] = payload
        print(f"extract_hf_job_evidence: wrote {summary_path.relative_to(ROOT)}")

    loss_rows = extract_loss_rows(text)
    if loss_rows:
        loss_csv = output_dir / "training_loss_rows.csv"
        write_csv(loss_csv, loss_rows)
        print(f"extract_hf_job_evidence: wrote {loss_csv.relative_to(ROOT)}")
        loss_plot = plot_dir / f"{args.run_label}_training_loss_curve.png"
        if draw_line([(int(row["step"]), float(row["loss"])) for row in loss_rows if isinstance(row.get("loss"), (int, float))], f"{args.run_label} real training loss", loss_plot):
            print(f"extract_hf_job_evidence: wrote {loss_plot.relative_to(ROOT)}")

    reward_plot = plot_dir / f"{args.run_label}_verifier_reward_comparison.png"
    if draw_reward_bars(summaries, reward_plot):
        print(f"extract_hf_job_evidence: wrote {reward_plot.relative_to(ROOT)}")

    status = {
        "log": str(args.log),
        "run_label": args.run_label,
        "post_complete_marker": "POST_CHALLENGE_CURRICULUM_0_5B_COMPLETE" in text
        or "POST_CHALLENGE_CURRICULUM_1_5B_COMPLETE" in text,
        "traceback_seen": "Traceback" in text,
        "error_seen": "ERROR" in text,
        "stop_seen": "STOP" in text,
        "summaries_extracted": sorted(summaries),
        "loss_rows": len(loss_rows),
    }
    status_path = output_dir / "extraction_status.json"
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"extract_hf_job_evidence: wrote {status_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
