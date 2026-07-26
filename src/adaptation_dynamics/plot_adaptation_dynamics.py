#!/usr/bin/env python3
"""Plot role-balanced OF/OPF adaptation dynamics with clustered CIs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/wacbench-matplotlib")
import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OF_BATCH = PROJECT_ROOT / "log" / "batch_032_no_opp_info_c_med_20days"
DEFAULT_OPF_BATCH = PROJECT_ROOT / "log" / "batch_031_full_code_access_c_med_20days"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "compare_result" / "adaptation_dynamics"
DEFAULT_REPLAY_DETAILS = PROJECT_ROOT / "compare_result" / "main_table" / "replay_details.csv"
DEFAULT_META_ROUNDS = (1, 2, 3)
EXP_PATTERN = re.compile(r"^exp_(\d+)$")

CONDITION_ORDER = ("OF", "OPF")
CONDITION_COLORS = {"OF": "#377EB8", "OPF": "#E68613"}
CONDITION_MARKERS = {"OF": "o", "OPF": "s"}


@dataclass(frozen=True)
class AgentRound:
    condition: str
    batch: str
    experiment_id: str
    experiment_number: int
    meta_round: int
    seed: int
    role: str
    model: str
    survival_days: float | None
    dead: float | None
    valid: bool


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_round(path: Path) -> Mapping[str, Any]:
    payload = load_json(path)
    if isinstance(payload, list):
        if not payload or not isinstance(payload[0], dict):
            raise ValueError(f"Expected a non-empty list containing an object: {path}")
        return payload[0]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Expected an object or list containing an object: {path}")


def experiment_sort_key(path: Path) -> Tuple[int, str]:
    match = EXP_PATTERN.match(path.name)
    if match:
        return int(match.group(1)), path.name
    return math.inf, path.name


def parse_model_map(exp_dir: Path) -> Dict[str, str]:
    config_path = exp_dir / "backend_config.json"
    payload = load_json(config_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected an object: {config_path}")
    result = {
        str(role): str(spec.get("model", "")).strip()
        for role, spec in payload.items()
        if isinstance(spec, dict) and str(spec.get("model", "")).strip()
    }
    if not result:
        raise ValueError(f"No role-to-model mapping found: {config_path}")
    return result


def safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def collect_batch(
    batch_dir: Path,
    condition: str,
    meta_rounds: Sequence[int],
) -> List[AgentRound]:
    if not batch_dir.is_dir():
        raise FileNotFoundError(f"Batch directory not found: {batch_dir}")

    rows: List[AgentRound] = []
    exp_dirs = sorted(
        (path for path in batch_dir.iterdir() if path.is_dir() and EXP_PATTERN.match(path.name)),
        key=experiment_sort_key,
    )
    if not exp_dirs:
        raise ValueError(f"No exp_### directories found: {batch_dir}")

    for exp_dir in exp_dirs:
        match = EXP_PATTERN.match(exp_dir.name)
        assert match is not None
        exp_number = int(match.group(1))
        model_map = parse_model_map(exp_dir)

        for meta_round in meta_rounds:
            round_path = exp_dir / f"meta_round_{meta_round}.json"
            if not round_path.is_file():
                raise FileNotFoundError(f"Missing meta-round file: {round_path}")
            record = load_round(round_path)
            round_valid = bool(record.get("outcome_valid", 0))
            agents = record.get("agents")
            if not isinstance(agents, list):
                raise ValueError(f"Missing agents list: {round_path}")

            seen_roles = set()
            for agent in agents:
                if not isinstance(agent, dict):
                    continue
                role = str(agent.get("agent_id", "")).strip()
                if not role:
                    continue
                seen_roles.add(role)
                metrics = agent.get("metrics")
                admitted = bool(agent.get("admitted", 0))
                agent_outcome_valid = bool(agent.get("outcome_valid", round_valid))
                valid = admitted and round_valid and agent_outcome_valid and isinstance(metrics, dict)
                survival = safe_float(metrics.get("survival_days")) if isinstance(metrics, dict) else None
                final_hp = safe_float(metrics.get("final_hp")) if isinstance(metrics, dict) else None
                if survival is None or final_hp is None:
                    valid = False

                rows.append(
                    AgentRound(
                        condition=condition,
                        batch=batch_dir.name,
                        experiment_id=exp_dir.name,
                        experiment_number=exp_number,
                        meta_round=meta_round,
                        seed=42,
                        role=role,
                        model=model_map.get(role, "UNKNOWN"),
                        survival_days=survival if valid else None,
                        dead=float(final_hp <= 0) if valid and final_hp is not None else None,
                        valid=valid,
                    )
                )

            missing_roles = sorted(set(model_map) - seen_roles)
            if missing_roles:
                raise ValueError(
                    f"Missing agents in {round_path}: {', '.join(missing_roles)}"
                )
    return rows


def collect_replay_details(
    path: Path,
    meta_rounds: Sequence[int],
) -> Dict[str, List[AgentRound]]:
    """Load complete multi-seed simulator replays produced by main_combine.py."""
    if not path.is_file():
        raise FileNotFoundError(f"Replay details not found: {path}")
    requested_rounds = set(meta_rounds)
    rows_by_condition: Dict[str, List[AgentRound]] = {
        condition: [] for condition in CONDITION_ORDER
    }
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "feedback", "batch", "exp_id", "meta_round", "seed", "role", "model",
            "survival_days", "final_hp", "dead",
        }
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Replay details is missing columns: {sorted(missing)}")
        for source in reader:
            condition = str(source["feedback"]).strip()
            if condition not in rows_by_condition:
                continue
            meta_round = int(source["meta_round"])
            if meta_round not in requested_rounds:
                continue
            exp_id = str(source["exp_id"]).strip()
            match = EXP_PATTERN.match(exp_id)
            if match is None:
                raise ValueError(f"Invalid experiment id in replay details: {exp_id}")
            survival = safe_float(source["survival_days"])
            final_hp = safe_float(source["final_hp"])
            dead = safe_float(source["dead"])
            valid = survival is not None and final_hp is not None and dead is not None
            rows_by_condition[condition].append(
                AgentRound(
                    condition=condition,
                    batch=str(source["batch"]),
                    experiment_id=exp_id,
                    experiment_number=int(match.group(1)),
                    meta_round=meta_round,
                    seed=int(source["seed"]),
                    role=str(source["role"]).strip(),
                    model=str(source["model"]).strip() or "UNKNOWN",
                    survival_days=survival if valid else None,
                    dead=dead if valid else None,
                    valid=valid,
                )
            )
    return rows_by_condition


def validate_design(
    rows_by_condition: Mapping[str, Sequence[AgentRound]],
    meta_rounds: Sequence[int],
) -> Tuple[List[str], List[str], List[str], List[int]]:
    exp_sets = {
        condition: {row.experiment_id for row in rows}
        for condition, rows in rows_by_condition.items()
    }
    reference = exp_sets[CONDITION_ORDER[0]]
    for condition in CONDITION_ORDER[1:]:
        if exp_sets[condition] != reference:
            missing = sorted(reference - exp_sets[condition])
            extra = sorted(exp_sets[condition] - reference)
            raise ValueError(
                f"Matched experiment sets differ for {condition}; "
                f"missing={missing[:10]}, extra={extra[:10]}"
            )

    experiments = sorted(reference, key=lambda value: int(value.split("_")[-1]))
    roles = sorted({row.role for rows in rows_by_condition.values() for row in rows})
    models = sorted({row.model for rows in rows_by_condition.values() for row in rows})
    seed_sets = {
        condition: {row.seed for row in rows}
        for condition, rows in rows_by_condition.items()
    }
    seeds = sorted(seed_sets[CONDITION_ORDER[0]])
    for condition in CONDITION_ORDER[1:]:
        if seed_sets[condition] != set(seeds):
            raise ValueError(
                f"Matched supply-seed sets differ: {CONDITION_ORDER[0]}={seeds}, "
                f"{condition}={sorted(seed_sets[condition])}"
            )
    if not seeds:
        raise ValueError("No supply seeds were found")
    if "UNKNOWN" in models:
        raise ValueError("At least one agent is missing a model mapping")

    expected_cells = {
        (condition, exp_id, meta_round, seed, role)
        for condition in CONDITION_ORDER
        for exp_id in experiments
        for meta_round in meta_rounds
        for seed in seeds
        for role in roles
    }
    observed_cells = [
        (row.condition, row.experiment_id, row.meta_round, row.seed, row.role)
        for rows in rows_by_condition.values()
        for row in rows
    ]
    observed_set = set(observed_cells)
    duplicate_cells = [cell for cell, count in Counter(observed_cells).items() if count != 1]
    if observed_set != expected_cells or duplicate_cells:
        missing = sorted(expected_cells - observed_set)
        extra = sorted(observed_set - expected_cells)
        raise ValueError(
            f"Incomplete design; missing={missing[:10]}, extra={extra[:10]}, "
            f"duplicates={duplicate_cells[:10]}"
        )
    return experiments, roles, models, seeds


def build_stratum_arrays(
    rows: Sequence[AgentRound],
    experiments: Sequence[str],
    roles: Sequence[str],
    models: Sequence[str],
    meta_rounds: Sequence[int],
    seeds: Sequence[int],
) -> Dict[str, np.ndarray]:
    exp_index = {value: index for index, value in enumerate(experiments)}
    round_index = {value: index for index, value in enumerate(meta_rounds)}
    seed_index = {value: index for index, value in enumerate(seeds)}
    stratum_index = {
        (model, role): index
        for index, (model, role) in enumerate(
            (model, role) for model in models for role in roles
        )
    }
    shape = (len(meta_rounds), len(stratum_index), len(experiments), len(seeds))
    survival = np.full(shape, np.nan, dtype=float)
    mortality = np.full(shape, np.nan, dtype=float)

    for row in rows:
        if not row.valid:
            continue
        r = round_index[row.meta_round]
        s = stratum_index[(row.model, row.role)]
        e = exp_index[row.experiment_id]
        z = seed_index[row.seed]
        if not np.isnan(survival[r, s, e, z]):
            raise ValueError(
                f"Duplicate model-role observation: {row.condition}, "
                f"{row.experiment_id}, MR{row.meta_round}, {row.model}, {row.role}"
            )
        survival[r, s, e, z] = float(row.survival_days)
        mortality[r, s, e, z] = float(row.dead)

    return {"survival_days": survival, "mortality": mortality}


def role_balanced_estimate(values: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Return the macro mean over model-role strata for each weight vector."""
    if values.ndim != 2:
        raise ValueError("values must have shape [strata, experiments]")
    if weights.ndim == 1:
        weights = weights[None, :]
    valid = np.isfinite(values).astype(float)
    filled = np.nan_to_num(values, nan=0.0)
    numerators = weights @ filled.T
    denominators = weights @ valid.T
    with np.errstate(divide="ignore", invalid="ignore"):
        stratum_means = numerators / denominators
    if np.any(~np.isfinite(stratum_means)):
        raise ValueError("A bootstrap sample omitted an entire model-role stratum")
    return np.mean(stratum_means, axis=1)


