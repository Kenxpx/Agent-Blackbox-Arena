#!/usr/bin/env bash
set -euo pipefail

MODEL_NAME="${MODEL_NAME:-Qwen/Qwen2.5-3B-Instruct}"
MODEL_LABEL="${MODEL_LABEL:-qwen25_3b_fast}"
OUTPUT_ROOT="${OUTPUT_ROOT:-outputs/larger_models/${MODEL_LABEL}}"
MAX_STEPS="${MAX_STEPS:-20}"
TRAIN_SEEDS="${TRAIN_SEEDS:-0-9}"
EVAL_SEEDS="${EVAL_SEEDS:-1000-1004}"
RUN_GRPO="${RUN_GRPO:-1}"
EVAL_BATCH_SIZE="${EVAL_BATCH_SIZE:-1}"

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

write_fast_sft_gate_report() {
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

summaries = {
    "standard": load(standard_path),
    "shuffled_surface_blind": load(shuffled_path),
    "combined_blind_shuffle": load(combined_path),
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
    if invalid_json > 0.10:
        failures.append(f"{name} invalid_json_rate={invalid_json:.4f} exceeds fast gate 0.10.")
    if overblocking > 0.05:
        failures.append(f"{name} overblocking_rate={overblocking:.4f} exceeds fast gate 0.05.")
    elif overblocking > 0.0:
        warnings.append(f"{name} overblocking_rate={overblocking:.4f} is nonzero; inspect before any final claim.")
    if hardcoded > 0.0:
        failures.append(f"{name} hardcoded_patch_rate={hardcoded:.4f} is nonzero.")

challenge_evidence = [
    float(summaries[name].get("evidence_correct_rate", 0.0))
    for name in ("shuffled_surface_blind", "combined_blind_shuffle")
    if not summaries[name].get("missing")
]
if not challenge_evidence or max(challenge_evidence) <= 0.0:
    failures.append("evidence_correct_rate is zero on both challenge variants.")

report = {
    "mode": "larger_model_fast_sft_gate",
    "model_name": model_name,
    "model_label": model_label,
    "sft_dir": sft_dir,
    "status": "PASS" if not failures else "STOP",
    "summaries": summaries,
    "failures": failures,
    "warnings": warnings,
    "decision_rule": (
        "Fast GRPO gate: invalid_json_rate <= 0.10 on every eval, challenge evidence > 0 "
        "on at least one challenge variant, overblocking_rate <= 0.05, and hardcoded_patch_rate == 0."
    ),
    "fallback": "The 0.5B challenge-curriculum SFT remains final selected evidence unless this fast stretch run wins on real audit metrics.",
}
path = report_dir / "fast_sft_gate_report.json"
path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"fast_sft_gate: wrote {path}")
print(f"fast_sft_gate: status={report['status']}")
PY
}

