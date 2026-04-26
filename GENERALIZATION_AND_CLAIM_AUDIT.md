# Generalization And Claim Audit

This file is intentionally conservative. It keeps leakage/generalization checks separate from final training claims so the submission does not overclaim. The selected final model is `Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200` from HF Job `69edcef7d70108f37acdfeb3`.

## 1. Leakage Audit Result

Result: **PASS**

- Hidden prompt leakage: `passed`
- Records checked across standard and challenge variants: `1050`
- Target JSON appears verbatim in eval prompts: `False`
- Incident IDs usable for hardcoding in prompts: `False`
- Candidate answer positions vary across train/eval/challenge slices: `True`
- Family-specific labels: public metadata in standard OpenEnv prompts; blind-family challenge prompts are available to test dependence on that metadata.

Candidate answer-position distribution:

```json
{
  "combined_blind_shuffle_eval": {
    "missing_verification": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 4,
          "1": 8,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 2,
          "1": 8,
          "2": 10
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 4,
          "1": 8,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 6,
          "2": 6,
          "3": 4,
          "4": 3
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    },
    "permission_scope": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 8,
          "2": 9
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 2,
          "1": 12,
          "2": 6
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 8,
          "2": 9
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 6,
          "1": 6,
          "2": 2,
          "3": 3,
          "4": 3
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    },
    "stale_retrieval": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 2,
          "1": 13,
          "2": 5
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 9,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 4,
          "1": 8,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 3,
          "2": 3,
          "3": 5,
          "4": 6
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    }
  },
  "sft_train_standard": {
    "missing_verification": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 2,
          "2": 3
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "1": 3,
          "2": 3
        },
        "positions_seen": [
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 3,
          "2": 3
        },
        "positions_seen": [
          0,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 2,
          "3": 1,
          "4": 2
        },
        "positions_seen": [
          0,
          1,
          3,
          4
        ],
        "single_position": false
      }
    },
    "permission_scope": {
      "forbid": {
        "always_first": false,
        "counts": {
          "1": 4,
          "2": 2
        },
        "positions_seen": [
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 1,
          "2": 4
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 1,
          "2": 4
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 2,
          "3": 1,
          "4": 2
        },
        "positions_seen": [
          0,
          1,
          3,
          4
        ],
        "single_position": false
      }
    },
    "stale_retrieval": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 2,
          "2": 3
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 2,
          "2": 3
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 4,
          "2": 1
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 1,
          "2": 1,
          "4": 1
        },
        "positions_seen": [
          0,
          1,
          2,
          4
        ],
        "single_position": false
      }
    }
  },
  "shuffled_surface_blind_eval": {
    "missing_verification": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 5,
          "1": 7,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 8,
          "2": 9
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 2,
          "1": 11,
          "2": 7
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 4,
          "1": 1,
          "2": 4,
          "3": 8,
          "4": 3
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    },
    "permission_scope": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 4,
          "2": 13
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 1,
          "1": 9,
          "2": 10
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 9,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 7,
          "1": 4,
          "2": 4,
          "3": 4,
          "4": 1
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    },
    "stale_retrieval": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 9,
          "2": 8
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 3,
          "1": 7,
          "2": 10
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 5,
          "1": 6,
          "2": 9
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 2,
          "1": 4,
          "2": 5,
          "3": 3,
          "4": 6
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    }
  },
  "standard_eval": {
    "missing_verification": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 16,
          "1": 17,
          "2": 17
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 7,
          "1": 19,
          "2": 24
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 6,
          "1": 20,
          "2": 24
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 10,
          "1": 10,
          "2": 7,
          "3": 10,
          "4": 13
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    },
    "permission_scope": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 6,
          "1": 23,
          "2": 21
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 8,
          "1": 17,
          "2": 25
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 7,
          "1": 23,
          "2": 20
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 4,
          "1": 14,
          "2": 11,
          "3": 9,
          "4": 12
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    },
    "stale_retrieval": {
      "forbid": {
        "always_first": false,
        "counts": {
          "0": 9,
          "1": 23,
          "2": 18
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "preserve": {
        "always_first": false,
        "counts": {
          "0": 6,
          "1": 29,
          "2": 15
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "require_first_clause": {
        "always_first": false,
        "counts": {
          "0": 9,
          "1": 15,
          "2": 26
        },
        "positions_seen": [
          0,
          1,
          2
        ],
        "single_position": false
      },
      "root_cause": {
        "always_first": false,
        "counts": {
          "0": 5,
          "1": 14,
          "2": 10,
          "3": 11,
          "4": 10
        },
        "positions_seen": [
          0,
          1,
          2,
          3,
          4
        ],
        "single_position": false
      }
    }
  }
}
```

