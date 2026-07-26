#!/usr/bin/env python3
"""Evaluate long-horizon action quality with paired counterfactual rollouts."""

import argparse
import copy
import csv
import inspect
import json
import math
import multiprocessing
import queue
import random
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
WACBENCH_ROOT = PROJECT_ROOT / "wacbench"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(WACBENCH_ROOT))

import delayed_scarcity as ds
from package_paths import package_relative
from sandbox_executor import _static_check


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "counterfactual_planning"
CHECKPOINT_DAYS = (4, 9, 14)
BASELINE_SEED = 7001
FUTURE_SEEDS = (8101, 8209, 8317)
BUDGET_FRACTIONS = (0.0, 0.10, 0.25, 0.50, 1.0)
NEAR_OPTIMAL_TOLERANCE_DAYS = 1.0 / len(FUTURE_SEEDS)

ROW_FIELDS = [
    "batch_id", "condition", "experiment_id", "meta_round_id", "agent_id",
    "backend", "model", "strategy_instance_id", "checkpoint_day", "checkpoint_supply",
    "checkpoint_hp", "checkpoint_budget", "checkpoint_no_water_days",
    "alive_opponent_count", "policy_bid", "candidate_action_count",
    "policy_expected_remaining_survival", "best_expected_remaining_survival",
    "worst_expected_remaining_survival", "survival_regret", "policy_long_horizon_value",
    "best_long_horizon_value", "worst_long_horizon_value", "long_horizon_value_regret",
    "normalized_action_quality", "optimal_action", "near_optimal_action",
    "informative_state", "best_actions", "action_values", "runtime_error",
    "meta_round_file",
]

SUMMARY_FIELDS = [
    "summary_level", "condition", "model", "agent_id", "strategy_instance_id", "checkpoint_day",
    "counterfactual_action_quality", "optimal_action_rate", "near_optimal_action_rate",
    "mean_survival_regret", "mean_long_horizon_value_regret",
    "mean_policy_expected_remaining_survival",
    "informative_state_rate", "informative_state_count", "valid_state_count",
    "total_state_count", "error_state_count", "error_rate",
]


def baseline_supplies() -> List[int]:
    rng = random.Random(BASELINE_SEED)
    return [rng.randint(15, 25) for _ in range(ds.EPISODE_DAYS)]


def future_supplies(seed: int, count: int) -> List[int]:
    rng = random.Random(seed)
    # Stress the action choice with persistent scarcity while staying inside
    # the experiment's declared medium-scenario range of [15, 25].
    return [rng.randint(15, 20) for _ in range(count)]


def initial_episode_state(profiles: Dict[str, ds.AgentProfile]) -> Dict[str, Any]:
    return {
        "runtime": {
            agent_id: {"hp": 8, "budget": 0.0, "no_water_days": 1, "alive": True}
            for agent_id in profiles
        },
        "traces": {agent_id: [] for agent_id in profiles},
    }


def call_focal_policy(policy: Any, parameter_count: int, target_id: str,
                      profiles: Dict[str, ds.AgentProfile], state: Dict[str, Any],
                      day: int, supply: float) -> Tuple[float, Optional[str]]:
    mine = state["runtime"][target_id]
    context = {"day": day, "supply": supply}
    my_status = {key: mine[key] for key in ("hp", "budget", "no_water_days")}
    opponents = ds.opponents_status(target_id, profiles, state["runtime"], state["traces"])
    args = (context, my_status, opponents)
    try:
        raw_bid = policy(*args) if parameter_count >= 3 else policy(*args[:2])
        return ds.sanitized_bid(raw_bid, mine["budget"]), None
    except Exception as exc:
        return 0.0, f"runtime_error: {exc}"


