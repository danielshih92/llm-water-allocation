#!/usr/bin/env python3
import argparse
from collections import defaultdict
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


def _aggregate_model_stats_from_batch(batch_dir: str) -> Dict[str, Dict[str, float]]:
    grouped: Dict[str, Dict[str, float]] = {}

    for summary_path in _collect_agent_average_files(batch_dir):
        exp_dir = os.path.dirname(summary_path)
        label_map = _load_backend_label_map(exp_dir)

        try:
            with open(summary_path, "r", encoding="utf-8") as handle:
                exp_data = json.load(handle)
        except Exception:
            continue

        averages = exp_data.get("agent_averages", {})
        if not isinstance(averages, dict):
            continue

        for role_name, stats in averages.items():
            if not isinstance(stats, dict):
                continue

            raw_model_name = str(stats.get("model_used", "Unknown Model"))
            model_name = label_map.get(role_name, raw_model_name)

            attempted_rounds = int(_safe_float(stats.get("attempted_meta_rounds"), 0) or 0)
            valid_rounds = int(_safe_float(stats.get("valid_meta_rounds"), 0) or 0)
            death_count, _ = _parse_death_count(stats.get("death_count", "0/0"))

            item = grouped.setdefault(
                model_name,
                {
                    "attempted_rounds": 0.0,
                    "valid_rounds": 0.0,
                    "deaths": 0.0,
                    "survival_weighted_sum": 0.0,
                    "daily_bid_weighted_sum": 0.0,
                    "complexity_weighted_sum": 0.0,
                    "strict_success_attempted_weighted_sum": 0.0,
                    "admission_attempted_weighted_sum": 0.0,
                    "outcome_valid_attempted_weighted_sum": 0.0,
                    "one_shot_strict_attempted_weighted_sum": 0.0,
                    "post_repair_strict_attempted_weighted_sum": 0.0,
                    "repair_used_attempted_weighted_sum": 0.0,
                    "repair_attempts_attempted_weighted_sum": 0.0,
                    "json_parse_fail_attempted_weighted_sum": 0.0,
                    "code_extraction_fail_attempted_weighted_sum": 0.0,
                    "one_shot_runtime_fail_attempted_weighted_sum": 0.0,
                    "admission_fail_attempted_weighted_sum": 0.0,
                },
            )

            item["attempted_rounds"] += attempted_rounds
            item["valid_rounds"] += valid_rounds
            item["deaths"] += death_count

            avg_survival_days = _safe_float(stats.get("avg_survival_days"), None)
            avg_daily_bid = _safe_float(stats.get("avg_daily_bid"), None)
            avg_strategy_complexity = _safe_float(stats.get("avg_strategy_complexity"), None)

            if avg_survival_days is not None and valid_rounds > 0:
                item["survival_weighted_sum"] += avg_survival_days * valid_rounds
            if avg_daily_bid is not None and valid_rounds > 0:
                item["daily_bid_weighted_sum"] += avg_daily_bid * valid_rounds
            if avg_strategy_complexity is not None and valid_rounds > 0:
                item["complexity_weighted_sum"] += avg_strategy_complexity * valid_rounds

            if attempted_rounds > 0:
                item["strict_success_attempted_weighted_sum"] += (_safe_float(stats.get("avg_strict_success_rate"), 0.0) or 0.0) * attempted_rounds
                item["admission_attempted_weighted_sum"] += (_safe_float(stats.get("admission_rate"), 0.0) or 0.0) * attempted_rounds
                item["outcome_valid_attempted_weighted_sum"] += (_safe_float(stats.get("outcome_valid_rate"), 0.0) or 0.0) * attempted_rounds
                item["one_shot_strict_attempted_weighted_sum"] += (_safe_float(stats.get("one_shot_strict_success_rate"), 0.0) or 0.0) * attempted_rounds
                item["post_repair_strict_attempted_weighted_sum"] += (_safe_float(stats.get("post_repair_strict_success_rate"), 0.0) or 0.0) * attempted_rounds
                item["repair_used_attempted_weighted_sum"] += (_safe_float(stats.get("repair_used_rate"), 0.0) or 0.0) * attempted_rounds
                item["repair_attempts_attempted_weighted_sum"] += (_safe_float(stats.get("avg_repair_attempts"), 0.0) or 0.0) * attempted_rounds

                json_parse_fail_rate = _safe_float(stats.get("json_parse_fail_rate"), 0.0) or 0.0
                one_shot_code_extracted_rate = _safe_float(stats.get("one_shot_code_extracted_rate"), 0.0) or 0.0
                one_shot_runtime_success_rate = _safe_float(stats.get("one_shot_runtime_success_rate"), 0.0) or 0.0
                admission_rate = _safe_float(stats.get("admission_rate"), 0.0) or 0.0

                item["json_parse_fail_attempted_weighted_sum"] += json_parse_fail_rate * attempted_rounds
                item["code_extraction_fail_attempted_weighted_sum"] += (1.0 - one_shot_code_extracted_rate) * attempted_rounds
                item["one_shot_runtime_fail_attempted_weighted_sum"] += (1.0 - one_shot_runtime_success_rate) * attempted_rounds
                item["admission_fail_attempted_weighted_sum"] += (1.0 - admission_rate) * attempted_rounds

    return grouped


