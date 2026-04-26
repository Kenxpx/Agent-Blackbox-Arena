# Final Safe Baseline

This file records the submission-safe historical fallback that was preserved before append-only larger-model stretch runs.

## Current Safe Result

Historical fallback trained evidence: **0.5B challenge-curriculum SFT**.

Model family: `Qwen/Qwen2.5-0.5B-Instruct`.

Metrics:

- Standard overall: `0.9492`
- Standard certificate: `0.9333`
- Standard evidence: `1.0000`
- Shuffled challenge overall: `0.6710`
- Shuffled challenge certificate: `0.1833`
- Shuffled challenge evidence: `0.1833`
- Combined challenge overall: `0.6753`
- Combined challenge certificate: `0.2167`
- Combined challenge evidence: `0.2167`
- Invalid JSON: `0.0`
- Challenge overblocking: `0.0`

## Space And Evidence Status

Working Hugging Face Space: https://huggingface.co/spaces/Kenxpx/Agent-Blackbox-Arena

Evidence package status:

- Historical fallback evidence is the real 0.5B challenge-curriculum SFT result.
- Extracted HF evidence is tracked under `outputs/model_eval/extracted_hf/hf_05b_challenge_curriculum/`.
- Historical fallback plots are tracked under `outputs/final_plots/`.
- Notebook/rerun guide is preserved at `notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb`.
- The final selected model is now Qwen3-4B H200 SFT+GRPO, job `69edcef7d70108f37acdfeb3`; this 0.5B file remains the fallback record.

## Larger-Model Stretch Policy

Larger-model runs are append-only experiments. Their outputs must go under `outputs/larger_models/` and must not overwrite the 0.5B fallback evidence, historical plots, notebook, or Hugging Face Space UI.

If the final Qwen3-4B evidence cannot be used administratively, the 0.5B challenge-curriculum SFT result remains the historical fallback.