def advance_day(state: Dict[str, Any], profiles: Dict[str, ds.AgentProfile],
                target_id: str, policy: Any, parameter_count: int, day: int,
                supply: float, forced_focal_bid: Optional[float] = None) -> Optional[str]:
    runtime, traces = state["runtime"], state["traces"]
    for agent_id, profile in profiles.items():
        if runtime[agent_id]["alive"]:
            runtime[agent_id]["budget"] += profile.daily_salary

    bids: Dict[str, float] = {}
    errors: Dict[str, Optional[str]] = {}
    for agent_id, profile in profiles.items():
        current = runtime[agent_id]
        if not current["alive"]:
            bids[agent_id], errors[agent_id] = 0.0, None
        elif agent_id == target_id:
            if forced_focal_bid is None:
                bids[agent_id], errors[agent_id] = call_focal_policy(
                    policy, parameter_count, target_id, profiles, state, day, supply
                )
            else:
                bids[agent_id] = ds.sanitized_bid(forced_focal_bid, current["budget"])
                errors[agent_id] = None
        else:
            bids[agent_id] = ds.fixed_opponent_bid(
                day, supply, current["hp"], current["no_water_days"],
                current["budget"], profile,
            )
            errors[agent_id] = None

    winners = set(ds.allocate(bids, profiles, supply, day))
    for agent_id in profiles:
        current = runtime[agent_id]
        if current["alive"]:
            if agent_id in winners:
                current["hp"] = min(10, current["hp"] + 2)
                current["budget"] -= bids[agent_id]
                current["no_water_days"] = 1
            else:
                current["hp"] -= current["no_water_days"]
                current["no_water_days"] += 1
            if current["hp"] <= 0:
                current["alive"], current["budget"] = False, 0.0
        traces[agent_id].append({
            "day": day, "bid": bids[agent_id], "supply": supply,
            "hp_after": current["hp"], "budget_after": current["budget"],
            "status": "alive" if current["alive"] else "dead",
            "error": errors[agent_id],
        })
    return errors.get(target_id)


def build_checkpoint_states(code: str, target_id: str,
                            profiles: Dict[str, ds.AgentProfile]) -> Tuple[
                                List[Tuple[int, float, Dict[str, Any], float]], Optional[str]
                            ]:
    policy, parameter_count = ds.compile_policy(code)
    supplies = baseline_supplies()
    state = initial_episode_state(profiles)
    checkpoints = []
    for day in range(1, ds.EPISODE_DAYS + 1):
        supply = float(supplies[day - 1])
        if day in CHECKPOINT_DAYS and state["runtime"][target_id]["alive"]:
            # Salary is credited before bidding in the real environment.
            snapshot = copy.deepcopy(state)
            for agent_id, profile in profiles.items():
                if snapshot["runtime"][agent_id]["alive"]:
                    snapshot["runtime"][agent_id]["budget"] += profile.daily_salary
            policy_bid, error = call_focal_policy(
                policy, parameter_count, target_id, profiles, snapshot, day, supply
            )
            if error:
                return [], error
            checkpoints.append((day, supply, copy.deepcopy(state), policy_bid))
        error = advance_day(state, profiles, target_id, policy, parameter_count, day, supply)
        if error:
            return [], error
    return checkpoints, None


def candidate_actions(policy_bid: float, available_budget: float) -> List[float]:
    candidates = [available_budget * fraction for fraction in BUDGET_FRACTIONS]
    candidates.append(policy_bid)
    return sorted({round(ds.sanitized_bid(value, available_budget), 6) for value in candidates})


