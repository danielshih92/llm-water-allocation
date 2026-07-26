#!/usr/bin/env python3
"""Build role-balanced, paper-ready objective outcome summaries."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from adaptation_dynamics import (  # noqa: E402
    CONDITION_ORDER,
    build_stratum_arrays,
    collect_replay_details,
    mean_over_fixed_seeds,
    percentile_interval,
    role_balanced_estimate,
    validate_design,
)
from package_paths import package_relative  # noqa: E402


DEFAULT_REPLAY_DETAILS = (
    PROJECT_ROOT / "data" / "paper_intermediates" / "main_table" / "replay_details.csv"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "objective_outcomes"
DEFAULT_META_ROUNDS = (2, 3)
DISPLAY_MODELS = {
    "gemini-3.5-flash": "Gemini 3.5 Flash",
    "claude-sonnet-5": "Claude Sonnet 5",
    "gpt-5.4": "GPT-5.4",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "gpt-5.4-nano": "GPT-5.4 Nano",
}


def summarize_model(
    arrays_by_condition: Mapping[str, Mapping[str, np.ndarray]],
    experiment_count: int,
    meta_rounds: Sequence[int],
    bootstrap_samples: int,
    bootstrap_seed: int,
    episode_days: int,
) -> List[Dict[str, Any]]:
    """Average fixed seeds and selected rounds before resampling experiments."""
    rng = np.random.default_rng(bootstrap_seed)
    weights = rng.multinomial(
        experiment_count,
        np.full(experiment_count, 1.0 / experiment_count),
        size=bootstrap_samples,
    ).astype(float)
    full_weights = np.ones(experiment_count, dtype=float)
    metric_specs = (
        ("WACScore", "survival_days", 100.0 / episode_days),
        ("Mortality", "mortality", 100.0),
    )

    rows: List[Dict[str, Any]] = []
    distributions: Dict[tuple[str, str], np.ndarray] = {}
    estimates: Dict[tuple[str, str], float] = {}
    for condition in CONDITION_ORDER:
        for metric, source, scale in metric_specs:
            values = arrays_by_condition[condition][source]
            # [round, role-stratum, experiment, seed] -> [role-stratum, experiment]
            seed_averaged = np.stack(
                [mean_over_fixed_seeds(values[index]) for index in range(len(meta_rounds))]
            )
            valid = np.isfinite(seed_averaged)
            counts = np.sum(valid, axis=0)
            totals = np.sum(np.where(valid, seed_averaged, 0.0), axis=0)
            selected_round_average = np.full(counts.shape, np.nan, dtype=float)
            np.divide(totals, counts, out=selected_round_average, where=counts > 0)
            point = float(role_balanced_estimate(selected_round_average, full_weights)[0] * scale)
            boot = role_balanced_estimate(selected_round_average, weights) * scale
            low, high = percentile_interval(boot)
            estimates[(condition, metric)] = point
            distributions[(condition, metric)] = boot
            rows.append(
                {
                    "condition": condition,
                    "metric": metric,
                    "estimate": point,
                    "ci95_low": low,
                    "ci95_high": high,
                    "meta_rounds": "+".join(str(value) for value in meta_rounds),
                    "bootstrap_samples": bootstrap_samples,
                }
            )

    for metric, _, _ in metric_specs:
        point = np.mean([estimates[(condition, metric)] for condition in CONDITION_ORDER])
        boot = np.mean(
            np.stack([distributions[(condition, metric)] for condition in CONDITION_ORDER]),
            axis=0,
        )
        low, high = percentile_interval(boot)
        rows.append(
            {
                "condition": "Avg",
                "metric": metric,
                "estimate": float(point),
                "ci95_low": low,
                "ci95_high": high,
                "meta_rounds": "+".join(str(value) for value in meta_rounds),
                "bootstrap_samples": bootstrap_samples,
            }
        )
    return rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_latex_table(path: Path, rows: Sequence[Mapping[str, Any]], model_order: Sequence[str]) -> None:
    lookup = {
        (str(row["model"]), str(row["condition"]), str(row["metric"])): float(row["estimate"])
        for row in rows
    }
    best_wac = {
        condition: max(lookup[(model, condition, "WACScore")] for model in model_order)
        for condition in (*CONDITION_ORDER, "Avg")
    }
    best_mortality = {
        condition: min(lookup[(model, condition, "Mortality")] for model in model_order)
        for condition in (*CONDITION_ORDER, "Avg")
    }

    def cell(model: str, condition: str, metric: str) -> str:
        value = lookup[(model, condition, metric)]
        best = best_wac[condition] if metric == "WACScore" else best_mortality[condition]
        rendered = f"{value:.2f}"
        return f"\\textbf{{{rendered}}}" if np.isclose(value, best) else rendered

    lines = [
        "% Generated by src/objective_outcomes/analyze_objective_outcomes.py",
        "\\begin{tabular}{lrrr rrr}",
        "    \\toprule",
        "    & \\multicolumn{3}{c}{WACScore $\\uparrow$}",
        "    & \\multicolumn{3}{c}{Mortality (\\%) $\\downarrow$} \\\\",
        "    \\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
        "    Model & OF & OPF & Avg. & OF & OPF & Avg. \\\\",
        "    \\midrule",
    ]
    for model in model_order:
        display = DISPLAY_MODELS.get(model, model)
        lines.append(
            f"    {display} & {cell(model, 'OF', 'WACScore')} & "
            f"{cell(model, 'OPF', 'WACScore')} & {cell(model, 'Avg', 'WACScore')} & "
            f"{cell(model, 'OF', 'Mortality')} & {cell(model, 'OPF', 'Mortality')} & "
            f"{cell(model, 'Avg', 'Mortality')} \\\\" 
        )
    lines.extend(["    \\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex_ci_table(
    path: Path, rows: Sequence[Mapping[str, Any]], model_order: Sequence[str]
) -> None:
    lookup = {
        (str(row["model"]), str(row["condition"]), str(row["metric"])): row
        for row in rows
    }
    lines = [
        "% Generated by src/objective_outcomes/analyze_objective_outcomes.py",
        "\\begin{tabular}{llrr}",
        "    \\toprule",
        "    Model & Feedback & WACScore (95\\% CI) & Mortality (95\\% CI) \\\\",
        "    \\midrule",
    ]
    for model in model_order:
        display = DISPLAY_MODELS.get(model, model)
        for index, condition in enumerate(CONDITION_ORDER):
            wac = lookup[(model, condition, "WACScore")]
            mortality = lookup[(model, condition, "Mortality")]
            label = display if index == 0 else ""
            lines.append(
                f"    {label} & {condition} & "
                f"{wac['estimate']:.2f} [{wac['ci95_low']:.2f}, {wac['ci95_high']:.2f}] & "
                f"{mortality['estimate']:.2f} [{mortality['ci95_low']:.2f}, "
                f"{mortality['ci95_high']:.2f}] \\\\"
            )
        if model != model_order[-1]:
            lines.append("    \\addlinespace")
    lines.extend(["    \\bottomrule", "\\end{tabular}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_summary(path: Path, rows: Sequence[Mapping[str, Any]], model_order: Sequence[str]) -> None:
    lookup = {
        (str(row["model"]), str(row["condition"]), str(row["metric"])): row
        for row in rows
    }
    lines = [
        "# Objective decision performance",
        "",
        "Policies from MR2 and MR3 are averaged, after averaging the five fixed supply seeds",
        "within each matched experiment. Estimates are macro-averaged over roles.",
        "Raw OF/OPF levels are descriptive and are not the baseline-adjusted policy-access effect.",
        "",
        "| Model | Feedback | WACScore (95% CI) | Mortality % (95% CI) |",
        "| --- | --- | ---: | ---: |",
    ]
    for model in model_order:
        for condition in (*CONDITION_ORDER, "Avg"):
            wac = lookup[(model, condition, "WACScore")]
            mortality = lookup[(model, condition, "Mortality")]
            lines.append(
                f"| {DISPLAY_MODELS.get(model, model)} | {condition} | "
                f"{wac['estimate']:.2f} [{wac['ci95_low']:.2f}, {wac['ci95_high']:.2f}] | "
                f"{mortality['estimate']:.2f} [{mortality['ci95_low']:.2f}, "
                f"{mortality['ci95_high']:.2f}] |"
            )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-details", type=Path, default=DEFAULT_REPLAY_DETAILS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--meta-rounds", nargs="+", type=int, default=list(DEFAULT_META_ROUNDS))
    parser.add_argument("--episode-days", type=int, default=20)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    args = parser.parse_args()
    if not args.meta_rounds or sorted(set(args.meta_rounds)) != args.meta_rounds:
        parser.error("--meta-rounds must be unique, increasing integers")
    if args.episode_days <= 0:
        parser.error("--episode-days must be positive")
    if args.bootstrap_samples < 100:
        parser.error("--bootstrap-samples must be at least 100")
    return args


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows_by_condition = collect_replay_details(args.replay_details.resolve(), args.meta_rounds)
    experiments, roles, models, seeds = validate_design(rows_by_condition, args.meta_rounds)

    all_rows: List[Dict[str, Any]] = []
    for model in models:
        arrays = {
            condition: build_stratum_arrays(
                [row for row in rows_by_condition[condition] if row.model == model],
                experiments,
                roles,
                [model],
                args.meta_rounds,
                seeds,
            )
            for condition in CONDITION_ORDER
        }
        all_rows.extend(
            {"model": model, **row}
            for row in summarize_model(
                arrays,
                len(experiments),
                args.meta_rounds,
                args.bootstrap_samples,
                args.bootstrap_seed,
                args.episode_days,
            )
        )

    model_order = sorted(
        models,
        key=lambda model: -next(
            float(row["estimate"])
            for row in all_rows
            if row["model"] == model and row["condition"] == "Avg" and row["metric"] == "WACScore"
        ),
    )
    rounded = [
        {key: round(value, 6) if isinstance(value, float) else value for key, value in row.items()}
        for row in all_rows
    ]
    write_csv(output_dir / "objective_performance.csv", rounded)
    write_latex_table(output_dir / "objective_performance_table.tex", rounded, model_order)
    write_latex_ci_table(output_dir / "objective_performance_ci_table.tex", rounded, model_order)
    write_summary(output_dir / "objective_performance_summary.md", rounded, model_order)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input": package_relative(args.replay_details),
        "output_dir": package_relative(output_dir),
        "experiments": len(experiments),
        "meta_rounds": args.meta_rounds,
        "supply_seeds": seeds,
        "roles": roles,
        "models": models,
        "aggregation": "mean over fixed seeds and selected revised-policy rounds within experiment, then macro mean over roles",
        "bootstrap": {
            "method": "matched experiment-cluster percentile bootstrap",
            "samples": args.bootstrap_samples,
            "seed": args.bootstrap_seed,
            "confidence_level": 0.95,
        },
        "interpretation": "OF and OPF levels are descriptive; baseline-adjusted effects are reported by adaptation_dynamics",
        "files": [
            "objective_performance.csv",
            "objective_performance_table.tex",
            "objective_performance_ci_table.tex",
            "objective_performance_summary.md",
        ],
    }
    (output_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote objective outcomes for {len(experiments)} matched experiments to {output_dir}")


if __name__ == "__main__":
    main()
