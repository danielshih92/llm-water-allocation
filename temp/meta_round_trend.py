#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple


META_ROUND_PATTERN = re.compile(r"^meta_round_(\d+)\.json$")


def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().upper() == "N/A":
            return default
        return float(value)
    except Exception:
        return default


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_log_dir(log_dir: str) -> str:
    if os.path.isabs(log_dir):
        return log_dir

    cwd_candidate = os.path.abspath(log_dir)
    if os.path.isdir(cwd_candidate):
        return cwd_candidate

    project_candidate = os.path.join(_project_root(), log_dir)
    if os.path.isdir(project_candidate):
        return project_candidate

    return cwd_candidate


def _resolve_batch_dir(log_dir: str, batch: str) -> Tuple[str, str]:
    if os.path.isabs(batch):
        return os.path.basename(batch.rstrip(os.sep)), batch

    direct = os.path.abspath(batch)
    if os.path.isdir(direct):
        return os.path.basename(direct.rstrip(os.sep)), direct

    return batch, os.path.join(log_dir, batch)


def _iter_meta_round_files(exp_dir: str) -> Iterable[Tuple[int, str]]:
    for name in sorted(os.listdir(exp_dir)):
        match = META_ROUND_PATTERN.match(name)
        if not match:
            continue

        path = os.path.join(exp_dir, name)
        if os.path.isfile(path):
            yield int(match.group(1)), path


def _load_round_payload(path: str) -> Optional[Dict[str, object]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None

    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        return None

    return payload[0]


def _collect_agent_records(batch_dir: str) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []

    for entry in sorted(os.listdir(batch_dir)):
        if not entry.startswith("exp_"):
            continue

        exp_dir = os.path.join(batch_dir, entry)
        if not os.path.isdir(exp_dir):
            continue

        for meta_round_id, meta_path in _iter_meta_round_files(exp_dir):
            round_payload = _load_round_payload(meta_path)
            if not round_payload:
                continue

            record_outcome_valid = int(_safe_float(round_payload.get("outcome_valid"), 0) or 0)
            environment = round_payload.get("environment")
            if not isinstance(environment, dict):
                environment = {}

            agents = round_payload.get("agents")
            if not isinstance(agents, list):
                continue

            for agent in agents:
                if not isinstance(agent, dict):
                    continue

                generation_stats = agent.get("generation_stats")
                if not isinstance(generation_stats, dict):
                    generation_stats = {}

                admitted = int(
                    _safe_float(agent.get("admitted", generation_stats.get("admitted", 0)), 0)
                    or 0
                )
                outcome_valid = int(
                    _safe_float(agent.get("outcome_valid", record_outcome_valid), record_outcome_valid)
                    or 0
                )

                metrics = agent.get("metrics")
                if not isinstance(metrics, dict):
                    metrics = None

                performance_valid = admitted == 1 and outcome_valid == 1 and metrics is not None
                final_hp = _safe_float(metrics.get("final_hp"), None) if metrics else None
                survival_days = _safe_float(metrics.get("survival_days"), None) if metrics else None
                strategy_complexity = (
                    _safe_float(metrics.get("strategy_complexity"), None)
                    if metrics
                    else None
                )

                records.append(
                    {
                        "exp_id": entry,
                        "meta_round_id": meta_round_id,
                        "agent_id": agent.get("agent_id", ""),
                        "performance_valid": performance_valid,
                        "survival_days": survival_days,
                        "final_hp": final_hp,
                        "strategy_complexity": strategy_complexity,
                        "seed": environment.get("seed"),
                    }
                )

    return records


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _summarize_round(records: List[Dict[str, object]]) -> Dict[str, object]:
    valid = [row for row in records if bool(row.get("performance_valid", False))]
    survival_values = [
        _safe_float(row.get("survival_days"), None)
        for row in valid
        if _safe_float(row.get("survival_days"), None) is not None
    ]
    complexity_values = [
        _safe_float(row.get("strategy_complexity"), None)
        for row in valid
        if _safe_float(row.get("strategy_complexity"), None) is not None
    ]
    deaths = sum(
        1
        for row in valid
        if _safe_float(row.get("final_hp"), 1.0) is not None
        and _safe_float(row.get("final_hp"), 1.0) <= 0
    )

    mortality_rate = None
    if valid:
        mortality_rate = deaths / len(valid) * 100.0

    return {
        "avg_survival": _mean(survival_values),
        "avg_complexity": _mean(complexity_values),
        "mortality_rate": mortality_rate,
        "valid_agents": len(valid),
        "total_agents": len(records),
    }


def _infer_present_name(batch_dir: str, batch_name: str) -> str:
    for entry in sorted(os.listdir(batch_dir)):
        if not entry.startswith("exp_"):
            continue

        config_path = os.path.join(batch_dir, entry, "backend_config.json")
        if not os.path.isfile(config_path):
            continue

        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        models = []
        for spec in data.values():
            if isinstance(spec, dict) and spec.get("model"):
                models.append(str(spec.get("model")))

        unique_models = sorted(set(models))
        if len(unique_models) == 1:
            return unique_models[0]
        if len(unique_models) > 1:
            return "mixed_models"

    return batch_name


def _format_number(value, decimals: int) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _format_percent(value, decimals: int) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def _format_delta(value) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}"