def remaining_survival_for_action(code: str, target_id: str,
                                  profiles: Dict[str, ds.AgentProfile],
                                  checkpoint_state: Dict[str, Any], checkpoint_day: int,
                                  checkpoint_supply: float, action: float,
                                  future_seed: int) -> Tuple[float, float, Optional[str]]:
    policy, parameter_count = ds.compile_policy(code)
    state = copy.deepcopy(checkpoint_state)
    error = advance_day(
        state, profiles, target_id, policy, parameter_count, checkpoint_day,
        checkpoint_supply, forced_focal_bid=action,
    )
    if error:
        return 0.0, 0.0, error
    survived = 1.0 if state["runtime"][target_id]["alive"] else 0.0
    remaining_days = ds.EPISODE_DAYS - checkpoint_day
    supplies = future_supplies(future_seed, remaining_days)
    for offset, supply in enumerate(supplies, start=1):
        if not state["runtime"][target_id]["alive"]:
            break
        day = checkpoint_day + offset
        error = advance_day(state, profiles, target_id, policy, parameter_count, day, float(supply))
        if error:
            return survived, 0.0, error
        if state["runtime"][target_id]["alive"]:
            survived += 1.0
    focal = state["runtime"][target_id]
    horizon_days = ds.EPISODE_DAYS - checkpoint_day + 1
    max_budget = (
        float(checkpoint_state["runtime"][target_id]["budget"])
        + profiles[target_id].daily_salary * horizon_days
    )
    terminal_hp = max(0.0, min(10.0, float(focal["hp"]))) / 10.0
    terminal_budget = max(0.0, float(focal["budget"])) / max_budget if max_budget > 0 else 0.0
    terminal_quality = 0.5 * terminal_hp + 0.5 * min(1.0, terminal_budget)
    # The tie-break is strictly smaller than one survival day, so surviving
    # one additional day always dominates terminal health or savings.
    long_horizon_value = survived + terminal_quality / (horizon_days + 1.0)
    return survived, long_horizon_value, None


def evaluate_checkpoint(code: str, target_id: str, profiles: Dict[str, ds.AgentProfile],
                        checkpoint: Tuple[int, float, Dict[str, Any], float]) -> Dict[str, Any]:
    day, supply, state, policy_bid = checkpoint
    pre_salary_budget = float(state["runtime"][target_id]["budget"])
    available_budget = pre_salary_budget + profiles[target_id].daily_salary
    actions = candidate_actions(policy_bid, available_budget)
    values: Dict[float, float] = {}
    survival_values: Dict[float, float] = {}
    for action in actions:
        outcomes = []
        value_outcomes = []
        for seed in FUTURE_SEEDS:
            survived, long_horizon_value, error = remaining_survival_for_action(
                code, target_id, profiles, state, day, supply, action, seed
            )
            if error:
                return {"runtime_error": error}
            outcomes.append(survived)
            value_outcomes.append(long_horizon_value)
        survival_values[action] = sum(outcomes) / len(outcomes)
        values[action] = sum(value_outcomes) / len(value_outcomes)

    policy_key = round(policy_bid, 6)
    policy_value = values[policy_key]
    best_value, worst_value = max(values.values()), min(values.values())
    value_regret = best_value - policy_value
    policy_survival = survival_values[policy_key]
    best_survival, worst_survival = max(survival_values.values()), min(survival_values.values())
    survival_regret = best_survival - policy_survival
    informative = best_value - worst_value > 1e-9
    quality = ((policy_value - worst_value) / (best_value - worst_value)) if informative else None
    best_actions = [action for action, value in values.items() if abs(value - best_value) <= 1e-9]
    runtime = state["runtime"][target_id]
    return {
        "checkpoint_day": day, "checkpoint_supply": supply,
        "checkpoint_hp": runtime["hp"], "checkpoint_budget": available_budget,
        "checkpoint_no_water_days": runtime["no_water_days"],
        "alive_opponent_count": sum(
            int(item["alive"]) for agent_id, item in state["runtime"].items()
            if agent_id != target_id
        ),
        "policy_bid": round(policy_bid, 6), "candidate_action_count": len(actions),
        "policy_expected_remaining_survival": round(policy_survival, 6),
        "best_expected_remaining_survival": round(best_survival, 6),
        "worst_expected_remaining_survival": round(worst_survival, 6),
        "survival_regret": round(survival_regret, 6),
        "policy_long_horizon_value": round(policy_value, 6),
        "best_long_horizon_value": round(best_value, 6),
        "worst_long_horizon_value": round(worst_value, 6),
        "long_horizon_value_regret": round(value_regret, 6),
        "normalized_action_quality": round(quality, 6) if quality is not None else None,
        "optimal_action": int(value_regret <= 1e-9),
        "near_optimal_action": int(survival_regret <= NEAR_OPTIMAL_TOLERANCE_DAYS + 1e-9),
        "informative_state": int(informative),
        "best_actions": json.dumps(best_actions),
        "action_values": json.dumps({str(key): round(value, 6) for key, value in values.items()}),
        "runtime_error": None,
    }


