# Submission Evidence

This file tracks real evidence only. No fake training results, fake plots, or fake notebooks are claimed.

## Execution Method

Training and evaluation have been run through Hugging Face Jobs CLI and repository scripts. No notebook was used; training was run via HF Jobs CLI and repo scripts.

## Known Hugging Face Jobs

| Job ID | Hardware | Status | Role |
|---|---|---|---|
| `69ed0befd2c8bd8662bce36c` | `cpu-basic` | completed | Early CPU smoke after dependency fixes. |
| `69ed0cebd2c8bd8662bce388` | `t4-small` | error | Failed because `generation_batch_size (1)` was not divisible by `num_generations (2)`. |
| `69ed0f55d2c8bd8662bce3d6` | `t4-small` | completed | Corrected batch size but invalid JSON collapse. |
| `69ed12abd70108f37acdedc6` | `cpu-basic` | completed | CPU smoke after JSON prompt hardening. |
| `69ed130dd2c8bd8662bce45b` | `t4-small` | completed | 0.5B GRPO attempt completed but failed quality stop-loss. |
| `69ed1880d2c8bd8662bce4e5` | `cpu-basic` | completed | Fresh HF runtime passed GRPO smoke, SFT smoke, self_check, Space smoke, and pytest. |
| `69ed18e7d2c8bd8662bce4f2` | `t4-small` | completed | Tiny 0.5B SFT format warmstart succeeded on reported small held-out eval. |
| `69ed1a3ed2c8bd8662bce516` | `t4-small` | completed | Tiny SFT warmstart plus 0.5B GRPO validation succeeded on reported small held-out eval. |
| `69ed520cd2c8bd8662bcea54` | `t4-small` | canceled | Larger-eval attempt canceled intentionally. |
| `69ed549bd70108f37acdf273` | `t4-small` | completed | Pre-hardening larger 0.5B standard and shuffled challenge evaluation. |

Post-hardening 0.5B job `69ed986cd70108f37acdf8ba` completed and printed `POST_HARDENING_0_5B_COMPLETE`. It is not final improvement evidence: challenge variants exposed evidence-grounding failure and GRPO stoploss reported `STOP`. The next evidence step is a 0.5B challenge-curriculum run, not 1.5B.

## Commands And Scripts

Primary local checks:

```bash
python scripts/self_check.py
python scripts/generalization_audit.py
python -m pytest
```

Hardened 0.5B HF run script:

```bash
bash scripts/hf_run_05b_hardened.sh
```

Evidence package command:

```bash
python scripts/package_submission_evidence.py
```

## Models And Hardware

| Stage | Model | Hardware | Notes |
|---|---|---|---|
| Base eval | `Qwen/Qwen2.5-0.5B-Instruct` | `t4-small` | Used as zero-shot comparison. |
| SFT warmstart | `Qwen/Qwen2.5-0.5B-Instruct` | `t4-small` | Format/action warmstart, not a standalone safety claim. |
| GRPO validation | SFT checkpoint | `t4-small` | Verifier-scored validation after SFT. |

No 1.5B or 4B run has been performed after the Rank-1 anti-leakage hardening patch.

## Seeds And Prompt Variants

Training seeds:

- SFT: `0-5`
- GRPO: `0-2`

Evaluation seeds:

- Small held-out checks: `1000-1002`
- Larger held-out checks: `1000-1019`
- Audit target range: `1000-1049`

Prompt variants:

- `standard`
- `shuffled_surface_blind`
- `combined_blind_shuffle`

## Metrics Summary

Baseline metrics are in `outputs/results.csv` and `outputs/baseline_summary.json`.

Known pre-hardening evidence:

- Base 0.5B zero-shot emitted invalid JSON on reported larger eval.
- SFT 0.5B fixed strict repair-plan JSON generation on reported held-out seeds.
- SFT+GRPO 0.5B passed reported standard hidden-regression and certificate metrics after SFT.
- Pre-hardening `shuffled_surface_blind` challenge did not collapse, but `overall_score` was `0.78`, which motivated stricter anti-leakage hardening.

Post-hardening evidence still required:

- fresh standard eval
- fresh `shuffled_surface_blind` eval
- fresh `combined_blind_shuffle` eval
- plots generated only from those real model-eval summaries

Next prepared evidence run:

- `scripts/hf_run_05b_challenge_curriculum.sh` is the next unlocked HF script.
- `scripts/hf_run_15b_challenge_curriculum.sh` exists but is locked until the 0.5B challenge-curriculum run passes.
- `scripts/hf_run_4b_stretch.sh` exists but is locked until the 1.5B run passes.
- H200 is not part of the evidence plan until smaller gates show the benchmark and curriculum are scientifically healthy.

Experimental tracking:

- CSV/JSON logs remain the source of truth.
- TensorBoard-compatible artifacts are written under `outputs/tracking/` during real SFT/GRPO runs.
- Lightweight loss/reward plots are written under `outputs/final_plots/` only when real tracking or verifier reward rows exist.

## Stop-Loss Decisions

Run 2 / 1.5B is locked until post-hardening 0.5B summaries are inspected.

Stop if any post-hardening 0.5B run shows:

- missing `summary.json`, `metrics.csv`, or sampled generations
- `invalid_json_rate > 0.10` for SFT or SFT+GRPO
- certificate success high while evidence/root-cause/patch diagnostics are weak
- hidden regression collapse
- valid preservation collapse
- overblocking or hardcoded-patch behavior
- no real model-eval logs

## Allowed Claims

Allowed only if supported by real logs:

- Agent BlackBox Arena is an OpenEnv-style repair environment with hidden regressions and certificate gating.
- Baseline policies score low while the oracle sanity solver scores high.
- The first 0.5B GRPO-only attempt exposed an invalid-JSON formatting bottleneck.
- A small SFT warmstart fixed strict repair-plan generation on the reported held-out seeds.
- The post-hardening 0.5B run passed standard and challenge metrics only after those fresh summaries exist.

## Unsafe Claims

Do not claim:

- broad production safety
- SOTA
- GRPO learned from scratch
- 1.5B or 4B results before those jobs run
- unlimited generalization
- trained improvement from fake or placeholder plots
- certificate as a global safety proof
