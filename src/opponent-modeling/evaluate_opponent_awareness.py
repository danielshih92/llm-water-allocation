#!/usr/bin/env python3
"""Offline paired probes of opponent-aware bidding behavior."""

from __future__ import annotations

import argparse
import csv
import inspect
import json
import math
import multiprocessing
import os
import queue
import signal
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
SRC_ROOT = HERE.parent
PROJECT_ROOT = SRC_ROOT.parent
sys.path.insert(0, str(SRC_ROOT))

from sandbox_executor import ALLOWED_BUILTINS, _static_check  # noqa: E402
from wac_programmatic import AgentProfile, default_agent_profiles  # noqa: E402


DEFAULT_BATCHES = (
    PROJECT_ROOT / "log" / "batch_032_no_opp_info_c_med_20days",
    PROJECT_ROOT / "log" / "batch_031_full_code_access_c_med_20days",
)
DEFAULT_OUTPUT = PROJECT_ROOT / "compare_result" / "opponent-modeling" / "opponent-awareness"
FOCAL_STATE = {"hp": 7, "no_water_days": 1}
BACKGROUNDS = (
    {"name": "early_resource_rich", "day": 3, "budget": 500.0, "supply": 24.0},
    {"name": "middle_normal", "day": 10, "budget": 300.0, "supply": 20.0},
    {"name": "late_resource_scarce", "day": 18, "budget": 150.0, "supply": 16.0},
)
PRESSURE_FACTORS = {"low": (0.15, 0.20), "high": (0.70, 0.80)}
RESPONSE_THRESHOLD_FRACTION = 0.01

PAIR_FIELDS = [
    "batch_id", "condition", "experiment_id", "meta_round_id", "agent_id",
    "backend", "model", "strategy_instance_id", "background", "day", "budget",
    "supply", "focal_hp", "focal_no_water_days", "low_bid", "high_bid", "bid_delta",
    "absolute_bid_delta", "response_threshold", "opponent_response", "increase",
    "decrease", "negligible", "normalized_opponent_adjustment",
    "signed_normalized_adjustment", "valid_pair", "low_error", "high_error",
    "meta_round_file",
]

SUMMARY_FIELDS = [
    "summary_level", "condition", "model", "agent_id", "strategy_instance_id",
    "background", "opponent_response_rate", "normalized_opponent_adjustment",
    "increase_rate", "decrease_rate", "negligible_rate", "mean_signed_adjustment",
    "mean_bid_delta", "median_absolute_bid_delta", "valid_pair_count", "total_pair_count",
    "error_pair_count", "error_rate",
]


def infer_condition(batch_path: Path) -> str:
    name = batch_path.name.lower()
    if "full_code_access" in name:
        return "OPF"
    if "no_opp_info" in name or "no_opponent_info" in name:
        return "OF"
    return "unknown"


