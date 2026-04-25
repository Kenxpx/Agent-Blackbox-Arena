# Final HF Training GO

Decision: **GO for larger 0.5B held-out and challenge evaluation; NO-GO for 1.5B until those artifacts are inspected**.

The first base 0.5B T4 attempts exposed two failure modes: an invalid GRPO batch/generation config and all-invalid JSON completions. After prompt hardening and a tiny SFT format warmstart, the latest 0.5B SFT+GRPO validation completed with real logs, sampled generations, held-out verifier metrics, and a saved checkpoint. This is strong pipeline evidence, not a broad trained-improvement claim, because the GRPO phase was saturated after SFT warmup.

## Framing

The environment is the innovation. Training exists to prove the environment teaches the repair loop:

```text
failed trace -> replay -> evidence spans -> root cause -> patch -> hidden regressions -> certificate
```

Do not let training claims replace the benchmark story. A small honest run with real logs is stronger than an expensive run with unclear reward evidence.

## Required Before HF Spend

- `python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke`
- `python scripts/training_preflight.py`
- `python scripts/self_check.py`
- `python -m pytest`
- manual inspection of `outputs/grpo_smoke/sampled_generations.jsonl`
- confirm the HF runtime can install `pip install -e ".[training]"`
- confirm any real run writes `run_config.json` and `stoploss_report.json`
- `python scripts/generalization_audit.py`
- larger base/SFT/SFT+GRPO eval with `training/evaluate_checkpoint.py`

The patched path uses conversational prompts for Qwen Instruct, a compact family-specific label set, and a small training-only JSON-format shaping reward. Benchmark claims still come only from verifier metrics: `overall_score`, certificate success, hidden regression pass, valid preservation, invalid JSON, overblocking, and hardcoding.

## Model Ladder

### Run 1 - Pipeline Validation

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Hardware: T4-small first
- Goal: prove deterministic verifier reward, strict JSON parsing, sampled generation logging, CSV/JSON metrics, held-out evaluation, and checkpoint saving
- Budget posture: spend the smallest useful amount
- Status: completed once after tiny SFT warmstart; repeat only if needed for cleaner artifacts, not by default

Tiny SFT warmstart command:

```bash
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
```

Command:

```bash
pip install -e ".[training]"

python training/train_json_grpo.py \
  --confirm-real-training \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --max-steps 10 \
  --train-seeds 0-2 \
  --eval-seeds 1000 \
  --output-dir outputs/grpo_tiny_hf \
  --num-generations 2 \
  --per-device-train-batch-size 2 \
  --gradient-accumulation-steps 1 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --format-reward-weight 0.2 \
  --save-steps 10
```

If the SFT warmstart passes held-out verifier checks, use:

```bash
--model outputs/sft_qwen25_05b_json/model
```

### Run 2 - Main Small Result

- Model: `Qwen/Qwen2.5-1.5B-Instruct` if available and stable
- Fallback: best small Qwen instruct alternative available in the runtime
- Hardware: T4-small first
- Goal: improve hidden-regression pass rate and certificate success while preserving valid behavior
- Status: approved only after Run 1 writes valid real logs
- Current gate: allowed only after `training_preflight_report.json`, `stoploss_report.json`, held-out metrics, and sampled generations are inspected
- Additional gate after perfect small eval: allowed only after standard seeds `1000-1049` and challenge variant `shuffled_surface_blind` are inspected

Template:

```bash
python training/train_json_grpo.py \
  --confirm-real-training \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --max-steps 20 \
  --train-seeds 0-5 \
  --eval-seeds 1000-1002 \
  --output-dir outputs/grpo_qwen25_15b \
  --num-generations 2 \
  --per-device-train-batch-size 2 \
  --gradient-accumulation-steps 1 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --format-reward-weight 0.2 \
  --save-steps 20 \
  --use-lora \
  --lora-r 8 \
  --lora-alpha 16 \
  --lora-dropout 0.05
```

### Run 3 - Stretch / Final Competitive Run

- Model: `Qwen/Qwen3-4B-Instruct-2507` only if available in the runtime
- Hardware: L4 only if needed
- Goal: stronger final result after smaller runs already prove the pipeline
- Status: optional stretch, not required for valid evidence

Run only if:

- Run 1 works
- Run 2 works or 1.5B is unavailable
- HF budget remains
- dependencies are stable
- invalid JSON is under control
- training throughput is acceptable

Template:

```bash
python training/train_json_grpo.py \
  --confirm-real-training \
  --model Qwen/Qwen3-4B-Instruct-2507 \
  --max-steps 20 \
  --train-seeds 0-5 \
  --eval-seeds 1000-1002 \
  --output-dir outputs/grpo_qwen3_4b_stretch \
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
  --lora-dropout 0.05
```

Optional Unsloth probe:

```bash
python training/train_json_grpo.py \
  --confirm-real-training \
  --model Qwen/Qwen3-4B-Instruct-2507 \
  --max-steps 5 \
  --train-seeds 0-1 \
  --eval-seeds 1000 \
  --output-dir outputs/grpo_qwen3_4b_unsloth_probe \
  --num-generations 2 \
  --per-device-train-batch-size 2 \
  --use-lora \
  --use-unsloth
```

If Unsloth is missing or incompatible, stop and use the plain LoRA path. Do not debug Unsloth at the expense of the 30 USD budget.

## Budget Recommendation

- Keep total HF spend under 30 USD.
- Reserve roughly 5 USD for setup failures and retries.
- Run 0.5B first on T4-small.
- Move to 1.5B only after Run 1 produces valid logs.
- Use L4 and 4B only as an optional final stretch after smaller metrics exist.

## Stop-Loss Rules

Stop immediately if:

- training dependencies fail before model training starts
- model load consumes more than the planned tiny-run budget
- `sampled_generations.jsonl` is missing
- `metrics.csv` is missing
- `heldout_eval_summary.json` is missing
- invalid JSON rate remains above `0.60`
- mean reward does not beat `random_patch` score `0.144`
- certificate success stays flat while reward rises
- overblocking rate increases
- hardcoded patch rate increases
- hidden regression pass improves while valid preservation collapses
- sampled generations are mostly markdown, prose-only answers, or copied incident IDs

## Expected Run 1 Outputs

- `outputs/grpo_tiny_hf/metrics.csv`
- `outputs/grpo_tiny_hf/summary.json`
- `outputs/grpo_tiny_hf/run_config.json`
- `outputs/grpo_tiny_hf/stoploss_report.json`
- `outputs/grpo_tiny_hf/sampled_generations.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_completions.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_metrics.csv`
- `outputs/grpo_tiny_hf/heldout_eval_summary.json`
- `outputs/grpo_tiny_hf/model/`
- `outputs/training_metrics.csv`

## What Not To Claim

- Do not claim trained-model improvement until real held-out metrics prove it.
- Do not claim robust generalization unless hidden regression pass and valid preservation both improve.
- Do not claim global safety or production certification.
- Do not present smoke or mock outputs as training results.
- Do not imply 4B is required for the project to be valid.
- Do not describe the saturated 0.5B GRPO phase as additional RL learning; describe it as pipeline validation unless a non-saturated run proves otherwise.
