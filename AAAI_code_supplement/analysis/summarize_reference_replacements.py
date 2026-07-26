#!/usr/bin/env python3
"""Rebuild non-LLM reference summaries from packaged paired replacements."""

import argparse
import csv
from pathlib import Path

import non_llm_reference as reference


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = (
    ROOT
    / "data"
    / "paper_intermediates"
    / "non_llm_reference"
    / "paired_replacements.csv"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "non_llm_reference"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    by_round = reference.grouped_summaries(
        rows, ("feedback", "meta_round"), args.bootstrap_replicates
    )
    by_model = reference.grouped_summaries(
        rows, ("feedback", "meta_round", "model"), args.bootstrap_replicates
    )
    by_role = reference.grouped_summaries(
        rows, ("feedback", "meta_round", "role"), args.bootstrap_replicates
    )
    reference.write_csv(args.output_dir / "paired_replacements.csv", rows)
    reference.write_csv(args.output_dir / "summary_by_round.csv", by_round)
    reference.write_csv(args.output_dir / "summary_by_model_round.csv", by_model)
    reference.write_csv(args.output_dir / "summary_by_role_round.csv", by_role)
    reference.write_json(args.output_dir / "summary_by_round.json", by_round)
    reference.write_json(args.output_dir / "summary_by_model_round.json", by_model)
    reference.write_json(args.output_dir / "summary_by_role_round.json", by_role)
    reference.write_paper_outputs(
        args.output_dir, rows, by_round, args.bootstrap_replicates
    )
    reference.write_summary_markdown(
        args.output_dir / "summary.md", by_round, by_model
    )
    print(f"Wrote summaries for {len(rows)} paired replacements to {args.output_dir}")


if __name__ == "__main__":
    main()

