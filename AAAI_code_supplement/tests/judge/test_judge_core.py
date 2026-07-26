import json
import os
import tempfile
import unittest

from judge_core import (
    _exclusive_output_lock,
    _prepare_run_config,
    run_judge_pipeline,
)


class JudgeRunConfigTests(unittest.TestCase):
    def test_requires_an_explicit_non_mock_judge_model(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with self.assertRaises(ValueError):
                run_judge_pipeline(
                    log_dir="unused",
                    batches=["batch"],
                    condition_labels=["condition"],
                    judge_backend="openai",
                    judge_model=None,
                    judge_temperature=0.0,
                    output_dir=output_dir,
                )

    def test_rejects_a_second_process_using_the_same_output_dir(self):
        with tempfile.TemporaryDirectory() as output_dir:
            with _exclusive_output_lock(output_dir):
                with self.assertRaises(RuntimeError):
                    with _exclusive_output_lock(output_dir):
                        pass

    def test_rejects_mixing_different_judge_protocols(self):
        with tempfile.TemporaryDirectory() as output_dir:
            records_path = os.path.join(
                output_dir,
                "judge_records.jsonl",
            )
            _prepare_run_config(
                output_dir=output_dir,
                records_path=records_path,
                batches=["batch"],
                condition_labels=["condition"],
                judge_backend="openai",
                judge_model="model-a",
                judge_temperature=0.0,
                blind_model_names=True,
                judge_valid_only=False,
            )

            with self.assertRaises(ValueError):
                _prepare_run_config(
                    output_dir=output_dir,
                    records_path=records_path,
                    batches=["batch"],
                    condition_labels=["condition"],
                    judge_backend="openai",
                    judge_model="model-b",
                    judge_temperature=0.0,
                    blind_model_names=True,
                    judge_valid_only=False,
                )

    def test_rejects_legacy_records_without_run_config(self):
        with tempfile.TemporaryDirectory() as output_dir:
            records_path = os.path.join(
                output_dir,
                "judge_records.jsonl",
            )
            with open(records_path, "w", encoding="utf-8") as handle:
                handle.write(
                    json.dumps({"item_id": "legacy-item"}) + "\n"
                )

            with self.assertRaises(ValueError):
                _prepare_run_config(
                    output_dir=output_dir,
                    records_path=records_path,
                    batches=["batch"],
                    condition_labels=["condition"],
                    judge_backend="openai",
                    judge_model="model-a",
                    judge_temperature=0.0,
                    blind_model_names=True,
                    judge_valid_only=False,
                )


if __name__ == "__main__":
    unittest.main()