def _build_rows(
    grouped_rounds: Dict[str, Dict[int, List[Dict[str, object]]]],
    max_round: int = 3,
) -> Tuple[List[Dict[str, str]], Dict[str, Dict[int, Dict[str, object]]]]:
    summaries: Dict[str, Dict[int, Dict[str, object]]] = {}

    for label, round_records in grouped_rounds.items():
        summaries[label] = {}
        for round_id, records in round_records.items():
            summaries[label][round_id] = _summarize_round(records)

    rows: List[Dict[str, str]] = []
    labels = sorted(summaries)
    for label in labels:
        summary = summaries[label]
        mr1_survival = summary.get(1, {}).get("avg_survival")
        mr2_survival = summary.get(2, {}).get("avg_survival")
        mr3_survival = summary.get(3, {}).get("avg_survival")
        mr1_complexity = summary.get(1, {}).get("avg_complexity")
        mr2_complexity = summary.get(2, {}).get("avg_complexity")
        mr3_complexity = summary.get(3, {}).get("avg_complexity")

        rows.append(
            {
                "Model": label,
                "MR1 Survival": _format_number(mr1_survival, 2),
                "MR2 Survival": _format_number(mr2_survival, 2),
                "MR3 Survival": _format_number(mr3_survival, 2),
                "MR2-MR1": _format_delta(
                    None if mr1_survival is None or mr2_survival is None else mr2_survival - mr1_survival
                ),
                "MR3-MR1": _format_delta(
                    None if mr1_survival is None or mr3_survival is None else mr3_survival - mr1_survival
                ),
                "MR1 Mort.": _format_percent(summary.get(1, {}).get("mortality_rate"), 1),
                "MR2 Mort.": _format_percent(summary.get(2, {}).get("mortality_rate"), 1),
                "MR3 Mort.": _format_percent(summary.get(3, {}).get("mortality_rate"), 1),
                "MR1 Complexity": _format_number(mr1_complexity, 1),
                "MR2 Complexity": _format_number(mr2_complexity, 1),
                "MR3 Complexity": _format_number(mr3_complexity, 1),
            }
        )

    average_rounds: Dict[int, List[Dict[str, object]]] = defaultdict(list)
    for round_records in grouped_rounds.values():
        for round_id, records in round_records.items():
            average_rounds[round_id].extend(records)

    if len(labels) > 1:
        average_summary = {
            round_id: _summarize_round(records)
            for round_id, records in average_rounds.items()
        }
        summaries["Average"] = average_summary

        mr1_survival = average_summary.get(1, {}).get("avg_survival")
        mr2_survival = average_summary.get(2, {}).get("avg_survival")
        mr3_survival = average_summary.get(3, {}).get("avg_survival")
        mr1_complexity = average_summary.get(1, {}).get("avg_complexity")
        mr2_complexity = average_summary.get(2, {}).get("avg_complexity")
        mr3_complexity = average_summary.get(3, {}).get("avg_complexity")
        rows.append(
            {
                "Model": "Average",
                "MR1 Survival": _format_number(mr1_survival, 2),
                "MR2 Survival": _format_number(mr2_survival, 2),
                "MR3 Survival": _format_number(mr3_survival, 2),
                "MR2-MR1": _format_delta(
                    None if mr1_survival is None or mr2_survival is None else mr2_survival - mr1_survival
                ),
                "MR3-MR1": _format_delta(
                    None if mr1_survival is None or mr3_survival is None else mr3_survival - mr1_survival
                ),
                "MR1 Mort.": _format_percent(average_summary.get(1, {}).get("mortality_rate"), 1),
                "MR2 Mort.": _format_percent(average_summary.get(2, {}).get("mortality_rate"), 1),
                "MR3 Mort.": _format_percent(average_summary.get(3, {}).get("mortality_rate"), 1),
                "MR1 Complexity": _format_number(mr1_complexity, 1),
                "MR2 Complexity": _format_number(mr2_complexity, 1),
                "MR3 Complexity": _format_number(mr3_complexity, 1),
            }
        )

    return rows, summaries


