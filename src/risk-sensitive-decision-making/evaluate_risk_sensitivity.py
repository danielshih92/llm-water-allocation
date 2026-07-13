#!/usr/bin/env python3
"""Offline synthetic-state evaluation of risk-sensitive bidding strategies."""

import argparse
import csv
import inspect
import json
import math
import multiprocessing
import statistics
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT))

from sandbox_executor import ALLOWED_BUILTINS, _static_check
from wac_programmatic import AgentProfile, default_agent_profiles


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BATCH = REPO_ROOT / "log" / "batch_031_full_code_access_c_med_20days"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "compare_result" / "risk-sensitive-decision-making"

SAFE_STATE = {"name": "safe", "hp": 7, "no_water_days": 1}
JOINT_STATES = [
    {"name": "mild", "hp": 6, "no_water_days": 2},
    {"name": "moderate", "hp": 3, "no_water_days": 2},
    {"name": "severe", "hp": 2, "no_water_days": 3},
]
HEALTH_STATES = [
    {"name": "mild", "hp": 6, "no_water_days": 1},
    {"name": "moderate", "hp": 3, "no_water_days": 1},
    {"name": "severe", "hp": 2, "no_water_days": 1},
]
DROUGHT_STATES = [
    {"name": "elevated", "hp": 7, "no_water_days": 2},
    {"name": "severe", "hp": 7, "no_water_days": 3},
]
BACKGROUNDS = [
    {"name": "early_resource_rich", "day": 3, "budget": 500.0, "supply": 24.0},
    {"name": "middle_normal", "day": 10, "budget": 300.0, "supply": 20.0},
    {"name": "late_resource_scarce", "day": 18, "budget": 150.0, "supply": 16.0},
]
COMPONENT_STATES = {
    "joint_risk_monotonicity": JOINT_STATES,
    "health_sensitivity": HEALTH_STATES,
    "drought_sensitivity": DROUGHT_STATES,
}

PAIR_FIELDS = [
    "batch_id", "condition", "experiment_id", "meta_round_id", "agent_id",
    "backend", "model", "strategy_instance_id", "component", "background",
    "risk_level", "day", "budget", "supply", "safe_hp", "safe_no_water_days",
    "risk_hp", "risk_no_water_days", "safe_bid", "risk_bid", "bid_delta",
    "normalized_bid_adjustment",
    "weak_monotonicity", "strict_sensitivity", "tie", "negative", "valid_pair",
    "safe_error", "risk_error", "meta_round_file",
]

SUMMARY_FIELDS = [
    "summary_level", "condition", "model", "agent_id", "strategy_instance_id",
    "joint_risk_monotonicity", "health_sensitivity", "drought_sensitivity",
    "risk_sensitivity", "joint_strict_sensitivity", "health_strict_sensitivity",
    "drought_strict_sensitivity", "strict_risk_sensitivity", "tie_rate",
    "negative_rate", "mean_bid_delta", "median_bid_delta", "normalized_bid_adjustment",
    "joint_normalized_bid_adjustment", "health_normalized_bid_adjustment",
    "drought_normalized_bid_adjustment", "valid_pair_count",
    "total_pair_count", "error_pair_count", "error_rate",
]


def infer_condition(batch_path: Path) -> str:
    name = batch_path.name.lower()
    if "full_code_access" in name:
        return "OPF"
    if "no_opp_info" in name or "no_opponent_info" in name:
        return "OF"
    return "unknown"


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_records(path: Path) -> Iterable[Dict[str, Any]]:
    payload = load_json_file(path)
    if isinstance(payload, list):
        yield from (item for item in payload if isinstance(item, dict))
    elif isinstance(payload, dict):
        yield payload


def normalize_path(value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else Path.cwd() / path).resolve()


def load_backend_config(exp_dir: Path) -> Dict[str, Dict[str, Any]]:
    path = exp_dir / "backend_config.json"
    if not path.exists():
        return {}
    payload = load_json_file(path)
    if not isinstance(payload, dict):
        return {}
    return {
        str(agent_id): config
        for agent_id, config in payload.items()
        if isinstance(config, dict)
    }


def is_valid_record(record: Dict[str, Any]) -> bool:
    return record.get("all_agents_admitted") == 1 and record.get("outcome_valid") == 1


