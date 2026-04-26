#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-3B-Instruct}"
MODEL_LABEL="${MODEL_LABEL:-qwen25_3b}"
OUTPUT_ROOT="${OUTPUT_ROOT:-outputs/larger_models/${MODEL_LABEL}}"
MAX_STEPS="${MAX_STEPS:-80}"
TRAIN_SEEDS="${TRAIN_SEEDS:-0-19}"
EVAL_SEEDS="${EVAL_SEEDS:-1000-1019}"
RUN_GRPO="${RUN_GRPO:-0}"

SFT_DIR="${OUTPUT_ROOT}/sft_${MODEL_LABEL}_challenge_curriculum"
GRPO_DIR="${OUTPUT_ROOT}/grpo_${MODEL_LABEL}_challenge_curriculum"
EVAL_ROOT="${OUTPUT_ROOT}/model_eval"
PLOT_ROOT="${OUTPUT_ROOT}/plots"
REPORT_ROOT="${OUTPUT_ROOT}/reports"
TRACKING_ROOT="${OUTPUT_ROOT}/tracking"
SFT_TRACKING_DIR="${TRACKING_ROOT}/sft_warmstart_sft_${MODEL_LABEL}_challenge_curriculum"
GRPO_TRACKING_DIR="${TRACKING_ROOT}/grpo_grpo_${MODEL_LABEL}_challenge_curriculum"

phase() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

print_json_if_exists() {
  local label="$1"
  local path="$2"
  echo
  echo "=== ${label} ==="
  if [[ -f "${path}" ]]; then
    python -m json.tool "${path}" || sed -n '1,220p' "${path}"
  else
    echo "MISSING: ${path}"
  fi
}

print_head_if_exists() {
  local label="$1"
  local path="$2"
  local lines="${3:-10}"
  echo
  echo "=== ${label} ==="
  if [[ -f "${path}" ]]; then
    sed -n "1,${lines}p" "${path}"
  else
    echo "MISSING: ${path}"
  fi
}

