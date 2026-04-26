# Training Plan

Gate 4/5 produced the training scaffold, and the first controlled 0.5B HF run has now validated the pipeline after an SFT format warmstart. The successful run proves that model loading, strict JSON output, deterministic verifier reward, sampled generation logging, held-out evaluation, checkpoint saving, and stop-loss reporting work. It does not by itself prove broad trained-model improvement, because the tiny GRPO phase was saturated after SFT warmup.

The environment is the innovation. Training evidence is used to show that the replay -> repair -> regress -> certify loop gives a learnable reward signal. The post-0.5B hardening pass now shuffles candidate answer order and tightens certificate gating, so any final trained claim should come from a fresh post-hardening evaluation.

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

Hardware escalation after challenge hardening:

- Use **T4-small** for 0.5B diagnosis, challenge-curriculum SFT, and tiny optional GRPO. This is the right hardware for fixing evidence grounding.
- Use **A10G-small or L4** for a 1.5B serious run only if the 0.5B challenge curriculum improves `shuffled_surface_blind` and `combined_blind_shuffle` evidence correctness and certificate success.
- Use **L4 / A10G / A100** for an optional 4B stretch only after the 1.5B run works and budget remains.
- Do **not** use H200 for prompt/curriculum bugs. H200 is only justifiable for a final large ablation after all smaller gates pass.

## Must Pass Before GPU

- `python -m pytest`
- `python scripts/self_check.py`
- `python scripts/training_preflight.py`
- `python scripts/evaluate_baselines.py`
- `python scripts/make_plots.py`
- `python training/make_dataset.py --smoke --output-dir outputs/training_smoke`
- `python training/train_json_grpo.py --smoke --output-dir outputs/grpo_smoke`
- `python training/evaluate_model.py --smoke --output-dir outputs/eval_smoke`
- `python training/train_sft_warmstart.py --smoke --output-dir outputs/sft_smoke`
- manual inspection of `outputs/grpo_smoke/sampled_generations.jsonl`
- automatic rejection of bad GRPO configs such as `--per-device-train-batch-size 1 --num-generations 2`

Install training-only dependencies on the training runtime, not in the CPU Space runtime:

```bash
pip install -e ".[training]"
```

## Experimental Tracking

Experimental tracking is enabled through CSV/JSON logs plus TensorBoard-compatible artifacts under `outputs/tracking/`.

Tracked signals include:

- SFT trainer loss when SFT runs
- GRPO trainer loss when GRPO runs
- verifier reward / `overall_score`
- `invalid_json_rate`
- `certificate_success_rate`
- `hidden_regression_pass_rate`
- `valid_preservation_rate`
- `evidence_correct_rate`
- `root_cause_correct_rate`
- `patch_blocks_rate`
- `overblocking_rate`
- `hardcoded_patch_rate`

CSV/JSON remains the source of truth. TensorBoard is an additional audit trail, not a replacement for `summary.json`, `metrics.csv`, `sampled_generations.jsonl`, or stop-loss reports.

## Model Ladder

Run 1 - pipeline validation:

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Hardware: T4-small first
- Scale: very tiny GRPO
- Goal: prove reward function, strict JSON parsing, logging, metrics, sampled generations, held-out evaluation, and checkpoint saving work
- Status: completed once after SFT warmstart with real HF logs; keep using this as the minimum proof pattern
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

Challenge-curriculum SFT command shape:

```bash
python training/train_sft_warmstart.py \
  --confirm-real-training \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --max-steps 60 \
  --train-seeds 0-9 \
  --eval-seeds 1000-1002 \
  --prompt-variants standard,shuffled_surface_blind,combined_blind_shuffle \
  --eval-prompt-variant combined_blind_shuffle \
  --output-dir outputs/sft_qwen25_05b_challenge_curriculum \
  --per-device-train-batch-size 1 \
  --gradient-accumulation-steps 1 \
  --learning-rate 1e-5 \
  --max-completion-length 160 \
  --save-steps 60
```

This trains strict JSON, evidence selection, root cause, patch clauses, and preservation clauses across standard and challenge prompts. It does not weaken the verifier or certificate gate.

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

After SFT warmstart, GRPO should be used only when there is still a harder-surface learning signal: for example standard plus `combined_blind_shuffle` challenge prompts where SFT is not already saturated. GRPO success requires nonzero reward variance or a clear improvement on challenge/generalization metrics. If `reward_std` is zero and `frac_reward_zero_std` is one, report the run as verifier-scored validation, not RL improvement.