def _load_backend_label_map(exp_dir: str) -> Dict[str, str]:
    backend_path = os.path.join(exp_dir, "backend_config.json")
    if not os.path.isfile(backend_path):
        return {}

    try:
        with open(backend_path, "r", encoding="utf-8") as handle:
            backend_cfg = json.load(handle)
    except Exception:
        return {}

    if not isinstance(backend_cfg, dict):
        return {}

    roles = _get_agent_profiles()
    model_by_role: Dict[str, str] = {}

    for role_name in roles:
        role_cfg = backend_cfg.get(role_name)
        if not isinstance(role_cfg, dict):
            continue
        model_name = str(role_cfg.get("model", "")).strip()
        if model_name:
            model_by_role[role_name] = model_name

    if not model_by_role:
        return {}

    total_counts: Dict[str, int] = defaultdict(int)
    for model_name in model_by_role.values():
        total_counts[model_name] += 1

    seen_counts: Dict[str, int] = defaultdict(int)
    labeled: Dict[str, str] = {}

    for role_name in roles:
        model_name = model_by_role.get(role_name)
        if not model_name:
            continue

        if total_counts[model_name] > 1:
            seen_counts[model_name] += 1
            labeled[role_name] = f"{model_name}({seen_counts[model_name]})"
        else:
            labeled[role_name] = model_name

    return labeled


def _get_agent_profiles() -> List[str]:
    return [profile.agent_id for profile in default_agent_profiles()]


def _build_role_model_metric_matrix(batch_dir: str, source_key: str) -> pd.DataFrame:
    roles = _get_agent_profiles()
    grouped: Dict[str, Dict[str, Dict[str, float]]] = {}

    for summary_path in _collect_agent_average_files(batch_dir):
        exp_dir = os.path.dirname(summary_path)
        label_map = _load_backend_label_map(exp_dir)

        try:
            with open(summary_path, "r", encoding="utf-8") as handle:
                exp_data = json.load(handle)
        except Exception:
            continue

        averages = exp_data.get("agent_averages", {})
        if not isinstance(averages, dict):
            continue

        for role_name in roles:
            stats = averages.get(role_name)
            if not isinstance(stats, dict):
                continue

            raw_model_name = str(stats.get("model_used", "Unknown Model"))
            model_name = label_map.get(role_name, raw_model_name)
            _, round_count = _parse_death_count(stats.get("death_count", "0/0"))
            if round_count <= 0:
                continue

            model_bucket = grouped.setdefault(model_name, {})
            role_bucket = model_bucket.setdefault(role_name, {"weighted_sum": 0.0, "rounds": 0.0})
            role_bucket["weighted_sum"] += float(stats.get(source_key, 0.0)) * round_count
            role_bucket["rounds"] += float(round_count)

    model_names = sorted(grouped.keys())
    matrix = pd.DataFrame(index=roles, columns=model_names, dtype=float)

    for model_name in model_names:
        for role_name in roles:
            role_bucket = grouped.get(model_name, {}).get(role_name)
            if not role_bucket or role_bucket["rounds"] <= 0:
                matrix.loc[role_name, model_name] = float("nan")
                continue
            matrix.loc[role_name, model_name] = role_bucket["weighted_sum"] / role_bucket["rounds"]

    return matrix


def _build_role_model_survival_matrix(batch_dir: str) -> pd.DataFrame:
    return _build_role_model_metric_matrix(batch_dir, "avg_survival_days")


def _build_role_model_complexity_matrix(batch_dir: str) -> pd.DataFrame:
    return _build_role_model_metric_matrix(batch_dir, "avg_strategy_complexity")


