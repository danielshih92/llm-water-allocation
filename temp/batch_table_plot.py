#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from wac_programmatic import default_agent_profiles


def _parse_percent(text: str) -> float:
    try:
        return float(str(text).strip().replace("%", ""))
    except Exception:
        return 0.0


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _parse_death_count(text: object) -> (int, int):
    death_count = 0
    round_count = 0
    parts = str(text).strip().split("/", 1)
    if len(parts) == 2:
        try:
            death_count = int(parts[0])
            round_count = int(parts[1])
        except Exception:
            return 0, 0
    return death_count, round_count


def _collect_agent_average_files(batch_dir: str) -> List[str]:
    paths = []
    for root, _, files in os.walk(batch_dir):
        if "agent_averages.json" not in files:
            continue
        paths.append(os.path.join(root, "agent_averages.json"))
    return sorted(paths)


def _build_role_model_rows_from_batch(batch_dir: str, agent_id: str) -> List[Dict[str, object]]:
    grouped: Dict[str, Dict[str, object]] = {}

    for summary_path in _collect_agent_average_files(batch_dir):
        try:
            with open(summary_path, "r", encoding="utf-8") as handle:
                exp_data = json.load(handle)
        except Exception:
            continue

        averages = exp_data.get("agent_averages", {})
        stats = averages.get(agent_id)
        if not isinstance(stats, dict):
            continue

        model_name = str(stats.get("model_used", "Unknown Model"))
        death_count, round_count = _parse_death_count(stats.get("death_count", "0/0"))
        if round_count <= 0:
            continue

        entry = grouped.setdefault(
            model_name,
            {
                "deaths": 0,
                "rounds": 0,
                "weighted_sums": {
                    "Survival Days": 0.0,
                    "Daily Bid": 0.0,
                    "Runtime Success (%)": 0.0,
                    "Code Complexity": 0.0,
                },
            },
        )

        entry["deaths"] += death_count
        entry["rounds"] += round_count
        entry["weighted_sums"]["Survival Days"] += float(stats.get("avg_survival_days", 0.0)) * round_count
        entry["weighted_sums"]["Daily Bid"] += float(stats.get("avg_daily_bid", 0.0)) * round_count
        entry["weighted_sums"]["Runtime Success (%)"] += float(stats.get("avg_runtime_success", 0.0)) * round_count * 100.0
        entry["weighted_sums"]["Code Complexity"] += float(stats.get("avg_strategy_complexity", 0.0)) * round_count

    rows = []
    for model_name, entry in grouped.items():
        rounds = entry["rounds"]
        if rounds <= 0:
            continue
        rows.append(
            {
                "Model": model_name,
                "Survival Days": entry["weighted_sums"]["Survival Days"] / rounds,
                "Mortality Rate (%)": f"{(entry['deaths'] / rounds) * 100:.1f}%",
                "Daily Bid": entry["weighted_sums"]["Daily Bid"] / rounds,
                "Runtime Success (%)": entry["weighted_sums"]["Runtime Success (%)"] / rounds,
                "Code Complexity": entry["weighted_sums"]["Code Complexity"] / rounds,
                "_mortality_numeric": (entry["deaths"] / rounds) * 100.0,
            }
        )

    return rows


