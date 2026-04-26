#!/usr/bin/env bash
set -euo pipefail

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

tail_if_exists() {
  local path="$1"
  echo
  echo "=== METRICS TAIL: ${path} ==="
  if [[ -f "${path}" ]]; then
    tail -n 20 "${path}"
  else
    echo "MISSING: ${path}"
  fi
}

head_if_exists() {
  local path="$1"
  echo
  echo "=== SAMPLE GENERATIONS: ${path} ==="
  if [[ -f "${path}" ]]; then
    head -n 10 "${path}"
  else
    echo "MISSING: ${path}"
  fi
}

phase "Preflight: self_check and generalization audit"
python scripts/self_check.py
python scripts/generalization_audit.py

phase "Base 0.5B standard eval"
python training/evaluate_checkpoint.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --model-label base_0_5b \
  --eval-seeds 1000-1019 \
  --output-dir outputs/model_eval/base_0_5b_standard

phase "Train 0.5B SFT warmstart"
python training/train_sft_warmstart.py \
  --confirm-real-training \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --max-steps 30 \
  --train-seeds 0-5 \
  --eval-seeds 1000-1002 \
  --output-dir outputs/sft_qwen25_05b_json \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 1 \
  --learning-rate 1e-5 \
  --max-completion-length 160 \
  --save-steps 30

phase "Evaluate SFT checkpoint on standard"
python training/evaluate_checkpoint.py \
  --model outputs/sft_qwen25_05b_json/model \
  --model-label sft_0_5b_standard \
  --eval-seeds 1000-1019 \
  --output-dir outputs/model_eval/sft_0_5b_standard

phase "Evaluate SFT checkpoint on shuffled_surface_blind"
python training/evaluate_checkpoint.py \
  --model outputs/sft_qwen25_05b_json/model \
  --model-label sft_0_5b_shuffled_surface_blind \
  --eval-seeds 1000-1019 \
  --prompt-variant shuffled_surface_blind \
  --output-dir outputs/model_eval/sft_0_5b_shuffled_surface_blind

phase "Evaluate SFT checkpoint on combined_blind_shuffle"
python training/evaluate_checkpoint.py \
  --model outputs/sft_qwen25_05b_json/model \
  --model-label sft_0_5b_combined_blind_shuffle \
  --eval-seeds 1000-1019 \
  --prompt-variant combined_blind_shuffle \
  --output-dir outputs/model_eval/sft_0_5b_combined_blind_shuffle

phase "Run 0.5B GRPO validation from SFT checkpoint"
python training/train_json_grpo.py \
  --confirm-real-training \
  --model outputs/sft_qwen25_05b_json/model \
  --max-steps 10 \
  --train-seeds 0-2 \
  --eval-seeds 1000 \
  --eval-prompt-variant combined_blind_shuffle \
  --output-dir outputs/grpo_tiny_hf \
  --num-generations 2 \
  --per-device-train-batch-size 2 \
  --gradient-accumulation-steps 1 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --format-reward-weight 0.2 \
  --save-steps 10

phase "Evaluate SFT+GRPO checkpoint on standard"
python training/evaluate_checkpoint.py \
  --model outputs/grpo_tiny_hf/model \
  --model-label sft_grpo_0_5b_standard \
  --eval-seeds 1000-1019 \
  --output-dir outputs/model_eval/sft_grpo_0_5b_standard

phase "Evaluate SFT+GRPO checkpoint on shuffled_surface_blind"
python training/evaluate_checkpoint.py \
  --model outputs/grpo_tiny_hf/model \
  --model-label sft_grpo_0_5b_shuffled_surface_blind \
  --eval-seeds 1000-1019 \
  --prompt-variant shuffled_surface_blind \
  --output-dir outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind

phase "Evaluate SFT+GRPO checkpoint on combined_blind_shuffle"
python training/evaluate_checkpoint.py \
  --model outputs/grpo_tiny_hf/model \
  --model-label sft_grpo_0_5b_combined_blind_shuffle \
  --eval-seeds 1000-1019 \
  --prompt-variant combined_blind_shuffle \
  --output-dir outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle

phase "Generate plots from real model-eval summaries if available"
if [[ -f outputs/model_eval/base_0_5b_standard/summary.json && \
      -f outputs/model_eval/sft_0_5b_standard/summary.json && \
      -f outputs/model_eval/sft_grpo_0_5b_standard/summary.json ]]; then
  python scripts/plot_model_eval.py \
    --summary base=outputs/model_eval/base_0_5b_standard/summary.json \
    --summary sft=outputs/model_eval/sft_0_5b_standard/summary.json \
    --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_standard/summary.json \
    --output-dir outputs/model_eval
else
  echo "Skipping standard plots because one or more summary files are missing."
fi

if [[ -f outputs/model_eval/sft_0_5b_shuffled_surface_blind/summary.json && \
      -f outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind/summary.json ]]; then
  python scripts/plot_model_eval.py \
    --summary sft=outputs/model_eval/sft_0_5b_shuffled_surface_blind/summary.json \
    --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind/summary.json \
    --output-dir outputs/model_eval/shuffled_surface_blind
else
  echo "Skipping shuffled_surface_blind plots because one or more summary files are missing."
fi

if [[ -f outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json && \
      -f outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json ]]; then
  python scripts/plot_model_eval.py \
    --summary sft=outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json \
    --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json \
    --output-dir outputs/model_eval/combined_blind_shuffle
else
  echo "Skipping combined_blind_shuffle plots because one or more summary files are missing."
fi

phase "Final summaries"
print_json_if_exists "BASE 0.5B STANDARD SUMMARY" "outputs/model_eval/base_0_5b_standard/summary.json"
print_json_if_exists "SFT TRAIN SUMMARY" "outputs/sft_qwen25_05b_json/sft_summary.json"
print_json_if_exists "SFT HELDOUT SUMMARY" "outputs/sft_qwen25_05b_json/heldout_eval_summary.json"
print_json_if_exists "SFT STANDARD SUMMARY" "outputs/model_eval/sft_0_5b_standard/summary.json"
print_json_if_exists "SFT SHUFFLED_SURFACE_BLIND SUMMARY" "outputs/model_eval/sft_0_5b_shuffled_surface_blind/summary.json"
print_json_if_exists "SFT COMBINED_BLIND_SHUFFLE SUMMARY" "outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json"
print_json_if_exists "GRPO SUMMARY" "outputs/grpo_tiny_hf/summary.json"
print_json_if_exists "GRPO HELDOUT SUMMARY" "outputs/grpo_tiny_hf/heldout_eval_summary.json"
print_json_if_exists "GRPO STOPLOSS REPORT" "outputs/grpo_tiny_hf/stoploss_report.json"
print_json_if_exists "SFT+GRPO STANDARD SUMMARY" "outputs/model_eval/sft_grpo_0_5b_standard/summary.json"
print_json_if_exists "SFT+GRPO SHUFFLED_SURFACE_BLIND SUMMARY" "outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind/summary.json"
print_json_if_exists "SFT+GRPO COMBINED_BLIND_SHUFFLE SUMMARY" "outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json"
tail_if_exists "outputs/grpo_tiny_hf/metrics.csv"
head_if_exists "outputs/grpo_tiny_hf/sampled_generations.jsonl"

echo
echo "POST_HARDENING_0_5B_COMPLETE"
echo "Inspect standard, shuffled_surface_blind, and combined_blind_shuffle summaries before running 1.5B."
