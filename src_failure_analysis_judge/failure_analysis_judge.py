#!/usr/bin/env python3
"""CLI for two-judge, failure-only analysis."""

import argparse
import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src_failure_analysis_judge.pipeline import run_failure_analysis


DEFAULT_LOG_DIR = os.path.join(PROJECT_ROOT, "log")
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "judge_result", "failure_analysis")
DEFAULT_BATCHES = [
    "batch_031_full_code_access_c_med_20days",
    "batch_032_no_opp_info_c_med_20days",
]
DEFAULT_CONDITIONS = ["OPF", "OF"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run two independent LLM judges on WACBench failure mechanisms "
            "and average their categorical votes."
        )
    )
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR)
    parser.add_argument("--batches", nargs="+", default=DEFAULT_BATCHES)
    parser.add_argument("--condition-labels", nargs="+", default=None)
    parser.add_argument(
        "--judge-backends",
        nargs=2,
        required=True,
        metavar=("BACKEND_1", "BACKEND_2"),
    )
    parser.add_argument(
        "--judge-models",
        nargs=2,
        required=True,
        metavar=("MODEL_1", "MODEL_2"),
    )
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument(
        "--judge-run-order",
        nargs=2,
        type=int,
        choices=(1, 2),
        default=[1, 2],
        metavar=("FIRST_JUDGE", "SECOND_JUDGE"),
        help=(
            "Execution order for the two configured judges. For example, "
            "'--judge-run-order 2 1' runs judge 2 first without changing "
            "judge identity or invalidating checkpoints."
        ),
    )
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--exp-start", type=int, default=None)
    parser.add_argument("--exp-end", type=int, default=None)
    parser.add_argument(
        "--max-items",
        type=int,
        default=0,
        help="Maximum new paired items selected this run; 0 means all.",
    )
    parser.add_argument(
        "--death-only",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Judge primary failure modes only for death cases (default: true).",
    )
    parser.add_argument(
        "--blind-model-names",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-base-seconds", type=float, default=1.0)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Compatibility flag; successful records are always resumed.",
    )
    args = parser.parse_args()

    if args.condition_labels is None:
        args.condition_labels = (
            list(DEFAULT_CONDITIONS)
            if args.batches == DEFAULT_BATCHES
            else list(args.batches)
        )
    if len(args.batches) != len(args.condition_labels):
        raise SystemExit("--condition-labels length must equal --batches length")
    if args.exp_start is not None and args.exp_start <= 0:
        raise SystemExit("--exp-start must be positive")
    if args.exp_end is not None and args.exp_end <= 0:
        raise SystemExit("--exp-end must be positive")
    if (
        args.exp_start is not None
        and args.exp_end is not None
        and args.exp_start > args.exp_end
    ):
        raise SystemExit("--exp-start must be <= --exp-end")
    if args.max_items < 0:
        raise SystemExit("--max-items cannot be negative")
    if args.max_attempts <= 0:
        raise SystemExit("--max-attempts must be positive")
    if sorted(args.judge_run_order) != [1, 2]:
        raise SystemExit("--judge-run-order must contain judge indices 1 and 2 once each")

    specs = [
        {"backend": backend, "model": model}
        for backend, model in zip(args.judge_backends, args.judge_models)
    ]
    if specs[0] == specs[1] and args.judge_backends != ["mock", "mock"]:
        raise SystemExit(
            "The two judges must use different backend/model specifications."
        )

    report = run_failure_analysis(
        log_dir=os.path.abspath(args.log_dir),
        batches=list(args.batches),
        condition_labels=list(args.condition_labels),
        judge_specs=specs,
        output_dir=os.path.abspath(args.output_dir),
        temperature=args.judge_temperature,
        blind_model_names=args.blind_model_names,
        death_only=args.death_only,
        exp_start=args.exp_start,
        exp_end=args.exp_end,
        max_items=args.max_items,
        max_attempts=args.max_attempts,
        retry_base_seconds=args.retry_base_seconds,
        judge_run_order=args.judge_run_order,
    )
    print("Failure-analysis pipeline complete")
    for key, value in report.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