def _build_role_model_rows_from_batch(batch_dir: str, agent_id: str) -> List[Dict[str, object]]:
    grouped: Dict[str, Dict[str, object]] = {}

    for summary_path in _collect_agent_average_files(batch_dir):
        exp_dir = os.path.dirname(summary_path)
        label_map = _load_backend_label_map(exp_dir)

        try:
            with open(summary_path, "r", encoding="utf-8") as handle:
                exp_data = json.load(handle)
        except Exception:
            continue

        averages = exp_data.get("agent_averages", {})
        stats = averages.get(agent_id)
        if not isinstance(stats, dict):
            continue

        raw_model_name = str(stats.get("model_used", "Unknown Model"))
        model_name = label_map.get(agent_id, raw_model_name)
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
                    "Strict Success Rate (%)": 0.0,
                    "Code Complexity": 0.0,
                },
            },
        )

        entry["deaths"] += death_count
        entry["rounds"] += round_count
        entry["weighted_sums"]["Survival Days"] += (_safe_float(stats.get("avg_survival_days"), 0.0) or 0.0) * round_count
        entry["weighted_sums"]["Daily Bid"] += (_safe_float(stats.get("avg_daily_bid"), 0.0) or 0.0) * round_count
        entry["weighted_sums"]["Strict Success Rate (%)"] += (_safe_float(stats.get("avg_strict_success_rate"), 0.0) or 0.0) * round_count * 100.0
        entry["weighted_sums"]["Code Complexity"] += (_safe_float(stats.get("avg_strategy_complexity"), 0.0) or 0.0) * round_count

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
                "Strict Success Rate (%)": entry["weighted_sums"]["Strict Success Rate (%)"] / rounds,
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
                "Survival Days": _safe_float(stats.get("grand_avg_survival_days"), 0.0) or 0.0,
                "Mortality Rate (%)": mortality_str,
                "Daily Bid": _safe_float(stats.get("grand_avg_daily_bid"), 0.0) or 0.0,
                "Strict Success Rate (%)": (_safe_float(stats.get("grand_avg_strict_success_rate"), 0.0) or 0.0) * 100.0,
                "Code Complexity": _safe_float(stats.get("grand_avg_strategy_complexity"), 0.0) or 0.0,
                "_mortality_numeric": _parse_percent(mortality_str),
            }
        )
    return rows


def _build_model_rows_from_batch(batch_dir: str) -> List[Dict[str, object]]:
    grouped: Dict[str, Dict[str, object]] = {}

    for summary_path in _collect_agent_average_files(batch_dir):
        exp_dir = os.path.dirname(summary_path)
        label_map = _load_backend_label_map(exp_dir)

        try:
            with open(summary_path, "r", encoding="utf-8") as handle:
                exp_data = json.load(handle)
        except Exception:
            continue

        averages = exp_data.get("agent_averages", {})
        if not isinstance(averages, dict):
            continue

        for role_name, stats in averages.items():
            if not isinstance(stats, dict):
                continue

            raw_model_name = str(stats.get("model_used", "Unknown Model"))
            model_name = label_map.get(role_name, raw_model_name)

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
                        "Strict Success Rate (%)": 0.0,
                        "Code Complexity": 0.0,
                    },
                },
            )

            entry["deaths"] += death_count
            entry["rounds"] += round_count
            entry["weighted_sums"]["Survival Days"] += (_safe_float(stats.get("avg_survival_days"), 0.0) or 0.0) * round_count
            entry["weighted_sums"]["Daily Bid"] += (_safe_float(stats.get("avg_daily_bid"), 0.0) or 0.0) * round_count
            entry["weighted_sums"]["Strict Success Rate (%)"] += (_safe_float(stats.get("avg_strict_success_rate"), 0.0) or 0.0) * round_count * 100.0
            entry["weighted_sums"]["Code Complexity"] += (_safe_float(stats.get("avg_strategy_complexity"), 0.0) or 0.0) * round_count

    rows: List[Dict[str, object]] = []
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
                "Strict Success Rate (%)": entry["weighted_sums"]["Strict Success Rate (%)"] / rounds,
                "Code Complexity": entry["weighted_sums"]["Code Complexity"] / rounds,
                "_mortality_numeric": (entry["deaths"] / rounds) * 100.0,
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
                "Survival Days": _safe_float(stats.get("grand_avg_survival_days"), 0.0) or 0.0,
                "Mortality Rate (%)": mortality_str,
                "Daily Bid": _safe_float(stats.get("grand_avg_daily_bid"), 0.0) or 0.0,
                "Strict Success Rate (%)": (_safe_float(stats.get("grand_avg_strict_success_rate"), 0.0) or 0.0) * 100.0,
                "Code Complexity": _safe_float(stats.get("grand_avg_strategy_complexity"), 0.0) or 0.0,
                "_mortality_numeric": _parse_percent(mortality_str),
            }
        )
    return rows


