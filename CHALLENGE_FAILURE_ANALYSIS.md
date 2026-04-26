# Challenge Failure Analysis

This analysis is based on the completed post-hardening 0.5B HF job `69ed986cd70108f37acdf8ba`, the captured log file `hf_job_05b_hardened_69ed986cd70108f37acdf8ba_logs.txt`, and the current CPU-only code review. No 1.5B, 4B, H200, or new GPU run was used.

## 1. Expected Evidence Span IDs

Before this patch, all families used canonical evidence spans `["s2", "s4"]` in every prompt variant:

| Family | Semantic evidence | Canonical old IDs |
|---|---|---|
| `stale_retrieval` | expired/stale context source plus unsafe final action | `s2`, `s4` |
| `missing_verification` | unverified information source plus irreversible final action | `s2`, `s4` |
| `permission_scope` | out-of-scope tool selection plus out-of-scope tool call | `s2`, `s4` |

After this patch, standard prompts keep canonical IDs, but challenge prompts use deterministic public aliases such as `v1` through `v4`. The target JSON now uses the public IDs visible in the current prompt variant.

## 2. Evidence ID Behavior Under Challenge Variants

Previous behavior:

- Span IDs were preserved as `s1` through `s4`.
- The `shuffled_surface_blind` and `combined_blind_shuffle` variants changed surface wording and trace order, but the target evidence IDs remained the same canonical IDs.
- Training used standard prompts only, so the model learned JSON format and standard evidence behavior without a challenge evidence curriculum.

New behavior:

- Standard prompt: canonical IDs such as `s2`, `s4`.
- Challenge prompts: public aliases such as `v2`, `v4`, determined by the visible shuffled trace order.
- The scorer canonicalizes valid public IDs internally for verifier execution, but public evidence correctness is measured against the IDs visible in the prompt.
- Old standard IDs such as `s2`/`s4` are invalid for aliased challenge prompts.

## 3. Does The Prompt Show Span IDs After Shuffling?

Yes. The prompt now prints every visible span as:

```text
- <visible_id> | event_type=<public_event_type> | tags=<public_tags> | text=<public_text>
```

It also prints:

```text
visible_span_ids: [...]
```

The prompt explicitly says:

- choose from `visible_span_ids` only
- identify both the failed final action and the earlier missing/unsafe control source
- do not assume old span IDs such as `s2`/`s4`
- re-read the current trace if order or wording changes

## 4. Is The Model Copying Standard Evidence IDs?

The captured HF log did not include full model-eval `completions.jsonl`, so we cannot prove every predicted evidence pattern from local files. However, the metrics show a clear collapse:

- SFT standard evidence_correct_rate: `1.0`
- SFT shuffled_surface_blind evidence_correct_rate: `0.0`
- SFT combined_blind_shuffle evidence_correct_rate: `0.0`
- SFT+GRPO standard evidence_correct_rate: `1.0`
- SFT+GRPO shuffled_surface_blind evidence_correct_rate: `0.0`
- SFT+GRPO combined_blind_shuffle evidence_correct_rate: `0.0`

This is consistent with a model that learned standard-format repair plans but did not learn to bind evidence selection to the current visible trace under challenge perturbations.

The new diagnostic script `scripts/diagnose_challenge_failures.py` will confirm exact predicted evidence IDs when the next HF job produces `outputs/model_eval/**/completions.jsonl`.

## 5. Why Evidence Correctness Collapsed

Most likely causes:

1. **Curriculum issue**: SFT warmstart trained on standard prompts only. It did not teach evidence selection under shuffled/blinded variants.
2. **Prompt issue**: The previous prompt said to output evidence IDs, but it did not strongly define evidence as a two-part grounding task: failed final action plus missing/unsafe control source.
3. **Benchmark shortcut risk**: Previous challenge variants preserved canonical IDs, so `s2`/`s4` could become a hidden shortcut even though the model failed to exploit it reliably.
4. **Not a verifier bug**: The stricter certificate gate is doing the right thing. It prevents a correct-looking patch from receiving a certificate when evidence is not grounded.
5. **Not primarily a GPU-size issue**: The 0.5B model already emits valid JSON and often predicts root cause correctly. The failure is specific to grounded evidence selection under challenge variants.

## 6. Family-Level Comparison From Latest HF Metrics

Full per-example completions are not locally available, but the summary metrics show the structure:

