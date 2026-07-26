import json
import unittest

from judge_parser import JudgeResponseParseError, parse_judge_response
from judge_prompt import build_judge_prompt


def _valid_judge_response():
    return {
        "strategy_quality_score": 3,
        "survival_risk_management_score": 2,
        "budget_efficiency_score": 3,
        "opponent_supply_adaptation_score": 2,
        "temporal_planning_score": 3,
        "reasoning_code_trace_consistency_score": 1,
        "implementation_quality_score": 1,
        "primary_failure_mode": "submission_format_failure",
        "failure_labels": ["submission_format_failure"],
        "failure_annotations": [
            {
                "label": "submission_format_failure",
                "severity": 5,
                "confidence": 5,
                "evidence_days": [1],
                "rationale": "The submitted policy was not executable.",
            }
        ],
        "strengths": [],
        "weaknesses": ["The policy could not be executed."],
        "evidence_summary": "Execution failed before a valid bid was produced.",
        "short_diagnosis": "Invalid agent submission.",
        "judge_confidence": 5,
    }


class JudgeParserTests(unittest.TestCase):
    def test_accepts_agent_submission_format_failure_as_a_real_label(self):
        parsed = parse_judge_response(json.dumps(_valid_judge_response()))

        self.assertEqual(
            parsed["primary_failure_mode"],
            "submission_format_failure",
        )
        self.assertEqual(
            parsed["failure_labels"],
            ["submission_format_failure"],
        )
        self.assertEqual(parsed["judge_confidence"], 5)

    def test_invalid_json_raises_parse_error(self):
        with self.assertRaises(JudgeResponseParseError):
            parse_judge_response("this is not JSON")

    def test_missing_required_field_raises_parse_error(self):
        response = _valid_judge_response()
        del response["short_diagnosis"]

        with self.assertRaises(JudgeResponseParseError):
            parse_judge_response(json.dumps(response))


class JudgePromptTests(unittest.TestCase):
    def test_prompt_blinds_identifiers_and_excludes_legacy_metric_labels(self):
        item = {
            "item_id": "SECRET_ITEM_ID",
            "condition": "SECRET_CONDITION",
            "experiment_id": "SECRET_EXPERIMENT",
            "meta_round_id": 2,
            "agent_id": "SECRET_AGENT_ID",
            "model_name": "SECRET_MODEL_NAME",
            "environment": {
                "scenario": "synthetic",
                "episode_days": 2,
                "players": [
                    {
                        "agent_id": "A",
                        "daily_salary": 100.0,
                        "water_requirement": 5.0,
                    }
                ],
            },
            "submission_status": {
                "one_shot_format_valid": True,
                "repair_used": False,
                "final_format_valid": True,
            },
            "policy": {
                "one_shot_reasoning": "Use a fixed bid.",
                "one_shot_code": "def get_bid(*args): return 10",
                "final_reasoning": "Use a fixed bid.",
                "final_code": "def get_bid(*args): return 10",
            },
            "trajectory": {
                "evidence_summary": {
                    "total_actual_payment": 10.0,
                    "budget_before_death_reset": 90.0,
                },
                "daily_evidence": [
                    {
                        "day": 1,
                        "bid": 10.0,
                        "won_water": True,
                        "actual_payment": 10.0,
                    }
                ],
                "daily_trace": [{"raw_trace_secret": "TRACE_LEAK"}],
                "metrics": {
                    "failure_types": ["LEGACY_FAILURE_LABEL_LEAK"],
                },
            },
        }

        prompt = build_judge_prompt(item, blind_model_names=True)
        lower_prompt = prompt.lower()

        self.assertNotIn("SECRET_ITEM_ID", prompt)
        self.assertNotIn("SECRET_CONDITION", prompt)
        self.assertNotIn("SECRET_EXPERIMENT", prompt)
        self.assertNotIn("SECRET_AGENT_ID", prompt)
        self.assertNotIn("SECRET_MODEL_NAME", prompt)
        self.assertNotIn('"item_id"', prompt)
        self.assertNotIn('"condition"', prompt)
        self.assertNotIn('"meta_round_id"', prompt)
        self.assertNotIn("LEGACY_FAILURE_LABEL_LEAK", prompt)
        self.assertNotIn("TRACE_LEAK", prompt)
        self.assertIn("daily_evidence", prompt)
        self.assertIn("actual_payment", prompt)
        self.assertIn("death", lower_prompt)
        self.assertIn("reset", lower_prompt)


if __name__ == "__main__":
    unittest.main()