## 2. Train/Eval Separation Result

- SFT train seeds: `0-5`
- GRPO train seeds: `0-2`
- Larger eval seeds prepared: `1000-1049`
- Train/eval seed overlap: `[]`
- Train/eval record ID overlap: `[]`

## 3. Final Held-Out Eval Metrics

The final selected Qwen3-4B H200 SFT+GRPO run completed verifier-scored evaluation over seeds `1000-1019`:

| Variant | Overall | Certificate | Evidence | Hidden pass | Valid preserve | Invalid JSON |
|---|---:|---:|---:|---:|---:|---:|
| `standard` | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 |
| `shuffled_surface_blind` | 0.9557 | 0.8833 | 0.8833 | 1.0000 | 1.0000 | 0.0000 |
| `combined_blind_shuffle` | 0.9367 | 0.8333 | 0.8333 | 1.0000 | 1.0000 | 0.0000 |

Safety rates were `overblocking_rate=0.0000`, `hardcoded_patch_rate=0.0000`, and stoploss `PASS`. The local oracle checks below remain useful as verifier sanity checks, not as the final trained-model metric source.

Local checkpoint availability:

- `outputs/sft_qwen25_05b_json/model`: `False`
- `outputs/grpo_tiny_hf/model`: `False`

Because the final trained checkpoint is not stored in this repository, this CPU audit does not rerun Qwen3-4B inference locally. The final model evidence comes from the completed HF Job log and checked-in final metrics/assets.

Oracle verifier sanity over the same larger seed range:

```json
{
  "by_family": {
    "missing_verification": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 50,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    },
    "permission_scope": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 50,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    },
    "stale_retrieval": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 50,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    }
  },
  "by_prompt_variant": {
    "standard": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 150,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    }
  },
  "certificate_gate_fail_rate": 0.0,
  "certificate_success_rate": 1.0,
  "episodes": 150,
  "eval_seeds": "1000-1049",
  "evidence_correct_rate": 1.0,
  "families": [
    "stale_retrieval",
    "missing_verification",
    "permission_scope"
  ],
  "hardcoded_patch_rate": 0.0,
  "hidden_regression_pass_rate": 1.0,
  "invalid_json_rate": 0.0,
  "mode": "mock",
  "model": "oracle_correct_solver_for_sanity",
  "model_label": "mock_oracle",
  "note": "CPU mock/oracle sanity check, not trained model evidence.",
  "overall_score": 1.0,
  "overblocking_rate": 0.0,
  "patch_blocks_rate": 1.0,
  "prompt_variant": "standard",
  "root_cause_correct_rate": 1.0,
  "valid_preservation_rate": 1.0
}
```

This oracle sanity check proves the verifier can score correct repair plans across the larger seed range. It is **not** trained-model evidence.

## 4. Challenge Eval Metrics

Challenge variants implemented: `shuffled_surface_blind`, `combined_blind_shuffle`

`shuffled_surface_blind` shuffles trace spans, rewrites surface wording, and blinds the family label as `agent_reliability_failure`. `combined_blind_shuffle` also changes service/requester/capability names while preserving the same root-cause semantics. The final Qwen3-4B run reports real model metrics for both challenge variants above.

Oracle sanity on challenge seeds `1000-1019`:

