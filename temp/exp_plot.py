#!/usr/bin/env python3
import argparse
import json
import os
import re
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _pretty_model_name(model_name: str) -> str:
    cleaned = str(model_name).strip().replace("_", " ")
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _collect_meta_round_files(exp_dir: str) -> List[Tuple[int, str]]:
    results: List[Tuple[int, str]] = []
    for name in os.listdir(exp_dir):
        match = re.match(r"^meta_round_(\d+)\.json$", name)
        if not match:
            continue
        path = os.path.join(exp_dir, name)
        if os.path.isfile(path):
            results.append((int(match.group(1)), path))
    return sorted(results, key=lambda item: item[0])


def _load_agent_model_map(exp_dir: str) -> Dict[str, str]:
    summary_path = os.path.join(exp_dir, "agent_averages.json")
    if not os.path.isfile(summary_path):
        return {}

    try:
        payload = _load_json(summary_path)
    except Exception:
        return {}

    averages = payload.get("agent_averages", {})
    if not isinstance(averages, dict):
        return {}

    model_map: Dict[str, str] = {}
    for agent_id, stats in averages.items():
        if isinstance(stats, dict):
            model_map[str(agent_id)] = str(stats.get("model_used", "Unknown Model"))
    return model_map


def _extract_round_data(meta_round_payload: dict, model_map: Dict[str, str]) -> Tuple[int, List[int], Dict[str, Dict[str, List[float]]]]:
    meta_round_id = int(meta_round_payload.get("meta_round_id", 0))
    environment = meta_round_payload.get("environment", {})
    supply_list = environment.get("supply_list", [])

    traces: Dict[str, Dict[str, List[float]]] = {}
    for agent in meta_round_payload.get("agents", []):
        if not isinstance(agent, dict):
            continue

        agent_id = str(agent.get("agent_id", "Unknown"))
        model_name = _pretty_model_name(model_map.get(agent_id, "Unknown Model"))
        label = f"{agent_id}({model_name})"

        daily_trace = agent.get("daily_trace", [])
        days: List[float] = []
        hp_values: List[float] = []
        bid_values: List[float] = []

        for day_entry in daily_trace:
            if not isinstance(day_entry, dict):
                continue
            try:
                days.append(float(day_entry.get("day", len(days) + 1)))
                hp_values.append(float(day_entry.get("hp_after", 0.0)))
                bid_values.append(float(day_entry.get("bid", 0.0)))
            except Exception:
                continue

        if days:
            traces[label] = {
                "days": days,
                "hp": hp_values,
                "bids": bid_values,
            }

    return meta_round_id, [int(x) for x in supply_list], traces


def _annotate_supply(ax, days: List[float], supply_list: List[int]) -> None:
    if not days or not supply_list:
        return

    y_min, y_max = ax.get_ylim()
    span = y_max - y_min
    y_text = y_min - 0.18 * span
    for idx, day in enumerate(days):
        supply = supply_list[idx] if idx < len(supply_list) else None
        if supply is None:
            continue
        ax.text(
            day,
            y_text,
            f"S={supply}",
            ha="center",
            va="top",
            fontsize=8,
            rotation=0,
            clip_on=False,
        )


def _build_series_bias_map(labels: List[str]) -> Dict[str, float]:
    if not labels:
        return {}

    sorted_labels = sorted(labels)
    if len(sorted_labels) == 1:
        return {sorted_labels[0]: 0.0}

    step = 0.02
    start = -step * (len(sorted_labels) - 1) / 2.0
    return {label: start + idx * step for idx, label in enumerate(sorted_labels)}


def _plot_meta_round(exp_dir: str, output_dir: str, meta_round_id: int, supply_list: List[int], traces: Dict[str, Dict[str, List[float]]]) -> None:
    if not traces:
        return

    max_days = max(len(entry["days"]) for entry in traces.values())
    days = list(range(1, max_days + 1))
    bias_map = _build_series_bias_map(list(traces.keys()))

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    fig.suptitle(f"{os.path.basename(exp_dir)} - Meta Round {meta_round_id}", fontsize=14)

    for label, series in traces.items():
        bias = bias_map.get(label, 0.0)
        biased_days = [day + bias for day in series["days"]]
        axes[0].plot(biased_days, series["hp"], marker="o", linewidth=1.8, label=label)
        axes[1].plot(biased_days, series["bids"], marker="o", linewidth=1.8, label=label)

    axes[0].set_ylabel("HP")
    axes[1].set_ylabel("Bids")
    axes[1].set_xlabel("Day")
    axes[0].set_title("HP by Day")
    axes[1].set_title("Bid by Day")
    axes[0].grid(True, alpha=0.25)
    axes[1].grid(True, alpha=0.25)

    if supply_list:
        x_ticks = list(range(1, min(len(supply_list), max_days) + 1))
    else:
        x_ticks = days
    axes[1].set_xticks(x_ticks)
    axes[1].set_xlim(0.5, max_days + 0.5)

    axes[0].legend(loc="upper left", fontsize=8, ncol=1)
    axes[1].legend(loc="upper left", fontsize=8, ncol=1)

    # Put supply annotations below the bottom subplot.
    bottom = axes[1]
    bottom.relim()
    bottom.autoscale_view()
    y_min, y_max = bottom.get_ylim()
    bottom.set_ylim(y_min - 0.22 * (y_max - y_min), y_max)
    _annotate_supply(bottom, days, supply_list)

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    exp_name = os.path.basename(exp_dir.rstrip(os.sep))
    out_path = os.path.join(output_dir, f"{exp_name}_meta_round_{meta_round_id}.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot HP and bid traces for one exp folder.")
    parser.add_argument("--log-dir", type=str, default="log", help="Root log directory.")
    parser.add_argument("--batch", type=str, required=True, help="Batch folder name, e.g. batch_005_no_opp_info.")
    parser.add_argument("--exp", type=str, required=True, help="Experiment folder name, e.g. exp_001.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for plots.")
    args = parser.parse_args()

    batch_dir = os.path.join(args.log_dir, args.batch)
    exp_dir = os.path.join(batch_dir, args.exp)
    if not os.path.isdir(exp_dir):
        raise SystemExit(f"Experiment folder not found: {exp_dir}")

    output_dir = args.output_dir or os.path.join(exp_dir, "output_analysis")
    _ensure_dir(output_dir)

    model_map = _load_agent_model_map(exp_dir)
    meta_round_files = _collect_meta_round_files(exp_dir)
    if not meta_round_files:
        raise SystemExit(f"No meta_round_*.json files found in: {exp_dir}")

    for _, meta_round_path in meta_round_files:
        payload = _load_json(meta_round_path)
        if not isinstance(payload, list) or not payload:
            continue

        round_payload = payload[0]
        if not isinstance(round_payload, dict):
            continue

        meta_round_id, supply_list, traces = _extract_round_data(round_payload, model_map)
        _plot_meta_round(exp_dir, output_dir, meta_round_id, supply_list, traces)


if __name__ == "__main__":
    main()