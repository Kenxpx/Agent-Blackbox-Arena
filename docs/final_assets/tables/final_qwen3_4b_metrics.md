# Final Qwen3-4B Metrics Table

Model: `Qwen/Qwen3-4B-Instruct-2507`

Checkpoint: `SFT+GRPO final H200`

HF Job: `69edcef7d70108f37acdfeb3`

Eval seeds: `1000-1019`

Stoploss: `PASS`

| variant | overall_score | certificate_success_rate | evidence_correct_rate | hidden_regression_pass_rate | valid_preservation_rate | invalid_json_rate | overblocking_rate | hardcoded_patch_rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| standard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| shuffled_surface_blind | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |
| combined_blind_shuffle | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 |

Claims are bounded to these reported synthetic families, prompt variants, and eval seeds.