```json
{
  "by_family": {
    "missing_verification": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 20,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    },
    "permission_scope": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 20,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    },
    "stale_retrieval": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 20,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    }
  },
  "by_prompt_variant": {
    "shuffled_surface_blind": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 60,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    }
  },
  "certificate_gate_fail_rate": 0.0,
  "certificate_success_rate": 1.0,
  "episodes": 60,
  "eval_seeds": "1000-1019",
  "evidence_correct_rate": 1.0,
  "families": [
    "stale_retrieval",
    "missing_verification",
    "permission_scope"
  ],
  "hardcoded_patch_rate": 0.0,
  "hidden_regression_pass_rate": 1.0,
  "invalid_json_rate": 0.0,
  "mode": "mock",
  "model": "oracle_correct_solver_for_sanity",
  "model_label": "mock_oracle",
  "note": "CPU mock/oracle sanity check, not trained model evidence.",
  "overall_score": 1.0,
  "overblocking_rate": 0.0,
  "patch_blocks_rate": 1.0,
  "prompt_variant": "shuffled_surface_blind",
  "root_cause_correct_rate": 1.0,
  "valid_preservation_rate": 1.0
}
```

Oracle sanity on `combined_blind_shuffle` seeds `1000-1019`:

```json
{
  "by_family": {
    "missing_verification": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 20,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    },
    "permission_scope": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 20,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    },
    "stale_retrieval": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 20,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    }
  },
  "by_prompt_variant": {
    "combined_blind_shuffle": {
      "certificate_gate_fail_rate": 0.0,
      "certificate_success_rate": 1.0,
      "episodes": 60,
      "evidence_correct_rate": 1.0,
      "hardcoded_patch_rate": 0.0,
      "hidden_regression_pass_rate": 1.0,
      "invalid_json_rate": 0.0,
      "overall_score": 1.0,
      "overblocking_rate": 0.0,
      "patch_blocks_rate": 1.0,
      "root_cause_correct_rate": 1.0,
      "valid_preservation_rate": 1.0
    }
  },
  "certificate_gate_fail_rate": 0.0,
  "certificate_success_rate": 1.0,
  "episodes": 60,
  "eval_seeds": "1000-1019",
  "evidence_correct_rate": 1.0,
  "families": [
    "stale_retrieval",
    "missing_verification",
    "permission_scope"
  ],
  "hardcoded_patch_rate": 0.0,
  "hidden_regression_pass_rate": 1.0,
  "invalid_json_rate": 0.0,
  "mode": "mock",
  "model": "oracle_correct_solver_for_sanity",
  "model_label": "mock_oracle",
  "note": "CPU mock/oracle sanity check, not trained model evidence.",
  "overall_score": 1.0,
  "overblocking_rate": 0.0,
  "patch_blocks_rate": 1.0,
  "prompt_variant": "combined_blind_shuffle",
  "root_cause_correct_rate": 1.0,
  "valid_preservation_rate": 1.0
}
```

## 5. Plots Created

No new trained-model plots are created by this CPU audit. Final selected plots and tables are stored under `docs/final_assets/` and are generated from the completed H200 run's reported metrics/log evidence.

## 6. README Changes

README should claim the Qwen3-4B final H200 SFT+GRPO result only within the reported synthetic MVP families, prompt variants, and eval seeds `1000-1019`.

## 7. TRAINING_RUN_LOG.md Update

TRAINING_RUN_LOG.md records:

- earlier failed base 0.5B GRPO attempt
- SFT warmstart recovery
- GRPO validation caveat
- final Qwen3-4B H200 selection
- failed/intermediate larger-model runs kept as audit evidence

The final H200 run is complete. The historical HF eval command remains here only as a reproducibility reference:

