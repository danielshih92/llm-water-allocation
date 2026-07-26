#!/usr/bin/env python3
"""Plot model-level LLM-minus-reference gaps across meta-rounds."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
DEFAULT_INPUT = (
    PROJECT_ROOT / "compare_result" / "non-llm-reference"
    / "summary_by_model_round.csv"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "compare_result" / "non-llm-reference"
    / "model_reference_gap"
)

MODEL_ORDER = [
    "gemini-3.5-flash",
    "claude-sonnet-5",
    "gpt-5.4",
    "deepseek-v4-flash",
    "gpt-5.4-nano",
]
MODEL_LABELS = {
    "gemini-3.5-flash": "Gemini 3.5 Flash",
    "claude-sonnet-5": "Claude Sonnet 5",
    "gpt-5.4": "GPT-5.4",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "gpt-5.4-nano": "GPT-5.4 Nano",
}
MODEL_STYLES = {
    "gemini-3.5-flash": ("#0072B2", "o"),
    "claude-sonnet-5": ("#D55E00", "s"),
    "gpt-5.4": ("#009E73", "^"),
    "deepseek-v4-flash": ("#CC79A7", "D"),
    "gpt-5.4-nano": ("#E69F00", "P"),
}
FEEDBACK_ORDER = ["OF", "OPF"]


def read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "feedback",
        "meta_round",
        "model",
        "wac_difference",
        "wac_difference_ci_low",
        "wac_difference_ci_high",
        "mortality_difference",
        "mortality_difference_ci_low",
        "mortality_difference_ci_high",
    }
    missing = required.difference(rows[0] if rows else {})
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    return rows


def metric_limits(rows: List[Dict[str, str]], prefix: str) -> tuple[float, float]:
    values = [0.0]
    for row in rows:
        values.extend([
            float(row[f"{prefix}_ci_low"]),
            float(row[f"{prefix}_ci_high"]),
        ])
    lower, upper = min(values), max(values)
    padding = max(1.0, 0.08 * (upper - lower))
    return lower - padding, upper + padding


def plot(rows: List[Dict[str, str]], output_stem: Path) -> None:
    lookup = {
        (row["feedback"], row["model"], int(row["meta_round"])): row
        for row in rows
    }
    expected = {
        (feedback, model, meta_round)
        for feedback in FEEDBACK_ORDER
        for model in MODEL_ORDER
        for meta_round in (1, 2, 3)
    }
    missing = expected.difference(lookup)
    if missing:
        raise ValueError(f"missing feedback/model/round rows: {sorted(missing)}")

    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
    })
    figure, axes = plt.subplots(
        2, 2, figsize=(10.2, 6.9), sharex=True,
        gridspec_kw={"hspace": 0.15, "wspace": 0.18},
    )
    metrics = [
        ("wac_difference", "LLM $-$ heuristic WACScore"),
        ("mortality_difference", "LLM $-$ heuristic mortality (pp)"),
    ]
    limits = {
        prefix: metric_limits(rows, prefix)
        for prefix, _ in metrics
    }

    legend_handles = []
    for column, feedback in enumerate(FEEDBACK_ORDER):
        axes[0, column].set_title(
            "Outcome Feedback (OF)"
            if feedback == "OF"
            else "Outcome-and-Policy Feedback (OPF)"
        )
        for row_index, (prefix, ylabel) in enumerate(metrics):
            axis = axes[row_index, column]
            axis.axhline(0, color="#4D4D4D", linewidth=1.0, linestyle="--", zorder=1)
            axis.grid(axis="y", color="#D9D9D9", linewidth=0.6, alpha=0.75)
            axis.set_axisbelow(True)
            axis.set_xlim(0.8, 3.2)
            axis.set_ylim(*limits[prefix])
            axis.spines["top"].set_visible(False)
            axis.spines["right"].set_visible(False)
            if column == 0:
                axis.set_ylabel(ylabel)
            for model in MODEL_ORDER:
                model_rows = [lookup[(feedback, model, round_id)] for round_id in (1, 2, 3)]
                points = [float(row[prefix]) for row in model_rows]
                lows = [float(row[f"{prefix}_ci_low"]) for row in model_rows]
                highs = [float(row[f"{prefix}_ci_high"]) for row in model_rows]
                color, marker = MODEL_STYLES[model]
                handle = axis.errorbar(
                    [1, 2, 3],
                    points,
                    yerr=[
                        [point - low for point, low in zip(points, lows)],
                        [high - point for point, high in zip(points, highs)],
                    ],
                    color=color,
                    marker=marker,
                    markersize=4.6,
                    linewidth=1.4,
                    capsize=2.2,
                    capthick=0.9,
                    label=MODEL_LABELS[model],
                    zorder=2,
                )
                if row_index == 0 and column == 0:
                    legend_handles.append(handle)
            if row_index == 1:
                axis.set_xticks([1, 2, 3], ["MR1", "MR2", "MR3"])
                axis.set_xlabel("Meta-round")

    figure.legend(
        legend_handles,
        [MODEL_LABELS[model] for model in MODEL_ORDER],
        loc="lower center",
        ncol=5,
        frameon=False,
        bbox_to_anchor=(0.5, -0.005),
        columnspacing=1.35,
        handlelength=1.8,
    )
    figure.subplots_adjust(bottom=0.13, left=0.09, right=0.985, top=0.94)
    output_stem.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    figure.savefig(output_stem.with_suffix(".pdf"), bbox_inches="tight")
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-stem", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plot(read_rows(args.input), args.output_stem)
    print(f"Wrote {args.output_stem.with_suffix('.png')}")
    print(f"Wrote {args.output_stem.with_suffix('.pdf')}")


if __name__ == "__main__":
    main()
