import argparse
import ast
import csv
import json
import math
import re
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


AGENTS = ["Alex", "Bob", "Cindy", "David", "Eric"]
OUTPUT_DIR_NAME = "extra_plots"


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def extract_number(text: str) -> int:
    match = re.search(r"(\d+)", text)

    if match is None:
        return -1

    return int(match.group(1))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_backend_config(exp_dir: Path) -> Dict[str, Dict[str, Any]]:
    candidate_paths = [
        exp_dir / "backend_config.json",
        exp_dir.parent / "backend_config.json",
    ]

    for path in candidate_paths:
        if path.exists():
            data = load_json(path)

            if isinstance(data, dict):
                return data

    return {}


def attach_model_info_to_rows(
    rows: List[Dict[str, Any]],
    backend_config: Dict[str, Dict[str, Any]],
) -> None:
    for row in rows:
        agent_id = str(row.get("agent_id", "unknown"))
        config = backend_config.get(agent_id, {})

        if not isinstance(config, dict):
            config = {}

        row["backend"] = config.get("backend", "unknown")
        row["model"] = config.get("model", "unknown")
        row["temperature"] = config.get("temperature", "")


def iter_meta_round_objects(path: Path) -> Iterable[Dict[str, Any]]:
    data = load_json(path)

    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
        return

    if isinstance(data, dict):
        yield data
        return


def find_exp_dirs(batch_dir: Path) -> List[Path]:
    exp_dirs = []

    for child in batch_dir.iterdir():
        if child.is_dir() and child.name.startswith("exp_"):
            exp_dirs.append(child)

    return sorted(exp_dirs, key=lambda p: extract_number(p.name))


def find_meta_round_files(exp_dir: Path) -> List[Path]:
    files = list(exp_dir.glob("meta_round_*.json"))
    return sorted(files, key=lambda p: extract_number(p.name))


def find_latest_batch(log_root: Path) -> Path:
    candidates = []

    for child in log_root.iterdir():
        if child.is_dir() and child.name.startswith("batch_"):
            candidates.append(child)

    if not candidates:
        raise FileNotFoundError(f"No batch directory found under {log_root}")

    return sorted(candidates, key=lambda p: p.name)[-1]


def get_meta_round_id(round_obj: Dict[str, Any], fallback_path: Optional[Path] = None) -> int:
    value = round_obj.get("meta_round_id")

    if isinstance(value, int):
        return value

    if fallback_path is not None:
        return extract_number(fallback_path.name)

    return -1