assert_append_only_root() {
  case "${OUTPUT_ROOT}" in
    outputs/larger_models/*) ;;
    *)
      echo "REFUSING: OUTPUT_ROOT must be under outputs/larger_models/ for append-only stretch runs."
      echo "Got OUTPUT_ROOT=${OUTPUT_ROOT}"
      exit 2
      ;;
  esac
}

write_sft_stoploss_report() {
  python - "$OUTPUT_ROOT" "$MODEL_NAME" "$MODEL_LABEL" "$SFT_DIR" \
    "$EVAL_ROOT/sft_${MODEL_LABEL}_standard/summary.json" \
    "$EVAL_ROOT/sft_${MODEL_LABEL}_shuffled_surface_blind/summary.json" \
    "$EVAL_ROOT/sft_${MODEL_LABEL}_combined_blind_shuffle/summary.json" <<'PY'
import json
import sys
from pathlib import Path

output_root, model_name, model_label, sft_dir, standard_path, shuffled_path, combined_path = sys.argv[1:]
report_dir = Path(output_root) / "reports"
report_dir.mkdir(parents=True, exist_ok=True)

def load(path: str) -> dict:
    path_obj = Path(path)
    if not path_obj.exists():
        return {"missing": True, "path": path}
    return json.loads(path_obj.read_text(encoding="utf-8"))

standard = load(standard_path)
shuffled = load(shuffled_path)
combined = load(combined_path)
summaries = {
    "standard": standard,
    "shuffled_surface_blind": shuffled,
    "combined_blind_shuffle": combined,
}

failures = []
warnings = []

for name, summary in summaries.items():
    if summary.get("missing"):
        failures.append(f"{name} summary is missing: {summary['path']}")
        continue
    invalid_json = float(summary.get("invalid_json_rate", 1.0))
    overblocking = float(summary.get("overblocking_rate", 1.0))
    hardcoded = float(summary.get("hardcoded_patch_rate", 1.0))
    overall = float(summary.get("overall_score", 0.0))
    evidence = float(summary.get("evidence_correct_rate", 0.0))
    certificate = float(summary.get("certificate_success_rate", 0.0))
    if invalid_json > 0.10:
        failures.append(f"{name} invalid_json_rate={invalid_json:.4f} exceeds 0.10.")
    if overblocking > 0.0:
        failures.append(f"{name} overblocking_rate={overblocking:.4f} is nonzero.")
    if hardcoded > 0.0:
        failures.append(f"{name} hardcoded_patch_rate={hardcoded:.4f} is nonzero.")
    if overall <= 0.144:
        failures.append(f"{name} overall_score={overall:.4f} does not beat random baseline 0.144.")
    if evidence == 0.0:
        failures.append(f"{name} evidence_correct_rate is zero.")
    if certificate == 0.0:
        warnings.append(f"{name} certificate_success_rate is zero; inspect completions before claiming results.")

report = {
    "mode": "larger_model_sft_stoploss",
    "model_name": model_name,
    "model_label": model_label,
    "sft_dir": sft_dir,
    "status": "PASS" if not failures else "STOP",
    "summaries": summaries,
    "failures": failures,
    "warnings": warnings,
    "decision_rule": (
        "Run GRPO only when SFT status is PASS: invalid_json <= 0.10, no overblocking, "
        "no hardcoded patches, above random baseline, and nonzero evidence on standard and challenge evals."
    ),
    "fallback": "The 0.5B challenge-curriculum SFT remains final selected evidence unless this stretch run produces real, healthier summaries.",
}
path = report_dir / "sft_stoploss_report.json"
path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"larger_model_stoploss: wrote {path}")
print(f"larger_model_stoploss: sft_quality_status={report['status']}")
PY
}

sft_quality_status() {
  python - "$REPORT_ROOT/sft_stoploss_report.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.exists():
    print("STOP")
else:
    print(json.loads(path.read_text(encoding="utf-8")).get("status", "STOP"))
PY
}

assert_append_only_root
mkdir -p "${OUTPUT_ROOT}" "${EVAL_ROOT}" "${PLOT_ROOT}" "${REPORT_ROOT}"
export AGENT_BLACKBOX_TRACKING_ROOT="${TRACKING_ROOT}"

phase "Run configuration"
cat <<EOF
MODEL_NAME=${MODEL_NAME}
MODEL_LABEL=${MODEL_LABEL}
OUTPUT_ROOT=${OUTPUT_ROOT}
MAX_STEPS=${MAX_STEPS}
TRAIN_SEEDS=${TRAIN_SEEDS}
EVAL_SEEDS=${EVAL_SEEDS}
RUN_GRPO=${RUN_GRPO}
SFT_DIR=${SFT_DIR}
GRPO_DIR=${GRPO_DIR}
TRACKING_ROOT=${TRACKING_ROOT}
EOF

phase "Preflight: self_check and generalization audit"
python scripts/self_check.py
python scripts/generalization_audit.py

phase "Base larger-model standard eval"
python training/evaluate_checkpoint.py \
  --model "${MODEL_NAME}" \
  --model-label "base_${MODEL_LABEL}" \
  --eval-seeds "${EVAL_SEEDS}" \
  --batch-size 1 \
  --output-dir "${EVAL_ROOT}/base_${MODEL_LABEL}_standard"

phase "Train larger-model LoRA SFT on mixed challenge curriculum"
python training/train_sft_warmstart.py \
  --confirm-real-training \
  --model "${MODEL_NAME}" \
  --max-steps "${MAX_STEPS}" \
  --train-seeds "${TRAIN_SEEDS}" \
  --eval-seeds "1000-1002" \
  --prompt-variants standard,shuffled_surface_blind,combined_blind_shuffle \
  --eval-prompt-variant combined_blind_shuffle \
  --output-dir "${SFT_DIR}" \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 2 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --save-steps "${MAX_STEPS}" \
  --use-lora \
  --lora-r 8 \
  --lora-alpha 16 \
  --lora-dropout 0.05 \
  --gradient-checkpointing \
  --torch-dtype bfloat16

phase "Evaluate larger-model SFT checkpoint"
python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label "sft_${MODEL_LABEL}_standard" \
  --eval-seeds "${EVAL_SEEDS}" \
  --batch-size 1 \
  --output-dir "${EVAL_ROOT}/sft_${MODEL_LABEL}_standard"

python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label "sft_${MODEL_LABEL}_shuffled_surface_blind" \
  --eval-seeds "${EVAL_SEEDS}" \
  --prompt-variant shuffled_surface_blind \
  --batch-size 1 \
  --output-dir "${EVAL_ROOT}/sft_${MODEL_LABEL}_shuffled_surface_blind"

python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label "sft_${MODEL_LABEL}_combined_blind_shuffle" \
  --eval-seeds "${EVAL_SEEDS}" \
  --prompt-variant combined_blind_shuffle \
  --batch-size 1 \
  --output-dir "${EVAL_ROOT}/sft_${MODEL_LABEL}_combined_blind_shuffle"

phase "Write SFT stop-loss report"
write_sft_stoploss_report

phase "Diagnose SFT challenge evidence predictions"
python scripts/diagnose_challenge_failures.py || true
print_head_if_exists "SFT COMBINED CHALLENGE COMPLETION EXAMPLES" "${EVAL_ROOT}/sft_${MODEL_LABEL}_combined_blind_shuffle/completions.jsonl" 10

if [[ "${RUN_GRPO}" == "1" ]]; then
  SFT_STATUS="$(sft_quality_status)"
  if [[ "${SFT_STATUS}" != "PASS" ]]; then
    echo "RUN_GRPO=1 requested, but SFT quality_status=${SFT_STATUS}; skipping GRPO by stop-loss."
  else
    phase "Run optional larger-model LoRA GRPO on mixed challenge curriculum"
    python training/train_json_grpo.py \
      --confirm-real-training \
      --model "${SFT_DIR}/model" \
      --max-steps 20 \
      --train-seeds "${TRAIN_SEEDS}" \
      --eval-seeds 1000 \
      --prompt-variants standard,shuffled_surface_blind,combined_blind_shuffle \
      --eval-prompt-variant combined_blind_shuffle \
      --output-dir "${GRPO_DIR}" \
      --num-generations 2 \
      --per-device-train-batch-size 2 \
      --gradient-accumulation-steps 1 \
      --learning-rate 3e-6 \
      --max-completion-length 160 \
      --format-reward-weight 0.2 \
      --save-steps 20 \
      --use-lora \
      --lora-r 8 \
      --lora-alpha 16 \
      --lora-dropout 0.05 \
      --gradient-checkpointing \
      --torch-dtype bfloat16 \
      --bf16

    phase "Evaluate optional larger-model SFT+GRPO checkpoint"
    python training/evaluate_checkpoint.py \
      --model "${GRPO_DIR}/model" \
      --model-label "sft_grpo_${MODEL_LABEL}_standard" \
      --eval-seeds "${EVAL_SEEDS}" \
      --batch-size 1 \
      --output-dir "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_standard"

    python training/evaluate_checkpoint.py \
      --model "${GRPO_DIR}/model" \
      --model-label "sft_grpo_${MODEL_LABEL}_shuffled_surface_blind" \
      --eval-seeds "${EVAL_SEEDS}" \
      --prompt-variant shuffled_surface_blind \
      --batch-size 1 \
      --output-dir "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_shuffled_surface_blind"

    python training/evaluate_checkpoint.py \
      --model "${GRPO_DIR}/model" \
      --model-label "sft_grpo_${MODEL_LABEL}_combined_blind_shuffle" \
      --eval-seeds "${EVAL_SEEDS}" \
      --prompt-variant combined_blind_shuffle \
      --batch-size 1 \
      --output-dir "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_combined_blind_shuffle"
  fi
else
  echo "RUN_GRPO=0, so optional GRPO is skipped. Inspect SFT stop-loss and challenge summaries first."
fi

phase "Generate plots from real larger-model summaries and tracking logs"
python scripts/plot_model_eval.py \
  --summary "base=${EVAL_ROOT}/base_${MODEL_LABEL}_standard/summary.json" \
  --summary "sft_std=${EVAL_ROOT}/sft_${MODEL_LABEL}_standard/summary.json" \
  --summary "sft_shuffle=${EVAL_ROOT}/sft_${MODEL_LABEL}_shuffled_surface_blind/summary.json" \
  --summary "sft_combined=${EVAL_ROOT}/sft_${MODEL_LABEL}_combined_blind_shuffle/summary.json" \
  --output-dir "${PLOT_ROOT}/model_eval"

python scripts/plot_training_tracking.py \
  --tracking-dir "${SFT_TRACKING_DIR}" \
  --output-dir "${PLOT_ROOT}/sft_training" || true

python scripts/plot_training_tracking.py \
  --tracking-dir "${GRPO_TRACKING_DIR}" \
  --reward-csv "${GRPO_DIR}/metrics.csv" \
  --output-dir "${PLOT_ROOT}/grpo_training" || true

phase "Final larger-model summaries"
print_json_if_exists "BASE STANDARD SUMMARY" "${EVAL_ROOT}/base_${MODEL_LABEL}_standard/summary.json"
print_json_if_exists "SFT TRAIN SUMMARY" "${SFT_DIR}/sft_summary.json"
print_json_if_exists "SFT HELDOUT SUMMARY" "${SFT_DIR}/heldout_eval_summary.json"
print_json_if_exists "SFT QUALITY REPORT" "${SFT_DIR}/sft_quality_report.json"
print_json_if_exists "SFT STOPLOSS REPORT" "${REPORT_ROOT}/sft_stoploss_report.json"
print_json_if_exists "SFT STANDARD SUMMARY" "${EVAL_ROOT}/sft_${MODEL_LABEL}_standard/summary.json"
print_json_if_exists "SFT SHUFFLED_SURFACE_BLIND SUMMARY" "${EVAL_ROOT}/sft_${MODEL_LABEL}_shuffled_surface_blind/summary.json"
print_json_if_exists "SFT COMBINED_BLIND_SHUFFLE SUMMARY" "${EVAL_ROOT}/sft_${MODEL_LABEL}_combined_blind_shuffle/summary.json"

if [[ -f "${GRPO_DIR}/stoploss_report.json" ]]; then
  print_json_if_exists "GRPO SUMMARY" "${GRPO_DIR}/summary.json"
  print_json_if_exists "GRPO HELDOUT SUMMARY" "${GRPO_DIR}/heldout_eval_summary.json"
  print_json_if_exists "GRPO STOPLOSS REPORT" "${GRPO_DIR}/stoploss_report.json"
  print_json_if_exists "SFT+GRPO STANDARD SUMMARY" "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_standard/summary.json"
  print_json_if_exists "SFT+GRPO SHUFFLED_SURFACE_BLIND SUMMARY" "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_shuffled_surface_blind/summary.json"
  print_json_if_exists "SFT+GRPO COMBINED_BLIND_SHUFFLE SUMMARY" "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_combined_blind_shuffle/summary.json"
fi

echo
echo "POST_LARGER_MODEL_STRETCH_COMPLETE model_label=${MODEL_LABEL}"
echo "Outputs are append-only under ${OUTPUT_ROOT}."
echo "No larger-model claim is valid unless the printed summaries and stop-loss reports are real and healthy."
echo "The 0.5B challenge-curriculum SFT remains fallback final evidence."