gate_status() {
  python - "$REPORT_ROOT/fast_sft_gate_report.json" <<'PY'
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

phase "Fast run configuration"
cat <<EOF
MODEL_NAME=${MODEL_NAME}
MODEL_LABEL=${MODEL_LABEL}
OUTPUT_ROOT=${OUTPUT_ROOT}
MAX_STEPS=${MAX_STEPS}
TRAIN_SEEDS=${TRAIN_SEEDS}
EVAL_SEEDS=${EVAL_SEEDS}
RUN_GRPO=${RUN_GRPO}
EVAL_BATCH_SIZE=${EVAL_BATCH_SIZE}
SFT_DIR=${SFT_DIR}
GRPO_DIR=${GRPO_DIR}
TRACKING_ROOT=${TRACKING_ROOT}
EOF

phase "Preflight: self_check and generalization audit"
python scripts/self_check.py
python scripts/generalization_audit.py

phase "Train fast larger-model LoRA SFT first"
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

phase "Evaluate fast SFT standard"
python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label "sft_${MODEL_LABEL}_standard" \
  --eval-seeds "${EVAL_SEEDS}" \
  --batch-size "${EVAL_BATCH_SIZE}" \
  --output-dir "${EVAL_ROOT}/sft_${MODEL_LABEL}_standard"

phase "Evaluate fast SFT shuffled_surface_blind"
python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label "sft_${MODEL_LABEL}_shuffled_surface_blind" \
  --eval-seeds "${EVAL_SEEDS}" \
  --prompt-variant shuffled_surface_blind \
  --batch-size "${EVAL_BATCH_SIZE}" \
  --output-dir "${EVAL_ROOT}/sft_${MODEL_LABEL}_shuffled_surface_blind"

phase "Evaluate fast SFT combined_blind_shuffle"
python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label "sft_${MODEL_LABEL}_combined_blind_shuffle" \
  --eval-seeds "${EVAL_SEEDS}" \
  --prompt-variant combined_blind_shuffle \
  --batch-size "${EVAL_BATCH_SIZE}" \
  --output-dir "${EVAL_ROOT}/sft_${MODEL_LABEL}_combined_blind_shuffle"

phase "Write fast SFT gate report"
write_fast_sft_gate_report

if [[ "${RUN_GRPO}" == "1" ]]; then
  SFT_STATUS="$(gate_status)"
  if [[ "${SFT_STATUS}" != "PASS" ]]; then
    echo "FAST_STOP: SFT fast gate status=${SFT_STATUS}; skipping GRPO and preserving logs."
  else
    phase "Run fast optional GRPO after SFT gate PASS"
    python training/train_json_grpo.py \
      --confirm-real-training \
      --model "${SFT_DIR}/model" \
      --max-steps 10 \
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
      --save-steps 10 \
      --use-lora \
      --lora-r 8 \
      --lora-alpha 16 \
      --lora-dropout 0.05 \
      --gradient-checkpointing \
      --torch-dtype bfloat16 \
      --bf16

    phase "Evaluate fast SFT+GRPO standard"
    python training/evaluate_checkpoint.py \
      --model "${GRPO_DIR}/model" \
      --model-label "sft_grpo_${MODEL_LABEL}_standard" \
      --eval-seeds "${EVAL_SEEDS}" \
      --batch-size "${EVAL_BATCH_SIZE}" \
      --output-dir "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_standard"

    phase "Evaluate fast SFT+GRPO shuffled_surface_blind"
    python training/evaluate_checkpoint.py \
      --model "${GRPO_DIR}/model" \
      --model-label "sft_grpo_${MODEL_LABEL}_shuffled_surface_blind" \
      --eval-seeds "${EVAL_SEEDS}" \
      --prompt-variant shuffled_surface_blind \
      --batch-size "${EVAL_BATCH_SIZE}" \
      --output-dir "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_shuffled_surface_blind"

    phase "Evaluate fast SFT+GRPO combined_blind_shuffle"
    python training/evaluate_checkpoint.py \
      --model "${GRPO_DIR}/model" \
      --model-label "sft_grpo_${MODEL_LABEL}_combined_blind_shuffle" \
      --eval-seeds "${EVAL_SEEDS}" \
      --prompt-variant combined_blind_shuffle \
      --batch-size "${EVAL_BATCH_SIZE}" \
      --output-dir "${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_combined_blind_shuffle"
  fi
else
  echo "RUN_GRPO=0, so GRPO is skipped."
fi

phase "Generate real fast plots"
python scripts/plot_model_eval.py \
  --summary "sft_std=${EVAL_ROOT}/sft_${MODEL_LABEL}_standard/summary.json" \
  --summary "sft_shuffle=${EVAL_ROOT}/sft_${MODEL_LABEL}_shuffled_surface_blind/summary.json" \
  --summary "sft_combined=${EVAL_ROOT}/sft_${MODEL_LABEL}_combined_blind_shuffle/summary.json" \
  --output-dir "${PLOT_ROOT}/sft_model_eval"

python scripts/plot_training_tracking.py \
  --tracking-dir "${SFT_TRACKING_DIR}" \
  --output-dir "${PLOT_ROOT}/sft_training" || true

if [[ -f "${GRPO_DIR}/metrics.csv" ]]; then
  python scripts/plot_model_eval.py \
    --summary "grpo_std=${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_standard/summary.json" \
    --summary "grpo_shuffle=${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_shuffled_surface_blind/summary.json" \
    --summary "grpo_combined=${EVAL_ROOT}/sft_grpo_${MODEL_LABEL}_combined_blind_shuffle/summary.json" \
    --output-dir "${PLOT_ROOT}/grpo_model_eval" || true
  python scripts/plot_training_tracking.py \
    --tracking-dir "${GRPO_TRACKING_DIR}" \
    --reward-csv "${GRPO_DIR}/metrics.csv" \
    --output-dir "${PLOT_ROOT}/grpo_training" || true
fi

phase "Final fast summaries"
print_json_if_exists "SFT TRAIN SUMMARY" "${SFT_DIR}/sft_summary.json"
print_json_if_exists "SFT HELDOUT SUMMARY" "${SFT_DIR}/heldout_eval_summary.json"
print_json_if_exists "FAST SFT GATE REPORT" "${REPORT_ROOT}/fast_sft_gate_report.json"
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
echo "POST_FAST_LARGER_MODEL_STRETCH_COMPLETE model_label=${MODEL_LABEL}"
echo "Outputs are append-only under ${OUTPUT_ROOT}."
echo "Use this model only if real summaries beat the 0.5B fallback on challenge audit quality."
echo "The 0.5B challenge-curriculum SFT remains fallback final evidence unless explicitly replaced by real metrics."
