# Training Plan

Gate 4/5 includes a training scaffold only. No real GRPO run has been executed yet, no GPU has been used, and no trained improvement is claimed.

The environment is the innovation. Training evidence is used to show that the replay -> repair -> regress -> certify loop gives a learnable reward signal.

## Budget Strategy

The practical budget target is approximately 30 USD of Hugging Face credit. Treat that as a validation budget, not an exploration budget.

Use CPU for:

- environment serving
- verifier reward
- dataset generation
- baseline evaluation
- smoke evaluation
- plotting

Use GPU only after every CPU gate passes.

Budget plan:

- Reserve roughly 5 USD for dependency/model-load failures and reruns.
- Spend the first paid minutes only on Run 1 with 0.5B.
- Move to 1.5B only if Run 1 writes valid logs and sampled generations.
- Move to 4B only if smaller runs have already produced valid metrics and budget remains.
- Stop before polishing plots if the training logs are weak; report modest results honestly.

Hardware recommendation:

- Use T4-small first for 0.5B and 1.5B runs.
- Use L4 only for the 4B stretch run if needed.
- Keep the environment server CPU-only; only model training needs GPU.

## Must Pass Before GPU

- `python -m pytest`
- `python scripts/self_check.py`
- `python scripts/evaluate_baselines.py`
- `python scripts/make_plots.py`
- `python training/make_dataset.py --smoke --output-dir outputs/training_smoke`
- `python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke`
- `python training/evaluate_model.py --smoke --output-dir outputs/eval_smoke`
- `python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke`
- manual inspection of `outputs/grpo_smoke/sampled_generations.jsonl`

Install training-only dependencies on the training runtime, not in the CPU Space runtime:

```bash
pip install -e ".[training]"
```

## Model Ladder

Run 1 - pipeline validation:

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Hardware: T4-small first
- Scale: very tiny GRPO
- Goal: prove reward function, strict JSON parsing, logging, metrics, sampled generations, held-out evaluation, and checkpoint saving work
- Stop-loss: stop if files are missing, invalid JSON is above 0.60, or reward does not beat `random_patch` score `0.144`

Run 2 - main small result:

- Model: `Qwen/Qwen2.5-1.5B-Instruct` if available and stable, otherwise the best small Qwen alternative available in the runtime
- Hardware: T4-small first
- Scale: still small; increase steps only after Run 1 is healthy
- Goal: improve hidden-regression pass rate and certificate success while preserving valid behavior
- Stop-loss: stop if throughput is too slow for the 30 USD budget, invalid JSON worsens, or hidden pass improves only through overblocking

Run 3 - stretch / final competitive run:

- Model: `Qwen/Qwen3-4B-Instruct-2507` only if the model is available in the runtime
- Hardware: L4 only if needed
- Scale: stretch run, not required for the first valid result
- Prefer LoRA/QLoRA/Unsloth-compatible path if supported by the runtime
- Run only if Run 1 works, Run 2 works or 1.5B is unavailable, budget remains, dependencies are stable, invalid JSON is under control, and throughput is acceptable

Do not require 4B for first evidence. A clean 0.5B or 1.5B run with honest metrics is better than a failed 4B spend.

## SFT Warmstart Purpose

Use SFT only if the base model cannot reliably emit strict JSON. SFT is formatting warmup, not the final evidence. It must stay small and must be followed by verifier-scored GRPO.

Smoke:

```bash
python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke
```

Tiny real SFT warmstart, if base GRPO keeps producing invalid JSON:

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

SFT writes:

- `outputs/sft_qwen25_05b_json/sft_summary.json`
- `outputs/sft_qwen25_05b_json/heldout_eval_summary.json`
- `outputs/sft_qwen25_05b_json/heldout_eval_completions.jsonl`
- `outputs/sft_qwen25_05b_json/model/`

Use the SFT checkpoint for GRPO only if held-out JSON improves and no overblocking or hardcoding appears. SFT alone is not the final RL result.

## GRPO Purpose

GRPO is the intended first RL path because the environment has deterministic verifier rewards. The model receives a public failed trace and outputs one strict JSON repair plan.

Smoke:

```bash
python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke
```

The smoke path tests parser, verifier reward, metrics logging, and sampled generation logging. It does not run full TRL training.

After the first HF T4 attempt, the training path was hardened for Qwen Instruct models:

- dataset prompts now use TRL's conversational message format so the model chat template is applied
- held-out generation uses the same chat template as training
- GRPO uses the deterministic verifier score plus a small training-only JSON-format shaping signal
- official metrics still report verifier `overall_score`, certificate success, hidden regression pass, valid preservation, invalid JSON, overblocking, and hardcoding separately