Mixed-variant GRPO command shape, only after challenge SFT looks healthy:

```bash
python training/train_json_grpo.py \
  --confirm-real-training \
  --model outputs/sft_qwen25_05b_challenge_curriculum/model \
  --max-steps 10 \
  --train-seeds 0-4 \
  --eval-seeds 1000 \
  --prompt-variants standard,shuffled_surface_blind,combined_blind_shuffle \
  --eval-prompt-variant combined_blind_shuffle \
  --output-dir outputs/grpo_05b_challenge_curriculum \
  --num-generations 2 \
  --per-device-train-batch-size 2 \
  --gradient-accumulation-steps 1 \
  --learning-rate 5e-6 \
  --max-completion-length 160 \
  --format-reward-weight 0.2 \
  --save-steps 10
```

## Training Quality Gate

Official TRL guidance confirms that GRPO uses groups of generated completions per prompt, custom reward functions can score those completions, and metrics such as `reward_std` and `frac_reward_zero_std` reveal whether the group has useful reward variation. The project now makes those assumptions explicit before any paid-capable run.

Run this before GPU:

```bash
python scripts/training_preflight.py
```

The preflight checks:

- conversational prompt format for Qwen Instruct models
- no hidden answers, hidden variants, or incident IDs in training prompts
- candidate answer positions vary across seeds and prompt variants
- SFT target JSON parses and scores 1.0 with the deterministic verifier
- the old failing config `--per-device-train-batch-size 1 --num-generations 2` is rejected locally
- the corrected config `--per-device-train-batch-size 2 --num-generations 2` passes
- invalid-JSON collapse triggers stop-loss
- saturated perfect GRPO rows produce a caveat instead of a fake learning claim

Real GRPO writes:

- `run_config.json`
- `summary.json`
- `metrics.csv`
- `sampled_generations.jsonl`
- `heldout_eval_summary.json`
- `heldout_eval_metrics.csv`
- `stoploss_report.json`

Real SFT writes:

- `run_config.json`
- `sft_summary.json`
- `heldout_eval_summary.json`
- `sft_quality_report.json`

If `stoploss_report.json` says `STOP`, do not run a bigger model. If it says `PASS` with a saturation warning, the pipeline is valid but the result should be described as format/pipeline validation, not extra GRPO learning.

## Generalization Gate Before 1.5B

Because the 0.5B SFT+GRPO validation is perfect on a small eval, Run 2 is blocked until the larger held-out and challenge checks are inspected.

After the hardening pass, the next 0.5B audit should be treated as the new evidence baseline because:

- candidate root-cause and patch-label options are seed-shuffled
- challenge prompts blind the family label, shuffle spans, rewrite surface text, and include the harder `combined_blind_shuffle` entity-renaming variant
- certificate success requires correct evidence, not only a patch that passes hidden regressions
- summaries include `evidence_correct_rate`, `root_cause_correct_rate`, `patch_blocks_rate`, and `certificate_gate_fail_rate`

CPU audit:

```bash
python scripts/generalization_audit.py
```

Preferred standard held-out eval:

```bash
python training/evaluate_checkpoint.py \
  --model Qwen/Qwen2.5-0.5B-Instruct \
  --model-label base_0_5b \
  --eval-seeds 1000-1049 \
  --output-dir outputs/model_eval/base_0_5b_standard

python training/evaluate_checkpoint.py \
  --model outputs/sft_qwen25_05b_json/model \
  --model-label sft_0_5b \
  --eval-seeds 1000-1049 \
  --output-dir outputs/model_eval/sft_0_5b_standard

python training/evaluate_checkpoint.py \
  --model outputs/grpo_tiny_hf/model \
  --model-label sft_grpo_0_5b \
  --eval-seeds 1000-1049 \
  --output-dir outputs/model_eval/sft_grpo_0_5b_standard
```

Challenge eval uses the same script with:

```bash
--prompt-variant shuffled_surface_blind
```

Harder combined challenge:

```bash
--prompt-variant combined_blind_shuffle
```

Plot only after the real model-eval summaries exist:

```bash
python scripts/plot_model_eval.py \
  --summary base=outputs/model_eval/base_0_5b_standard/summary.json \
  --summary sft=outputs/model_eval/sft_0_5b_standard/summary.json \
  --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_standard/summary.json \
  --output-dir outputs/model_eval
```