def get_agents(round_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    agents = round_obj.get("agents", [])

    if not isinstance(agents, list):
        return []

    ordered = []
    by_id = {}

    for agent in agents:
        if not isinstance(agent, dict):
            continue

        agent_id = agent.get("agent_id")

        if isinstance(agent_id, str):
            by_id[agent_id] = agent

    for agent_id in AGENTS:
        if agent_id in by_id:
            ordered.append(by_id[agent_id])

    extra_agents = []

    for agent in agents:
        agent_id = agent.get("agent_id")

        if agent_id not in AGENTS:
            extra_agents.append(agent)

    extra_agents = sorted(
        extra_agents,
        key=lambda agent: str(agent.get("agent_id", "unknown")),
    )

    ordered.extend(extra_agents)

    return ordered


def get_agent_order_from_rows(rows: List[Dict[str, Any]]) -> List[str]:
    existing_agents = []

    for row in rows:
        agent_id = row.get("agent_id")

        if isinstance(agent_id, str) and agent_id not in existing_agents:
            existing_agents.append(agent_id)

    ordered_agents = []

    for agent_id in AGENTS:
        if agent_id in existing_agents:
            ordered_agents.append(agent_id)

    extra_agents = []

    for agent_id in existing_agents:
        if agent_id not in AGENTS:
            extra_agents.append(agent_id)

    extra_agents = sorted(extra_agents)
    ordered_agents.extend(extra_agents)

    return ordered_agents


def get_trace(agent: Dict[str, Any]) -> List[Dict[str, Any]]:
    trace = agent.get("daily_trace", [])

    if not isinstance(trace, list):
        return []

    rows = []

    for row in trace:
        if isinstance(row, dict):
            rows.append(row)

    return rows


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(number) or math.isinf(number):
        return None

    return number


def normalize_success_value(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, bool):
        return 1.0 if value else 0.0

    if isinstance(value, str):
        lower = value.strip().lower()

        if lower in {"true", "yes", "success", "ok", "pass", "passed"}:
            return 1.0

        if lower in {"false", "no", "fail", "failed", "error"}:
            return 0.0

    number = safe_float(value)

    if number is None:
        return None

    return 1.0 if number > 0 else 0.0


def get_nested_metric(agent: Dict[str, Any], metric_names: List[str]) -> Optional[Any]:
    candidate_dict_names = [
        "metrics",
        "summary",
        "statistics",
        "performance",
        "code_metrics",
        "execution_metrics",
    ]

    for metric_name in metric_names:
        if metric_name in agent:
            return agent.get(metric_name)

    for dict_name in candidate_dict_names:
        candidate = agent.get(dict_name)

        if not isinstance(candidate, dict):
            continue

        for metric_name in metric_names:
            if metric_name in candidate:
                return candidate.get(metric_name)

    return None


def get_strategy_code(agent: Dict[str, Any]) -> str:
    value = agent.get("strategy_code", "")

    if isinstance(value, str):
        return value

    return ""


def estimate_strategy_complexity(agent: Dict[str, Any]) -> float:
    direct_value = get_nested_metric(
        agent,
        [
            "strategy_complexity",
            "avg_strategy_complexity",
            "complexity",
            "ast_node_count",
        ],
    )

    direct_number = safe_float(direct_value)

    if direct_number is not None:
        return direct_number

    code = get_strategy_code(agent)

    if not code.strip():
        return 0.0

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0.0

    return float(sum(1 for _ in ast.walk(tree)))


def infer_compile_success(agent: Dict[str, Any]) -> float:
    direct_value = get_nested_metric(
        agent,
        [
            "compile_success",
            "avg_compile_success",
            "compiled",
        ],
    )

    direct_success = normalize_success_value(direct_value)

    if direct_success is not None:
        return direct_success

    trace = get_trace(agent)

    for row in trace:
        error = row.get("error")

        if error and "compile_error" in str(error).lower():
            return 0.0

    code = get_strategy_code(agent)

    if not code.strip():
        return 1.0 if trace else 0.0

    try:
        ast.parse(code)
    except SyntaxError:
        return 0.0

    return 1.0


def infer_runtime_success(agent: Dict[str, Any]) -> float:
    direct_value = get_nested_metric(
        agent,
        [
            "runtime_success",
            "avg_runtime_success",
            "executed",
        ],
    )

    direct_success = normalize_success_value(direct_value)

    if direct_success is not None:
        return direct_success

    trace = get_trace(agent)

    for row in trace:
        if row.get("error"):
            return 0.0

    return 1.0 if trace else 0.0


def get_days_and_values(agent: Dict[str, Any], metric: str) -> tuple[List[int], List[float]]:
    days = []
    values = []

    for row in get_trace(agent):
        day_value = safe_float(row.get("day"))
        metric_value = safe_float(row.get(metric))

        if day_value is None or metric_value is None:
            continue

        days.append(int(day_value))
        values.append(metric_value)

    return days, values


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_line_plot(
    round_obj: Dict[str, Any],
    output_dir: Path,
    metric: str,
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    ensure_dir(output_dir)

    fig, ax = plt.subplots(figsize=(11, 6))

    has_data = False

    for agent in get_agents(round_obj):
        agent_id = agent.get("agent_id", "unknown")
        days, values = get_days_and_values(agent, metric)

        if not days:
            continue

        has_data = True
        ax.plot(days, values, marker="o", linewidth=2, label=agent_id)

        for row in get_trace(agent):
            if row.get("status") == "dead":
                dead_day = safe_float(row.get("day"))
                dead_value = safe_float(row.get(metric))

                if dead_day is not None and dead_value is not None:
                    ax.scatter([dead_day], [dead_value], marker="x", s=90)

                break

    if not has_data:
        plt.close(fig)
        return

    ax.set_title(title)
    ax.set_xlabel("Day")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=160)
    plt.close(fig)


def save_supply_plot(round_obj: Dict[str, Any], output_dir: Path, meta_round_id: int) -> None:
    environment = round_obj.get("environment", {})

    if not isinstance(environment, dict):
        return

    supply_list = environment.get("supply_list", [])

    if not isinstance(supply_list, list) or not supply_list:
        return

    days = list(range(1, len(supply_list) + 1))
    values = []

    for value in supply_list:
        number = safe_float(value)

        if number is None:
            values.append(float("nan"))
        else:
            values.append(number)

    fig, ax = plt.subplots(figsize=(11, 5))

    ax.plot(days, values, marker="o", linewidth=2)
    ax.set_title(f"Meta Round {meta_round_id}: Supply by Day")
    ax.set_xlabel("Day")
    ax.set_ylabel("Supply")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "supply_by_day.png", dpi=160)
    plt.close(fig)