The format shaping reward exists only to escape the all-invalid-JSON cold start. It is not an environment score and must not be reported as benchmark improvement.

## Dataset Command

```bash
python training/make_dataset.py --smoke --output-dir outputs/training_smoke
```

Future larger dataset:

```bash
python training/make_dataset.py \
  --train-seeds 0-59 \
  --eval-seeds 1000-1014 \
  --output-dir outputs/training_dataset
```

## Run 1: Exact 0.5B Tiny Command

Run only after the pre-training audit is green. The non-smoke path requires `--confirm-real-training` so paid-capable training cannot start by accident.

```bash
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

If the SFT warmstart passed, replace the model with:

```bash
--model outputs/sft_qwen25_05b_json/model
```

Expected files:

- `outputs/grpo_tiny_hf/metrics.csv`
- `outputs/grpo_tiny_hf/summary.json`
- `outputs/grpo_tiny_hf/sampled_generations.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_completions.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_metrics.csv`
- `outputs/grpo_tiny_hf/heldout_eval_summary.json`
- `outputs/grpo_tiny_hf/model/`
- `outputs/training_metrics.csv`

## Run 2: 1.5B Command Template

Use only after Run 1 writes valid metrics and sampled generations:

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

If `Qwen/Qwen2.5-1.5B-Instruct` is unavailable or unstable in the runtime, stop and choose the closest small Qwen instruct model. Do not jump straight to 4B without a working small-model log.

## Run 3: 4B Stretch Template

Use only if Run 1 works, Run 2 works or 1.5B is unavailable, budget remains, dependencies are stable, invalid JSON is under control, and throughput is acceptable:

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

Optional Unsloth runtime check for the stretch path:

```bash
python training/train_json_grpo.py \
  --confirm-real-training \
  --model Qwen/Qwen3-4B-Instruct-2507 \
  --max-steps 5 \
  --train-seeds 0-1 \
  --eval-seeds 1000 \
  --output-dir outputs/grpo_qwen3_4b_unsloth_probe \
  --num-generations 2 \
  --use-lora \
  --use-unsloth
```

Run the Unsloth probe only after plain TRL and LoRA have already worked. If Unsloth is missing or incompatible, stop and use the plain LoRA path.

## Stop-Loss Rules

Stop immediately if:

- dependencies fail to import cleanly before the model starts training
- model download or startup burns more than the planned tiny-run budget
- invalid JSON remains above 60 percent after warmup
- mean reward does not beat `random_patch` baseline score `0.144` within the first tiny run
- reward rises while certificate success does not
- block-everything behavior appears
- hardcoded incident IDs appear
- hidden valid preservation collapses
- hidden regression pass rate improves only by overblocking
- logs are missing reward, invalid JSON, hidden pass rate, valid preservation, or certificate success
- `outputs/grpo_tiny_hf/sampled_generations.jsonl` is missing or contains only mock completions

Per-run stop-loss:

- Run 1: stop on any missing output file, import error, invalid JSON above 0.60, or mean reward at or below 0.144.
- Run 2: stop if certificate success does not improve, hidden regression pass improves only with valid preservation collapse, or runtime cost threatens the 30 USD budget.
- Run 3: stop if setup is not stable within the first few minutes, throughput is unacceptable, or LoRA/Unsloth compatibility is unclear.

## Metrics To Monitor

- overall score
- certificate success rate
- hidden regression pass rate
- valid preservation rate
- invalid JSON rate
- overblocking rate
- hardcoded patch rate
- sampled generations

Expected real-run files:

- `outputs/grpo_tiny_hf/metrics.csv`
- `outputs/grpo_tiny_hf/summary.json`
- `outputs/grpo_tiny_hf/sampled_generations.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_summary.json`
- `outputs/grpo_tiny_hf/model/`
- `outputs/training_metrics.csv`

## Plots After Real Training

After a real run, generate only from real logs:

- reward curve
- loss curve if available
- certificate success over steps
- hidden regression pass over steps
- valid preservation over steps
- invalid JSON over steps
- baseline vs trained comparison

Do not create these before real training.

## LoRA / QLoRA Saving Warning

If LoRA or QLoRA is used, test post-training inference immediately. Do not naively upcast a 4-bit model to 16-bit and merge adapters. Use the proper adapter save or merged-save path for the training stack.

## No Fake Results

Do not claim trained model improvement, SOTA, production certification, or global safety. Current results are baseline and smoke results only.