| Stage | Variant | Overall | Evidence | Root Cause | Patch Blocks | Certificate | Overblocking |
|---|---|---:|---:|---:|---:|---:|---:|
| SFT | standard | 0.8353 | 1.0000 | 0.9667 | 0.7000 | 0.6500 | 0.0000 |
| SFT | shuffled_surface_blind | 0.2680 | 0.0000 | 0.8000 | 0.3000 | 0.0000 | 0.1000 |
| SFT | combined_blind_shuffle | 0.4050 | 0.0000 | 0.9333 | 0.4833 | 0.0000 | 0.0333 |
| SFT+GRPO | standard | 0.7727 | 1.0000 | 0.9500 | 0.7167 | 0.5167 | 0.0000 |
| SFT+GRPO | shuffled_surface_blind | 0.2970 | 0.0000 | 0.7500 | 0.4333 | 0.0000 | 0.1167 |
| SFT+GRPO | combined_blind_shuffle | 0.3850 | 0.0000 | 0.8833 | 0.5833 | 0.0000 | 0.0333 |

Interpretation:

- Root cause remains relatively high under challenge prompts.
- Evidence collapses to zero.
- Patch quality partially survives, especially on combined challenge, but certificate success is zero because certificate gating requires correct evidence.
- Overblocking appears in challenge settings, which means the model sometimes chooses preserve/forbid combinations that block failures at the cost of valid behavior.

## 7. Why Root Cause Stays High While Evidence Collapses

Root cause can be inferred from candidate labels, trace vocabulary, and family-level semantics even when span grounding is weak. Evidence selection is harder: it requires selecting exact current visible IDs after trace-order and surface-form perturbations.

The previous SFT setup mostly taught:

- strict JSON
- family/root cause mapping
- patch clause mapping

It did not teach:

- locate evidence in shuffled traces
- adapt evidence IDs to current visible IDs
- avoid using memorized standard span IDs

## 8. Why Overblocking Appears

Overblocking appears when the model includes controls or preserve clauses from the wrong family, or when it blocks a failure mode without preserving the corresponding valid flow. The HF samples show this pattern in training generations: some completions mix `fresh_context_check` or `valid_fresh_context_flow` into `missing_verification`. That can block risk but fail valid preservation.

The fix is not to loosen the verifier. The fix is to train the model to emit family-consistent `require`, `forbid`, and `preserve` clauses under mixed prompt variants.

## 9. Classification Of The Failure

This is primarily a **curriculum and prompt-grounding issue**, with one benchmark-hardening issue fixed in this patch.

- Benchmark design bug fixed: challenge traces now use variant-specific public span aliases, so canonical `s2`/`s4` shortcuts are invalid.
- Prompt issue fixed: evidence instructions now define the two evidence roles and visible ID constraint.
- Curriculum issue fixed: SFT and optional GRPO can train on mixed `standard`, `shuffled_surface_blind`, and `combined_blind_shuffle` variants.
- Certificate gate: keep strict; no loosening was needed.

## 10. Diagnostic Script

Created:

```text
scripts/diagnose_challenge_failures.py
```

It reads:

- `outputs/model_eval/**/completions.jsonl`
- `outputs/grpo_tiny_hf/heldout_eval_completions.jsonl`
- `outputs/grpo_tiny_hf/sampled_generations.jsonl`

It reports:

- expected vs predicted evidence
- wrong evidence examples
- by-family failure counts
- by-prompt-variant failure counts
- certificate gate failure reasons
- overblocking examples
- repeated wrong clause patterns
- whether the model copied old standard `s2`/`s4` IDs

Current local limitation:

```text
The latest HF job printed summaries and sampled GRPO training generations, but full challenge eval completions were not persisted locally. The diagnostic script is ready for the next HF run, where scripts/hf_run_05b_challenge_curriculum.sh will produce model_eval completions.
```

## 11. Fix Implemented

The fix keeps verifier truth intact:

- challenge-aware SFT data via `--prompt-variants standard,shuffled_surface_blind,combined_blind_shuffle`
- variant-specific visible span IDs for shuffled challenge prompts
- prompt instruction that evidence must come from current visible span IDs
- public span metadata: visible ID, event type, visible tags, and public text
- scoring canonicalizes public IDs internally but measures public evidence correctness against the current prompt
- optional GRPO mixed-variant curriculum via `--prompt-variants`
- default next HF script skips GRPO unless `RUN_GRPO=1`

## 12. Next HF Run Gate

The next run should be a 0.5B challenge-curriculum run, not 1.5B:

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

Run 1.5B only if this 0.5B run improves challenge evidence correctness and certificate success without increasing invalid JSON, overblocking, or hardcoding.