def normalize_path(value: str | Path) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else Path.cwd() / path).resolve()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_records(path: Path) -> Iterable[Dict[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        yield from (item for item in payload if isinstance(item, dict))
    elif isinstance(payload, dict):
        yield payload


def load_backend_config(exp_dir: Path) -> Dict[str, Dict[str, Any]]:
    path = exp_dir / "backend_config.json"
    if not path.exists():
        return {}
    payload = load_json(path)
    return {
        str(agent_id): spec for agent_id, spec in payload.items()
        if isinstance(payload, dict) and isinstance(spec, dict)
    }


def valid_record(record: Mapping[str, Any]) -> bool:
    return record.get("all_agents_admitted") == 1 and record.get("outcome_valid") == 1


def profile_map(record: Mapping[str, Any]) -> Dict[str, AgentProfile]:
    players = record.get("environment", {}).get("players", [])
    profiles = {}
    for item in players if isinstance(players, list) else []:
        if not isinstance(item, dict) or not str(item.get("agent_id", "")).strip():
            continue
        agent_id = str(item["agent_id"]).strip()
        profiles[agent_id] = AgentProfile(
            agent_id, int(item.get("water_requirement", 0)), float(item.get("daily_salary", 0.0))
        )
    return profiles or {profile.agent_id: profile for profile in default_agent_profiles()}


def sanitize_bid(value: Any, budget: float) -> Tuple[float, Optional[str]]:
    try:
        bid = float(value)
    except Exception:
        return 0.0, "invalid_bid_type"
    if not math.isfinite(bid):
        return 0.0, "invalid_bid_value"
    return min(float(budget), max(0.0, bid)), None


def opponent_status(
    target_id: str, profiles: Mapping[str, AgentProfile], background: Mapping[str, Any],
    pressure: str,
) -> Dict[str, Dict[str, Any]]:
    factors = PRESSURE_FACTORS[pressure]
    day = int(background["day"])
    supply = float(background["supply"])
    # Current opponent states are deliberately identical across the pair.
    current_budget = float(background["budget"])
    history_days = (max(1, day - 2), max(1, day - 1))
    output = {}
    for agent_id in sorted(profiles):
        if agent_id == target_id:
            continue
        profile = profiles[agent_id]
        bids = [min(current_budget, round(profile.daily_salary * factor, 6)) for factor in factors]
        history = [
            {
                "day": history_day, "bid": bid, "supply": supply, "hp_after": 8,
                "budget_after": current_budget, "status": "alive",
            }
            for history_day, bid in zip(history_days, bids)
        ]
        output[agent_id] = {
            "agent_id": agent_id, "hp": 8, "budget": current_budget,
            "no_water_days": 1, "alive": True,
            "water_requirement": profile.water_requirement,
            "daily_salary": profile.daily_salary,
            "last_bid": bids[-1], "last_status": "alive", "last_hp_after": 8,
            "last_budget_after": current_budget, "trace_history": history,
        }
    return output


def make_case(background: Mapping[str, Any], opponents: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "day_context": {"day": int(background["day"]), "supply": float(background["supply"])},
        "my_status": {
            "hp": FOCAL_STATE["hp"], "budget": float(background["budget"]),
            "no_water_days": FOCAL_STATE["no_water_days"],
        },
        "opponents_status": deepcopy(opponents),
    }


def build_cases(agent_id: str, profiles: Mapping[str, AgentProfile]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    cases, specs = [], []
    for background in BACKGROUNDS:
        low = make_case(background, opponent_status(agent_id, profiles, background, "low"))
        high = make_case(background, opponent_status(agent_id, profiles, background, "high"))
        low_index = len(cases); cases.append(low)
        high_index = len(cases); cases.append(high)
        specs.append({
            "background": background, "low_index": low_index, "high_index": high_index,
        })
    return cases, specs


def _worker(output: multiprocessing.Queue, code: str, cases: List[Dict[str, Any]]) -> None:
    namespace: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
    try:
        exec(code, namespace, namespace)
        policy = namespace.get("get_bid")
        if not callable(policy):
            output.put({"error": "missing_get_bid", "results": []})
            return
        parameter_count = len(inspect.signature(policy).parameters)
        results = []
        for case in cases:
            try:
                args = (case["day_context"], case["my_status"], case["opponents_status"])
                raw = policy(*args) if parameter_count >= 3 else policy(*args[:2])
                bid, error = sanitize_bid(raw, case["my_status"]["budget"])
                results.append({"bid": bid, "error": error})
            except Exception as exc:
                results.append({"bid": None, "error": f"runtime_error: {exc}"})
        output.put({"error": None, "results": results})
    except BaseException as exc:
        output.put({"error": f"compile_error: {exc}", "results": []})


def execute_cases(code: str, cases: List[Dict[str, Any]], timeout: float) -> List[Tuple[Optional[float], Optional[str]]]:
    error = _static_check(code)
    if error:
        return [(None, error) for _ in cases]
    output: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    process = multiprocessing.Process(target=_worker, args=(output, code, cases), daemon=True)
    process.start()
    try:
        payload = output.get(timeout=timeout)
    except queue.Empty:
        process.terminate(); process.join()
        return [(None, "runtime_timeout") for _ in cases]
    process.join(1.0)
    if process.is_alive():
        process.terminate(); process.join()
    if payload.get("error"):
        return [(None, str(payload["error"])) for _ in cases]
    raw_results = payload.get("results", [])
    return [
        (
            raw_results[index].get("bid"), raw_results[index].get("error")
        ) if index < len(raw_results) else (None, "runtime_error: missing_case_result")
        for index in range(len(cases))
    ]


def execute_cases_in_process(
    code: str, cases: List[Dict[str, Any]], timeout: float,
) -> List[Tuple[Optional[float], Optional[str]]]:
    error = _static_check(code)
    if error:
        return [(None, error) for _ in cases]

    def alarm_handler(signum: int, frame: Any) -> None:
        del signum, frame
        raise TimeoutError("runtime_timeout")

    previous_handler = signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        namespace: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
        exec(code, namespace, namespace)
        policy = namespace.get("get_bid")
        if not callable(policy):
            return [(None, "missing_get_bid") for _ in cases]
        parameter_count = len(inspect.signature(policy).parameters)
        output = []
        for case in cases:
            try:
                args = (case["day_context"], case["my_status"], case["opponents_status"])
                raw = policy(*args) if parameter_count >= 3 else policy(*args[:2])
                bid, case_error = sanitize_bid(raw, case["my_status"]["budget"])
                output.append((bid if case_error is None else None, case_error))
            except TimeoutError:
                raise
            except Exception as exc:
                output.append((None, f"runtime_error: {exc}"))
        return output
    except TimeoutError:
        return [(None, "runtime_timeout") for _ in cases]
    except Exception as exc:
        return [(None, f"compile_error: {exc}") for _ in cases]
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def assert_paired_cases(low: Mapping[str, Any], high: Mapping[str, Any]) -> None:
    assert low["day_context"] == high["day_context"]
    assert low["my_status"] == high["my_status"]
    assert set(low["opponents_status"]) == set(high["opponents_status"])
    for agent_id in low["opponents_status"]:
        left, right = deepcopy(low["opponents_status"][agent_id]), deepcopy(high["opponents_status"][agent_id])
        left_last, right_last = left.pop("last_bid"), right.pop("last_bid")
        left_history, right_history = left.pop("trace_history"), right.pop("trace_history")
        assert left == right
        assert left_last == left_history[-1]["bid"] and right_last == right_history[-1]["bid"]
        for left_trace, right_trace in zip(left_history, right_history):
            left_bid, right_bid = left_trace.pop("bid"), right_trace.pop("bid")
            assert left_trace == right_trace
            assert right_bid > left_bid


def pair_row(metadata: Mapping[str, Any], spec: Mapping[str, Any],
             cases: List[Dict[str, Any]], results: List[Tuple[Optional[float], Optional[str]]]) -> Dict[str, Any]:
    low_case, high_case = cases[spec["low_index"]], cases[spec["high_index"]]
    assert_paired_cases(low_case, high_case)
    low_bid, low_error = results[spec["low_index"]]
    high_bid, high_error = results[spec["high_index"]]
    valid = low_error is None and high_error is None and low_bid is not None and high_bid is not None
    budget = float(spec["background"]["budget"])
    threshold = RESPONSE_THRESHOLD_FRACTION * budget
    delta = float(high_bid - low_bid) if valid else None
    absolute = abs(delta) if delta is not None else None
    row = dict(metadata)
    row.update({
        "background": spec["background"]["name"], "day": spec["background"]["day"],
        "budget": budget, "supply": spec["background"]["supply"],
        "focal_hp": FOCAL_STATE["hp"], "focal_no_water_days": FOCAL_STATE["no_water_days"],
        "low_bid": round(low_bid, 6) if low_bid is not None else None,
        "high_bid": round(high_bid, 6) if high_bid is not None else None,
        "bid_delta": round(delta, 6) if delta is not None else None,
        "absolute_bid_delta": round(absolute, 6) if absolute is not None else None,
        "response_threshold": threshold,
        "opponent_response": int(absolute > threshold) if valid else None,
        "increase": int(delta > threshold) if valid else None,
        "decrease": int(delta < -threshold) if valid else None,
        "negligible": int(absolute <= threshold) if valid else None,
        "normalized_opponent_adjustment": round(absolute / budget, 6) if valid else None,
        "signed_normalized_adjustment": round(delta / budget, 6) if valid else None,
        "valid_pair": int(valid), "low_error": low_error, "high_error": high_error,
    })
    return row


def evaluate_strategy_task(task: Tuple[Dict[str, Any], str, str, Dict[str, AgentProfile]],
                           timeout: float, execution_mode: str) -> List[Dict[str, Any]]:
    metadata, code, agent_id, profiles = task
    cases, specs = build_cases(agent_id, profiles)
    results = (
        execute_cases_in_process(code, cases, timeout)
        if execution_mode == "in-process" else execute_cases(code, cases, timeout)
    )
    return [pair_row(metadata, spec, cases, results) for spec in specs]


def evaluate_batches(batch_paths: Sequence[Path], timeout: float,
                     strategy_offset: int, max_strategies: Optional[int], workers: int,
                     execution_mode: str) -> List[Dict[str, Any]]:
    tasks: List[Tuple[Dict[str, Any], str, str, Dict[str, AgentProfile]]] = []
    for batch_path in batch_paths:
        if not batch_path.exists():
            raise FileNotFoundError(batch_path)
        for meta_file in sorted(batch_path.glob("exp_*/meta_round_*.json")):
            configs = load_backend_config(meta_file.parent)
            for record in iter_records(meta_file):
                if not valid_record(record):
                    continue
                profiles = profile_map(record)
                for agent in record.get("agents", []):
                    if not isinstance(agent, dict):
                        continue
                    agent_id, code = str(agent.get("agent_id", "")).strip(), agent.get("strategy_code")
                    if not agent_id or not isinstance(code, str) or not code.strip():
                        continue
                    config = configs.get(agent_id, {})
                    meta_round_id = record.get("meta_round_id")
                    metadata = {
                        "batch_id": batch_path.name, "condition": infer_condition(batch_path),
                        "experiment_id": meta_file.parent.name, "meta_round_id": meta_round_id,
                        "agent_id": agent_id, "backend": str(config.get("backend", "unknown")),
                        "model": str(config.get("model", "unknown")),
                        "strategy_instance_id": f"{batch_path.name}/{meta_file.parent.name}/mr_{meta_round_id}/{agent_id}",
                        "meta_round_file": str(meta_file),
                    }
                    tasks.append((metadata, code, agent_id, profiles))
    tasks = tasks[max(0, strategy_offset):]
    if max_strategies is not None:
        tasks = tasks[:max_strategies]
    rows = []
    if execution_mode == "in-process":
        for task in tasks:
            rows.extend(evaluate_strategy_task(task, timeout, execution_mode))
    else:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
            for task_rows in executor.map(
                lambda task: evaluate_strategy_task(task, timeout, execution_mode), tasks
            ):
                rows.extend(task_rows)
    return rows


METRIC_FIELDS = {
    "opponent_response_rate": "opponent_response",
    "normalized_opponent_adjustment": "normalized_opponent_adjustment",
    "increase_rate": "increase", "decrease_rate": "decrease",
    "negligible_rate": "negligible", "mean_signed_adjustment": "signed_normalized_adjustment",
    "mean_bid_delta": "bid_delta",
}


def mean(rows: Sequence[Mapping[str, Any]], field: str) -> Optional[float]:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return sum(values) / len(values) if values else None


def role_balanced_mean(rows: Sequence[Mapping[str, Any]], field: str) -> Optional[float]:
    grouped: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["agent_id"])].append(row)
    values = [mean(group, field) for group in grouped.values()]
    valid = [value for value in values if value is not None]
    return sum(valid) / len(valid) if valid else None


def rounded(value: Optional[float]) -> Optional[float]:
    return round(value, 6) if value is not None else None


def summarize(rows: List[Dict[str, Any]], labels: Mapping[str, Any], role_balanced: bool) -> Dict[str, Any]:
    valid = [row for row in rows if row["valid_pair"] == 1]
    calculator = role_balanced_mean if role_balanced else mean
    result = {
        "summary_level": labels.get("summary_level"), "condition": labels.get("condition", "ALL"),
        "model": labels.get("model", "ALL"), "agent_id": labels.get("agent_id", "ALL"),
        "strategy_instance_id": labels.get("strategy_instance_id", "ALL"),
        "background": labels.get("background", "ALL"),
    }
    for output, source in METRIC_FIELDS.items():
        result[output] = rounded(calculator(valid, source))
    absolute_deltas = [float(row["absolute_bid_delta"]) for row in valid]
    result["median_absolute_bid_delta"] = round(statistics.median(absolute_deltas), 6) if absolute_deltas else None
    result.update({
        "valid_pair_count": len(valid), "total_pair_count": len(rows),
        "error_pair_count": len(rows) - len(valid),
        "error_rate": round((len(rows) - len(valid)) / len(rows), 6) if rows else None,
    })
    return result


def grouped_summaries(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    definitions = {
        "strategy": (("condition", "model", "agent_id", "strategy_instance_id"), False),
        "role": (("condition", "model", "agent_id"), False),
        "model": (("condition", "model"), True),
        "condition": (("condition",), True),
        "background": (("condition", "model", "background"), True),
    }
    output = {}
    for level, (fields, role_balanced) in definitions.items():
        groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row[field] for field in fields)].append(row)
        output[level] = []
        for key, items in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
            labels = dict(zip(fields, key)); labels["summary_level"] = level
            output[level].append(summarize(items, labels, role_balanced))
    return output