def _build_model_rows(perf_by_model: Dict[str, Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for model_name, stats in perf_by_model.items():
        mortality_str = str(stats.get("global_mortality_rate", "0%"))
        rows.append(
            {
                "Model": model_name,
                "Survival Days": float(stats.get("grand_avg_survival_days", 0.0)),
                "Mortality Rate (%)": mortality_str,
                "Daily Bid": float(stats.get("grand_avg_daily_bid", 0.0)),
                "Runtime Success (%)": float(stats.get("grand_avg_runtime_success", 0.0)) * 100.0,
                "Code Complexity": float(stats.get("grand_avg_strategy_complexity", 0.0)),
                "_mortality_numeric": _parse_percent(mortality_str),
            }
        )
    return rows


def _build_role_rows(perf_by_agent: Dict[str, Dict[str, object]]) -> List[Dict[str, object]]:
    profile_map = {
        profile.agent_id: profile
        for profile in default_agent_profiles()
    }
    rows = []
    for agent_id, stats in perf_by_agent.items():
        mortality_str = str(stats.get("global_mortality_rate", "0%"))
        profile = profile_map.get(agent_id)
        if profile is None:
            role_label = agent_id
        else:
            role_label = f"{agent_id}({int(profile.daily_salary)},{int(profile.water_requirement)})"
        rows.append(
            {
                "Role": role_label,
                "Survival Days": float(stats.get("grand_avg_survival_days", 0.0)),
                "Mortality Rate (%)": mortality_str,
                "Daily Bid": float(stats.get("grand_avg_daily_bid", 0.0)),
                "Runtime Success (%)": float(stats.get("grand_avg_runtime_success", 0.0)) * 100.0,
                "Code Complexity": float(stats.get("grand_avg_strategy_complexity", 0.0)),
                "_mortality_numeric": _parse_percent(mortality_str),
            }
        )
    return rows


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    table = df.copy()
    table["Survival Days"] = table["Survival Days"].map(lambda v: f"{v:.2f}")
    table["Daily Bid"] = table["Daily Bid"].map(lambda v: f"{v:.2f}")
    table["Code Complexity"] = table["Code Complexity"].map(lambda v: f"{v:.2f}")
    table["Runtime Success (%)"] = table["Runtime Success (%)"].map(lambda v: f"{v:.2f}%")
    return table


def _save_markdown_table(df: pd.DataFrame, path: str) -> None:
    headers = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        values = [str(row[col]) for col in headers]
        lines.append("| " + " | ".join(values) + " |")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _estimate_col_widths(df: pd.DataFrame) -> List[float]:
    lengths = []
    for col in df.columns:
        max_len = max([len(str(col))] + [len(str(v)) for v in df[col].tolist()])
        lengths.append(max_len)
    total = float(sum(lengths)) or 1.0
    return [max(0.08, l / total) for l in lengths]


def _save_table_png(df: pd.DataFrame, path: str, title: str = "Model-Level Performance Summary") -> None:
    fig_height = max(2.5, 0.45 * (len(df) + 1))
    fig, ax = plt.subplots(figsize=(12, fig_height))
    ax.axis("off")
    col_widths = _estimate_col_widths(df)
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.4)
    ax.set_title(title, fontsize=12, pad=12)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


def _bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    path: str,
    sort_by: str,
    ascending: bool,
    y_label: str = None,
) -> None:
    data = df.sort_values(sort_by, ascending=ascending)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(data[x], data[y])
    ax.set_title(title)
    ax.set_ylabel(y_label or y)
    ax.set_xlabel("Model")
    ax.tick_params(axis="x", rotation=30)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


def _boxes_overlap(a, b, pad: float = 2.0) -> bool:
    return not (
        a.x1 + pad < b.x0
        or a.x0 - pad > b.x1
        or a.y1 + pad < b.y0
        or a.y0 - pad > b.y1
    )


def _annotate_points(ax, df: pd.DataFrame, x_col: str, y_col: str, label_col: str = "Model") -> None:
    offsets = [
        (8, 8), (8, -8), (-8, 8), (-8, -8),
        (12, 0), (-12, 0), (0, 12), (0, -12),
        (16, 8), (16, -8), (-16, 8), (-16, -8),
        (20, 0), (-20, 0), (0, 16), (0, -16),
    ]
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    placed = []

    for _, row in df.sort_values([x_col, y_col]).iterrows():
        label = row[label_col]
        x_val = row[x_col]
        y_val = row[y_col]
        annotation = None
        for offset in offsets:
            annotation = ax.annotate(
                label,
                (x_val, y_val),
                textcoords="offset points",
                xytext=offset,
                ha="left",
                va="bottom",
            )
            fig.canvas.draw()
            bbox = annotation.get_window_extent(renderer=renderer)
            if all(not _boxes_overlap(bbox, other) for other in placed):
                placed.append(bbox)
                break
            annotation.remove()
            annotation = None
        if annotation is None:
            annotation = ax.annotate(
                label,
                (x_val, y_val),
                textcoords="offset points",
                xytext=(12, 12),
                ha="left",
                va="bottom",
            )
            fig.canvas.draw()
            bbox = annotation.get_window_extent(renderer=renderer)
            placed.append(bbox)


def _scatter_with_labels(df: pd.DataFrame, x: str, y: str, title: str, path: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df[x], df[y])
    _annotate_points(ax, df, x, y)
    ax.set_title(title)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


