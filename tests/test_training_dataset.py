import json

from training.evaluate_model import score_completion
from training.make_dataset import CHALLENGE_VARIANTS, build_records
from training.train_sft_warmstart import build_sft_records


def prompt_as_text(record):
    return json.dumps(record["prompt"], ensure_ascii=False)


def test_training_prompts_use_chat_format_without_hidden_answers():
    records = build_records("train", [0])
    assert records
    for record in records:
        prompt = record["prompt"]
        text = prompt_as_text(record)
        assert isinstance(prompt, list)
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"
        assert "Return ONLY valid JSON" in text
        assert "incident_id" not in text
        assert "hidden_regression_variants" not in text
        assert "expected_patch" not in text
        assert "one_allowed_require_clause" not in text


def test_sft_targets_are_verifier_correct_json():
    rows = build_sft_records("train", [0])
    assert rows
    for row in rows:
        completion = row["completion"][0]["content"]
        parsed = json.loads(completion)
        assert set(parsed) == {"evidence_spans", "root_cause", "patch", "regression_tests", "rationale"}
        metrics = score_completion(row["family"], int(row["seed"]), completion)
        assert metrics["overall_score"] == 1.0
        assert metrics["certificate_success"] == 1.0
        assert metrics["invalid_json"] == 0.0


def test_challenge_prompt_variants_do_not_leak_hidden_answers():
    for variant in CHALLENGE_VARIANTS:
        records = build_records("eval", [1000], prompt_variant=variant)
        assert records
        for record in records:
            text = prompt_as_text(record)
            target = json.dumps(record["target_json"], ensure_ascii=False, sort_keys=True)
            assert target not in text
            assert f"{record['family']}_{int(record['seed']):03d}" not in text
            assert "hidden_regression_variants" not in text
            assert "answer_key_clause_ids" not in text
            if "blind_family" in variant or variant == "shuffled_surface_blind":
                assert "agent_reliability_failure" in text
                assert f"family: {record['family']}" not in text