def mean_over_fixed_seeds(values: np.ndarray) -> np.ndarray:
    """Average repeated supply seeds while retaining missing model-role cells."""
    if values.ndim != 3:
        raise ValueError("values must have shape [strata, experiments, seeds]")
    valid = np.isfinite(values)
    counts = np.sum(valid, axis=2)
    totals = np.sum(np.where(valid, values, 0.0), axis=2)
    result = np.full(counts.shape, np.nan, dtype=float)
    np.divide(totals, counts, out=result, where=counts > 0)
    return result


def percentile_interval(values: np.ndarray) -> Tuple[float, float]:
    low, high = np.percentile(values, [2.5, 97.5])
    return float(low), float(high)


def transition_pairs(meta_rounds: Sequence[int]) -> List[Tuple[int, int]]:
    """Adjacent revisions plus the full first-to-last adaptation effect."""
    pairs = [
        (meta_rounds[index - 1], meta_rounds[index])
        for index in range(1, len(meta_rounds))
    ]
    overall = (meta_rounds[0], meta_rounds[-1])
    if len(meta_rounds) > 2 and overall not in pairs:
        pairs.append(overall)
    return pairs


def summarize_with_bootstrap(
    arrays_by_condition: Mapping[str, Mapping[str, np.ndarray]],
    experiment_count: int,
    meta_rounds: Sequence[int],
    bootstrap_samples: int,
    bootstrap_seed: int,
    episode_days: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    rng = np.random.default_rng(bootstrap_seed)
    weights_full = np.ones(experiment_count, dtype=float)
    bootstrap_weights = rng.multinomial(
        experiment_count,
        np.full(experiment_count, 1.0 / experiment_count),
        size=bootstrap_samples,
    ).astype(float)

    metric_scale = {"wac_score": 100.0 / episode_days, "mortality_rate": 100.0}
    source_key = {"wac_score": "survival_days", "mortality_rate": "mortality"}
    display_name = {"wac_score": "WACScore", "mortality_rate": "Mortality"}

    estimates: Dict[str, Dict[str, Dict[int, float]]] = {}
    distributions: Dict[str, Dict[str, Dict[int, np.ndarray]]] = {}
    summary_rows: List[Dict[str, Any]] = []

    for condition in CONDITION_ORDER:
        estimates[condition] = {}
        distributions[condition] = {}
        for metric in ("wac_score", "mortality_rate"):
            estimates[condition][metric] = {}
            distributions[condition][metric] = {}
            values = arrays_by_condition[condition][source_key[metric]]
            scale = metric_scale[metric]
            for round_position, meta_round in enumerate(meta_rounds):
                seed_averaged = mean_over_fixed_seeds(values[round_position])
                point = float(role_balanced_estimate(seed_averaged, weights_full)[0] * scale)
                boot = role_balanced_estimate(seed_averaged, bootstrap_weights) * scale
                low, high = percentile_interval(boot)
                estimates[condition][metric][meta_round] = point
                distributions[condition][metric][meta_round] = boot
                summary_rows.append(
                    {
                        "condition": condition,
                        "meta_round": meta_round,
                        "metric": display_name[metric],
                        "estimate": point,
                        "ci95_low": low,
                        "ci95_high": high,
                        "bootstrap_samples": bootstrap_samples,
                    }
                )

    transitions = transition_pairs(meta_rounds)
    change_rows: List[Dict[str, Any]] = []
    change_distributions: Dict[str, Dict[str, Dict[str, np.ndarray]]] = {
        condition: {"wac_score": {}, "mortality_rate": {}}
        for condition in CONDITION_ORDER
    }
    for condition in CONDITION_ORDER:
        for metric in ("wac_score", "mortality_rate"):
            for start, end in transitions:
                label = f"MR{end}-MR{start}"
                point = estimates[condition][metric][end] - estimates[condition][metric][start]
                boot = (
                    distributions[condition][metric][end]
                    - distributions[condition][metric][start]
                )
                low, high = percentile_interval(boot)
                change_distributions[condition][metric][label] = boot
                change_rows.append(
                    {
                        "condition": condition,
                        "transition": label,
                        "metric": display_name[metric],
                        "estimate": point,
                        "ci95_low": low,
                        "ci95_high": high,
                        "bootstrap_samples": bootstrap_samples,
                    }
                )

    contrast_rows: List[Dict[str, Any]] = []
    for metric in ("wac_score", "mortality_rate"):
        for start, end in transitions:
            label = f"MR{end}-MR{start}"
            opf_point = estimates["OPF"][metric][end] - estimates["OPF"][metric][start]
            of_point = estimates["OF"][metric][end] - estimates["OF"][metric][start]
            point = opf_point - of_point
            boot = (
                change_distributions["OPF"][metric][label]
                - change_distributions["OF"][metric][label]
            )
            low, high = percentile_interval(boot)
            contrast_rows.append(
                {
                    "contrast": "OPF-minus-OF change",
                    "transition": label,
                    "metric": display_name[metric],
                    "estimate": point,
                    "ci95_low": low,
                    "ci95_high": high,
                    "bootstrap_samples": bootstrap_samples,
                }
            )

    analysis = {
        "estimates": estimates,
        "distributions": distributions,
        "change_distributions": change_distributions,
    }
    return summary_rows, change_rows, contrast_rows, analysis


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write an empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def rounded_rows(rows: Sequence[Mapping[str, Any]], digits: int = 6) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for row in rows:
        output: Dict[str, Any] = {}
        for key, value in row.items():
            output[key] = round(value, digits) if isinstance(value, float) else value
        result.append(output)
    return result


def ci_width_comparison_rows(
    multi_seed_sets: Sequence[Tuple[str, Sequence[Mapping[str, Any]], Sequence[str]]],
    seed42_sets: Sequence[Tuple[str, Sequence[Mapping[str, Any]], Sequence[str]]],
) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    seed42_by_analysis = {name: (rows, keys) for name, rows, keys in seed42_sets}
    for analysis, multi_rows, keys in multi_seed_sets:
        one_rows, one_keys = seed42_by_analysis[analysis]
        if tuple(keys) != tuple(one_keys):
            raise ValueError(f"CI comparison keys differ for {analysis}")
        one_lookup = {
            tuple(str(row[key]) for key in keys): row for row in one_rows
        }
        for row in multi_rows:
            identity = tuple(str(row[key]) for key in keys)
            single = one_lookup[identity]
            single_width = float(single["ci95_high"]) - float(single["ci95_low"])
            multi_width = float(row["ci95_high"]) - float(row["ci95_low"])
            result.append(
                {
                    "analysis": analysis,
                    "comparison_key": " | ".join(identity),
                    "seed42_ci_width": single_width,
                    "multi_seed_ci_width": multi_width,
                    "width_reduction_percent": (
                        100.0 * (1.0 - multi_width / single_width)
                        if single_width > 0 else math.nan
                    ),
                }
            )
    return result


def summary_lookup(rows: Sequence[Mapping[str, Any]]) -> Dict[Tuple[str, str, int], Mapping[str, Any]]:
    return {
        (str(row["condition"]), str(row["metric"]), int(row["meta_round"])): row
        for row in rows
    }


def change_lookup(rows: Sequence[Mapping[str, Any]]) -> Dict[Tuple[str, str, str], Mapping[str, Any]]:
    return {
        (str(row["condition"]), str(row["metric"]), str(row["transition"])): row
        for row in rows
    }


def configure_axis(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#D5D5D5", linewidth=0.8, alpha=0.7)
    ax.set_axisbelow(True)


def plot_trajectories(
    summary_rows: Sequence[Mapping[str, Any]],
    meta_rounds: Sequence[int],
    output_path: Path,
) -> None:
    lookup = summary_lookup(summary_rows)
    # Compact AAAI single-column layout. The two three-point trajectories
    # share one legend and fit side by side at roughly 3.3 inches total.
    fig, axes = plt.subplots(1, 2, figsize=(3.35, 1.82), sharex=True)
    panels = (
        ("WACScore", "(a) WACScore", "WACScore"),
        ("Mortality", "(b) Mortality", "Mortality (%)"),
    )

    for ax, (metric, title, ylabel) in zip(axes, panels):
        for condition in CONDITION_ORDER:
            rows = [lookup[(condition, metric, meta_round)] for meta_round in meta_rounds]
            points = np.array([float(row["estimate"]) for row in rows])
            lows = np.array([float(row["ci95_low"]) for row in rows])
            highs = np.array([float(row["ci95_high"]) for row in rows])
            ax.plot(
                meta_rounds,
                points,
                color=CONDITION_COLORS[condition],
                marker=CONDITION_MARKERS[condition],
                linewidth=1.25,
                markersize=3.4,
                label=condition,
            )
            ax.fill_between(
                meta_rounds,
                lows,
                highs,
                color=CONDITION_COLORS[condition],
                alpha=0.16,
                linewidth=0,
            )
        ax.set_title(title, fontsize=7.2, weight="bold", pad=2.5)
        ax.set_ylabel(ylabel, fontsize=6.8, labelpad=2)
        ax.set_xticks(meta_rounds, [f"MR{value}" for value in meta_rounds])
        ax.tick_params(axis="both", labelsize=6.5, pad=1.5, length=2.5)
        configure_axis(ax)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.94),
        ncol=2, frameon=False,
        fontsize=6.7, handlelength=1.7, columnspacing=1.2,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.91), w_pad=0.7)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_changes(
    change_rows: Sequence[Mapping[str, Any]],
    transitions: Sequence[str],
    output_path: Path,
) -> None:
    lookup = change_lookup(change_rows)
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.2))
    panels = (
        ("WACScore", "Change in WACScore", "WACScore change (pp)"),
        ("Mortality", "Change in mortality", "Mortality change (pp)"),
    )
    x = np.arange(len(transitions), dtype=float)
    width = 0.34

    for ax, (metric, title, ylabel) in zip(axes, panels):
        for index, condition in enumerate(CONDITION_ORDER):
            rows = [lookup[(condition, metric, transition)] for transition in transitions]
            points = np.array([float(row["estimate"]) for row in rows])
            lows = np.array([float(row["ci95_low"]) for row in rows])
            highs = np.array([float(row["ci95_high"]) for row in rows])
            positions = x + (index - 0.5) * width
            ax.bar(
                positions,
                points,
                width=width,
                color=CONDITION_COLORS[condition],
                alpha=0.88,
                label=condition,
                zorder=3,
            )
            ax.errorbar(
                positions,
                points,
                yerr=np.vstack([points - lows, highs - points]),
                fmt="none",
                ecolor="#222222",
                elinewidth=1.2,
                capsize=3,
                zorder=4,
            )
        ax.axhline(0, color="#333333", linewidth=1.0)
        ax.set_title(title, fontsize=12, weight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xticks(x, transitions)
        configure_axis(ax)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Paired Policy-Revision Effects", fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0.10, 1, 0.94))
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def combine_figures(
    summary_rows: Sequence[Mapping[str, Any]],
    change_rows: Sequence[Mapping[str, Any]],
    meta_rounds: Sequence[int],
    output_path: Path,
) -> None:
    summary = summary_lookup(summary_rows)
    changes = change_lookup(change_rows)
    transitions = [f"MR{end}-MR{start}" for start, end in transition_pairs(meta_rounds)]
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 8.0))

    for ax, metric, title, ylabel in (
        (axes[0, 0], "WACScore", "A. WACScore trajectory", "WACScore"),
        (axes[0, 1], "Mortality", "B. Mortality trajectory", "Mortality rate (%)"),
    ):
        for condition in CONDITION_ORDER:
            rows = [summary[(condition, metric, meta_round)] for meta_round in meta_rounds]
            points = np.array([float(row["estimate"]) for row in rows])
            lows = np.array([float(row["ci95_low"]) for row in rows])
            highs = np.array([float(row["ci95_high"]) for row in rows])
            ax.plot(
                meta_rounds,
                points,
                color=CONDITION_COLORS[condition],
                marker=CONDITION_MARKERS[condition],
                linewidth=2.4,
                markersize=7,
                label=condition,
            )
            ax.fill_between(meta_rounds, lows, highs, color=CONDITION_COLORS[condition], alpha=0.16)
        ax.set_title(title, loc="left", fontsize=12, weight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xticks(meta_rounds, [f"MR{value}" for value in meta_rounds])
        configure_axis(ax)

    x = np.arange(len(transitions), dtype=float)
    width = 0.34
    for ax, metric, title, ylabel in (
        (axes[1, 0], "WACScore", "C. Policy-revision WACScore change", "Change (pp)"),
        (axes[1, 1], "Mortality", "D. Policy-revision mortality change", "Change (pp)"),
    ):
        for index, condition in enumerate(CONDITION_ORDER):
            rows = [changes[(condition, metric, transition)] for transition in transitions]
            points = np.array([float(row["estimate"]) for row in rows])
            lows = np.array([float(row["ci95_low"]) for row in rows])
            highs = np.array([float(row["ci95_high"]) for row in rows])
            positions = x + (index - 0.5) * width
            ax.bar(positions, points, width=width, color=CONDITION_COLORS[condition], alpha=0.88, label=condition, zorder=3)
            ax.errorbar(
                positions,
                points,
                yerr=np.vstack([points - lows, highs - points]),
                fmt="none",
                ecolor="#222222",
                elinewidth=1.2,
                capsize=3,
                zorder=4,
            )
        ax.axhline(0, color="#333333", linewidth=1.0)
        ax.set_title(title, loc="left", fontsize=12, weight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xticks(x, transitions)
        configure_axis(ax)

    for ax in axes.flat:
        ax.set_xlabel("Meta-round" if ax in axes[0] else "Policy revision")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Adaptation Dynamics under Outcome and Policy Feedback", fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0.06, 1, 0.95), h_pad=2.2)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_model_trajectories(
    summary_rows: Sequence[Mapping[str, Any]],
    models: Sequence[str],
    meta_rounds: Sequence[int],
    seeds: Sequence[int],
    output_path: Path,
) -> None:
    lookup = {
        (str(row["model"]), str(row["condition"]), str(row["metric"]), int(row["meta_round"])): row
        for row in summary_rows
    }
    fig, axes = plt.subplots(
        2, len(models), figsize=(3.15 * len(models), 6.6), sharey="row", squeeze=False
    )
    for column, model in enumerate(models):
        for row_index, (metric, ylabel) in enumerate(
            (("WACScore", "WACScore"), ("Mortality", "Mortality rate (%)"))
        ):
            ax = axes[row_index, column]
            for condition in CONDITION_ORDER:
                items = [
                    lookup[(model, condition, metric, meta_round)]
                    for meta_round in meta_rounds
                ]
                points = np.array([float(item["estimate"]) for item in items])
                lows = np.array([float(item["ci95_low"]) for item in items])
                highs = np.array([float(item["ci95_high"]) for item in items])
                ax.plot(
                    meta_rounds, points, color=CONDITION_COLORS[condition],
                    marker=CONDITION_MARKERS[condition], linewidth=2.0,
                    markersize=5.5, label=condition,
                )
                ax.fill_between(
                    meta_rounds, lows, highs, color=CONDITION_COLORS[condition],
                    alpha=0.14, linewidth=0,
                )
            if row_index == 0:
                ax.set_title(model, fontsize=10.5, weight="bold")
            if column == 0:
                ax.set_ylabel(ylabel)
            if row_index == 1:
                ax.set_xlabel("Meta-round")
            ax.set_xticks(meta_rounds, [f"MR{value}" for value in meta_rounds])
            configure_axis(ax)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle(
        f"Model-Level Adaptation across {len(seeds)} Fixed Supply Seed"
        f"{'s' if len(seeds) != 1 else ''}",
        fontsize=14,
        weight="bold",
    )
    fig.tight_layout(rect=(0, 0.07, 1, 0.94), w_pad=1.2, h_pad=1.8)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def display_model_name(model: str) -> str:
    return {
        "gemini-3.5-flash": "Gemini 3.5 Flash",
        "claude-sonnet-5": "Claude Sonnet 5",
        "gpt-5.4": "GPT-5.4",
        "deepseek-v4-flash": "DeepSeek V4 Flash",
        "gpt-5.4-nano": "GPT-5.4 Nano",
    }.get(model, model)


def plot_model_revision_contrasts(
    contrast_rows: Sequence[Mapping[str, Any]],
    models: Sequence[str],
    transition: str,
    output_path: Path,
) -> None:
    """Plot model-level baseline-adjusted OPF-minus-OF revision effects."""
    lookup = {
        (str(row["model"]), str(row["metric"]), str(row["transition"])): row
        for row in contrast_rows
    }
    ordered_models = list(models)
    y = np.arange(len(ordered_models), dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.5), sharey=True)
    panels = (
        ("WACScore", "WACScore", "OPF-minus-OF change (pp)"),
        ("Mortality", "Mortality", "OPF-minus-OF change (pp)"),
    )
    for ax, (metric, title, xlabel) in zip(axes, panels):
        items = [lookup[(model, metric, transition)] for model in ordered_models]
        points = np.array([float(item["estimate"]) for item in items])
        lows = np.array([float(item["ci95_low"]) for item in items])
        highs = np.array([float(item["ci95_high"]) for item in items])
        ax.errorbar(
            points,
            y,
            xerr=np.vstack([points - lows, highs - points]),
            fmt="o",
            color="#222222",
            markerfacecolor="#8C5AA8",
            markeredgecolor="#5D3A70",
            markersize=7,
            elinewidth=1.5,
            capsize=3,
        )
        ax.axvline(0, color="#666666", linewidth=1.0, linestyle="--")
        ax.set_title(title, fontsize=12, weight="bold")
        ax.set_xlabel(xlabel)
        ax.set_yticks(y, [display_model_name(model) for model in ordered_models])
        ax.grid(axis="x", color="#D5D5D5", linewidth=0.8, alpha=0.7)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[0].invert_yaxis()
    fig.suptitle(f"Model-Level Policy-Transparency Effects ({transition})", fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93), w_pad=2.4)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def summarize_cross_model_dispersion(
    model_arrays: Mapping[str, Mapping[str, Mapping[str, np.ndarray]]],
    experiment_count: int,
    meta_rounds: Sequence[int],
    bootstrap_samples: int,
    bootstrap_seed: int,
    episode_days: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Estimate descriptive dispersion across the five fixed model backends."""
    rng = np.random.default_rng(bootstrap_seed)
    bootstrap_weights = rng.multinomial(
        experiment_count,
        np.full(experiment_count, 1.0 / experiment_count),
        size=bootstrap_samples,
    ).astype(float)
    full_weights = np.ones(experiment_count, dtype=float)
    specs = (
        ("WACScore SD", "survival_days", 100.0 / episode_days),
        ("Mortality SD", "mortality", 100.0),
    )
    estimates: Dict[Tuple[str, str, int], float] = {}
    distributions: Dict[Tuple[str, str, int], np.ndarray] = {}
    summary_rows: List[Dict[str, Any]] = []

    for condition in CONDITION_ORDER:
        for metric, source, scale in specs:
            for round_index, meta_round in enumerate(meta_rounds):
                model_points = []
                model_boots = []
                for model in model_arrays:
                    values = model_arrays[model][condition][source][round_index]
                    seed_averaged = mean_over_fixed_seeds(values)
                    model_points.append(
                        role_balanced_estimate(seed_averaged, full_weights)[0] * scale
                    )
                    model_boots.append(
                        role_balanced_estimate(seed_averaged, bootstrap_weights) * scale
                    )
                point = float(np.std(np.asarray(model_points), ddof=0))
                boot = np.std(np.stack(model_boots), axis=0, ddof=0)
                low, high = percentile_interval(boot)
                estimates[(condition, metric, meta_round)] = point
                distributions[(condition, metric, meta_round)] = boot
                summary_rows.append(
                    {
                        "condition": condition,
                        "meta_round": meta_round,
                        "metric": metric,
                        "estimate": point,
                        "ci95_low": low,
                        "ci95_high": high,
                        "model_count": len(model_arrays),
                        "bootstrap_samples": bootstrap_samples,
                    }
                )

    change_rows: List[Dict[str, Any]] = []
    contrast_rows: List[Dict[str, Any]] = []
    for start, end in transition_pairs(meta_rounds):
        transition = f"MR{end}-MR{start}"
        for metric, _, _ in specs:
            condition_changes: Dict[str, Tuple[float, np.ndarray]] = {}
            for condition in CONDITION_ORDER:
                point = estimates[(condition, metric, end)] - estimates[(condition, metric, start)]
                boot = (
                    distributions[(condition, metric, end)]
                    - distributions[(condition, metric, start)]
                )
                low, high = percentile_interval(boot)
                condition_changes[condition] = (point, boot)
                change_rows.append(
                    {
                        "condition": condition,
                        "transition": transition,
                        "metric": metric,
                        "estimate": point,
                        "ci95_low": low,
                        "ci95_high": high,
                        "bootstrap_samples": bootstrap_samples,
                    }
                )
            point = condition_changes["OPF"][0] - condition_changes["OF"][0]
            boot = condition_changes["OPF"][1] - condition_changes["OF"][1]
            low, high = percentile_interval(boot)
            contrast_rows.append(
                {
                    "contrast": "OPF-minus-OF dispersion change",
                    "transition": transition,
                    "metric": metric,
                    "estimate": point,
                    "ci95_low": low,
                    "ci95_high": high,
                    "bootstrap_samples": bootstrap_samples,
                }
            )
    return summary_rows, change_rows, contrast_rows


def plot_performance_dispersion(
    rows: Sequence[Mapping[str, Any]],
    meta_rounds: Sequence[int],
    output_path: Path,
) -> None:
    lookup = {
        (str(row["condition"]), str(row["metric"]), int(row["meta_round"])): row
        for row in rows
    }
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.1))
    panels = (
        ("WACScore SD", "Cross-model WACScore dispersion", "SD across model means"),
        ("Mortality SD", "Cross-model mortality dispersion", "SD across model means (pp)"),
    )
    for ax, (metric, title, ylabel) in zip(axes, panels):
        for condition in CONDITION_ORDER:
            items = [lookup[(condition, metric, meta_round)] for meta_round in meta_rounds]
            points = np.array([float(item["estimate"]) for item in items])
            lows = np.array([float(item["ci95_low"]) for item in items])
            highs = np.array([float(item["ci95_high"]) for item in items])
            ax.plot(
                meta_rounds, points, color=CONDITION_COLORS[condition],
                marker=CONDITION_MARKERS[condition], linewidth=2.3,
                markersize=6.5, label=condition,
            )
            ax.fill_between(meta_rounds, lows, highs, color=CONDITION_COLORS[condition], alpha=0.16)
        ax.set_title(title, fontsize=11.5, weight="bold")
        ax.set_ylabel(ylabel)
        ax.set_xlabel("Meta-round")
        ax.set_xticks(meta_rounds, [f"MR{value}" for value in meta_rounds])
        configure_axis(ax)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Descriptive Performance Convergence", fontsize=14, weight="bold")
    fig.tight_layout(rect=(0, 0.10, 1, 0.94), w_pad=2.2)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_markdown_summary(
    output_path: Path,
    summary_rows: Sequence[Mapping[str, Any]],
    change_rows: Sequence[Mapping[str, Any]],
    contrast_rows: Sequence[Mapping[str, Any]],
    meta_rounds: Sequence[int],
    seeds: Sequence[int],
    model_change_rows: Sequence[Mapping[str, Any]],
    models: Sequence[str],
) -> None:
    summary = summary_lookup(summary_rows)
    changes = change_lookup(change_rows)
    lines = [
        "# Adaptation dynamics summary",
        "",
        "All intervals are 95% matched experiment-cluster bootstrap intervals,",
        f"conditional on the fixed supply seeds {list(seeds)}.",
        "The supply-seed outcomes are averaged within each experiment before resampling.",
        "WACScore and mortality are macro-averaged over model-by-role strata.",
        "",
        "## Meta-round trajectories",
        "",
        "| Condition | MR | WACScore (95% CI) | Mortality % (95% CI) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for condition in CONDITION_ORDER:
        for meta_round in meta_rounds:
            wac = summary[(condition, "WACScore", meta_round)]
            mortality = summary[(condition, "Mortality", meta_round)]
            lines.append(
                f"| {condition} | {meta_round} | "
                f"{wac['estimate']:.2f} [{wac['ci95_low']:.2f}, {wac['ci95_high']:.2f}] | "
                f"{mortality['estimate']:.2f} [{mortality['ci95_low']:.2f}, {mortality['ci95_high']:.2f}] |"
            )

    lines.extend(
        [
            "",
            "## Policy-revision and full-horizon changes",
            "",
            "| Condition | Transition | WACScore change (pp) | Mortality change (pp) |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    transitions = [f"MR{end}-MR{start}" for start, end in transition_pairs(meta_rounds)]
    for condition in CONDITION_ORDER:
        for transition in transitions:
            wac = changes[(condition, "WACScore", transition)]
            mortality = changes[(condition, "Mortality", transition)]
            lines.append(
                f"| {condition} | {transition} | "
                f"{wac['estimate']:+.2f} [{wac['ci95_low']:+.2f}, {wac['ci95_high']:+.2f}] | "
                f"{mortality['estimate']:+.2f} [{mortality['ci95_low']:+.2f}, {mortality['ci95_high']:+.2f}] |"
            )

    lines.extend(
        [
            "",
            "## Difference in revision effects (OPF minus OF)",
            "",
            "| Transition | Metric | Estimate (95% CI) |",
            "| --- | --- | ---: |",
        ]
    )
    for row in contrast_rows:
        lines.append(
            f"| {row['transition']} | {row['metric']} | "
            f"{row['estimate']:+.2f} [{row['ci95_low']:+.2f}, {row['ci95_high']:+.2f}] |"
        )

    full_transition = f"MR{meta_rounds[-1]}-MR{meta_rounds[0]}"
    model_changes = {
        (str(row["model"]), str(row["condition"]), str(row["metric"])): row
        for row in model_change_rows
        if str(row["transition"]) == full_transition
    }
    lines.extend(
        [
            "",
            f"## Model-level full adaptation ({full_transition})",
            "",
            "| Model | Condition | WACScore change (95% CI) | Mortality change (95% CI) |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for model in models:
        for condition in CONDITION_ORDER:
            wac = model_changes[(model, condition, "WACScore")]
            mortality = model_changes[(model, condition, "Mortality")]
            lines.append(
                f"| {model} | {condition} | "
                f"{wac['estimate']:+.2f} [{wac['ci95_low']:+.2f}, {wac['ci95_high']:+.2f}] | "
                f"{mortality['estimate']:+.2f} [{mortality['ci95_low']:+.2f}, {mortality['ci95_high']:+.2f}] |"
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_record_rows(rows_by_condition: Mapping[str, Sequence[AgentRound]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for condition in CONDITION_ORDER:
        for row in sorted(
            rows_by_condition[condition],
            key=lambda item: (
                item.experiment_number, item.meta_round, item.seed, item.role
            ),
        ):
            result.append(
                {
                    "condition": row.condition,
                    "batch": row.batch,
                    "experiment_id": row.experiment_id,
                    "meta_round": row.meta_round,
                    "seed": row.seed,
                    "role": row.role,
                    "model": row.model,
                    "survival_days": row.survival_days,
                    "dead": int(row.dead) if row.dead is not None else "",
                    "valid": int(row.valid),
                }
            )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-mode", choices=("replay", "logs"), default="replay",
        help="Use multi-seed replay_details.csv (default) or original single-seed logs.",
    )
    parser.add_argument("--replay-details", type=Path, default=DEFAULT_REPLAY_DETAILS)
    parser.add_argument("--of-batch", type=Path, default=DEFAULT_OF_BATCH)
    parser.add_argument("--opf-batch", type=Path, default=DEFAULT_OPF_BATCH)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--meta-rounds", nargs="+", type=int, default=list(DEFAULT_META_ROUNDS))
    parser.add_argument("--episode-days", type=int, default=20)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    args = parser.parse_args()
    if len(args.meta_rounds) < 2 or sorted(set(args.meta_rounds)) != args.meta_rounds:
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

    if args.input_mode == "replay":
        rows_by_condition = collect_replay_details(
            args.replay_details.resolve(), args.meta_rounds
        )
        input_source = str(args.replay_details.resolve())
    else:
        rows_by_condition = {
            "OF": collect_batch(args.of_batch.resolve(), "OF", args.meta_rounds),
            "OPF": collect_batch(args.opf_batch.resolve(), "OPF", args.meta_rounds),
        }
        input_source = "original batch logs (seed 42)"
    experiments, roles, models, seeds = validate_design(rows_by_condition, args.meta_rounds)
    arrays_by_condition = {
        condition: build_stratum_arrays(
            rows_by_condition[condition], experiments, roles, models, args.meta_rounds, seeds
        )
        for condition in CONDITION_ORDER
    }

    summary_rows, change_rows, contrast_rows, _ = summarize_with_bootstrap(
        arrays_by_condition=arrays_by_condition,
        experiment_count=len(experiments),
        meta_rounds=args.meta_rounds,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_seed=args.bootstrap_seed,
        episode_days=args.episode_days,
    )
    ci_comparison_rows: List[Dict[str, Any]] = []
    if 42 in seeds and len(seeds) > 1:
        seed_position = seeds.index(42)
        seed42_arrays = {
            condition: {
                metric: values[..., seed_position : seed_position + 1]
                for metric, values in arrays_by_condition[condition].items()
            }
            for condition in CONDITION_ORDER
        }
        seed42_summary, seed42_changes, seed42_contrasts, _ = summarize_with_bootstrap(
            arrays_by_condition=seed42_arrays,
            experiment_count=len(experiments),
            meta_rounds=args.meta_rounds,
            bootstrap_samples=args.bootstrap_samples,
            bootstrap_seed=args.bootstrap_seed,
            episode_days=args.episode_days,
        )
        ci_comparison_rows = ci_width_comparison_rows(
            (
                ("trajectory", summary_rows, ("condition", "meta_round", "metric")),
                ("revision", change_rows, ("condition", "transition", "metric")),
                ("OPF-minus-OF", contrast_rows, ("transition", "metric")),
            ),
            (
                ("trajectory", seed42_summary, ("condition", "meta_round", "metric")),
                ("revision", seed42_changes, ("condition", "transition", "metric")),
                ("OPF-minus-OF", seed42_contrasts, ("transition", "metric")),
            ),
        )
    summary_rows = rounded_rows(summary_rows)
    change_rows = rounded_rows(change_rows)
    contrast_rows = rounded_rows(contrast_rows)
    ci_comparison_rows = rounded_rows(ci_comparison_rows)

    model_summary_rows: List[Dict[str, Any]] = []
    model_change_rows: List[Dict[str, Any]] = []
    model_contrast_rows: List[Dict[str, Any]] = []
    model_arrays_by_name: Dict[str, Dict[str, Dict[str, np.ndarray]]] = {}
    for model in models:
        model_arrays = {
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
        model_arrays_by_name[model] = model_arrays
        model_summary, model_changes, model_contrasts, _ = summarize_with_bootstrap(
            arrays_by_condition=model_arrays,
            experiment_count=len(experiments),
            meta_rounds=args.meta_rounds,
            bootstrap_samples=args.bootstrap_samples,
            bootstrap_seed=args.bootstrap_seed,
            episode_days=args.episode_days,
        )
        for destination, source_rows in (
            (model_summary_rows, model_summary),
            (model_change_rows, model_changes),
            (model_contrast_rows, model_contrasts),
        ):
            destination.extend({"model": model, **row} for row in source_rows)
    model_summary_rows = rounded_rows(model_summary_rows)
    model_change_rows = rounded_rows(model_change_rows)
    model_contrast_rows = rounded_rows(model_contrast_rows)

    dispersion_rows, dispersion_change_rows, dispersion_contrast_rows = (
        summarize_cross_model_dispersion(
            model_arrays=model_arrays_by_name,
            experiment_count=len(experiments),
            meta_rounds=args.meta_rounds,
            bootstrap_samples=args.bootstrap_samples,
            bootstrap_seed=args.bootstrap_seed,
            episode_days=args.episode_days,
        )
    )
    dispersion_rows = rounded_rows(dispersion_rows)
    dispersion_change_rows = rounded_rows(dispersion_change_rows)
    dispersion_contrast_rows = rounded_rows(dispersion_contrast_rows)

    record_rows = build_record_rows(rows_by_condition)
    write_csv(output_dir / "agent_round_records.csv", record_rows)
    write_csv(output_dir / "meta_round_summary.csv", summary_rows)
    write_csv(output_dir / "meta_round_changes.csv", change_rows)
    write_csv(output_dir / "opf_minus_of_revision_effect.csv", contrast_rows)
    write_csv(output_dir / "meta_round_summary_by_model.csv", model_summary_rows)
    write_csv(output_dir / "meta_round_changes_by_model.csv", model_change_rows)
    write_csv(output_dir / "opf_minus_of_revision_effect_by_model.csv", model_contrast_rows)
    write_csv(output_dir / "cross_model_performance_dispersion.csv", dispersion_rows)
    write_csv(output_dir / "cross_model_performance_dispersion_changes.csv", dispersion_change_rows)
    write_csv(
        output_dir / "opf_minus_of_performance_dispersion_change.csv",
        dispersion_contrast_rows,
    )
    if ci_comparison_rows:
        write_csv(output_dir / "ci_width_comparison.csv", ci_comparison_rows)

    transitions = [
        f"MR{end}-MR{start}" for start, end in transition_pairs(args.meta_rounds)
    ]
    plot_trajectories(summary_rows, args.meta_rounds, output_dir / "adaptation_trajectories.png")
    plot_changes(change_rows, transitions, output_dir / "adaptation_changes.png")
    combine_figures(summary_rows, change_rows, args.meta_rounds, output_dir / "adaptation_dynamics.png")
    plot_model_trajectories(
        model_summary_rows, models, args.meta_rounds, seeds,
        output_dir / "adaptation_by_model.png",
    )
    full_transition = f"MR{args.meta_rounds[-1]}-MR{args.meta_rounds[0]}"
    plot_model_revision_contrasts(
        model_contrast_rows,
        models,
        full_transition,
        output_dir / "model_revision_effects.png",
    )
    plot_performance_dispersion(
        dispersion_rows,
        args.meta_rounds,
        output_dir / "performance_dispersion.png",
    )
    write_markdown_summary(
        output_dir / "adaptation_summary.md",
        summary_rows,
        change_rows,
        contrast_rows,
        args.meta_rounds,
        seeds,
        model_change_rows,
        models,
    )

    validity = {
        condition: {
            "valid_items": sum(row.valid for row in rows),
            "total_items": len(rows),
            "invalid_items": sum(not row.valid for row in rows),
        }
        for condition, rows in rows_by_condition.items()
    }
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "of_batch": str(args.of_batch.resolve()),
        "opf_batch": str(args.opf_batch.resolve()),
        "output_dir": str(output_dir),
        "input_mode": args.input_mode,
        "input_source": input_source,
        "experiments": len(experiments),
        "experiment_ids": experiments,
        "meta_rounds": args.meta_rounds,
        "supply_seeds": seeds,
        "roles": roles,
        "models": models,
        "episode_days": args.episode_days,
        "bootstrap": {
            "method": "matched experiment-cluster percentile bootstrap after within-experiment seed averaging",
            "samples": args.bootstrap_samples,
            "seed": args.bootstrap_seed,
            "confidence_level": 0.95,
        },
        "aggregation": "mean over fixed supply seeds within experiment, then macro mean over model-by-role strata",
        "inference_scope": "conditional on the selected fixed supply seeds",
        "validity": validity,
        "files": [
            "adaptation_dynamics.png",
            "adaptation_trajectories.png",
            "adaptation_changes.png",
            "adaptation_summary.md",
            "meta_round_summary.csv",
            "meta_round_changes.csv",
            "opf_minus_of_revision_effect.csv",
            "agent_round_records.csv",
            "adaptation_by_model.png",
            "meta_round_summary_by_model.csv",
            "meta_round_changes_by_model.csv",
            "opf_minus_of_revision_effect_by_model.csv",
            "model_revision_effects.png",
            "performance_dispersion.png",
            "cross_model_performance_dispersion.csv",
            "cross_model_performance_dispersion_changes.csv",
            "opf_minus_of_performance_dispersion_change.csv",
            *(["ci_width_comparison.csv"] if ci_comparison_rows else []),
        ],
    }
    (output_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Wrote adaptation analysis for {len(experiments)} matched experiments to {output_dir}")
    for condition in CONDITION_ORDER:
        info = validity[condition]
        print(f"- {condition}: {info['valid_items']}/{info['total_items']} valid agent-seed-rounds")


if __name__ == "__main__":
    main()