def _format_table(df: pd.DataFrame) -> pd.DataFrame:
    table = df.copy()
    table["Survival Days"] = table["Survival Days"].map(lambda v: f"{v:.2f}")
    table["Daily Bid"] = table["Daily Bid"].map(lambda v: f"{v:.2f}")
    table["Code Complexity"] = table["Code Complexity"].map(lambda v: f"{v:.2f}")
    table["Strict Success Rate (%)"] = table["Strict Success Rate (%)"].map(lambda v: f"{v:.2f}%")
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
    sizes = df["Strict Success Rate (%)"] * 8.0
    ax.scatter(df["Code Complexity"], df["Survival Days"], s=sizes, alpha=0.6)
    _annotate_points(ax, df, "Code Complexity", "Survival Days")
    ax.set_title("Code Complexity, Survival, and Strict Success")
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
        "Strict Success Rate (%)",
        "Code Complexity",
    ]]
    formatted_table = _format_table(table_df)
    _save_markdown_table(formatted_table, os.path.join(output_dir, f"{file_stem}.md"))
    _save_table_png(formatted_table, os.path.join(output_dir, f"{file_stem}.png"), title=title)


def _save_role_model_matrix(batch_dir: str, output_dir: str, matrix: pd.DataFrame, file_stem: str, title: str, value_format: str = "{:.2f}") -> None:
    if matrix.empty:
        return

    display_df = matrix.copy()
    display_df.insert(0, "Role", display_df.index)
    for col in display_df.columns[1:]:
        display_df[col] = display_df[col].map(lambda v: "" if pd.isna(v) else value_format.format(float(v)))

    _save_markdown_table(display_df, os.path.join(output_dir, f"{file_stem}.md"))

    fig_height = max(3.5, 0.55 * (len(display_df) + 1))
    fig_width = max(10.0, 1.5 * (len(display_df.columns) + 1))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")
    col_widths = _estimate_col_widths(display_df)
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        cellLoc="center",
        loc="center",
        colWidths=col_widths,
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.35)
    ax.set_title(title, fontsize=12, pad=12)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f"{file_stem}.png"), dpi=300)
    plt.close(fig)


def _pct_or_na(value: float) -> str:
    val = _safe_float(value, None)
    if val is None:
        return "N/A"
    return f"{val * 100.0:.2f}%"


def _num_or_na(value: float, decimals: int = 2) -> str:
    val = _safe_float(value, None)
    if val is None:
        return "N/A"
    return f"{val:.{decimals}f}"