def _write_csv(rows: List[Dict[str, str]], path: str) -> None:
    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _write_detail_csv(
    summaries: Dict[str, Dict[int, Dict[str, object]]],
    path: str,
) -> None:
    rows: List[Dict[str, str]] = []
    for label in sorted(summaries):
        if label == "Average":
            continue

        for round_id in sorted(summaries[label]):
            summary = summaries[label][round_id]
            rows.append(
                {
                    "Model": label,
                    "Meta Round": f"MR{round_id}",
                    "Avg Survival": _format_number(summary.get("avg_survival"), 4),
                    "Mortality Rate": _format_percent(summary.get("mortality_rate"), 4),
                    "Avg Complexity": _format_number(summary.get("avg_complexity"), 4),
                    "Valid Agents": str(summary.get("valid_agents", 0)),
                    "Total Agents": str(summary.get("total_agents", 0)),
                }
            )

    _write_csv(rows, path)


def _print_valid_agent_totals(summaries: Dict[str, Dict[int, Dict[str, object]]]) -> None:
    print("\nValid agent totals:")
    for label in sorted(summaries):
        if label == "Average":
            continue

        parts = []
        total_valid = 0
        total_agents = 0

        for round_id in sorted(summaries[label]):
            summary = summaries[label][round_id]
            valid_agents = int(summary.get("valid_agents", 0) or 0)
            agents = int(summary.get("total_agents", 0) or 0)
            total_valid += valid_agents
            total_agents += agents
            parts.append(f"MR{round_id}: {valid_agents}/{agents}")

        print(f"- {label}: total {total_valid}/{total_agents} valid agents ({', '.join(parts)})")


def _series_style(index: int) -> Dict[str, object]:
    markers = ["o", "s", "^", "D", "P", "X", "v", "*"]
    return {
        "marker": markers[index % len(markers)],
        "linestyle": "-",
    }


def _offset_x_values(round_ids: List[int], index: int, series_count: int) -> List[float]:
    if series_count <= 1:
        return [float(round_id) for round_id in round_ids]

    offset_step = 0.005
    offset = (index - ((series_count - 1) / 2.0)) * offset_step
    return [float(round_id) + offset for round_id in round_ids]


