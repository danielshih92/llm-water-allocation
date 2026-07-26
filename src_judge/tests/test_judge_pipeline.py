import io
import json
import os
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from judge_core import run_judge_pipeline


def _judge_item():
    return {
        "item_id": "batch::exp_001::meta_1::A",
        "batch_name": "batch",
        "condition": "condition",
        "experiment_id": "exp_001",
        "meta_round_id": 1,
        "agent_id": "A",
        "model_name": "evaluated-model",
        "is_valid_item": True,
        "submission_status": {
            "admitted": 1,
            "outcome_valid": 1,
            "repair_used": 0,
        },
        "environment": {
            "scenario": "synthetic",
            "supply_range": [10, 10],
            "episode_days": 1,
            "players": [
                {
                    "agent_id": "A",
                    "daily_salary": 100,
                    "water_requirement": 5,
                }
            ],
        },
        "policy": {
            "final_reasoning": "Bid enough to win.",
            "final_code": "def get_bid(*args): return 10",
        },
        "trajectory": {
            "evidence_summary": {
                "reconstruction_valid": True,
                "active_decision_days": 1,
            },
            "daily_evidence": [
                {
                    "day": 1,
                    "budget_before_bid": 100,
                    "bid": 10,
                    "won_water": True,
                    "actual_payment": 10,
                }
            ],
        },
    }


def _valid_response():
    return json.dumps(
        {
            "strategy_quality_score": 4,
            "survival_risk_management_score": 4,
            "budget_efficiency_score": 4,
            "opponent_supply_adaptation_score": 3,
            "temporal_planning_score": 3,
            "reasoning_code_trace_consistency_score": 4,
            "implementation_quality_score": 4,
            "primary_failure_mode": "none",
            "failure_labels": ["none"],
            "failure_annotations": [],
            "strengths": ["Valid policy."],
            "weaknesses": [],
            "evidence_summary": "The single observed bid won.",
            "short_diagnosis": "No material failure in this item.",
            "judge_confidence": 4,
        }
    )


def _table_module():
    module = types.ModuleType("judge_table_plot")
    module.generate_judge_tables = lambda aggregation, output_dir: None
    return module


class JudgePipelineCheckpointTests(unittest.TestCase):
    def test_retries_then_checkpoints_success_and_skips_it_on_rerun(self):
        class RetryBackend:
            calls = 0

            def __init__(self, **kwargs):
                pass

            def generate(self, prompt):
                type(self).calls += 1
                if type(self).calls < 3:
                    raise RuntimeError("temporary failure")
                return _valid_response()

        backend_module = types.ModuleType("judge_backend")
        backend_module.JudgeBackend = RetryBackend

        with tempfile.TemporaryDirectory() as output_dir:
            with (
                patch(
                    "judge_core.scan_judge_items",
                    return_value=[_judge_item()],
                ),
                patch.dict(
                    sys.modules,
                    {
                        "judge_backend": backend_module,
                        "judge_table_plot": _table_module(),
                    },
                ),
                redirect_stdout(io.StringIO()),
            ):
                result = run_judge_pipeline(
                    log_dir="unused",
                    batches=["batch"],
                    condition_labels=["condition"],
                    judge_backend="mock",
                    judge_model="mock-model",
                    judge_temperature=0.0,
                    output_dir=output_dir,
                    max_attempts=3,
                    retry_base_seconds=0.0,
                )
                rerun = run_judge_pipeline(
                    log_dir="unused",
                    batches=["batch"],
                    condition_labels=["condition"],
                    judge_backend="mock",
                    judge_model="mock-model",
                    judge_temperature=0.0,
                    output_dir=output_dir,
                    max_attempts=3,
                    retry_base_seconds=0.0,
                )

            self.assertEqual(RetryBackend.calls, 3)
            self.assertEqual(result["new_judged_items"], 1)
            self.assertEqual(result["failed_items"], 0)
            self.assertEqual(result["current_range_coverage_rate"], 1.0)
            self.assertEqual(rerun["planned_api_calls"], 0)
            self.assertEqual(rerun["skipped_existing_items"], 1)
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        output_dir,
                        "judge_run_report.json",
                    )
                )
            )

            records_path = os.path.join(
                output_dir,
                "judge_records.jsonl",
            )
            with open(records_path, "r", encoding="utf-8") as handle:
                records = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(len(records), 1)
            self.assertTrue(records[0]["judge_response_format_valid"])

    def test_permanent_failure_is_logged_and_does_not_create_success(self):
        class FailingBackend:
            calls = 0

            def __init__(self, **kwargs):
                pass

            def generate(self, prompt):
                type(self).calls += 1
                raise RuntimeError("permanent failure")

        backend_module = types.ModuleType("judge_backend")
        backend_module.JudgeBackend = FailingBackend

        with tempfile.TemporaryDirectory() as output_dir:
            with (
                patch(
                    "judge_core.scan_judge_items",
                    return_value=[_judge_item()],
                ),
                patch.dict(
                    sys.modules,
                    {
                        "judge_backend": backend_module,
                        "judge_table_plot": _table_module(),
                    },
                ),
                redirect_stdout(io.StringIO()),
            ):
                result = run_judge_pipeline(
                    log_dir="unused",
                    batches=["batch"],
                    condition_labels=["condition"],
                    judge_backend="mock",
                    judge_model="mock-model",
                    judge_temperature=0.0,
                    output_dir=output_dir,
                    max_attempts=2,
                    retry_base_seconds=0.0,
                )

            self.assertEqual(FailingBackend.calls, 2)
            self.assertEqual(result["new_judged_items"], 0)
            self.assertEqual(result["failed_items"], 1)
            self.assertEqual(result["total_judged_items"], 0)

            errors_path = os.path.join(
                output_dir,
                "judge_errors.jsonl",
            )
            with open(errors_path, "r", encoding="utf-8") as handle:
                errors = [json.loads(line) for line in handle if line.strip()]
            self.assertEqual(len(errors), 1)
            self.assertEqual(errors[0]["attempts"], 2)
            self.assertEqual(errors[0]["error_type"], "RuntimeError")


if __name__ == "__main__":
    unittest.main()