Do not use oracle challenge metrics as trained-model evidence. They are verifier sanity checks only.

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

- `outputs/grpo_tiny_hf/run_config.json`
- `outputs/grpo_tiny_hf/metrics.csv`
- `outputs/grpo_tiny_hf/summary.json`
- `outputs/grpo_tiny_hf/stoploss_report.json`
- `outputs/grpo_tiny_hf/sampled_generations.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_completions.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_metrics.csv`
- `outputs/grpo_tiny_hf/heldout_eval_summary.json`
- `outputs/grpo_tiny_hf/model/`
- `outputs/training_metrics.csv`

## Challenge-Curriculum 0.5B HF Command

Use this before any 1.5B spend. It trains 0.5B SFT on mixed standard and challenge variants, evaluates standard / `shuffled_surface_blind` / `combined_blind_shuffle`, prints summary JSON, and skips GRPO by default.

```bash
hf jobs run \
  --flavor t4-small \
  --timeout 120m \
  python:3.11 \
  -- \
  bash \
  -lc \
  "apt-get update && apt-get install -y git && git clone https://github.com/Kenxpx/Agent-Blackbox-Arena.git && cd Agent-Blackbox-Arena && pip install -e '.[training]' && bash scripts/hf_run_05b_challenge_curriculum.sh"
```

Enable optional GRPO only after SFT challenge metrics are healthy:

```bash
RUN_GRPO=1 bash scripts/hf_run_05b_challenge_curriculum.sh
```

Do not run 1.5B until the 0.5B challenge-curriculum run shows nonzero challenge evidence correctness and certificate success, invalid JSON near zero, overblocking near zero, and hardcoded patch rate zero.

## Run 2: 1.5B Locked HF Command

Use only after the 0.5B challenge-curriculum run shows recovered challenge evidence correctness and certificate success. The script is locked by default and exits unless `CONFIRM_15B_CHALLENGE_PASSED=1` is set.

```bash
hf jobs run \
  --flavor l4x1 \
  --timeout 150m \
  python:3.11 \
  -- \
  bash \
  -lc \
  "apt-get update && apt-get install -y git && git clone https://github.com/Kenxpx/Agent-Blackbox-Arena.git && cd Agent-Blackbox-Arena && pip install -e '.[training]' && CONFIRM_15B_CHALLENGE_PASSED=1 bash scripts/hf_run_15b_challenge_curriculum.sh"
```

The 1.5B script uses `Qwen/Qwen2.5-1.5B-Instruct`, LoRA SFT on mixed standard + challenge variants, standard / `shuffled_surface_blind` / `combined_blind_shuffle` eval, and optional GRPO only when `RUN_GRPO=1`. If the model is unavailable or unstable in the runtime, stop and choose the closest small Qwen instruct model. Do not jump straight to 4B without a working 1.5B log.

## Run 3: 4B Stretch Locked HF Command

Use only if 1.5B works, budget remains, dependencies are stable, invalid JSON is under control, challenge evidence is healthy, and throughput is acceptable. The script is locked by default and exits unless `CONFIRM_4B_AFTER_15B_PASSED=1` is set.

```bash
hf jobs run \
  --flavor a10g-large \
  --timeout 180m \
  python:3.11 \
  -- \
  bash \
  -lc \
  "apt-get update && apt-get install -y git && git clone https://github.com/Kenxpx/Agent-Blackbox-Arena.git && cd Agent-Blackbox-Arena && pip install -e '.[training]' && CONFIRM_4B_AFTER_15B_PASSED=1 bash scripts/hf_run_4b_stretch.sh"
```

The 4B script uses `Qwen/Qwen3-4B-Instruct-2507`, LoRA SFT, the same challenge evals, and optional GRPO only when `RUN_GRPO=1`. H200 is optional only for a final ablation after this path is already validated; it should not be used to debug evidence prompts.

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
- `outputs/grpo_tiny_hf/stoploss_report.json`
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

Do not claim trained model improvement, SOTA, production certification, or global safety from baseline, smoke, or saturated tiny-run evidence alone.

Allowed current claim: the first 0.5B HF run validates the strict JSON training pipeline and verifier-scored held-out evaluation after a tiny SFT warmstart. Do not claim broad improvement until a non-saturated run or a wider held-out comparison proves it.