def build_profile_map(record: Dict[str, Any]) -> Dict[str, AgentProfile]:
    environment = record.get("environment", {})
    players = environment.get("players", []) if isinstance(environment, dict) else []
    profiles: Dict[str, AgentProfile] = {}
    for item in players if isinstance(players, list) else []:
        if not isinstance(item, dict) or not str(item.get("agent_id", "")).strip():
            continue
        agent_id = str(item["agent_id"]).strip()
        profiles[agent_id] = AgentProfile(
            agent_id=agent_id,
            water_requirement=int(item.get("water_requirement", 0) or 0),
            daily_salary=float(item.get("daily_salary", 0.0) or 0.0),
        )
    if profiles:
        return profiles
    return {profile.agent_id: profile for profile in default_agent_profiles()}


def sanitize_bid(value: Any, budget: float) -> float:
    try:
        bid = float(value)
    except Exception:
        return 0.0
    if not math.isfinite(bid):
        return 0.0
    return min(float(budget), max(0.0, bid))


def synthetic_opponents_status(
    target_agent_id: str,
    profiles: Dict[str, AgentProfile],
    background: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Create deterministic opponent context shared by every state in a pair."""
    status: Dict[str, Dict[str, Any]] = {}
    supply = float(background["supply"])
    starting_budget = float(background["budget"])
    day = int(background["day"])
    history_days = [max(1, day - 2), max(1, day - 1)]
    for agent_id in sorted(profiles):
        if agent_id == target_agent_id:
            continue
        profile = profiles[agent_id]
        bids = [
            min(starting_budget, round(profile.daily_salary * factor, 4))
            for factor in (0.70, 0.80)
        ]
        remaining = starting_budget
        history = []
        for history_day, bid in zip(history_days, bids):
            remaining = max(0.0, remaining - bid)
            history.append({
                "day": history_day, "bid": bid, "supply": supply, "hp_after": 8,
                "budget_after": round(remaining, 4), "status": "alive", "error": None,
            })
        status[agent_id] = {
            "agent_id": agent_id, "hp": 8, "budget": round(remaining, 4),
            "no_water_days": 1, "alive": True,
            "water_requirement": profile.water_requirement,
            "daily_salary": profile.daily_salary, "last_bid": bids[-1],
            "last_status": "alive", "last_hp_after": 8,
            "last_budget_after": round(remaining, 4), "trace_history": history,
        }
    return status


def make_case(
    background: Dict[str, Any],
    state: Dict[str, Any],
    opponents_status: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "day_context": {"day": int(background["day"]), "supply": float(background["supply"])},
        "my_status": {
            "hp": int(state["hp"]), "budget": float(background["budget"]),
            "no_water_days": int(state["no_water_days"]),
        },
        "opponents_status": deepcopy(opponents_status),
    }


def _worker(queue: multiprocessing.Queue, strategy_code: str, cases: List[Dict[str, Any]]) -> None:
    namespace: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
    try:
        exec(strategy_code, namespace, namespace)
        get_bid = namespace.get("get_bid")
        if not callable(get_bid):
            queue.put({"global_error": "missing_get_bid", "results": []})
            return
        param_count = len(inspect.signature(get_bid).parameters)
    except Exception as exc:
        queue.put({"global_error": f"compile_error: {exc}", "results": []})
        return
    results = []
    for case in cases:
        try:
            args = (case["day_context"], case["my_status"], case["opponents_status"])
            raw_bid = get_bid(*args) if param_count >= 3 else get_bid(*args[:2])
            bid = float(raw_bid)
            results.append({
                "bid": bid if math.isfinite(bid) else 0.0,
                "error": None if math.isfinite(bid) else "invalid_bid_value",
            })
        except Exception as exc:
            results.append({"bid": 0.0, "error": f"runtime_error: {exc}"})
    queue.put({"global_error": None, "results": results})


def execute_strategy_cases(
    strategy_code: str, cases: List[Dict[str, Any]], timeout_seconds: float,
) -> List[Tuple[float, Optional[str]]]:
    static_error = _static_check(strategy_code)
    if static_error:
        return [(0.0, static_error) for _ in cases]
    queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    process = multiprocessing.Process(target=_worker, args=(queue, strategy_code, cases), daemon=True)
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        return [(0.0, "runtime_timeout") for _ in cases]
    if queue.empty():
        return [(0.0, "runtime_error: no_result") for _ in cases]
    payload = queue.get_nowait()
    if payload.get("global_error"):
        return [(0.0, payload["global_error"]) for _ in cases]
    raw_results = payload.get("results", [])
    output = []
    for index, case in enumerate(cases):
        item = raw_results[index] if index < len(raw_results) else {}
        error = item.get("error", "runtime_error: missing_case_result")
        output.append((sanitize_bid(item.get("bid", 0.0), case["my_status"]["budget"]), error))
    return output


def build_strategy_cases(
    agent_id: str, profiles: Dict[str, AgentProfile],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    cases: List[Dict[str, Any]] = []
    specs: List[Dict[str, Any]] = []
    for background in BACKGROUNDS:
        opponents = synthetic_opponents_status(agent_id, profiles, background)
        for component, risk_states in COMPONENT_STATES.items():
            for risk_state in risk_states:
                safe_index = len(cases)
                cases.append(make_case(background, SAFE_STATE, opponents))
                risk_index = len(cases)
                cases.append(make_case(background, risk_state, opponents))
                specs.append({
                    "component": component, "background": background,
                    "risk_state": risk_state, "safe_index": safe_index, "risk_index": risk_index,
                })
    return cases, specs


def make_pair_row(metadata: Dict[str, Any], spec: Dict[str, Any], results: List[Tuple[float, Optional[str]]]) -> Dict[str, Any]:
    safe_bid, safe_error = results[spec["safe_index"]]
    risk_bid, risk_error = results[spec["risk_index"]]
    valid = safe_error is None and risk_error is None
    delta = risk_bid - safe_bid if valid else None
    background = spec["background"]
    normalized_delta = delta / float(background["budget"]) if valid else None
    risk = spec["risk_state"]
    row = dict(metadata)
    row.update({
        "component": spec["component"], "background": background["name"],
        "risk_level": risk["name"], "day": background["day"],
        "budget": background["budget"], "supply": background["supply"],
        "safe_hp": SAFE_STATE["hp"], "safe_no_water_days": SAFE_STATE["no_water_days"],
        "risk_hp": risk["hp"], "risk_no_water_days": risk["no_water_days"],
        "safe_bid": round(safe_bid, 6), "risk_bid": round(risk_bid, 6),
        "bid_delta": round(delta, 6) if delta is not None else None,
        "normalized_bid_adjustment": round(normalized_delta, 6) if normalized_delta is not None else None,
        "weak_monotonicity": int(delta >= 0) if valid else None,
        "strict_sensitivity": int(delta > 0) if valid else None,
        "tie": int(delta == 0) if valid else None,
        "negative": int(delta < 0) if valid else None,
        "valid_pair": int(valid), "safe_error": safe_error, "risk_error": risk_error,
    })
    return row


def evaluate_batches(
    batch_paths: Sequence[Path], timeout_seconds: float,
    max_files: Optional[int] = None, max_strategies: Optional[int] = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    strategy_count = 0
    for batch_path in batch_paths:
        if not batch_path.exists():
            raise FileNotFoundError(f"Batch path does not exist: {batch_path}")
        files = sorted(batch_path.glob("exp_*/meta_round_*.json"))
        if max_files is not None:
            files = files[:max_files]
        for meta_round_file in files:
            configs = load_backend_config(meta_round_file.parent)
            for record in iter_records(meta_round_file):
                if not is_valid_record(record):
                    continue
                profiles = build_profile_map(record)
                agents = record.get("agents", [])
                for agent in agents if isinstance(agents, list) else []:
                    if not isinstance(agent, dict):
                        continue
                    code = agent.get("strategy_code")
                    agent_id = str(agent.get("agent_id", "")).strip()
                    if not agent_id or not isinstance(code, str) or not code.strip():
                        continue
                    if max_strategies is not None and strategy_count >= max_strategies:
                        return rows
                    strategy_count += 1
                    config = configs.get(agent_id, {})
                    meta_round_id = record.get("meta_round_id")
                    instance_id = f"{batch_path.name}/{meta_round_file.parent.name}/mr_{meta_round_id}/{agent_id}"
                    metadata = {
                        "batch_id": batch_path.name, "condition": infer_condition(batch_path),
                        "experiment_id": meta_round_file.parent.name, "meta_round_id": meta_round_id,
                        "agent_id": agent_id, "backend": str(config.get("backend", "unknown")),
                        "model": str(config.get("model", "unknown")),
                        "strategy_instance_id": instance_id, "meta_round_file": str(meta_round_file),
                    }
                    cases, specs = build_strategy_cases(agent_id, profiles)
                    results = execute_strategy_cases(code, cases, timeout_seconds)
                    rows.extend(make_pair_row(metadata, spec, results) for spec in specs)
    return rows


def mean_or_none(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def round_or_none(value: Optional[float]) -> Optional[float]:
    return round(value, 6) if value is not None else None


def summarize_group(rows: List[Dict[str, Any]], labels: Dict[str, Any]) -> Dict[str, Any]:
    valid = [row for row in rows if row["valid_pair"] == 1]
    weak_by_component: Dict[str, Optional[float]] = {}
    strict_by_component: Dict[str, Optional[float]] = {}
    normalized_by_component: Dict[str, Optional[float]] = {}
    for component in COMPONENT_STATES:
        component_rows = [row for row in valid if row["component"] == component]
        weak_by_component[component] = mean_or_none([float(row["weak_monotonicity"]) for row in component_rows])
        strict_by_component[component] = mean_or_none([float(row["strict_sensitivity"]) for row in component_rows])
        normalized_by_component[component] = mean_or_none([
            float(row["normalized_bid_adjustment"]) for row in component_rows
        ])
    weak_values = list(weak_by_component.values())
    strict_values = list(strict_by_component.values())
    risk_sensitivity = mean_or_none([value for value in weak_values if value is not None]) if all(value is not None for value in weak_values) else None
    strict_risk_sensitivity = mean_or_none([value for value in strict_values if value is not None]) if all(value is not None for value in strict_values) else None
    normalized_values = list(normalized_by_component.values())
    normalized_bid_adjustment = mean_or_none(
        [value for value in normalized_values if value is not None]
    ) if all(value is not None for value in normalized_values) else None
    deltas = [float(row["bid_delta"]) for row in valid]
    total = len(rows)
    result = {
        "summary_level": labels.get("summary_level"), "condition": labels.get("condition", "ALL"),
        "model": labels.get("model", "ALL"), "agent_id": labels.get("agent_id", "ALL"),
        "strategy_instance_id": labels.get("strategy_instance_id", "ALL"),
        "joint_risk_monotonicity": round_or_none(weak_by_component["joint_risk_monotonicity"]),
        "health_sensitivity": round_or_none(weak_by_component["health_sensitivity"]),
        "drought_sensitivity": round_or_none(weak_by_component["drought_sensitivity"]),
        "risk_sensitivity": round_or_none(risk_sensitivity),
        "joint_strict_sensitivity": round_or_none(strict_by_component["joint_risk_monotonicity"]),
        "health_strict_sensitivity": round_or_none(strict_by_component["health_sensitivity"]),
        "drought_strict_sensitivity": round_or_none(strict_by_component["drought_sensitivity"]),
        "strict_risk_sensitivity": round_or_none(strict_risk_sensitivity),
        "tie_rate": round_or_none(mean_or_none([float(row["tie"]) for row in valid])),
        "negative_rate": round_or_none(mean_or_none([float(row["negative"]) for row in valid])),
        "mean_bid_delta": round_or_none(mean_or_none(deltas)),
        "median_bid_delta": round(statistics.median(deltas), 6) if deltas else None,
        "normalized_bid_adjustment": round_or_none(normalized_bid_adjustment),
        "joint_normalized_bid_adjustment": round_or_none(normalized_by_component["joint_risk_monotonicity"]),
        "health_normalized_bid_adjustment": round_or_none(normalized_by_component["health_sensitivity"]),
        "drought_normalized_bid_adjustment": round_or_none(normalized_by_component["drought_sensitivity"]),
        "valid_pair_count": len(valid), "total_pair_count": total,
        "error_pair_count": total - len(valid),
        "error_rate": round((total - len(valid)) / total, 6) if total else None,
    }
    return result


def grouped_summaries(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    definitions = {
        "strategy": ("condition", "model", "agent_id", "strategy_instance_id"),
        "agent": ("condition", "model", "agent_id"),
        "model": ("condition", "model"),
        "condition": ("condition",),
    }
    outputs: Dict[str, List[Dict[str, Any]]] = {}
    for level, fields in definitions.items():
        groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row[field] for field in fields)].append(row)
        summaries = []
        for key, group_rows in sorted(groups.items(), key=lambda item: tuple(str(x) for x in item[0])):
            labels = {field: value for field, value in zip(fields, key)}
            labels["summary_level"] = level
            summaries.append(summarize_group(group_rows, labels))
        outputs[level] = summaries
    return outputs


def compute_opf_minus_of(model_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_model: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for row in model_rows:
        by_model[str(row["model"])][str(row["condition"])] = row
    fields = [
        "joint_risk_monotonicity", "health_sensitivity", "drought_sensitivity",
        "risk_sensitivity", "strict_risk_sensitivity", "tie_rate", "negative_rate",
        "mean_bid_delta", "normalized_bid_adjustment", "error_rate",
    ]
    output = []
    for model, conditions in sorted(by_model.items()):
        if "OF" not in conditions or "OPF" not in conditions:
            continue
        row: Dict[str, Any] = {"model": model, "comparison": "OPF-OF"}
        for field in fields:
            opf, of = conditions["OPF"].get(field), conditions["OF"].get(field)
            row[field] = round(float(opf) - float(of), 6) if opf is not None and of is not None else None
        output.append(row)
    return output


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: Optional[List[str]] = None) -> None:
    fields = fields or (list(rows[0].keys()) if rows else [])
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fields:
            return
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in rows)


def fmt(value: Any) -> str:
    return "NA" if value is None else (f"{value:.4f}" if isinstance(value, float) else str(value))


def write_markdown(path: Path, model_rows: List[Dict[str, Any]], deltas: List[Dict[str, Any]]) -> None:
    fields = [
        ("condition", "Condition"), ("model", "Model"),
        ("risk_sensitivity", "Risk Sensitivity"),
        ("joint_risk_monotonicity", "Joint RM"), ("health_sensitivity", "Health"),
        ("drought_sensitivity", "Drought"), ("strict_risk_sensitivity", "Strict"),
        ("tie_rate", "Tie Rate"), ("negative_rate", "Negative Rate"),
        ("mean_bid_delta", "Mean Bid Delta"),
        ("normalized_bid_adjustment", "Normalized Bid Adjustment"),
        ("error_rate", "Error Rate"),
    ]
    lines = ["# Risk Sensitivity Results", "", "| " + " | ".join(label for _, label in fields) + " |",
             "| " + " | ".join("---" for _ in fields) + " |"]
    for row in model_rows:
        lines.append("| " + " | ".join(fmt(row.get(field)) for field, _ in fields) + " |")
    if deltas:
        lines.extend(["", "## OPF - OF", "", "| Model | Risk Sensitivity | Joint RM | Health | Drought | Strict |",
                      "| --- | --- | --- | --- | --- | --- |"])
        for row in deltas:
            lines.append("| " + " | ".join(fmt(row.get(field)) for field in (
                "model", "risk_sensitivity", "joint_risk_monotonicity", "health_sensitivity",
                "drought_sensitivity", "strict_risk_sensitivity")) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_table_png(path: Path, model_rows: List[Dict[str, Any]]) -> None:
    if not model_rows:
        return
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(path.parent / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    columns = [
        ("condition", "Condition"), ("model", "Model"),
        ("risk_sensitivity", "Risk\nSensitivity"),
        ("joint_risk_monotonicity", "Joint\nRM"),
        ("health_sensitivity", "Health"), ("drought_sensitivity", "Drought"),
        ("strict_risk_sensitivity", "Strict"), ("tie_rate", "Tie\nRate"),
        ("negative_rate", "Negative\nRate"), ("mean_bid_delta", "Mean Bid\nDelta"),
        ("normalized_bid_adjustment", "Normalized Bid\nAdjustment"),
        ("error_rate", "Error\nRate"),
    ]
    rows = sorted(model_rows, key=lambda row: (str(row.get("condition")), str(row.get("model"))))
    cell_text = [[fmt(row.get(field)) for field, _ in columns] for row in rows]
    fig_height = max(2.8, 0.48 * (len(rows) + 2))
    fig, ax = plt.subplots(figsize=(15, fig_height))
    ax.axis("off")
    table = ax.table(
        cellText=cell_text,
        colLabels=[label for _, label in columns],
        cellLoc="center",
        loc="center",
        colWidths=[0.07, 0.16, 0.08, 0.065, 0.065, 0.065, 0.065, 0.065, 0.08, 0.085, 0.10, 0.065],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.45)
    for column in range(len(columns)):
        table[(0, column)].set_text_props(weight="bold")
        table[(0, column)].set_facecolor("#D9EAF7")
    ax.set_title("Risk Sensitivity by Feedback Condition and Model", fontsize=12, pad=12)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def configuration(batch_paths: Sequence[Path], timeout_seconds: float) -> Dict[str, Any]:
    return {
        "input_batches": [str(path) for path in batch_paths], "timeout_seconds": timeout_seconds,
        "safe_state": SAFE_STATE, "joint_risk_states": JOINT_STATES,
        "health_states": HEALTH_STATES, "drought_states": DROUGHT_STATES,
        "backgrounds": BACKGROUNDS,
        "metrics": {
            "weak_component": "mean(I(risk_bid >= safe_bid))",
            "strict_component": "mean(I(risk_bid > safe_bid))",
            "risk_sensitivity": "equal-weight mean(joint_risk_monotonicity, health_sensitivity, drought_sensitivity)",
            "normalized_bid_adjustment": "equal-weight mean by component of mean((risk_bid-safe_bid)/budget)",
            "invalid_policy": "invalid pairs excluded; composite unavailable if any component has no valid pair",
        },
        "condition_mapping": {"full_code_access": "OPF", "no_opponent_info": "OF"},
    }


def write_outputs(output_dir: Path, rows: List[Dict[str, Any]], timeout_seconds: float, batch_paths: Sequence[Path]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = grouped_summaries(rows)
    deltas = compute_opf_minus_of(summaries["model"])
    write_csv(output_dir / "risk_pairs.csv", rows, PAIR_FIELDS)
    (output_dir / "risk_pairs.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for level, summary_rows in summaries.items():
        write_csv(output_dir / f"risk_summary_by_{level}.csv", summary_rows, SUMMARY_FIELDS)
        (output_dir / f"risk_summary_by_{level}.json").write_text(json.dumps(summary_rows, indent=2), encoding="utf-8")
    write_csv(output_dir / "opf_minus_of_by_model.csv", deltas)
    (output_dir / "opf_minus_of_by_model.json").write_text(json.dumps(deltas, indent=2), encoding="utf-8")
    write_markdown(output_dir / "risk_sensitivity_table.md", summaries["model"], deltas)
    write_table_png(output_dir / "risk_sensitivity_table.png", summaries["model"])
    (output_dir / "run_config.json").write_text(
        json.dumps(configuration(batch_paths, timeout_seconds), indent=2), encoding="utf-8"
    )


def days_until_death(hp: int, no_water_days: int) -> int:
    days = 0
    while hp > 0:
        hp -= no_water_days
        no_water_days += 1
        days += 1
    return days


def run_self_test() -> None:
    assert [days_until_death(state["hp"], state["no_water_days"]) for state in [SAFE_STATE] + JOINT_STATES] == [4, 3, 2, 1]
    profiles = {profile.agent_id: profile for profile in default_agent_profiles()}
    cases, specs = build_strategy_cases("Alex", profiles)
    for spec in specs:
        safe, risk = cases[spec["safe_index"]], cases[spec["risk_index"]]
        assert safe["day_context"] == risk["day_context"]
        assert safe["opponents_status"] == risk["opponents_status"]
        assert safe["my_status"]["budget"] == risk["my_status"]["budget"]
    strategies = {
        "risk_up": "def get_bid(day_context, my_status, opponents_status):\n    return 200 - 10 * my_status['hp'] + 10 * my_status['no_water_days']\n",
        "risk_down": "def get_bid(day_context, my_status, opponents_status):\n    return 10 * my_status['hp'] - 5 * my_status['no_water_days']\n",
        "constant": "def get_bid(day_context, my_status, opponents_status):\n    return 50\n",
        "health_only": "def get_bid(day_context, my_status, opponents_status):\n    return 100 - my_status['hp']\n",
        "drought_only": "def get_bid(day_context, my_status, opponents_status):\n    return 10 * my_status['no_water_days']\n",
    }
    expected = {
        "risk_up": (1.0, 1.0, 0.0), "risk_down": (0.0, 0.0, 1.0),
        "constant": (1.0, 0.0, 0.0),
    }
    for name, code in strategies.items():
        results = execute_strategy_cases(code, cases, 3.0)
        rows = [make_pair_row({
            "batch_id": "test", "condition": "OPF", "experiment_id": "exp",
            "meta_round_id": 1, "agent_id": "Alex", "backend": "test", "model": name,
            "strategy_instance_id": name, "meta_round_file": "test",
        }, spec, results) for spec in specs]
        summary = summarize_group(rows, {"summary_level": "strategy", "condition": "OPF", "model": name})
        if name in expected:
            weak, strict, negative = expected[name]
            assert summary["risk_sensitivity"] == weak
            assert summary["strict_risk_sensitivity"] == strict
            assert summary["negative_rate"] == negative
            assert summary["normalized_bid_adjustment"] is not None
        if name == "constant":
            assert summary["normalized_bid_adjustment"] == 0.0
        if name == "health_only":
            assert summary["health_strict_sensitivity"] == 1.0
            assert summary["drought_strict_sensitivity"] == 0.0
        if name == "drought_only":
            assert summary["health_strict_sensitivity"] == 0.0
            assert summary["drought_strict_sensitivity"] == 1.0
    invalid_codes = [
        "def get_bid(day_context, my_status, opponents_status):\n    return float('nan')\n",
        "def get_bid(day_context, my_status, opponents_status):\n    raise ValueError('x')\n",
        "def get_bid(day_context, my_status, opponents_status):\n    while True:\n        pass\n",
    ]
    for index, code in enumerate(invalid_codes):
        results = execute_strategy_cases(code, cases[:2], 0.1 if index == 2 else 2.0)
        assert all(error is not None for _, error in results)
    assert sanitize_bid(-10, 100) == 0.0 and sanitize_bid(1000, 100) == 100.0
    assert infer_condition(Path("batch_full_code_access")) == "OPF"
    assert infer_condition(Path("batch_no_opponent_info")) == "OF"
    fake = []
    for condition, score in (("OF", 0.25), ("OPF", 0.75)):
        fake.append({"condition": condition, "model": "m", "risk_sensitivity": score})
    assert compute_opf_minus_of(fake)[0]["risk_sensitivity"] == 0.5
    print("Self-test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate risk sensitivity from existing WAC strategy logs.")
    parser.add_argument("--batch", action="append", help="Batch directory; repeat for OF and OPF. Defaults to batch_031.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--output-folder", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--max-files", type=int, default=None)
    parser.add_argument("--max-strategies", type=int, default=None)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        run_self_test()
        return
    batch_paths = [normalize_path(value) for value in (args.batch or [str(DEFAULT_BATCH)])]
    output_dir = normalize_path(args.output_dir)
    if args.output_folder:
        output_dir /= str(args.output_folder).strip()
    rows = evaluate_batches(batch_paths, args.timeout_seconds, args.max_files, args.max_strategies)
    write_outputs(output_dir, rows, args.timeout_seconds, batch_paths)
    print(f"Wrote {len(rows)} pair rows to {output_dir}")
    for row in grouped_summaries(rows)["model"]:
        print(
            f"{row['condition']},{row['model']},risk_sensitivity={row['risk_sensitivity']},"
            f"joint={row['joint_risk_monotonicity']},health={row['health_sensitivity']},"
            f"drought={row['drought_sensitivity']},error_rate={row['error_rate']}"
        )


if __name__ == "__main__":
    main()
