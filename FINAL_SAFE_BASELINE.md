# Final Safe Baseline

This file records the current submission-safe fallback before append-only larger-model stretch runs.

## Current Safe Result

Final selected trained evidence: **0.5B challenge-curriculum SFT**.

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

- Current final evidence is the real 0.5B challenge-curriculum SFT result.
- Extracted HF evidence is tracked under `outputs/model_eval/extracted_hf/hf_05b_challenge_curriculum/`.
- Final real plots are tracked under `outputs/final_plots/`.
- Notebook/rerun guide is preserved at `notebooks/Agent_BlackBox_Arena_Training_Rerun.ipynb`.
- No 1.5B, 3B, 4B, or H200 result is claimed as final evidence.

## Larger-Model Stretch Policy

Larger-model runs are append-only experiments. Their outputs must go under `outputs/larger_models/` and must not overwrite the current 0.5B evidence, final plots, notebook, or Hugging Face Space UI.

If larger-model runs fail, stop by quality gate, or do not produce real verifier-scored improvements, the 0.5B challenge-curriculum SFT result remains the fallback final submission result.