```bash
hf jobs run \
  --flavor t4-small \
  --timeout 90m \
  python:3.11 \
  -- \
  bash \
  -lc \
  "apt-get update && apt-get install -y git && git clone https://github.com/Kenxpx/Agent-Blackbox-Arena.git && cd Agent-Blackbox-Arena && pip install -e '.[training]' && python scripts/self_check.py && python training/evaluate_checkpoint.py --model Qwen/Qwen2.5-0.5B-Instruct --model-label base_0_5b --eval-seeds 1000-1019 --output-dir outputs/model_eval/base_0_5b_standard && python training/train_sft_warmstart.py --confirm-real-training --model Qwen/Qwen2.5-0.5B-Instruct --max-steps 30 --train-seeds 0-5 --eval-seeds 1000-1002 --output-dir outputs/sft_qwen25_05b_json --per-device-train-batch-size 1 --gradient-accumulation-steps 1 --learning-rate 1e-5 --max-completion-length 160 --save-steps 30 && python training/evaluate_checkpoint.py --model outputs/sft_qwen25_05b_json/model --model-label sft_0_5b --eval-seeds 1000-1019 --output-dir outputs/model_eval/sft_0_5b_standard && python training/evaluate_checkpoint.py --model outputs/sft_qwen25_05b_json/model --model-label sft_0_5b_shuffled_surface_blind --eval-seeds 1000-1019 --prompt-variant shuffled_surface_blind --output-dir outputs/model_eval/sft_0_5b_shuffled_surface_blind && python training/evaluate_checkpoint.py --model outputs/sft_qwen25_05b_json/model --model-label sft_0_5b_combined_blind_shuffle --eval-seeds 1000-1019 --prompt-variant combined_blind_shuffle --output-dir outputs/model_eval/sft_0_5b_combined_blind_shuffle && python training/train_json_grpo.py --confirm-real-training --model outputs/sft_qwen25_05b_json/model --max-steps 10 --train-seeds 0-2 --eval-seeds 1000 --eval-prompt-variant combined_blind_shuffle --output-dir outputs/grpo_tiny_hf --num-generations 2 --per-device-train-batch-size 2 --gradient-accumulation-steps 1 --learning-rate 5e-6 --max-completion-length 160 --format-reward-weight 0.2 --save-steps 10 && python training/evaluate_checkpoint.py --model outputs/grpo_tiny_hf/model --model-label sft_grpo_0_5b --eval-seeds 1000-1019 --output-dir outputs/model_eval/sft_grpo_0_5b_standard && python training/evaluate_checkpoint.py --model outputs/grpo_tiny_hf/model --model-label sft_grpo_0_5b_shuffled_surface_blind --eval-seeds 1000-1019 --prompt-variant shuffled_surface_blind --output-dir outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind && python training/evaluate_checkpoint.py --model outputs/grpo_tiny_hf/model --model-label sft_grpo_0_5b_combined_blind_shuffle --eval-seeds 1000-1019 --prompt-variant combined_blind_shuffle --output-dir outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle && python scripts/plot_model_eval.py --summary base=outputs/model_eval/base_0_5b_standard/summary.json --summary sft=outputs/model_eval/sft_0_5b_standard/summary.json --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_standard/summary.json --output-dir outputs/model_eval && python scripts/plot_model_eval.py --summary sft=outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json --summary sft_grpo=outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json --output-dir outputs/model_eval/combined_blind_shuffle && echo '=== BASE SUMMARY ===' && cat outputs/model_eval/base_0_5b_standard/summary.json && echo '=== SFT STANDARD SUMMARY ===' && cat outputs/model_eval/sft_0_5b_standard/summary.json && echo '=== SFT SHUFFLED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_0_5b_shuffled_surface_blind/summary.json && echo '=== SFT COMBINED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_0_5b_combined_blind_shuffle/summary.json && echo '=== SFT+GRPO STANDARD SUMMARY ===' && cat outputs/model_eval/sft_grpo_0_5b_standard/summary.json && echo '=== SFT+GRPO SHUFFLED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_grpo_0_5b_shuffled_surface_blind/summary.json && echo '=== SFT+GRPO COMBINED CHALLENGE SUMMARY ===' && cat outputs/model_eval/sft_grpo_0_5b_combined_blind_shuffle/summary.json"

```

## 8. Larger-Model Decision

Decision: **Qwen3-4B final H200 SFT+GRPO is selected.**

Reason: the selected run improves the reported challenge evidence/certificate metrics while keeping invalid JSON, overblocking, and hardcoded patch rates at `0.0000`.

## 9. GO / NO-GO For Final Training Claims

Decision: **GO for bounded final Qwen3-4B claims.**

Safe claim today:

> Qwen/Qwen3-4B-Instruct-2507 SFT+GRPO final H200 is the selected trained result for the reported synthetic MVP families, prompt variants, and eval seeds `1000-1019`.

Unsafe claims:

- GRPO learned the task from scratch
- broad production safety
- SOTA
- unlimited generalization
- 1.5B success
- Qwen2.5-3B success
- failed/error H200 jobs as successful
