#!/usr/bin/env bash
set -euo pipefail

if [[ "${CONFIRM_4B_AFTER_15B_PASSED:-0}" != "1" ]]; then
  echo "LOCKED: 4B stretch is disabled until 1.5B challenge-curriculum evidence passes."
  echo "Set CONFIRM_4B_AFTER_15B_PASSED=1 only after 1.5B summaries justify the extra spend."
  exit 2
fi

RUN_GRPO="${RUN_GRPO:-0}"
MODEL_ID="${MODEL_ID:-Qwen/Qwen3-4B-Instruct-2507}"
SFT_DIR="${SFT_DIR:-outputs/sft_qwen3_4b_challenge_curriculum}"
GRPO_DIR="${GRPO_DIR:-outputs/grpo_4b_challenge_curriculum}"

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
    cat "${path}"
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
    head -n "${lines}" "${path}"
  else
    echo "MISSING: ${path}"
  fi
}

phase "Preflight: self_check and generalization audit"
python scripts/self_check.py
python scripts/generalization_audit.py

phase "Base 4B standard eval"
python training/evaluate_checkpoint.py \
  --model "${MODEL_ID}" \
  --model-label base_4b \
  --eval-seeds 1000-1019 \
  --output-dir outputs/model_eval/base_4b_standard

phase "Train 4B LoRA SFT stretch on mixed challenge curriculum"
python training/train_sft_warmstart.py \
  --confirm-real-training \
  --model "${MODEL_ID}" \
  --max-steps 80 \
  --train-seeds 0-19 \
  --eval-seeds 1000-1002 \
  --prompt-variants standard,shuffled_surface_blind,combined_blind_shuffle \
  --eval-prompt-variant combined_blind_shuffle \
  --output-dir "${SFT_DIR}" \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 2 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --save-steps 80 \
  --use-lora \
  --lora-r 8 \
  --lora-alpha 16 \
  --lora-dropout 0.05 \
  --gradient-checkpointing

phase "Evaluate 4B SFT stretch checkpoint"
python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label sft_4b_challenge_curriculum_standard \
  --eval-seeds 1000-1019 \
  --output-dir outputs/model_eval/sft_4b_challenge_curriculum_standard

python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label sft_4b_challenge_curriculum_shuffled_surface_blind \
  --eval-seeds 1000-1019 \
  --prompt-variant shuffled_surface_blind \
  --output-dir outputs/model_eval/sft_4b_challenge_curriculum_shuffled_surface_blind

python training/evaluate_checkpoint.py \
  --model "${SFT_DIR}/model" \
  --model-label sft_4b_challenge_curriculum_combined_blind_shuffle \
  --eval-seeds 1000-1019 \
  --prompt-variant combined_blind_shuffle \
  --output-dir outputs/model_eval/sft_4b_challenge_curriculum_combined_blind_shuffle

phase "Diagnose 4B SFT challenge evidence predictions"
python scripts/diagnose_challenge_failures.py
print_head_if_exists "4B SFT COMBINED CHALLENGE COMPLETIONS" "outputs/model_eval/sft_4b_challenge_curriculum_combined_blind_shuffle/completions.jsonl" 10

if [[ "${RUN_GRPO}" == "1" ]]; then
  phase "Run optional 4B LoRA GRPO stretch on mixed challenge curriculum"
  python training/train_json_grpo.py \
    --confirm-real-training \
    --model "${SFT_DIR}/model" \
    --max-steps 20 \
    --train-seeds 0-9 \
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
    --gradient-checkpointing
else
  echo "RUN_GRPO=0, so 4B GRPO is skipped by default. Inspect SFT challenge summaries first."
fi

phase "Generate plots from real 4B model-eval summaries"
python scripts/plot_model_eval.py \
  --summary base=outputs/model_eval/base_4b_standard/summary.json \
  --summary sft_std=outputs/model_eval/sft_4b_challenge_curriculum_standard/summary.json \
  --summary sft_shuffle=outputs/model_eval/sft_4b_challenge_curriculum_shuffled_surface_blind/summary.json \
  --summary sft_combined=outputs/model_eval/sft_4b_challenge_curriculum_combined_blind_shuffle/summary.json \
  --output-dir outputs/model_eval/challenge_curriculum_4b

phase "Final 4B summaries"
print_json_if_exists "BASE 4B STANDARD SUMMARY" "outputs/model_eval/base_4b_standard/summary.json"
print_json_if_exists "4B SFT TRAIN SUMMARY" "${SFT_DIR}/sft_summary.json"
print_json_if_exists "4B SFT HELDOUT SUMMARY" "${SFT_DIR}/heldout_eval_summary.json"
print_json_if_exists "4B SFT STANDARD SUMMARY" "outputs/model_eval/sft_4b_challenge_curriculum_standard/summary.json"
print_json_if_exists "4B SFT SHUFFLED_SURFACE_BLIND SUMMARY" "outputs/model_eval/sft_4b_challenge_curriculum_shuffled_surface_blind/summary.json"
print_json_if_exists "4B SFT COMBINED_BLIND_SHUFFLE SUMMARY" "outputs/model_eval/sft_4b_challenge_curriculum_combined_blind_shuffle/summary.json"

if [[ "${RUN_GRPO}" == "1" ]]; then
  print_json_if_exists "4B GRPO SUMMARY" "${GRPO_DIR}/summary.json"
  print_json_if_exists "4B GRPO HELDOUT SUMMARY" "${GRPO_DIR}/heldout_eval_summary.json"
  print_json_if_exists "4B GRPO STOPLOSS REPORT" "${GRPO_DIR}/stoploss_report.json"
fi

echo
echo "POST_CHALLENGE_CURRICULUM_4B_STRETCH_COMPLETE"
echo "Use 4B results only if all metrics are real, challenge-safe, and not overblocked."