def strategy_worker(output: multiprocessing.Queue, code: str, target_id: str,
                    raw_profiles: List[Tuple[str, int, float]]) -> None:
    try:
        profiles = {item[0]: ds.AgentProfile(*item) for item in raw_profiles}
        checkpoints, error = build_checkpoint_states(code, target_id, profiles)
        if error:
            output.put({"error": error, "rows": []})
            return
        rows = [evaluate_checkpoint(code, target_id, profiles, checkpoint) for checkpoint in checkpoints]
        error_rows = [row for row in rows if row.get("runtime_error")]
        output.put({"error": error_rows[0]["runtime_error"] if error_rows else None, "rows": rows})
    except Exception as exc:
        output.put({"error": f"runtime_error: {exc}", "rows": []})


def evaluate_strategy(code: str, target_id: str, profiles: Dict[str, ds.AgentProfile],
                      timeout: float) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    static_error = _static_check(code)
    if static_error:
        return [], static_error
    output: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    raw_profiles = [(p.agent_id, p.water_requirement, p.daily_salary) for p in profiles.values()]
    process = multiprocessing.Process(
        target=strategy_worker, args=(output, code, target_id, raw_profiles), daemon=True
    )
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join()
        return [], "runtime_timeout"
    try:
        payload = output.get_nowait()
    except queue.Empty:
        return [], "runtime_error: no_result"
    return payload.get("rows", []), payload.get("error")


def evaluate_one_task(task: Tuple[Dict[str, Any], str, str, Dict[str, ds.AgentProfile]],
                      timeout: float) -> List[Dict[str, Any]]:
    metadata, code, agent_id, profiles = task
    output_rows = []
    results, error = evaluate_strategy(code, agent_id, profiles, timeout)
    if error and not results:
        for day in CHECKPOINT_DAYS:
            row = dict(metadata)
            row.update({"checkpoint_day": day, "runtime_error": error})
            output_rows.append(row)
    else:
        for result in results:
            row = dict(metadata)
            row.update(result)
            output_rows.append(row)
    return output_rows


def evaluate_batches(batch_paths: Sequence[Path], timeout: float,
                     max_strategies: Optional[int], workers: int) -> List[Dict[str, Any]]:
    tasks = []
    for batch_path in batch_paths:
        for meta_file in sorted(batch_path.glob("exp_*/meta_round_*.json")):
            configs = ds.load_backend_config(meta_file.parent)
            for record in ds.iter_records(meta_file):
                if not ds.valid_record(record):
                    continue
                profiles = ds.profile_map(record)
                for agent in record.get("agents", []):
                    if not isinstance(agent, dict):
                        continue
                    agent_id, code = str(agent.get("agent_id", "")).strip(), agent.get("strategy_code")
                    if not agent_id or agent_id not in profiles or not isinstance(code, str) or not code.strip():
                        continue
                    if max_strategies is not None and len(tasks) >= max_strategies:
                        break
                    config = configs.get(agent_id, {})
                    metadata = {
                        "batch_id": batch_path.name, "condition": ds.infer_condition(batch_path),
                        "experiment_id": meta_file.parent.name,
                        "meta_round_id": record.get("meta_round_id"), "agent_id": agent_id,
                        "backend": str(config.get("backend", "unknown")),
                        "model": str(config.get("model", "unknown")),
                        "strategy_instance_id": (
                            f"{batch_path.name}/{meta_file.parent.name}/"
                            f"mr_{record.get('meta_round_id')}/{agent_id}"
                        ),
                        "meta_round_file": package_relative(meta_file),
                    }
                    tasks.append((metadata, code, agent_id, profiles))
                if max_strategies is not None and len(tasks) >= max_strategies:
                    break
            if max_strategies is not None and len(tasks) >= max_strategies:
                break
        if max_strategies is not None and len(tasks) >= max_strategies:
            break

    rows = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        for task_rows in executor.map(lambda task: evaluate_one_task(task, timeout), tasks):
            rows.extend(task_rows)
    return rows


def mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def rounded(value: Optional[float]) -> Optional[float]:
    return round(value, 6) if value is not None else None


def summarize(rows: List[Dict[str, Any]], labels: Dict[str, Any]) -> Dict[str, Any]:
    valid = [row for row in rows if not row.get("runtime_error")]
    informative = [row for row in valid if row.get("informative_state") == 1]
    total = len(rows)
    return {
        "summary_level": labels.get("summary_level"),
        "condition": labels.get("condition", "ALL"), "model": labels.get("model", "ALL"),
        "agent_id": labels.get("agent_id", "ALL"),
        "strategy_instance_id": labels.get("strategy_instance_id", "ALL"),
        "checkpoint_day": labels.get("checkpoint_day", "ALL"),
        "counterfactual_action_quality": rounded(mean([
            float(row["normalized_action_quality"]) for row in informative
        ])),
        "optimal_action_rate": rounded(mean([float(row["optimal_action"]) for row in informative])),
        "near_optimal_action_rate": rounded(mean([
            float(row["near_optimal_action"]) for row in informative
        ])),
        "mean_survival_regret": rounded(mean([float(row["survival_regret"]) for row in informative])),
        "mean_long_horizon_value_regret": rounded(mean([
            float(row["long_horizon_value_regret"]) for row in informative
        ])),
        "mean_policy_expected_remaining_survival": rounded(mean([
            float(row["policy_expected_remaining_survival"]) for row in valid
        ])),
        "informative_state_rate": rounded(len(informative) / len(valid)) if valid else None,
        "informative_state_count": len(informative), "valid_state_count": len(valid),
        "total_state_count": total, "error_state_count": total - len(valid),
        "error_rate": rounded((total - len(valid)) / total) if total else None,
    }


def grouped_summaries(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    definitions = {
        "strategy": ("condition", "model", "agent_id", "strategy_instance_id"),
        "agent": ("condition", "model", "agent_id"),
        "model": ("condition", "model"),
        "checkpoint": ("condition", "model", "checkpoint_day"),
    }
    output = {}
    for level, fields in definitions.items():
        groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[tuple(row[field] for field in fields)].append(row)
        output[level] = []
        for key, group in sorted(groups.items(), key=lambda item: tuple(str(x) for x in item[0])):
            labels = dict(zip(fields, key))
            labels["summary_level"] = level
            output[level].append(summarize(group, labels))
    return output


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field) for field in fields} for row in rows)


