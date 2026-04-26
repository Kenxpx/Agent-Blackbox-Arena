# Final Recent H200 Runs Report

This report summarizes the five most relevant recent larger-model H200 runs after the CUDA-image fix path. Metrics are real verifier-scored summaries from saved HF job logs. Failed/error runs are marked honestly and are not selected as final evidence.

## Final Selected Model Decision

Final selected model for submission: **Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200** from job `69edcef7d70108f37acdfeb3`.

Reason: it is the strongest real result, with standard `1.0000`, shuffled challenge `0.9557`, combined challenge `0.9367`, `invalid_json_rate=0.0`, `overblocking_rate=0.0`, and `hardcoded_patch_rate=0.0`. It beats the previous 0.5B fallback on challenge evidence and certificate rates by a large margin. The older 0.5B result remains a safe fallback only if final docs/packaging are not updated to claim the Qwen3-4B evidence.

## Run 1: Final Qwen3-4B H200

- Job ID: `69edcef7d70108f37acdfeb3`
- Job status: `COMPLETED`
- Model used: `Qwen/Qwen3-4B-Instruct-2507`
- Output root: `outputs/larger_models/qwen3_4b_2507_final_h200/`
- Selected checkpoint for metrics: `SFT+GRPO`
- Standard summary: overall `1.0000`, certificate `1.0000`, evidence `1.0000`, hidden `1.0000`, valid preservation `1.0000`, invalid JSON `0.0000`
- Shuffled_surface_blind summary: overall `0.9557`, certificate `0.8833`, evidence `0.8833`, hidden `1.0000`, valid preservation `1.0000`, invalid JSON `0.0000`
- Combined_blind_shuffle summary: overall `0.9367`, certificate `0.8333`, evidence `0.8333`, hidden `1.0000`, valid preservation `1.0000`, invalid JSON `0.0000`
- Stoploss report: `PASS`; GRPO verifier overall `0.9402`, evidence `0.8625`, certificate `0.8625`, no failures, no warnings
- invalid_json_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- evidence_correct_rate for shuffled + combined: shuffled `0.8833`, combined `0.8333`
- certificate_success_rate for shuffled + combined: shuffled `0.8833`, combined `0.8333`
- overblocking_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- hardcoded_patch_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- Plot paths:
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_model_eval/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/sft_training/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_model_eval/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/plots/grpo_training/`
- Tracking path:
  - `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/sft_warmstart_sft_qwen3_4b_2507_final_h200_challenge_curriculum/`
  - `outputs/larger_models/qwen3_4b_2507_final_h200/tracking/grpo_grpo_qwen3_4b_2507_final_h200_challenge_curriculum/`
- Log file: `logs/final/hf_job_qwen3_4b_final_h200_69edcef7d70108f37acdfeb3_tail.txt`

## Run 2: Qwen3-4B Fast R2 H200

- Job ID: `69edcb9ad70108f37acdfe5e`
- Job status: `COMPLETED`
- Model used: `Qwen/Qwen3-4B-Instruct-2507`
- Output root: `outputs/larger_models/qwen3_4b_2507_fast_r2/`
- Selected checkpoint for metrics: `SFT+GRPO`
- Standard summary: overall `0.7613`, certificate `0.4667`, evidence `0.6667`, hidden `0.8667`, valid preservation `1.0000`, invalid JSON `0.0000`
- Shuffled_surface_blind summary: overall `0.7400`, certificate `0.4667`, evidence `0.7333`, hidden `0.8333`, valid preservation `1.0000`, invalid JSON `0.0000`
- Combined_blind_shuffle summary: overall `0.6707`, certificate `0.4000`, evidence `0.4667`, hidden `0.8333`, valid preservation `1.0000`, invalid JSON `0.0000`
- Stoploss report: `PASS`; warning noted that held-out score beat random while held-out certificate success was zero
- invalid_json_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- evidence_correct_rate for shuffled + combined: shuffled `0.7333`, combined `0.4667`
- certificate_success_rate for shuffled + combined: shuffled `0.4667`, combined `0.4000`
- overblocking_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- hardcoded_patch_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- Plot paths:
  - `outputs/larger_models/qwen3_4b_2507_fast_r2/plots/sft_model_eval/`
  - `outputs/larger_models/qwen3_4b_2507_fast_r2/plots/sft_training/`
  - `outputs/larger_models/qwen3_4b_2507_fast_r2/plots/grpo_model_eval/`
  - `outputs/larger_models/qwen3_4b_2507_fast_r2/plots/grpo_training/`
- Tracking path:
  - `outputs/larger_models/qwen3_4b_2507_fast_r2/tracking/sft_warmstart_sft_qwen3_4b_2507_fast_r2_challenge_curriculum/`
  - `outputs/larger_models/qwen3_4b_2507_fast_r2/tracking/grpo_grpo_qwen3_4b_2507_fast_r2_challenge_curriculum/`
- Log file: `logs/archive/hf_job_qwen3_4b_fast_r2_h200_cuda128_69edcb9ad70108f37acdfe5e_logs.txt`

## Run 3: Qwen2.5-3B Fast R2 H200

- Job ID: `69edcb91d70108f37acdfe5a`
- Job status: `COMPLETED`
- Model used: `Qwen/Qwen2.5-3B-Instruct`
- Output root: `outputs/larger_models/qwen25_3b_fast_r2/`
- Selected checkpoint for metrics: `SFT`; GRPO skipped because SFT fast gate stopped
- Standard summary: overall `0.1520`, certificate `0.0000`, evidence `0.3333`, hidden `0.0333`, valid preservation `0.0667`, invalid JSON `0.3333`
- Shuffled_surface_blind summary: overall `0.1467`, certificate `0.0000`, evidence `0.3333`, hidden `0.1000`, valid preservation `0.2000`, invalid JSON `0.0000`
- Combined_blind_shuffle summary: overall `0.1507`, certificate `0.0000`, evidence `0.2667`, hidden `0.1000`, valid preservation `0.2000`, invalid JSON `0.0667`
- Stoploss report: `STOP`; SFT fast gate stopped because JSON and overblocking behavior were not healthy enough for GRPO
- invalid_json_rate: standard `0.3333`, shuffled `0.0000`, combined `0.0667`
- evidence_correct_rate for shuffled + combined: shuffled `0.3333`, combined `0.2667`
- certificate_success_rate for shuffled + combined: shuffled `0.0000`, combined `0.0000`
- overblocking_rate: standard `0.0667`, shuffled `0.2667`, combined `0.2000`
- hardcoded_patch_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- Plot paths:
  - `outputs/larger_models/qwen25_3b_fast_r2/plots/sft_model_eval/`
  - `outputs/larger_models/qwen25_3b_fast_r2/plots/sft_training/`
- Tracking path:
  - `outputs/larger_models/qwen25_3b_fast_r2/tracking/sft_warmstart_sft_qwen25_3b_fast_r2_challenge_curriculum/`
- Log file: `logs/archive/hf_job_3b_fast_r2_h200_cuda128_69edcb91d70108f37acdfe5a_logs.txt`

## Run 4: Qwen3-4B Fast CUDA Retry H200

- Job ID: `69edc9c3d2c8bd8662bcf93c`
- Job status: `ERROR`
- Model used: `Qwen/Qwen3-4B-Instruct-2507`
- Output root: `outputs/larger_models/qwen3_4b_2507_fast/`
- Selected checkpoint for metrics: `SFT`; SFT+GRPO evaluation failed after GRPO because the saved adapter referenced `None`
- Standard summary: overall `0.7920`, certificate `0.5333`, evidence `0.6667`, hidden `0.9000`, valid preservation `1.0000`, invalid JSON `0.0000`
- Shuffled_surface_blind summary: overall `0.8013`, certificate `0.6000`, evidence value not printed in short tail but SFT gate passed, hidden `0.9000`, invalid JSON `0.0000`
- Combined_blind_shuffle summary: overall `0.6907`, certificate `0.4000`, evidence value not printed in short tail but SFT gate passed, hidden `0.8667`, invalid JSON `0.0000`
- Stoploss report: GRPO stoploss `PASS`, but job ended `ERROR` during SFT+GRPO evaluation with `OSError: None is not a local folder and is not a valid model identifier`
- invalid_json_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- evidence_correct_rate for shuffled + combined: SFT gate passed, exact printed values not fully preserved in this tail log
- certificate_success_rate for shuffled + combined: shuffled `0.6000`, combined `0.4000`
- overblocking_rate: not shown in short progress lines; SFT gate passed
- hardcoded_patch_rate: not shown in short progress lines; SFT gate passed
- Plot paths: not generated because the job errored before the plot phase
- Tracking path:
  - `outputs/larger_models/qwen3_4b_2507_fast/tracking/sft_warmstart_sft_qwen3_4b_2507_fast_challenge_curriculum/`
  - `outputs/larger_models/qwen3_4b_2507_fast/tracking/grpo_grpo_qwen3_4b_2507_fast_challenge_curriculum/`
- Log file: `logs/archive/hf_job_qwen3_4b_fast_h200_cuda128_69edc9c3d2c8bd8662bcf93c_tail.txt`

## Run 5: Qwen2.5-3B Fast CUDA Retry H200

- Job ID: `69edc9b8d2c8bd8662bcf937`
- Job status: `COMPLETED`
- Model used: `Qwen/Qwen2.5-3B-Instruct`
- Output root: `outputs/larger_models/qwen25_3b_fast/`
- Selected checkpoint for metrics: `SFT`; GRPO skipped because SFT fast gate stopped
- Standard summary: overall `0.1520`, certificate `0.0000`, evidence `0.3333`, hidden `0.0333`, valid preservation `0.0667`, invalid JSON `0.2667`
- Shuffled_surface_blind summary: overall `0.1520`, certificate `0.0000`, evidence `0.3333`, hidden `0.1333`, valid preservation `0.2667`, invalid JSON `0.0000`
- Combined_blind_shuffle summary: overall `0.1507`, certificate `0.0000`, evidence `0.2667`, hidden `0.1000`, valid preservation `0.2000`, invalid JSON `0.0667`
- Stoploss report: `STOP`; fast SFT gate stopped and skipped GRPO
- invalid_json_rate: standard `0.2667`, shuffled `0.0000`, combined `0.0667`
- evidence_correct_rate for shuffled + combined: shuffled `0.3333`, combined `0.2667`
- certificate_success_rate for shuffled + combined: shuffled `0.0000`, combined `0.0000`
- overblocking_rate: standard `0.1333`, shuffled `0.2667`, combined `0.2000`
- hardcoded_patch_rate: standard `0.0000`, shuffled `0.0000`, combined `0.0000`
- Plot paths:
  - `outputs/larger_models/qwen25_3b_fast/plots/sft_model_eval/`
  - `outputs/larger_models/qwen25_3b_fast/plots/sft_training/`
- Tracking path:
  - `outputs/larger_models/qwen25_3b_fast/tracking/sft_warmstart_sft_qwen25_3b_fast_challenge_curriculum/`
- Log file: `logs/archive/hf_job_3b_fast_h200_cuda128_69edc9b8d2c8bd8662bcf937_tail.txt`

## Ranking

1. `69edcef7d70108f37acdfeb3` - Qwen3-4B final SFT+GRPO: **selected final model**
2. `69edcb9ad70108f37acdfe5e` - Qwen3-4B fast r2 SFT+GRPO: useful intermediate, weaker than final
3. `69edc9c3d2c8bd8662bcf93c` - Qwen3-4B fast CUDA retry: useful SFT signal, but job errored after GRPO
4. `69edcb91d70108f37acdfe5a` - Qwen2.5-3B fast r2: stopped by SFT gate
5. `69edc9b8d2c8bd8662bcf937` - Qwen2.5-3B fast CUDA retry: stopped by SFT gate

## Final Recommendation

Use `Qwen/Qwen3-4B-Instruct-2507` final H200 SFT+GRPO as the selected trained model. The older 0.5B challenge-curriculum SFT remains a historical fallback, while the final Qwen3-4B run is the best real verifier-scored result.
