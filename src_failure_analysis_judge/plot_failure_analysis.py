#!/usr/bin/env python3
"""Create compact paper figures from the two-judge failure analysis."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/wacbench-matplotlib")
import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_INPUT_DIR = (
    PROJECT_ROOT / "judge_result" / "failure_analysis_full_gpt_deepseek_v3"
)
DEFAULT_LOG_DIR = PROJECT_ROOT / "log"
EXP_PATTERN = re.compile(r"^exp_(\d+)$")

MODEL_ORDER = (
    "gemini-3.5-flash",
    "claude-sonnet-5",
    "gpt-5.4",
    "deepseek-v4-flash",
    "gpt-5.4-nano",
)
MODEL_LABELS = {
    "gemini-3.5-flash": "Gemini 3.5 Flash",
    "claude-sonnet-5": "Claude Sonnet 5",
    "gpt-5.4": "GPT-5.4",
    "deepseek-v4-flash": "DeepSeek V4 Flash",
    "gpt-5.4-nano": "GPT-5.4 Nano",
}

POLICY_FAILURE_MODES = (
    "fatal_undercommitment",
    "winners_curse_overpayment",
    "emergency_response_failure",
    "competitive_threshold_miscalibration",
)
PRIMARY_FACTORS = ("resource_disadvantaged_role",) + POLICY_FAILURE_MODES
FACTOR_LABELS = {
    "resource_disadvantaged_role": "Disadv.\nrole",
    "fatal_undercommitment": "Under-\ncommit.",
    "winners_curse_overpayment": "Winner's\ncurse",
    "emergency_response_failure": "Emerg.\nresp.",
    "competitive_threshold_miscalibration": "Thresh.\nerror",
}
ATTRIBUTABLE_STATUSES = {
    "dominant_policy_failure",
    "mixed_policy_and_context",
}

MORTALITY_COLOR = "#5B7FA3"
MISMATCH_COLORS = ("#D95F5F", "#4C78A8")


@dataclass(frozen=True)
class OutcomeRow:
    experiment_id: str
    model: str
    dead: float
    disadvantaged_role: float


def disadvantaged_role_ids(environment: Mapping[str, Any]) -> set[str]:
    """Identify structurally disadvantaged roles from simulator profiles.

    A role is exposed when its salary is below the within-game median and its
    water requirement is above the within-game median. This is a deterministic
    context flag, not a causal failure attribution.
    """
    players = environment.get("players", [])
    profiles = [row for row in players if isinstance(row, dict)]
    salaries = sorted(
        value
        for value in (safe_float(row.get("daily_salary")) for row in profiles)
        if value is not None
    )
    requirements = sorted(
        value
        for value in (safe_float(row.get("water_requirement")) for row in profiles)
        if value is not None
    )
    if not salaries or not requirements:
        return set()
    median_salary = salaries[len(salaries) // 2]
    median_requirement = requirements[len(requirements) // 2]
    return {
        str(row.get("agent_id"))
        for row in profiles
        if (
            safe_float(row.get("daily_salary")) is not None
            and safe_float(row.get("water_requirement")) is not None
            and float(row["daily_salary"]) < median_salary
            and float(row["water_requirement"]) > median_requirement
        )
    }


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl_by_id(path: Path) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    if not path.is_file():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and row.get("item_id"):
                rows[str(row["item_id"])] = row
    return rows


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def experiment_number(path: Path) -> int:
    match = EXP_PATTERN.fullmatch(path.name)
    return int(match.group(1)) if match else 10**9


def in_range(exp_id: str, start: int | None, end: int | None) -> bool:
    match = EXP_PATTERN.fullmatch(exp_id)
    if match is None:
        return False
    number = int(match.group(1))
    return (start is None or number >= start) and (end is None or number <= end)


def collect_outcomes(
    log_dir: Path,
    batch_names: Sequence[str],
    exp_start: int | None,
    exp_end: int | None,
) -> List[OutcomeRow]:
    """Read the generation trajectories used to define judged death cases."""
    rows: List[OutcomeRow] = []
    for batch_name in batch_names:
        batch_dir = log_dir / batch_name
        if not batch_dir.is_dir():
            raise FileNotFoundError(f"Batch directory not found: {batch_dir}")
        exp_dirs = sorted(
            (
                path
                for path in batch_dir.iterdir()
                if path.is_dir()
                and EXP_PATTERN.fullmatch(path.name)
                and in_range(path.name, exp_start, exp_end)
            ),
            key=experiment_number,
        )
        if not exp_dirs:
            raise ValueError(f"No experiments found in requested range: {batch_dir}")

        for exp_dir in exp_dirs:
            config_path = exp_dir / "backend_config.json"
            if not config_path.is_file():
                raise FileNotFoundError(f"Missing backend config: {config_path}")
            config = load_json(config_path)
            if not isinstance(config, dict):
                raise ValueError(f"Invalid backend config: {config_path}")

            meta_paths = sorted(exp_dir.glob("meta_round_*.json"))
            if not meta_paths:
                raise ValueError(f"No meta-round files found: {exp_dir}")
            for meta_path in meta_paths:
                payload = load_json(meta_path)
                if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
                    raise ValueError(f"Invalid meta-round payload: {meta_path}")
                record = payload[0]
                round_valid = bool(record.get("outcome_valid", 0))
                environment = record.get("environment", {})
                disadvantaged_ids = (
                    disadvantaged_role_ids(environment)
                    if isinstance(environment, dict)
                    else set()
                )
                agents = record.get("agents")
                if not isinstance(agents, list):
                    raise ValueError(f"Missing agents list: {meta_path}")
                for agent in agents:
                    if not isinstance(agent, dict):
                        continue
                    agent_id = str(agent.get("agent_id", ""))
                    spec = config.get(agent_id, {})
                    model = str(spec.get("model", "")) if isinstance(spec, dict) else ""
                    metrics = agent.get("metrics")
                    admitted = bool(agent.get("admitted", 0))
                    agent_valid = bool(agent.get("outcome_valid", round_valid))
                    final_hp = (
                        safe_float(metrics.get("final_hp"))
                        if isinstance(metrics, dict)
                        else None
                    )
                    if not (admitted and round_valid and agent_valid and model and final_hp is not None):
                        continue
                    rows.append(
                        OutcomeRow(
                            experiment_id=exp_dir.name,
                            model=model,
                            dead=float(final_hp <= 0.0),
                            disadvantaged_role=float(agent_id in disadvantaged_ids),
                        )
                    )
    return rows


def load_paired_rows(path: Path, exp_start: int | None, exp_end: int | None) -> List[Dict[str, Any]]:
    rows = load_jsonl_by_id(path)
    return [
        row
        for row in rows.values()
        if in_range(str(row.get("experiment_id", "")), exp_start, exp_end)
    ]


def ordered_models(outcomes: Sequence[OutcomeRow], paired: Sequence[Mapping[str, Any]]) -> List[str]:
    observed = {row.model for row in outcomes}
    observed.update(str(row.get("model_name", "")) for row in paired)
    observed.discard("")
    return [model for model in MODEL_ORDER if model in observed] + sorted(
        observed - set(MODEL_ORDER)
    )


def model_label(model: str) -> str:
    return MODEL_LABELS.get(model, model)


def build_cluster_arrays(
    outcomes: Sequence[OutcomeRow],
    paired: Sequence[Mapping[str, Any]],
    models: Sequence[str],
) -> Tuple[List[str], np.ndarray, np.ndarray]:
    clusters = sorted(
        {row.experiment_id for row in outcomes}.union(
            str(row.get("experiment_id")) for row in paired
        ),
        key=lambda value: int(value.split("_")[-1]),
    )
    cluster_index = {value: index for index, value in enumerate(clusters)}
    model_index = {value: index for index, value in enumerate(models)}

    # Outcome features: total policy-rounds, deaths, disadvantaged-role deaths.
    outcome_arrays = np.zeros((len(clusters), len(models), 3), dtype=float)
    for row in outcomes:
        if row.model not in model_index:
            continue
        cell = outcome_arrays[cluster_index[row.experiment_id], model_index[row.model]]
        cell[0] += 1.0
        cell[1] += row.dead
        cell[2] += row.dead * row.disadvantaged_role

    # Judge features: paired n, attributable vote, four primary-mechanism
    # scores, reasoning-policy mismatch, and policy-trajectory mismatch.
    judge_arrays = np.zeros(
        (len(clusters), len(models), 2 + len(POLICY_FAILURE_MODES) + 2),
        dtype=float,
    )
    for row in paired:
        model = str(row.get("model_name", ""))
        exp_id = str(row.get("experiment_id", ""))
        if model not in model_index or exp_id not in cluster_index:
            continue
        cell = judge_arrays[cluster_index[exp_id], model_index[model]]
        cell[0] += 1.0
        statuses = (
            str(row.get("judge_1_attribution_status", "")),
            str(row.get("judge_2_attribution_status", "")),
        )
        cell[1] += sum(status in ATTRIBUTABLE_STATUSES for status in statuses) / 2.0
        scores = row.get("averaged_primary_vote", {})
        if isinstance(scores, dict):
            for offset, mode in enumerate(POLICY_FAILURE_MODES, start=2):
                cell[offset] += float(scores.get(mode, 0.0))
        cell[2 + len(POLICY_FAILURE_MODES)] += float(
            row.get("reasoning_policy_mismatch_score", 0.0)
        )
        cell[3 + len(POLICY_FAILURE_MODES)] += float(
            row.get("policy_trajectory_mismatch_score", 0.0)
        )
    return clusters, outcome_arrays, judge_arrays


def ratio(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    return np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan, dtype=float),
        where=denominator > 0,
    )


def percentile_interval(values: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    return np.nanpercentile(values, 2.5, axis=0), np.nanpercentile(values, 97.5, axis=0)


def summarize(
    outcome_arrays: np.ndarray,
    judge_arrays: np.ndarray,
    bootstrap_samples: int,
    bootstrap_seed: int,
) -> Dict[str, np.ndarray]:
    rng = np.random.default_rng(bootstrap_seed)
    cluster_count = outcome_arrays.shape[0]
    samples = rng.integers(0, cluster_count, size=(bootstrap_samples, cluster_count))

    outcome_total = outcome_arrays.sum(axis=0)
    judge_total = judge_arrays.sum(axis=0)
    mortality = 100.0 * ratio(outcome_total[:, 1], outcome_total[:, 0])
    role_exposure_rate = 100.0 * ratio(outcome_total[:, 2], outcome_total[:, 1])
    policy_failure_rates = 100.0 * ratio(
        judge_total[:, 2 : 2 + len(POLICY_FAILURE_MODES)],
        judge_total[:, 0, None],
    )
    factor_rates = np.column_stack((role_exposure_rate, policy_failure_rates))
    mismatch_rates = 100.0 * ratio(
        judge_total[
            :,
            2 + len(POLICY_FAILURE_MODES) : 4 + len(POLICY_FAILURE_MODES),
        ],
        judge_total[:, 0, None],
    )

    boot_outcomes = outcome_arrays[samples].sum(axis=1)
    boot_judges = judge_arrays[samples].sum(axis=1)
    boot_mortality = 100.0 * ratio(boot_outcomes[:, :, 1], boot_outcomes[:, :, 0])
    boot_role_exposure = 100.0 * ratio(
        boot_outcomes[:, :, 2], boot_outcomes[:, :, 1]
    )
    boot_policy_failure = 100.0 * ratio(
        boot_judges[:, :, 2 : 2 + len(POLICY_FAILURE_MODES)],
        boot_judges[:, :, 0, None],
    )
    boot_factors = np.concatenate(
        (boot_role_exposure[:, :, None], boot_policy_failure), axis=2
    )
    boot_mismatch = 100.0 * ratio(
        boot_judges[
            :,
            :,
            2 + len(POLICY_FAILURE_MODES) : 4 + len(POLICY_FAILURE_MODES),
        ],
        boot_judges[:, :, 0, None],
    )

    mortality_low, mortality_high = percentile_interval(boot_mortality)
    factor_low, factor_high = percentile_interval(boot_factors)
    mismatch_low, mismatch_high = percentile_interval(boot_mismatch)
    return {
        "outcome_total": outcome_total,
        "judge_total": judge_total,
        "mortality": mortality,
        "mortality_low": mortality_low,
        "mortality_high": mortality_high,
        "factor_rates": factor_rates,
        "factor_low": factor_low,
        "factor_high": factor_high,
        "mismatch_rates": mismatch_rates,
        "mismatch_low": mismatch_low,
        "mismatch_high": mismatch_high,
    }


def configure_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.size": 7.2,
            "axes.titlesize": 8.0,
            "axes.labelsize": 7.2,
            "xtick.labelsize": 6.6,
            "ytick.labelsize": 6.8,
            "legend.fontsize": 6.7,
            "axes.linewidth": 0.65,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
        }
    )


def configure_numeric_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#D9D9D9", linewidth=0.45, alpha=0.8)
    ax.set_axisbelow(True)


def draw_mortality_panel(
    ax: plt.Axes,
    models: Sequence[str],
    summary: Mapping[str, np.ndarray],
    show_model_labels: bool,
    title: str,
) -> None:
    y = np.arange(len(models))
    estimates = summary["mortality"]
    low = summary["mortality_low"]
    high = summary["mortality_high"]
    deaths = summary["outcome_total"][:, 1].astype(int)
    bars = ax.barh(y, estimates, height=0.58, color=MORTALITY_COLOR, alpha=0.9)
    ax.errorbar(
        estimates,
        y,
        xerr=np.vstack((estimates - low, high - estimates)),
        fmt="none",
        ecolor="#2F3E4E",
        elinewidth=0.7,
        capsize=1.7,
        capthick=0.7,
        zorder=3,
    )
    max_value = max(75.0, float(np.nanmax(high)) + 12.0)
    ax.set_xlim(0.0, max_value)
    for index, (bar, value, count) in enumerate(zip(bars, estimates, deaths)):
        label_x = min(high[index] + 0.8, max_value - 0.5)
        ax.text(
            label_x,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}% ({count})",
            va="center",
            ha="left" if label_x < max_value - 0.5 else "right",
            fontsize=6.2,
        )
    ax.set_yticks(y)
    ax.set_yticklabels([model_label(model) for model in models] if show_model_labels else [])
    ax.invert_yaxis()
    ax.set_xlabel("Mortality (%)")
    ax.set_title(title, loc="left", fontweight="bold", pad=3)
    configure_numeric_axis(ax)


def draw_primary_failure_heatmap(
    ax: plt.Axes,
    models: Sequence[str],
    summary: Mapping[str, np.ndarray],
    show_model_labels: bool,
    title: str,
) -> None:
    values = summary["factor_rates"]
    image = ax.imshow(values, cmap="YlGnBu", vmin=0.0, vmax=80.0, aspect="auto")
    del image  # Values are printed in every cell; a colorbar would add redundant width.
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            value = values[row, column]
            color = "white" if value >= 48.0 else "#1F1F1F"
            ax.text(
                column,
                row,
                f"{value:.0f}",
                ha="center",
                va="center",
                fontsize=6.2,
                color=color,
            )
    ax.set_xticks(np.arange(len(PRIMARY_FACTORS)))
    ax.set_xticklabels([FACTOR_LABELS[mode] for mode in PRIMARY_FACTORS])
    ax.set_yticks(np.arange(len(models)))
    ax.set_yticklabels([model_label(model) for model in models] if show_model_labels else [])
    ax.tick_params(length=0)
    ax.set_title(title, loc="left", fontweight="bold", pad=3)
    # Separate deterministic role exposure from judge-annotated mechanisms.
    ax.axvline(0.5, color="white", linewidth=1.5)
    ax.axvline(0.5, color="#555555", linewidth=0.45)
    for spine in ax.spines.values():
        spine.set_linewidth(0.55)
        spine.set_color("#777777")


def draw_mismatch_panel(
    ax: plt.Axes,
    models: Sequence[str],
    summary: Mapping[str, np.ndarray],
    show_model_labels: bool,
    title: str,
) -> None:
    y = np.arange(len(models))
    offsets = (-0.15, 0.15)
    labels = ("Reasoning-policy", "Policy-trajectory")
    for index, (offset, label, color) in enumerate(zip(offsets, labels, MISMATCH_COLORS)):
        estimates = summary["mismatch_rates"][:, index]
        low = summary["mismatch_low"][:, index]
        high = summary["mismatch_high"][:, index]
        ax.barh(y + offset, estimates, height=0.25, color=color, alpha=0.9, label=label)
        ax.errorbar(
            estimates,
            y + offset,
            xerr=np.vstack((estimates - low, high - estimates)),
            fmt="none",
            ecolor="#333333",
            elinewidth=0.65,
            capsize=1.4,
            capthick=0.65,
            zorder=3,
        )
    ax.set_yticks(y)
    ax.set_yticklabels([model_label(model) for model in models] if show_model_labels else [])
    ax.invert_yaxis()
    ax.set_xlim(0.0, max(20.0, float(np.nanmax(summary["mismatch_high"])) + 3.0))
    ax.set_xlabel("Mismatch rate (%)")
    # Keep the shared legend immediately below the title. A larger title pad
    # reserves a separate line without increasing the plot's overall width.
    ax.set_title(title, loc="left", fontweight="bold", pad=15)
    ax.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=2,
        frameon=False,
        handlelength=1.1,
        columnspacing=0.8,
        borderaxespad=0.0,
    )
    configure_numeric_axis(ax)


def save_figure(fig: plt.Figure, base_path: Path, dpi: int) -> None:
    for suffix in (".png", ".pdf"):
        fig.savefig(
            base_path.with_suffix(suffix),
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.025,
        )
    plt.close(fig)


def plot_combined(
    output_dir: Path,
    models: Sequence[str],
    summary: Mapping[str, np.ndarray],
    dpi: int,
) -> None:
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(7.05, 2.35),
        gridspec_kw={"width_ratios": (1.12, 1.58, 1.05)},
    )
    draw_mortality_panel(axes[0], models, summary, True, "A  Mortality")
    draw_primary_failure_heatmap(
        axes[1], models, summary, False, "B  Primary failure and role (%)"
    )
    draw_mismatch_panel(
        axes[2], models, summary, False, "C  Mismatch"
    )
    fig.subplots_adjust(left=0.125, right=0.995, bottom=0.19, top=0.81, wspace=0.26)
    save_figure(fig, output_dir / "failure_analysis_panels", dpi)


def plot_standalone(
    output_dir: Path,
    models: Sequence[str],
    summary: Mapping[str, np.ndarray],
    dpi: int,
) -> None:
    fig, ax = plt.subplots(figsize=(3.35, 2.15))
    draw_mortality_panel(ax, models, summary, True, "Generation-trajectory mortality")
    fig.subplots_adjust(left=0.37, right=0.98, bottom=0.22, top=0.90)
    save_figure(fig, output_dir / "mortality_by_model", dpi)

    fig, ax = plt.subplots(figsize=(3.35, 2.10))
    draw_primary_failure_heatmap(
        ax, models, summary, True, "Primary failure and role exposure (%)"
    )
    fig.subplots_adjust(left=0.36, right=0.99, bottom=0.25, top=0.89)
    save_figure(fig, output_dir / "primary_failure_with_role_heatmap", dpi)

    fig, ax = plt.subplots(figsize=(3.35, 2.15))
    draw_mismatch_panel(ax, models, summary, True, "Death-case mismatch")
    fig.subplots_adjust(left=0.37, right=0.98, bottom=0.22, top=0.74)
    save_figure(fig, output_dir / "death_case_mismatch_rates", dpi)


def write_plot_data(
    path: Path,
    models: Sequence[str],
    summary: Mapping[str, np.ndarray],
    bootstrap_samples: int,
) -> None:
    fields = [
        "panel",
        "model",
        "metric",
        "numerator",
        "denominator",
        "estimate_percent",
        "ci95_low",
        "ci95_high",
        "bootstrap_samples",
    ]
    rows: List[Dict[str, Any]] = []
    outcomes = summary["outcome_total"]
    judges = summary["judge_total"]
    for index, model in enumerate(models):
        rows.append(
            {
                "panel": "A",
                "model": model,
                "metric": "mortality",
                "numerator": int(outcomes[index, 1]),
                "denominator": int(outcomes[index, 0]),
                "estimate_percent": summary["mortality"][index],
                "ci95_low": summary["mortality_low"][index],
                "ci95_high": summary["mortality_high"][index],
                "bootstrap_samples": bootstrap_samples,
            }
        )
        rows.append(
            {
                "panel": "B",
                "model": model,
                "metric": "resource_disadvantaged_role_exposure",
                "numerator": outcomes[index, 2],
                "denominator": outcomes[index, 1],
                "estimate_percent": summary["factor_rates"][index, 0],
                "ci95_low": summary["factor_low"][index, 0],
                "ci95_high": summary["factor_high"][index, 0],
                "bootstrap_samples": bootstrap_samples,
            }
        )
        for mode_index, mode in enumerate(POLICY_FAILURE_MODES):
            rows.append(
                {
                    "panel": "B",
                    "model": model,
                    "metric": mode,
                    "numerator": judges[index, 2 + mode_index],
                    "denominator": judges[index, 0],
                    "estimate_percent": summary["factor_rates"][
                        index, 1 + mode_index
                    ],
                    "ci95_low": summary["factor_low"][index, 1 + mode_index],
                    "ci95_high": summary["factor_high"][index, 1 + mode_index],
                    "bootstrap_samples": bootstrap_samples,
                }
            )
        for mismatch_index, metric in enumerate(
            ("reasoning_policy_mismatch", "policy_trajectory_mismatch")
        ):
            rows.append(
                {
                    "panel": "C",
                    "model": model,
                    "metric": metric,
                    "numerator": judges[
                        index, 2 + len(POLICY_FAILURE_MODES) + mismatch_index
                    ],
                    "denominator": judges[index, 0],
                    "estimate_percent": summary["mismatch_rates"][index, mismatch_index],
                    "ci95_low": summary["mismatch_low"][index, mismatch_index],
                    "ci95_high": summary["mismatch_high"][index, mismatch_index],
                    "bootstrap_samples": bootstrap_samples,
                }
            )
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: round(value, 6) if isinstance(value, (float, np.floating)) else value
                    for key, value in row.items()
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--exp-start", type=int, default=1)
    parser.add_argument("--exp-end", type=int, default=120)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()
    if args.exp_start <= 0 or args.exp_end <= 0 or args.exp_start > args.exp_end:
        parser.error("experiment range must be positive and exp-start <= exp-end")
    if args.bootstrap_samples < 100:
        parser.error("--bootstrap-samples must be at least 100")
    if args.dpi <= 0:
        parser.error("--dpi must be positive")
    return args


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir is not None
        else input_dir / "figures"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    config_path = input_dir / "failure_run_config.json"
    paired_path = input_dir / "paired_judge_records.jsonl"
    agreement_path = input_dir / "judge_agreement.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Failure-analysis config not found: {config_path}")
    if not paired_path.is_file():
        raise FileNotFoundError(f"Paired judge records not found: {paired_path}")
    if not agreement_path.is_file():
        raise FileNotFoundError(f"Judge agreement summary not found: {agreement_path}")
    config = load_json(config_path)
    mappings = config.get("batch_condition_mapping", [])
    batch_names = [str(row["batch"]) for row in mappings if isinstance(row, dict)]
    if not batch_names:
        raise ValueError("failure_run_config.json has no batch-condition mapping")

    outcomes = collect_outcomes(
        args.log_dir.resolve(), batch_names, args.exp_start, args.exp_end
    )
    paired = load_paired_rows(paired_path, args.exp_start, args.exp_end)
    if not outcomes:
        raise ValueError("No valid generation-trajectory outcomes were found")
    if not paired:
        raise ValueError("No paired judge records were found")
    models = ordered_models(outcomes, paired)
    clusters, outcome_arrays, judge_arrays = build_cluster_arrays(outcomes, paired, models)
    summary = summarize(
        outcome_arrays,
        judge_arrays,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
    )

    death_count = int(summary["outcome_total"][:, 1].sum())
    paired_count = int(summary["judge_total"][:, 0].sum())
    if paired_count > death_count:
        raise ValueError(
            f"Paired judge count ({paired_count}) exceeds source deaths ({death_count})"
        )
    if paired_count < death_count:
        print(
            f"Warning: plotting {paired_count}/{death_count} paired death cases "
            f"({100.0 * paired_count / death_count:.2f}% coverage)."
        )

    configure_style()
    plot_combined(output_dir, models, summary, args.dpi)
    plot_standalone(output_dir, models, summary, args.dpi)
    write_plot_data(
        output_dir / "failure_analysis_plot_data.csv",
        models,
        summary,
        args.bootstrap_samples,
    )

    judge_1 = load_jsonl_by_id(input_dir / "judge_1_records.jsonl")
    judge_2 = load_jsonl_by_id(input_dir / "judge_2_records.jsonl")
    agreement = load_json(agreement_path)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "log_dir": str(args.log_dir.resolve()),
        "batches": batch_names,
        "experiment_range_inclusive": [args.exp_start, args.exp_end],
        "experiment_clusters": len(clusters),
        "models": list(models),
        "valid_generation_policy_rounds": int(summary["outcome_total"][:, 0].sum()),
        "eligible_source_deaths": death_count,
        "judge_1_successes": len(judge_1),
        "judge_2_successes": len(judge_2),
        "paired_death_cases": paired_count,
        "paired_coverage_rate": round(paired_count / death_count, 6),
        "bootstrap_samples": args.bootstrap_samples,
        "bootstrap_seed": args.bootstrap_seed,
        "displayed_primary_factors": list(PRIMARY_FACTORS),
        "judge_agreement": agreement.get("overall", {}),
        "panel_scope": {
            "A": "All valid original generation-trajectory policy-rounds.",
            "B": (
                "Deterministic disadvantaged-role exposure among source deaths, "
                "followed by two-judge averaged primary-mechanism votes among "
                "paired death cases. All percentages use deaths as the denominator. "
                "Role exposure can overlap with a primary mechanism; omitted "
                "no-primary and rare allocation labels mean displayed policy "
                "columns need not sum to 100."
            ),
            "C": "Two-judge averaged mismatch annotations among paired death cases only.",
        },
    }
    with (output_dir / "failure_analysis_figure_manifest.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)

    print(f"Output directory: {output_dir}")
    print(f"Valid generation policy-rounds: {manifest['valid_generation_policy_rounds']}")
    print(f"Eligible source deaths: {death_count}")
    print(f"Paired judged deaths: {paired_count} ({100.0 * paired_count / death_count:.2f}%)")
    print("Created combined and standalone PNG/PDF figures.")


if __name__ == "__main__":
    main()