def write_table_png(path: Path, rows: List[Dict[str, Any]]) -> None:
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(path.parent / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ordered = sorted(rows, key=lambda row: (str(row["model"]), str(row["condition"])))
    cells = [[row["model"], row["condition"],
              f"{100 * row['counterfactual_action_quality']:.1f}" if row["counterfactual_action_quality"] is not None else "NA",
              f"{100 * row['optimal_action_rate']:.1f}" if row["optimal_action_rate"] is not None else "NA",
              f"{row['mean_long_horizon_value_regret']:.3f}" if row["mean_long_horizon_value_regret"] is not None else "NA",
              f"{100 * row['informative_state_rate']:.1f}" if row["informative_state_rate"] is not None else "NA"]
             for row in ordered]
    fig, ax = plt.subplots(figsize=(10.5, max(3.2, 0.43 * (len(cells) + 3))))
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=[
        "Model", "Feedback", "Action quality (%)", "Optimal (%)",
        "Survival regret", "Informative (%)",
    ], cellLoc="center", loc="center", colWidths=[0.25, 0.11, 0.18, 0.15, 0.16, 0.15])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)
    for column in range(6):
        table[(0, column)].set_text_props(weight="bold")
    ax.set_title("Counterfactual Long-Horizon Action Quality", fontsize=12, pad=12)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_outputs(output_dir: Path, rows: List[Dict[str, Any]], batch_paths: Sequence[Path],
                  timeout: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = grouped_summaries(rows)
    write_csv(output_dir / "counterfactual_states.csv", rows, ROW_FIELDS)
    (output_dir / "counterfactual_states.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for level, values in summaries.items():
        write_csv(output_dir / f"counterfactual_summary_by_{level}.csv", values, SUMMARY_FIELDS)
        (output_dir / f"counterfactual_summary_by_{level}.json").write_text(
            json.dumps(values, indent=2), encoding="utf-8"
        )
    write_table_png(output_dir / "counterfactual_table.png", summaries["model"])
    config = {
        "input_batches": [package_relative(path) for path in batch_paths],
        "checkpoint_days": list(CHECKPOINT_DAYS), "baseline_seed": BASELINE_SEED,
        "future_seeds": list(FUTURE_SEEDS), "candidate_budget_fractions": list(BUDGET_FRACTIONS),
        "future_supply_range": [15, 20],
        "candidate_policy_action_included": True,
        "value": "mean remaining survival days plus a sub-one-day terminal HP/budget tie-break",
        "terminal_tie_break": "0.5*(HP/10)+0.5*(final budget/max attainable budget), divided by horizon_days+1",
        "counterfactual_action_quality": "(V(policy)-V(worst))/(V(best)-V(worst)); informative states only",
        "near_optimal_tolerance_days": NEAR_OPTIMAL_TOLERANCE_DAYS,
        "timeout_seconds_per_strategy": timeout,
    }
    (output_dir / "run_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def self_test() -> None:
    profiles = {profile.agent_id: profile for profile in ds.default_agent_profiles()}
    code = "def get_bid(day_context, my_status, opponents_status):\n    return min(60, my_status['budget'])\n"
    checkpoints, error = build_checkpoint_states(code, "Alex", profiles)
    assert error is None and checkpoints
    rows, error = evaluate_strategy(code, "Alex", profiles, 10.0)
    assert error is None and rows
    assert all(0 <= row["normalized_action_quality"] <= 1 for row in rows if row["informative_state"])
    assert all(row["survival_regret"] >= 0 for row in rows)
    actions = candidate_actions(37.0, 100.0)
    assert 37.0 in actions and 0.0 in actions and 100.0 in actions
    print("Self-test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Counterfactual rollout evaluation of WAC planning actions.")
    parser.add_argument("--batch", action="append", help="Batch directory; repeat for OF and OPF.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-strategies", type=int, default=None)
    parser.add_argument(
        "--merge-input", action="append",
        help="Result directory containing counterfactual_states.json; repeat to merge without replay.",
    )
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        self_test()
        return
    batches = [ds.normalize_path(value) for value in args.batch] if args.batch else ds.DEFAULT_BATCHES
    output_dir = ds.normalize_path(args.output_dir)
    if args.merge_input:
        rows = []
        for value in args.merge_input:
            path = ds.normalize_path(value) / "counterfactual_states.json"
            payload = ds.load_json(path)
            if not isinstance(payload, list):
                raise ValueError(f"Expected a JSON list: {path}")
            rows.extend(item for item in payload if isinstance(item, dict))
    else:
        rows = evaluate_batches(batches, args.timeout_seconds, args.max_strategies, args.workers)
    write_outputs(output_dir, rows, batches, args.timeout_seconds)
    print(f"Wrote {len(rows)} checkpoint rows to {output_dir}")
    for row in grouped_summaries(rows)["model"]:
        print(
            f"{row['condition']},{row['model']},quality={row['counterfactual_action_quality']},"
            f"optimal={row['optimal_action_rate']},regret={row['mean_survival_regret']},"
            f"informative={row['informative_state_rate']},error={row['error_rate']}"
        )


if __name__ == "__main__":
    main()