def summarize_agent(
    round_obj: Dict[str, Any],
    agent: Dict[str, Any],
    meta_round_id: int,
    exp_name: str,
) -> Dict[str, Any]:
    agent_id = agent.get("agent_id", "unknown")
    trace = get_trace(agent)

    bids = []
    hp_values = []
    budget_values = []
    alive_days = 0
    error_count = 0
    death_day = ""

    for row in trace:
        bid = safe_float(row.get("bid"))
        hp = safe_float(row.get("hp_after"))
        budget = safe_float(row.get("budget_after"))

        if bid is not None:
            bids.append(bid)

        if hp is not None:
            hp_values.append(hp)

        if budget is not None:
            budget_values.append(budget)

        if row.get("status") == "alive":
            alive_days += 1

        if row.get("status") == "dead" and death_day == "":
            death_day = row.get("day", "")

        if row.get("error"):
            error_count += 1

    total_bid = sum(bids)
    avg_bid = total_bid / len(bids) if bids else 0.0
    bid_variance = statistics.pvariance(bids) if len(bids) >= 2 else 0.0
    final_hp = hp_values[-1] if hp_values else 0.0
    final_budget = budget_values[-1] if budget_values else 0.0
    final_status = trace[-1].get("status", "") if trace else ""

    is_dead = 0

    if final_status == "dead":
        is_dead = 1

    if death_day != "":
        is_dead = 1

    status_alive = 0.0 if is_dead else 1.0
    death_count = float(is_dead)
    mortality_rate = death_count * 100.0

    compile_success = infer_compile_success(agent)
    runtime_success = infer_runtime_success(agent)
    strategy_complexity = estimate_strategy_complexity(agent)

    return {
        "exp": exp_name,
        "meta_round_id": meta_round_id,
        "agent_id": agent_id,
        "survival_days": alive_days,
        "death_day": death_day,
        "death_count": death_count,
        "mortality_rate": mortality_rate,
        "final_status": final_status,
        "status_alive": status_alive,
        "final_hp": final_hp,
        "final_budget": final_budget,
        "total_bid": total_bid,
        "avg_bid": avg_bid,
        "bid_variance": bid_variance,
        "max_bid": max(bids) if bids else 0.0,
        "min_bid": min(bids) if bids else 0.0,
        "error_count": error_count,
        "compile_success": compile_success,
        "runtime_success": runtime_success,
        "strategy_complexity": strategy_complexity,
    }


def save_bar_plot(
    rows: List[Dict[str, Any]],
    output_dir: Path,
    metric: str,
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    labels = []
    values = []

    for row in rows:
        labels.append(str(row.get("agent_id", "unknown")))
        value = safe_float(row.get(metric))
        values.append(value if value is not None else 0.0)

    if not labels:
        return

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_xlabel("Agent")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)

    if values:
        ymax = max(values)

        if ymax <= 0:
            ymax = 1.0

        ax.set_ylim(0, ymax * 1.18)

    for i, value in enumerate(values):
        ax.text(i, value, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=160)
    plt.close(fig)