def _write_trend_plot(
    summaries: Dict[str, Dict[int, Dict[str, object]]],
    path: str,
    title: str,
) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"Skipping trend plot because matplotlib is unavailable: {exc}")
        return False

    labels = [label for label in sorted(summaries) if label != "Average"]
    if not labels:
        return False

    round_ids = sorted(
        {
            round_id
            for label in labels
            for round_id in summaries.get(label, {})
        }
    )
    round_ids = [round_id for round_id in round_ids if 1 <= round_id <= 3]
    if not round_ids:
        return False

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))

    for index, label in enumerate(labels):
        style = _series_style(index)
        x_values = _offset_x_values(round_ids, index, len(labels))
        survival_values = [
            summaries[label].get(round_id, {}).get("avg_survival")
            for round_id in round_ids
        ]
        mortality_values = [
            summaries[label].get(round_id, {}).get("mortality_rate")
            for round_id in round_ids
        ]
        axes[0].plot(
            x_values,
            survival_values,
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=2,
            label=label,
        )
        axes[1].plot(
            x_values,
            mortality_values,
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=2,
            label=label,
        )

    if "Average" in summaries:
        average_survival = [
            summaries["Average"].get(round_id, {}).get("avg_survival")
            for round_id in round_ids
        ]
        average_mortality = [
            summaries["Average"].get(round_id, {}).get("mortality_rate")
            for round_id in round_ids
        ]
        axes[0].plot(
            round_ids,
            average_survival,
            marker="o",
            linewidth=3.5,
            linestyle="--",
            color="black",
            label="Average",
        )
        axes[1].plot(
            round_ids,
            average_mortality,
            marker="o",
            linewidth=3.5,
            linestyle="--",
            color="black",
            label="Average",
        )

    axes[0].set_title("Average Survival")
    axes[0].set_xlabel("Meta Round")
    axes[0].set_ylabel("Survival Days")
    axes[0].set_xticks(round_ids)
    axes[0].grid(True, alpha=0.25)

    axes[1].set_title("Mortality Rate")
    axes[1].set_xlabel("Meta Round")
    axes[1].set_ylabel("Mortality (%)")
    axes[1].set_xticks(round_ids)
    axes[1].grid(True, alpha=0.25)

    handles, plot_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, plot_labels, loc="lower center", ncol=min(3, len(plot_labels)))
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=(0, 0.12, 1, 0.92))
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return True


def _write_complexity_plot(
    summaries: Dict[str, Dict[int, Dict[str, object]]],
    path: str,
    title: str,
) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"Skipping complexity plot because matplotlib is unavailable: {exc}")
        return False

    labels = [label for label in sorted(summaries) if label != "Average"]
    if not labels:
        return False

    round_ids = sorted(
        {
            round_id
            for label in labels
            for round_id in summaries.get(label, {})
        }
    )
    round_ids = [round_id for round_id in round_ids if 1 <= round_id <= 3]
    if not round_ids:
        return False

    fig, ax = plt.subplots(figsize=(7.2, 4.4))

    for index, label in enumerate(labels):
        style = _series_style(index)
        x_values = _offset_x_values(round_ids, index, len(labels))
        complexity_values = [
            summaries[label].get(round_id, {}).get("avg_complexity")
            for round_id in round_ids
        ]
        ax.plot(
            x_values,
            complexity_values,
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=2,
            label=label,
        )

    if "Average" in summaries:
        average_complexity = [
            summaries["Average"].get(round_id, {}).get("avg_complexity")
            for round_id in round_ids
        ]
        ax.plot(
            round_ids,
            average_complexity,
            marker="o",
            linewidth=3.5,
            linestyle="--",
            color="black",
            label="Average",
        )

    ax.set_title("Code Complexity")
    ax.set_xlabel("Meta Round")
    ax.set_ylabel("Average Strategy Complexity")
    ax.set_xticks(round_ids)
    ax.grid(True, alpha=0.25)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=min(3, len(labels) + 1))
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=(0, 0.12, 1, 0.92))
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return True


