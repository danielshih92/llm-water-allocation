import argparse
import os

from judge_core import run_judge_pipeline


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG_DIR = os.path.join(PROJECT_ROOT, "log")
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "judge_result")
DEFAULT_BATCH = "batch_031_full_code_access_c_med_20days"


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline LLM judge pipeline for completed experiment logs.")
    parser.add_argument("--log-dir", type=str, default=DEFAULT_LOG_DIR)
    parser.add_argument("--batches", nargs="+", default=[DEFAULT_BATCH])
    parser.add_argument(
        "--condition-labels",
        nargs="+",
        default=None,
        help="Defaults to the corresponding batch names",
    )
    parser.add_argument("--judge-backend", type=str, default="openai")
    parser.add_argument(
        "--judge-model",
        type=str,
        default=None,
        help="Required for non-mock backends to keep runs reproducible",
    )
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--exp-start", type=int, default=None, help="Inclusive experiment number")
    parser.add_argument("--exp-end", type=int, default=None, help="Inclusive experiment number")
    parser.add_argument("--max-items", type=int, default=0, help="0 means judge all items")
    parser.add_argument("--judge-valid-only", action="store_true", help="Only judge admitted outcome-valid trajectories")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Compatibility flag; successful existing items are always skipped",
    )
    parser.add_argument(
        "--blind-model-names",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Hide evaluated model names from the judge prompt (default: enabled)",
    )

    args = parser.parse_args()

    if args.condition_labels is None:
        args.condition_labels = list(args.batches)
    if len(args.batches) != len(args.condition_labels):
        raise SystemExit("--condition-labels length must equal --batches length")
    if args.judge_backend != "mock" and not args.judge_model:
        raise SystemExit(
            "--judge-model is required for non-mock judge backends"
        )
    if args.exp_start is not None and args.exp_start <= 0:
        raise SystemExit("--exp-start must be a positive integer")
    if args.exp_end is not None and args.exp_end <= 0:
        raise SystemExit("--exp-end must be a positive integer")
    if (
        args.exp_start is not None
        and args.exp_end is not None
        and args.exp_start > args.exp_end
    ):
        raise SystemExit("--exp-start must be less than or equal to --exp-end")

    result = run_judge_pipeline(
        log_dir=args.log_dir,
        batches=args.batches,
        condition_labels=args.condition_labels,
        judge_backend=args.judge_backend,
        judge_model=args.judge_model,
        judge_temperature=args.judge_temperature,
        output_dir=args.output_dir,
        max_items=args.max_items,
        judge_valid_only=args.judge_valid_only,
        resume=args.resume,
        blind_model_names=args.blind_model_names,
        exp_start=args.exp_start,
        exp_end=args.exp_end,
    )

    print("Judge pipeline complete")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