def save_bar_plot_by_key(
    rows: List[Dict[str, Any]],
    output_dir: Path,
    x_key: str,
    metric: str,
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    labels = []
    values = []

    for row in rows:
        labels.append(str(row.get(x_key, "unknown")))
        value = safe_float(row.get(metric))
        values.append(value if value is not None else 0.0)

    if not labels:
        return

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.bar(labels, values)
    ax.set_title(title)
    ax.set_xlabel(x_key)
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    ax.tick_params(axis="x", rotation=25)

    if values:
        ymax = max(values)

        if ymax <= 0:
            ymax = 1.0

        ax.set_ylim(0, ymax * 1.18)

    for i, value in enumerate(values):
        ax.text(i, value, f"{value:.2f}", ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=160)
    plt.close(fig)


def mean_numeric(rows: List[Dict[str, Any]], metric: str) -> float:
    values = []

    for row in rows:
        value = safe_float(row.get(metric))

        if value is not None:
            values.append(value)

    if not values:
        return 0.0

    return sum(values) / len(values)


def sum_numeric(rows: List[Dict[str, Any]], metric: str) -> float:
    total = 0.0

    for row in rows:
        value = safe_float(row.get(metric))

        if value is not None:
            total += value

    return total


def aggregate_rows_by_agent(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for row in rows:
        agent_id = str(row.get("agent_id", "unknown"))
        grouped.setdefault(agent_id, []).append(row)

    summary_rows = []

    for agent_id, agent_rows in grouped.items():
        exp_names = set()
        model_names = set()
        backend_names = set()
        meta_round_keys = set()

        for row in agent_rows:
            exp_names.add(str(row.get("exp", "")))
            model_names.add(str(row.get("model", "unknown")))
            backend_names.add(str(row.get("backend", "unknown")))
            meta_round_keys.add((str(row.get("exp", "")), str(row.get("meta_round_id", ""))))

        total_death_count = sum_numeric(agent_rows, "death_count")
        sample_count = len(agent_rows)
        mortality_rate = total_death_count / sample_count * 100.0 if sample_count > 0 else 0.0

        summary_rows.append(
            {
                "agent_id": agent_id,
                "model": ",".join(sorted(model_names)),
                "backend": ",".join(sorted(backend_names)),
                "sample_count": sample_count,
                "exp_count": len(exp_names),
                "meta_round_record_count": len(meta_round_keys),
                "avg_survival_days": mean_numeric(agent_rows, "survival_days"),
                "avg_final_hp": mean_numeric(agent_rows, "final_hp"),
                "avg_final_budget": mean_numeric(agent_rows, "final_budget"),
                "avg_total_bid": mean_numeric(agent_rows, "total_bid"),
                "avg_daily_bid": mean_numeric(agent_rows, "avg_bid"),
                "avg_bid_variance": mean_numeric(agent_rows, "bid_variance"),
                "avg_max_bid": mean_numeric(agent_rows, "max_bid"),
                "avg_min_bid": mean_numeric(agent_rows, "min_bid"),
                "avg_error_count": mean_numeric(agent_rows, "error_count"),
                "avg_compile_success": mean_numeric(agent_rows, "compile_success"),
                "avg_runtime_success": mean_numeric(agent_rows, "runtime_success"),
                "avg_strategy_complexity": mean_numeric(agent_rows, "strategy_complexity"),
                "avg_status_alive": mean_numeric(agent_rows, "status_alive"),
                "total_death_count": total_death_count,
                "mortality_rate": mortality_rate,
            }
        )

    ordered_rows = []

    for agent_id in AGENTS:
        for row in summary_rows:
            if row["agent_id"] == agent_id:
                ordered_rows.append(row)

    for row in sorted(summary_rows, key=lambda item: str(item["agent_id"])):
        if row["agent_id"] not in AGENTS:
            ordered_rows.append(row)

    return ordered_rows


def aggregate_rows_by_model(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for row in rows:
        model = str(row.get("model", "unknown"))
        grouped.setdefault(model, []).append(row)

    summary_rows = []

    for model, model_rows in grouped.items():
        exp_names = set()
        agent_names = set()
        backend_names = set()
        meta_round_keys = set()

        for row in model_rows:
            exp_names.add(str(row.get("exp", "")))
            agent_names.add(str(row.get("agent_id", "")))
            backend_names.add(str(row.get("backend", "unknown")))
            meta_round_keys.add((str(row.get("exp", "")), str(row.get("meta_round_id", ""))))

        total_death_count = sum_numeric(model_rows, "death_count")
        sample_count = len(model_rows)
        mortality_rate = total_death_count / sample_count * 100.0 if sample_count > 0 else 0.0

        summary_rows.append(
            {
                "model": model,
                "backend": ",".join(sorted(backend_names)),
                "sample_count": sample_count,
                "agent_count": len(agent_names),
                "exp_count": len(exp_names),
                "meta_round_record_count": len(meta_round_keys),
                "avg_survival_days": mean_numeric(model_rows, "survival_days"),
                "avg_final_hp": mean_numeric(model_rows, "final_hp"),
                "avg_final_budget": mean_numeric(model_rows, "final_budget"),
                "avg_total_bid": mean_numeric(model_rows, "total_bid"),
                "avg_daily_bid": mean_numeric(model_rows, "avg_bid"),
                "avg_bid_variance": mean_numeric(model_rows, "bid_variance"),
                "avg_max_bid": mean_numeric(model_rows, "max_bid"),
                "avg_min_bid": mean_numeric(model_rows, "min_bid"),
                "avg_error_count": mean_numeric(model_rows, "error_count"),
                "avg_compile_success": mean_numeric(model_rows, "compile_success"),
                "avg_runtime_success": mean_numeric(model_rows, "runtime_success"),
                "avg_strategy_complexity": mean_numeric(model_rows, "strategy_complexity"),
                "avg_status_alive": mean_numeric(model_rows, "status_alive"),
                "total_death_count": total_death_count,
                "mortality_rate": mortality_rate,
            }
        )

    return sorted(summary_rows, key=lambda row: str(row.get("model", "unknown")))


def write_agent_average_summary_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    if not rows:
        return

    fieldnames = [
        "agent_id",
        "model",
        "backend",
        "sample_count",
        "exp_count",
        "meta_round_record_count",
        "avg_survival_days",
        "avg_final_hp",
        "avg_final_budget",
        "avg_total_bid",
        "avg_daily_bid",
        "avg_bid_variance",
        "avg_max_bid",
        "avg_min_bid",
        "avg_error_count",
        "avg_compile_success",
        "avg_runtime_success",
        "avg_strategy_complexity",
        "avg_status_alive",
        "total_death_count",
        "mortality_rate",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def write_model_average_summary_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    if not rows:
        return

    fieldnames = [
        "model",
        "backend",
        "sample_count",
        "agent_count",
        "exp_count",
        "meta_round_record_count",
        "avg_survival_days",
        "avg_final_hp",
        "avg_final_budget",
        "avg_total_bid",
        "avg_daily_bid",
        "avg_bid_variance",
        "avg_max_bid",
        "avg_min_bid",
        "avg_error_count",
        "avg_compile_success",
        "avg_runtime_success",
        "avg_strategy_complexity",
        "avg_status_alive",
        "total_death_count",
        "mortality_rate",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def save_agent_average_summary_plots(
    rows: List[Dict[str, Any]],
    output_dir: Path,
    prefix: str,
    title_prefix: str,
) -> None:
    ensure_dir(output_dir)

    metrics = [
        ("avg_survival_days", "Average Survival Days"),
        ("avg_final_hp", "Average Final HP"),
        ("avg_final_budget", "Average Final Budget"),
        ("avg_total_bid", "Average Total Bid"),
        ("avg_daily_bid", "Average Daily Bid"),
        ("avg_bid_variance", "Average Bid Variance"),
        ("avg_error_count", "Average Error Count"),
        ("avg_compile_success", "Average Compile Success"),
        ("avg_runtime_success", "Average Runtime Success"),
        ("avg_strategy_complexity", "Average Strategy Complexity"),
        ("total_death_count", "Total Death Count"),
        ("mortality_rate", "Mortality Rate (%)"),
    ]

    for metric, ylabel in metrics:
        save_bar_plot(
            rows=rows,
            output_dir=output_dir,
            metric=metric,
            ylabel=ylabel,
            title=f"{title_prefix}: {ylabel}",
            filename=f"{prefix}_{metric}_bar.png",
        )


def save_model_average_summary_plots(
    rows: List[Dict[str, Any]],
    output_dir: Path,
    prefix: str,
    title_prefix: str,
) -> None:
    ensure_dir(output_dir)

    metrics = [
        ("avg_survival_days", "Average Survival Days"),
        ("avg_final_hp", "Average Final HP"),
        ("avg_final_budget", "Average Final Budget"),
        ("avg_total_bid", "Average Total Bid"),
        ("avg_daily_bid", "Average Daily Bid"),
        ("avg_bid_variance", "Average Bid Variance"),
        ("avg_error_count", "Average Error Count"),
        ("avg_compile_success", "Average Compile Success"),
        ("avg_runtime_success", "Average Runtime Success"),
        ("avg_strategy_complexity", "Average Strategy Complexity"),
        ("total_death_count", "Total Death Count"),
        ("mortality_rate", "Mortality Rate (%)"),
    ]

    for metric, ylabel in metrics:
        save_bar_plot_by_key(
            rows=rows,
            output_dir=output_dir,
            x_key="model",
            metric=metric,
            ylabel=ylabel,
            title=f"{title_prefix}: {ylabel}",
            filename=f"{prefix}_model_{metric}_bar.png",
        )


def save_meta_round_plots(
    round_obj: Dict[str, Any],
    output_dir: Path,
    meta_round_id: int,
    exp_name: str,
) -> List[Dict[str, Any]]:
    ensure_dir(output_dir)

    save_line_plot(
        round_obj=round_obj,
        output_dir=output_dir,
        metric="bid",
        ylabel="Bid",
        title=f"{exp_name} Meta Round {meta_round_id}: Agent Bid by Day",
        filename="bid_by_day.png",
    )

    save_line_plot(
        round_obj=round_obj,
        output_dir=output_dir,
        metric="hp_after",
        ylabel="HP After",
        title=f"{exp_name} Meta Round {meta_round_id}: Agent HP by Day",
        filename="hp_by_day.png",
    )

    save_line_plot(
        round_obj=round_obj,
        output_dir=output_dir,
        metric="budget_after",
        ylabel="Budget After",
        title=f"{exp_name} Meta Round {meta_round_id}: Agent Budget by Day",
        filename="budget_by_day.png",
    )

    save_supply_plot(round_obj, output_dir, meta_round_id)

    summary_rows = []

    for agent in get_agents(round_obj):
        summary_rows.append(
            summarize_agent(
                round_obj=round_obj,
                agent=agent,
                meta_round_id=meta_round_id,
                exp_name=exp_name,
            )
        )

    meta_round_bar_specs = [
        ("survival_days", "Survival Days", "survival_days_bar.png"),
        ("total_bid", "Total Bid", "total_bid_bar.png"),
        ("final_hp", "Final HP", "final_hp_bar.png"),
        ("final_budget", "Final Budget", "final_budget_bar.png"),
        ("mortality_rate", "Mortality Rate (%)", "mortality_rate_bar.png"),
        ("death_count", "Death Count", "death_count_bar.png"),
        ("status_alive", "Status Alive (alive=1, dead=0)", "final_status_bar.png"),
        ("error_count", "Error Count", "error_count_bar.png"),
        ("compile_success", "Compile Success", "compile_success_bar.png"),
        ("runtime_success", "Runtime Success", "runtime_success_bar.png"),
        ("strategy_complexity", "Strategy Complexity", "strategy_complexity_bar.png"),
    ]

    for metric, ylabel, filename in meta_round_bar_specs:
        save_bar_plot(
            rows=summary_rows,
            output_dir=output_dir,
            metric=metric,
            ylabel=ylabel,
            title=f"{exp_name} Meta Round {meta_round_id}: {ylabel}",
            filename=filename,
        )

    return summary_rows


def write_summary_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    if not rows:
        return

    fieldnames = [
        "exp",
        "meta_round_id",
        "agent_id",
        "backend",
        "model",
        "temperature",
        "survival_days",
        "death_day",
        "death_count",
        "mortality_rate",
        "final_status",
        "status_alive",
        "final_hp",
        "final_budget",
        "total_bid",
        "avg_bid",
        "bid_variance",
        "max_bid",
        "min_bid",
        "error_count",
        "compile_success",
        "runtime_success",
        "strategy_complexity",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


def save_exp_trend_plot(
    rows: List[Dict[str, Any]],
    output_dir: Path,
    metric: str,
    ylabel: str,
    title: str,
    filename: str,
) -> None:
    ensure_dir(output_dir)

    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for row in rows:
        agent_id = str(row.get("agent_id", "unknown"))
        grouped.setdefault(agent_id, []).append(row)

    fig, ax = plt.subplots(figsize=(11, 6))

    has_data = False

    for agent_id in get_agent_order_from_rows(rows):
        agent_rows = grouped.get(agent_id, [])

        if not agent_rows:
            continue

        agent_rows = sorted(agent_rows, key=lambda x: int(x["meta_round_id"]))

        x_values = []
        y_values = []

        for row in agent_rows:
            x = safe_float(row.get("meta_round_id"))
            y = safe_float(row.get(metric))

            if x is None or y is None:
                continue

            x_values.append(int(x))
            y_values.append(y)

        if not x_values:
            continue

        has_data = True
        ax.plot(x_values, y_values, marker="o", linewidth=2, label=agent_id)

    if not has_data:
        plt.close(fig)
        return

    ax.set_title(title)
    ax.set_xlabel("Meta Round")
    ax.set_ylabel(ylabel)
    ax.grid(True, alpha=0.3)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_dir / filename, dpi=160)
    plt.close(fig)


def save_exp_summary_plots(rows: List[Dict[str, Any]], output_dir: Path, exp_name: str) -> None:
    trend_specs = [
        ("survival_days", "Survival Days", "exp_survival_days_trend.png"),
        ("total_bid", "Total Bid", "exp_total_bid_trend.png"),
        ("avg_bid", "Average Bid", "exp_avg_bid_trend.png"),
        ("final_budget", "Final Budget", "exp_final_budget_trend.png"),
        ("mortality_rate", "Mortality Rate (%)", "exp_mortality_rate_trend.png"),
        ("death_count", "Death Count", "exp_death_count_trend.png"),
        ("status_alive", "Status Alive (alive=1, dead=0)", "exp_final_status_trend.png"),
        ("error_count", "Error Count", "exp_error_count_trend.png"),
        ("compile_success", "Compile Success", "exp_compile_success_trend.png"),
        ("runtime_success", "Runtime Success", "exp_runtime_success_trend.png"),
        ("strategy_complexity", "Strategy Complexity", "exp_strategy_complexity_trend.png"),
    ]

    for metric, ylabel, filename in trend_specs:
        save_exp_trend_plot(
            rows=rows,
            output_dir=output_dir,
            metric=metric,
            ylabel=ylabel,
            title=f"{exp_name}: {ylabel} by Meta Round",
            filename=filename,
        )


def process_exp(exp_dir: Path) -> List[Dict[str, Any]]:
    meta_files = find_meta_round_files(exp_dir)

    if not meta_files:
        print(f"[WARN] No meta_round_*.json found in {exp_dir}")
        return []

    exp_output_dir = exp_dir / OUTPUT_DIR_NAME
    ensure_dir(exp_output_dir)

    all_rows = []
    backend_config = load_backend_config(exp_dir)

    for meta_file in meta_files:
        for round_obj in iter_meta_round_objects(meta_file):
            meta_round_id = get_meta_round_id(round_obj, meta_file)
            round_output_dir = exp_output_dir / f"meta_round_{meta_round_id:03d}"

            print(f"[INFO] Processing {exp_dir.name} {meta_file.name}")

            rows = save_meta_round_plots(
                round_obj=round_obj,
                output_dir=round_output_dir,
                meta_round_id=meta_round_id,
                exp_name=exp_dir.name,
            )

            attach_model_info_to_rows(rows, backend_config)
            all_rows.extend(rows)

    write_summary_csv(all_rows, exp_output_dir / "performance_summary.csv")
    save_exp_summary_plots(all_rows, exp_output_dir, exp_dir.name)

    exp_agent_average_rows = aggregate_rows_by_agent(all_rows)

    write_agent_average_summary_csv(
        exp_agent_average_rows,
        exp_output_dir / "agent_average_summary.csv",
    )

    save_agent_average_summary_plots(
        rows=exp_agent_average_rows,
        output_dir=exp_output_dir / "agent_average",
        prefix="exp",
        title_prefix=f"{exp_dir.name} Agent Average",
    )

    exp_model_average_rows = aggregate_rows_by_model(all_rows)

    write_model_average_summary_csv(
        exp_model_average_rows,
        exp_output_dir / "model_average_summary.csv",
    )

    save_model_average_summary_plots(
        rows=exp_model_average_rows,
        output_dir=exp_output_dir / "model_average",
        prefix="exp",
        title_prefix=f"{exp_dir.name} Model Average",
    )

    return all_rows


def process_batch(batch_dir: Path) -> None:
    if not batch_dir.exists():
        raise FileNotFoundError(f"Batch directory does not exist: {batch_dir}")

    exp_dirs = find_exp_dirs(batch_dir)

    if not exp_dirs:
        raise FileNotFoundError(f"No exp_* directory found under {batch_dir}")

    batch_rows = []

    for exp_dir in exp_dirs:
        rows = process_exp(exp_dir)
        batch_rows.extend(rows)

    batch_output_dir = batch_dir / OUTPUT_DIR_NAME
    ensure_dir(batch_output_dir)

    write_summary_csv(
        batch_rows,
        batch_output_dir / "all_exp_performance_summary.csv",
    )

    batch_agent_average_rows = aggregate_rows_by_agent(batch_rows)

    write_agent_average_summary_csv(
        batch_agent_average_rows,
        batch_output_dir / "batch_agent_average_summary.csv",
    )

    save_agent_average_summary_plots(
        rows=batch_agent_average_rows,
        output_dir=batch_output_dir / "agent_average",
        prefix="batch",
        title_prefix="All Experiments Agent Average",
    )

    batch_model_average_rows = aggregate_rows_by_model(batch_rows)

    write_model_average_summary_csv(
        batch_model_average_rows,
        batch_output_dir / "batch_model_average_summary.csv",
    )

    save_model_average_summary_plots(
        rows=batch_model_average_rows,
        output_dir=batch_output_dir / "model_average",
        prefix="batch",
        title_prefix="All Experiments Model Average",
    )

    print(f"[DONE] Plots generated under: {batch_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate per-exp and per-meta-round performance plots for Water Allocation logs."
    )

    parser.add_argument(
        "--batch-dir",
        type=str,
        default=None,
        help="Path to a batch directory, for example log/batch_20260518_230245",
    )

    parser.add_argument(
        "--latest-batch",
        action="store_true",
        help="Automatically use the latest batch directory under log/",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_root = get_project_root()

    if args.latest_batch:
        batch_dir = find_latest_batch(project_root / "log")
    elif args.batch_dir is not None:
        batch_dir = Path(args.batch_dir)

        if not batch_dir.is_absolute():
            batch_dir = project_root / batch_dir
    else:
        raise ValueError("Please provide --batch-dir or --latest-batch")

    process_batch(batch_dir)


if __name__ == "__main__":
    main()