def condition_differences(model_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in model_rows:
        grouped[str(row["model"])][str(row["condition"])] = row
    output = []
    fields = list(METRIC_FIELDS) + ["error_rate"]
    for model, conditions in sorted(grouped.items()):
        if "OF" not in conditions or "OPF" not in conditions:
            continue
        row = {"model": model, "comparison": "OPF-OF"}
        for field in fields:
            opf, of = conditions["OPF"].get(field), conditions["OF"].get(field)
            row[field] = round(float(opf) - float(of), 6) if opf is not None and of is not None else None
        output.append(row)
    return output


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Optional[Sequence[str]] = None) -> None:
    selected = list(fields or (list(rows[0]) if rows else []))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected, extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fmt(value: Any, percent: bool = False) -> str:
    if value is None:
        return "NA"
    return f"{100 * float(value):.1f}" if percent else f"{float(value):.4f}"


def write_markdown(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    lines = [
        "# Opponent-Aware Decision-Making Results", "",
        "| Condition | Model | ORR (%) | NOA (%) | Increase (%) | Decrease (%) | Negligible (%) | Error (%) |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in sorted(rows, key=lambda item: (str(item["condition"]), str(item["model"]))):
        lines.append(
            f"| {row['condition']} | {row['model']} | {fmt(row['opponent_response_rate'], True)} | "
            f"{fmt(row['normalized_opponent_adjustment'], True)} | {fmt(row['increase_rate'], True)} | "
            f"{fmt(row['decrease_rate'], True)} | {fmt(row['negligible_rate'], True)} | "
            f"{fmt(row['error_rate'], True)} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_plots(output_dir: Path, model_rows: Sequence[Mapping[str, Any]]) -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = sorted(model_rows, key=lambda item: (str(item["model"]), str(item["condition"])))
    cells = [[
        row["model"], row["condition"], fmt(row["opponent_response_rate"], True),
        fmt(row["normalized_opponent_adjustment"], True), fmt(row["increase_rate"], True),
        fmt(row["decrease_rate"], True), fmt(row["negligible_rate"], True),
    ] for row in rows]
    fig, ax = plt.subplots(figsize=(12, max(3.2, 0.45 * (len(cells) + 3))))
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=[
        "Model", "Feedback", "ORR (%)", "NOA (%)", "Increase (%)", "Decrease (%)", "Negligible (%)"
    ], cellLoc="center", loc="center")
    table.auto_set_font_size(False); table.set_fontsize(8.5); table.scale(1, 1.45)
    for column in range(7):
        table[(0, column)].set_text_props(weight="bold"); table[(0, column)].set_facecolor("#D9EAF7")
    ax.set_title("Opponent-Aware Decision Making", pad=12)
    fig.tight_layout(); fig.savefig(output_dir / "opponent_awareness_table.png", dpi=300, bbox_inches="tight"); plt.close(fig)

    labels = [f"{row['model']}\n{row['condition']}" for row in rows]
    increase = [100 * float(row["increase_rate"]) for row in rows]
    decrease = [100 * float(row["decrease_rate"]) for row in rows]
    negligible = [100 * float(row["negligible_rate"]) for row in rows]
    y = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(12, max(4.5, 0.45 * len(rows))))
    ax.barh(y, increase, label="Increase", color="#4C9F70")
    ax.barh(y, decrease, left=increase, label="Decrease", color="#D65F5F")
    ax.barh(y, negligible, left=[a + b for a, b in zip(increase, decrease)], label="Negligible", color="#BFC5CA")
    ax.set_yticks(y, labels); ax.set_xlim(0, 100); ax.set_xlabel("Paired opponent-pressure responses (%)")
    ax.invert_yaxis(); ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    fig.tight_layout(); fig.savefig(output_dir / "direction_breakdown.png", dpi=300, bbox_inches="tight"); plt.close(fig)


def write_outputs(output_dir: Path, rows: List[Dict[str, Any]], batch_paths: Sequence[Path],
                  timeout: float, workers: int, execution_mode: str, skip_plots: bool,
                  merge_inputs: Optional[Sequence[str]] = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = grouped_summaries(rows)
    differences = condition_differences(summaries["model"])
    write_csv(output_dir / "opponent_pressure_pairs.csv", rows, PAIR_FIELDS)
    write_json(output_dir / "opponent_pressure_pairs.json", rows)
    for level in ("strategy", "role", "model", "condition"):
        write_csv(output_dir / f"summary_by_{level}.csv", summaries[level], SUMMARY_FIELDS)
        write_json(output_dir / f"summary_by_{level}.json", summaries[level])
    write_csv(output_dir / "summary_by_background.csv", summaries["background"], SUMMARY_FIELDS)
    write_json(output_dir / "summary_by_background.json", summaries["background"])
    write_csv(output_dir / "opf_minus_of_by_model.csv", differences)
    write_json(output_dir / "opf_minus_of_by_model.json", differences)
    write_markdown(output_dir / "opponent_awareness_table.md", summaries["model"])
    meta_rounds = sorted({int(row["meta_round_id"]) for row in rows if row.get("meta_round_id") is not None})
    config = {
        "input_batches": [str(path) for path in batch_paths], "timeout_seconds": timeout,
        "workers": workers,
        "execution_mode": execution_mode,
        "merge_inputs": list(merge_inputs or []),
        "focal_state": FOCAL_STATE, "backgrounds": list(BACKGROUNDS),
        "pressure_factors_by_daily_salary": PRESSURE_FACTORS,
        "response_threshold_fraction_of_focal_budget": RESPONSE_THRESHOLD_FRACTION,
        "meta_rounds": meta_rounds,
        "metrics": {
            "ORR": "mean(I(abs(high_bid-low_bid) > 0.01*focal_budget))",
            "NOA": "mean(abs(high_bid-low_bid)/focal_budget)",
            "direction": "increase/decrease use the same strict 1% threshold; boundary is negligible",
            "aggregation": "model summaries first average within agent role, then equally across observed roles",
        },
        "total_pair_count": len(rows), "valid_pair_count": sum(row["valid_pair"] for row in rows),
        "error_pair_count": sum(1 - row["valid_pair"] for row in rows),
    }
    write_json(output_dir / "run_config.json", config)
    if not skip_plots:
        try:
            write_plots(output_dir, summaries["model"])
        except ModuleNotFoundError as exc:
            if exc.name != "matplotlib":
                raise
            print("Warning: matplotlib is unavailable; skipped PNG outputs.")


def self_test() -> None:
    profiles = {profile.agent_id: profile for profile in default_agent_profiles()}
    cases, specs = build_cases("Alex", profiles)
    for spec in specs:
        assert_paired_cases(cases[spec["low_index"]], cases[spec["high_index"]])
    strategies = {
        "constant": "def get_bid(day_context, my_status, opponents_status):\n    return 50.0\n",
        "increase": "def get_bid(day_context, my_status, opponents_status):\n    return sum(float(x.get('last_bid', 0.0)) for x in opponents_status.values())\n",
        "decrease": "def get_bid(day_context, my_status, opponents_status):\n    return max(0.0, my_status['budget'] - sum(float(x.get('last_bid', 0.0)) for x in opponents_status.values()))\n",
        "self_only": "def get_bid(day_context, my_status, opponents_status):\n    return my_status['budget'] * 0.2\n",
        "tiny": "def get_bid(day_context, my_status, opponents_status):\n    return 50.0 + 0.001 * sum(float(x.get('last_bid', 0.0)) for x in opponents_status.values())\n",
    }
    expected = {
        "constant": (0.0, 0.0, 0.0, 1.0), "increase": (1.0, 1.0, 0.0, 0.0),
        "decrease": (1.0, 0.0, 1.0, 0.0), "self_only": (0.0, 0.0, 0.0, 1.0),
        "tiny": (0.0, 0.0, 0.0, 1.0),
    }
    for name, code in strategies.items():
        results = execute_cases(code, cases, 3.0)
        rows = [pair_row({
            "batch_id": "test", "condition": "OPF", "experiment_id": "exp",
            "meta_round_id": 1, "agent_id": "Alex", "backend": "test", "model": name,
            "strategy_instance_id": name, "meta_round_file": "test",
        }, spec, cases, results) for spec in specs]
        summary = summarize(rows, {"summary_level": "strategy", "condition": "OPF", "model": name}, False)
        values = (summary["opponent_response_rate"], summary["increase_rate"], summary["decrease_rate"], summary["negligible_rate"])
        assert values == expected[name], (name, values)
        assert abs(summary["increase_rate"] + summary["decrease_rate"] + summary["negligible_rate"] - 1.0) < 1e-9
        if name in ("constant", "self_only"):
            assert summary["normalized_opponent_adjustment"] == 0.0
    invalid = "def get_bid(day_context, my_status, opponents_status):\n    while True:\n        pass\n"
    assert all(error == "runtime_timeout" for _, error in execute_cases(invalid, cases, 0.1))
    print("Self-test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", action="append", help="Batch path; repeat for OF and OPF.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--execution-mode", choices=("isolated", "in-process"), default="isolated")
    parser.add_argument("--strategy-offset", type=int, default=0)
    parser.add_argument("--max-strategies", type=int, default=None)
    parser.add_argument(
        "--merge-input", action="append",
        help="Result directory containing opponent_pressure_pairs.json; repeat to merge shards.",
    )
    parser.add_argument("--skip-plots", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        self_test(); return
    batches = [normalize_path(value) for value in args.batch] if args.batch else list(DEFAULT_BATCHES)
    output_dir = normalize_path(args.output_dir)
    if args.merge_input:
        rows_by_pair: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for value in args.merge_input:
            payload = load_json(normalize_path(value) / "opponent_pressure_pairs.json")
            if not isinstance(payload, list):
                raise ValueError(f"Expected JSON list in {value}")
            for item in payload:
                if not isinstance(item, dict):
                    continue
                key = (str(item.get("strategy_instance_id", "")), str(item.get("background", "")))
                rows_by_pair[key] = item
        rows = sorted(
            rows_by_pair.values(),
            key=lambda row: (str(row.get("condition", "")), str(row.get("model", "")),
                             str(row.get("strategy_instance_id", "")), str(row.get("background", ""))),
        )
    else:
        rows = evaluate_batches(
            batches, args.timeout_seconds, args.strategy_offset, args.max_strategies,
            args.workers, args.execution_mode,
        )
    write_outputs(
        output_dir, rows, batches, args.timeout_seconds, args.workers,
        "merged" if args.merge_input else args.execution_mode, args.skip_plots,
        args.merge_input,
    )
    print(f"Wrote {len(rows)} opponent-pressure pairs to {output_dir}")
    for row in grouped_summaries(rows)["model"]:
        print(
            f"{row['condition']},{row['model']},ORR={row['opponent_response_rate']},"
            f"NOA={row['normalized_opponent_adjustment']},error={row['error_rate']}"
        )


if __name__ == "__main__":
    main()