def _bubble_chart(df: pd.DataFrame, path: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    sizes = df["Runtime Success (%)"] * 8.0
    ax.scatter(df["Code Complexity"], df["Survival Days"], s=sizes, alpha=0.6)
    _annotate_points(ax, df, "Code Complexity", "Survival Days")
    ax.set_title("Code Complexity, Survival, and Runtime Reliability")
    ax.set_xlabel("Code Complexity")
    ax.set_ylabel("Survival Days")
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


def _save_model_comparison_table(rows: List[Dict[str, object]], output_dir: str, file_stem: str, title: str) -> None:
    if not rows:
        return

    df = pd.DataFrame(rows)
    df_sorted = df.sort_values("Survival Days", ascending=False)
    table_df = df_sorted[[
        "Model",
        "Survival Days",
        "Mortality Rate (%)",
        "Daily Bid",
        "Runtime Success (%)",
        "Code Complexity",
    ]]
    formatted_table = _format_table(table_df)
    _save_markdown_table(formatted_table, os.path.join(output_dir, f"{file_stem}.md"))
    _save_table_png(formatted_table, os.path.join(output_dir, f"{file_stem}.png"), title=title)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build model-level summary tables and figures.")
    parser.add_argument("--log-dir", type=str, default="log", help="Root log directory.")
    parser.add_argument("--batch", type=str, required=True, help="Batch folder name (e.g., batch_004).")
    parser.add_argument("--output-dir", type=str, default=None, help="Output folder (defaults to batch/output_analysis).")
    args = parser.parse_args()

    batch_dir = os.path.join(args.log_dir, args.batch)
    report_path = os.path.join(batch_dir, "global_batch_report.json")
    if not os.path.isfile(report_path):
        raise SystemExit(f"global_batch_report.json not found: {report_path}")

    output_dir = args.output_dir or os.path.join(batch_dir, "output_analysis")
    _ensure_dir(output_dir)

    with open(report_path, "r", encoding="utf-8") as handle:
        report = json.load(handle)

    perf_by_model = report.get("performance_by_model", {})
    rows = _build_model_rows(perf_by_model)
    if not rows:
        raise SystemExit("No model-level metrics found in global_batch_report.json")

    df = pd.DataFrame(rows)

    df_sorted = df.sort_values("Survival Days", ascending=False)
    table_df = df_sorted[[
        "Model",
        "Survival Days",
        "Mortality Rate (%)",
        "Daily Bid",
        "Runtime Success (%)",
        "Code Complexity",
    ]]

    formatted_table = _format_table(table_df)

    _save_markdown_table(formatted_table, os.path.join(output_dir, "model_summary_table.md"))
    _save_table_png(formatted_table, os.path.join(output_dir, "model_summary_table.png"))

    _bar_chart(
        df,
        x="Model",
        y="Survival Days",
        title="Average Survival Days by Model",
        path=os.path.join(output_dir, "fig_survival_days_by_model.png"),
        sort_by="Survival Days",
        ascending=False,
    )

    _bar_chart(
        df,
        x="Model",
        y="_mortality_numeric",
        title="Mortality Rate by Model",
        path=os.path.join(output_dir, "fig_mortality_rate_by_model.png"),
        sort_by="_mortality_numeric",
        ascending=True,
        y_label="Mortality Rate (%)",
    )

    _scatter_with_labels(
        df,
        x="Daily Bid",
        y="Survival Days",
        title="Daily Bid vs. Survival Days",
        path=os.path.join(output_dir, "fig_daily_bid_vs_survival.png"),
    )

    _scatter_with_labels(
        df,
        x="Code Complexity",
        y="Survival Days",
        title="Code Complexity vs. Survival Days",
        path=os.path.join(output_dir, "fig_complexity_vs_survival.png"),
    )

    _scatter_with_labels(
        df,
        x="Code Complexity",
        y="Runtime Success (%)",
        title="Code Complexity vs. Runtime Success",
        path=os.path.join(output_dir, "fig_complexity_vs_runtime_success.png"),
    )

    _bubble_chart(
        df,
        path=os.path.join(output_dir, "fig_complexity_survival_runtime_bubble.png"),
    )

    perf_by_agent = report.get("performance_by_agent", {})
    role_rows = _build_role_rows(perf_by_agent)
    if role_rows:
        role_df = pd.DataFrame(role_rows)
        role_df_sorted = role_df.sort_values("Survival Days", ascending=False)
        role_table_df = role_df_sorted[[
            "Role",
            "Survival Days",
            "Mortality Rate (%)",
            "Daily Bid",
            "Runtime Success (%)",
            "Code Complexity",
        ]]
        formatted_role_table = _format_table(role_table_df)
        _save_markdown_table(formatted_role_table, os.path.join(output_dir, "role_summary_table.md"))
        _save_table_png(formatted_role_table, os.path.join(output_dir, "role_summary_table.png"), title="Role-Level Performance Summary")

    alex_rows = _build_role_model_rows_from_batch(batch_dir, "Alex")
    _save_model_comparison_table(alex_rows, output_dir, "Alex_table", "Model Performance When Selected as Alex")

    eric_rows = _build_role_model_rows_from_batch(batch_dir, "Eric")
    _save_model_comparison_table(eric_rows, output_dir, "Eric_table", "Model Performance When Selected as Eric")


if __name__ == "__main__":
    main()