def _slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    slug = slug.strip("_")
    return slug or "meta_round_trend"


def _validate_present_names(batch_count: int, present_names: Optional[List[str]]) -> List[Optional[str]]:
    if not present_names:
        return [None] * batch_count

    if len(present_names) != batch_count:
        raise SystemExit(
            "--present-name must be provided once per --batch when used "
            f"({len(present_names)} names for {batch_count} batches)."
        )

    return present_names


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build a meta-round trend table and plot from up to five batch folders. "
            "Use the same --present-name for multiple seed batches to aggregate them."
        )
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="log",
        help="Root log directory. Defaults to PROJECT_ROOT/log when run outside Alympics/.",
    )
    parser.add_argument(
        "--batch",
        action="append",
        required=True,
        help="Batch folder name or path. Repeat up to five times.",
    )
    parser.add_argument(
        "--present-name",
        action="append",
        default=None,
        help=(
            "Name shown in the Model column for the corresponding --batch. "
            "Repeat once per batch. Reusing a name aggregates those batches."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output folder. Defaults to PROJECT_ROOT/compare_result/meta_round.",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default=None,
        help="Output filename prefix. Defaults to meta_round_trend_<first_present_name_or_batch>.",
    )
    args = parser.parse_args()

    if len(args.batch) > 5:
        raise SystemExit("--batch supports at most five batch folders.")

    log_dir = _resolve_log_dir(args.log_dir)
    present_names = _validate_present_names(len(args.batch), args.present_name)

    grouped_rounds: Dict[str, Dict[int, List[Dict[str, object]]]] = defaultdict(lambda: defaultdict(list))
    batch_labels: List[str] = []

    for batch_arg, present_name in zip(args.batch, present_names):
        batch_name, batch_dir = _resolve_batch_dir(log_dir, batch_arg)
        if not os.path.isdir(batch_dir):
            raise SystemExit(f"Batch folder not found: {batch_dir}")

        label = present_name or _infer_present_name(batch_dir, batch_name)
        batch_labels.append(label)

        records = _collect_agent_records(batch_dir)
        if not records:
            print(f"[WARN] No meta-round agent records found in {batch_dir}")
            continue

        for record in records:
            round_id = int(record.get("meta_round_id", 0) or 0)
            grouped_rounds[label][round_id].append(record)

    if not grouped_rounds:
        raise SystemExit("No comparable meta-round records found.")

    rows, summaries = _build_rows(grouped_rounds)
    if not rows:
        raise SystemExit("No summary rows could be built.")

    output_dir = args.output_dir or os.path.join(_project_root(), "compare_result", "meta_round")
    _ensure_dir(output_dir)

    default_prefix_source = batch_labels[0] if batch_labels else "meta_round_trend"
    output_prefix = args.output_prefix or f"meta_round_trend_{_slugify(default_prefix_source)}"
    output_prefix = _slugify(output_prefix)

    csv_path = os.path.join(output_dir, f"{output_prefix}.csv")
    detail_csv_path = os.path.join(output_dir, f"{output_prefix}_details.csv")
    png_path = os.path.join(output_dir, f"{output_prefix}.png")
    complexity_png_path = os.path.join(output_dir, f"{output_prefix}_complexity.png")

    _write_csv(rows, csv_path)
    _write_detail_csv(summaries, detail_csv_path)
    wrote_png = _write_trend_plot(summaries, png_path, "Meta-Round Trend")
    wrote_complexity_png = _write_complexity_plot(
        summaries,
        complexity_png_path,
        "Meta-Round Code Complexity",
    )
    _print_valid_agent_totals(summaries)

    print(f"Wrote summary CSV: {csv_path}")
    print(f"Wrote detail CSV: {detail_csv_path}")
    if wrote_png:
        print(f"Wrote trend PNG: {png_path}")
    if wrote_complexity_png:
        print(f"Wrote complexity PNG: {complexity_png_path}")


if __name__ == "__main__":
    main()