def _build_model_reliability_rows(grouped: Dict[str, Dict[str, float]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for model_name, item in sorted(grouped.items()):
        attempted = item.get("attempted_rounds", 0.0)
        if attempted <= 0:
            continue

        admission_rate = item["admission_attempted_weighted_sum"] / attempted
        outcome_valid_rate = item["outcome_valid_attempted_weighted_sum"] / attempted
        one_shot_strict_success = item["one_shot_strict_attempted_weighted_sum"] / attempted
        post_repair_strict_success = item["post_repair_strict_attempted_weighted_sum"] / attempted
        repair_used_rate = item["repair_used_attempted_weighted_sum"] / attempted
        avg_repair_attempts = item["repair_attempts_attempted_weighted_sum"] / attempted

        rows.append(
            {
                "Model": model_name,
                "Admission Rate (%)": _pct_or_na(admission_rate),
                "Outcome-valid Rate (%)": _pct_or_na(outcome_valid_rate),
                "One-shot Strict Success (%)": _pct_or_na(one_shot_strict_success),
                "Post-repair Strict Success (%)": _pct_or_na(post_repair_strict_success),
                "Repair Used (%)": _pct_or_na(repair_used_rate),
                "Avg Repair Attempts": _num_or_na(avg_repair_attempts, 4),
                "_sort": _safe_float(post_repair_strict_success, 0.0) or 0.0,
            }
        )
    return rows


def _build_model_valid_performance_rows(grouped: Dict[str, Dict[str, float]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for model_name, item in sorted(grouped.items()):
        valid_rounds = int(item.get("valid_rounds", 0.0))
        attempted = item.get("attempted_rounds", 0.0)

        if valid_rounds > 0:
            survival_days = item["survival_weighted_sum"] / valid_rounds
            daily_bid = item["daily_bid_weighted_sum"] / valid_rounds
            code_complexity = item["complexity_weighted_sum"] / valid_rounds
            mortality_rate = (item["deaths"] / valid_rounds) * 100.0
            mortality_text = f"{mortality_rate:.1f}%"
            survival_text = _num_or_na(survival_days, 2)
            daily_bid_text = _num_or_na(daily_bid, 2)
            complexity_text = _num_or_na(code_complexity, 2)
        else:
            mortality_text = "N/A"
            survival_text = "N/A"
            daily_bid_text = "N/A"
            complexity_text = "N/A"

        strict_success_rate = None
        if attempted > 0:
            strict_success_rate = item["strict_success_attempted_weighted_sum"] / attempted

        rows.append(
            {
                "Model": model_name,
                "Valid Rounds": valid_rounds,
                "Survival Days": survival_text,
                "Mortality Rate (%)": mortality_text,
                "Daily Bid": daily_bid_text,
                "Strict Success Rate (%)": _pct_or_na(strict_success_rate),
                "Code Complexity": complexity_text,
                "_sort": _safe_float(strict_success_rate, 0.0) or 0.0,
            }
        )
    return rows


def _build_model_failure_breakdown_rows(grouped: Dict[str, Dict[str, float]]) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for model_name, item in sorted(grouped.items()):
        attempted = item.get("attempted_rounds", 0.0)
        if attempted <= 0:
            continue

        rows.append(
            {
                "Model": model_name,
                "JSON Parse Fail (%)": _pct_or_na(item["json_parse_fail_attempted_weighted_sum"] / attempted),
                "Code Extraction Fail (%)": _pct_or_na(item["code_extraction_fail_attempted_weighted_sum"] / attempted),
                "One-shot Runtime Fail (%)": _pct_or_na(item["one_shot_runtime_fail_attempted_weighted_sum"] / attempted),
                "Validation/Admission Fail (%)": _pct_or_na(item["admission_fail_attempted_weighted_sum"] / attempted),
                "Repair Used (%)": _pct_or_na(item["repair_used_attempted_weighted_sum"] / attempted),
                "Post-repair Strict Success (%)": _pct_or_na(item["post_repair_strict_attempted_weighted_sum"] / attempted),
                "_sort": _safe_float(item["admission_fail_attempted_weighted_sum"] / attempted, 0.0) or 0.0,
            }
        )
    return rows


def _save_simple_table(rows: List[Dict[str, object]], output_dir: str, file_stem: str, title: str, sort_key: str = "_sort", descending: bool = True) -> None:
    if not rows:
        return

    df = pd.DataFrame(rows)
    if sort_key in df.columns:
        df = df.sort_values(sort_key, ascending=not descending)
        df = df.drop(columns=[sort_key])

    _save_markdown_table(df, os.path.join(output_dir, f"{file_stem}.md"))
    _save_table_png(df, os.path.join(output_dir, f"{file_stem}.png"), title=title)


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

    grouped = _aggregate_model_stats_from_batch(batch_dir)

    reliability_rows = _build_model_reliability_rows(grouped)
    _save_simple_table(
        reliability_rows,
        output_dir,
        "model_reliability_table",
        "Model Reliability Summary",
    )

    valid_perf_rows = _build_model_valid_performance_rows(grouped)
    _save_simple_table(
        valid_perf_rows,
        output_dir,
        "model_valid_performance_table",
        "Model Valid-only Performance Summary",
    )

    failure_rows = _build_model_failure_breakdown_rows(grouped)
    _save_simple_table(
        failure_rows,
        output_dir,
        "model_failure_breakdown_table",
        "Model Failure Breakdown Summary",
        sort_key="_sort",
        descending=True,
    )

    rows = _build_model_rows_from_batch(batch_dir)
    if not rows:
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
        "Strict Success Rate (%)",
        "Code Complexity",
    ]]

    formatted_table = _format_table(table_df)

    _save_markdown_table(formatted_table, os.path.join(output_dir, "model_summary_table.md"))
    _save_table_png(formatted_table, os.path.join(output_dir, "model_summary_table.png"), title="Model Summary Table")

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
        y="Strict Success Rate (%)",
        title="Code Complexity vs. Strict Success Rate",
        path=os.path.join(output_dir, "fig_complexity_vs_strict_success_rate.png"),
    )

    _bubble_chart(
        df,
        path=os.path.join(output_dir, "fig_complexity_survival_runtime_bubble.png"),
    )

    survival_matrix = _build_role_model_survival_matrix(batch_dir)
    _save_role_model_matrix(
        batch_dir,
        output_dir,
        survival_matrix,
        "role_model_survival_matrix",
        "Average Survival Days by Role and Model",
    )

    complexity_matrix = _build_role_model_complexity_matrix(batch_dir)
    _save_role_model_matrix(
        batch_dir,
        output_dir,
        complexity_matrix,
        "role_model_complexity_matrix",
        "Average Code Complexity by Role and Model",
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
            "Strict Success Rate (%)",
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
