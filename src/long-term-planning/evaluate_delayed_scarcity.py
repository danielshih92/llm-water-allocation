#!/usr/bin/env python3
"""Replay existing WAC policies under controlled delayed-scarcity schedules."""

import argparse
import csv
import inspect
import json
import math
import multiprocessing
import queue
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT))

from sandbox_executor import ALLOWED_BUILTINS, _static_check
from wac_programmatic import AgentProfile, default_agent_profiles


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BATCHES = [
    REPO_ROOT / "log" / "batch_031_full_code_access_c_med_20days",
    REPO_ROOT / "log" / "batch_032_no_opp_info_c_med_20days",
]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "compare_result" / "long-term-planning" / "delayed-scarcity"
EPISODE_DAYS = 20
CRISIS_START_DAY = 15
DEFAULT_SEEDS = [1103, 2207, 3319, 4421, 5531]
SCHEDULES = ("uniform", "frontloaded_scarcity", "backloaded_scarcity")

REPLAY_FIELDS = [
    "batch_id", "condition", "experiment_id", "meta_round_id", "agent_id",
    "backend", "model", "strategy_instance_id", "seed", "schedule",
    "crisis_start_day", "survival_days", "post_crisis_survival_ratio",
    "alive_at_crisis", "episode_survival", "budget_at_crisis",
    "budget_reserve_ratio", "pre_crisis_paid_spending_ratio", "final_budget",
    "runtime_error", "meta_round_file",
]

SUMMARY_FIELDS = [
    "summary_level", "condition", "model", "agent_id", "strategy_instance_id",
    "delayed_scarcity_robustness", "uniform_robustness",
    "frontloaded_scarcity_robustness", "backloaded_episode_survival",
    "backloaded_alive_at_crisis", "budget_reserve_ratio",
    "pre_crisis_paid_spending_ratio", "delayed_scarcity_gap",
    "valid_replay_count", "total_replay_count", "error_replay_count", "error_rate",
]


def infer_condition(batch_path: Path) -> str:
    name = batch_path.name.lower()
    if "full_code_access" in name:
        return "OPF"
    if "no_opp_info" in name or "no_opponent_info" in name:
        return "OF"
    return "unknown"


def normalize_path(value: str) -> Path:
    path = Path(value).expanduser()
    return (path if path.is_absolute() else Path.cwd() / path).resolve()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
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
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items() if isinstance(value, dict)}


def valid_record(record: Dict[str, Any]) -> bool:
    return record.get("all_agents_admitted") == 1 and record.get("outcome_valid") == 1


def profile_map(record: Dict[str, Any]) -> Dict[str, AgentProfile]:
    environment = record.get("environment", {})
    players = environment.get("players", []) if isinstance(environment, dict) else []
    profiles = {}
    for item in players if isinstance(players, list) else []:
        if not isinstance(item, dict):
            continue
        agent_id = str(item.get("agent_id", "")).strip()
        if agent_id:
            profiles[agent_id] = AgentProfile(
                agent_id, int(item.get("water_requirement", 0) or 0),
                float(item.get("daily_salary", 0.0) or 0.0),
            )
    return profiles or {profile.agent_id: profile for profile in default_agent_profiles()}


def build_schedules(seed: int) -> Dict[str, List[int]]:
    rng = random.Random(seed)
    supplies = [rng.randint(15, 25) for _ in range(EPISODE_DAYS)]
    # Every schedule has the same multiset and therefore the same total supply.
    return {
        "uniform": supplies,
        "frontloaded_scarcity": sorted(supplies),
        "backloaded_scarcity": sorted(supplies, reverse=True),
    }


def compile_policy(code: str):
    namespace: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
    exec(code, namespace, namespace)
    function = namespace.get("get_bid")
    if not callable(function):
        raise ValueError("missing_get_bid")
    return function, len(inspect.signature(function).parameters)


def sanitized_bid(value: Any, budget: float) -> float:
    try:
        bid = float(value)
    except Exception:
        return 0.0
    if not math.isfinite(bid):
        return 0.0
    return min(budget, max(0.0, bid))


def fixed_opponent_bid(day: int, supply: float, hp: int, no_water_days: int,
                       budget: float, profile: AgentProfile) -> float:
    if supply < profile.water_requirement or budget <= 0:
        return 0.0
    urgency = max(0, 7 - hp) * 8.0 + max(0, no_water_days - 1) * 15.0
    late_adjustment = max(0, day - 14) * 2.5
    scarcity_adjustment = max(0.0, 21.0 - supply) * 2.0
    target = 0.42 * profile.daily_salary + urgency + late_adjustment + scarcity_adjustment
    return min(budget, max(0.0, target))


def compact_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    if not trace:
        return {"day": None, "bid": 0.0, "supply": None, "hp_after": None,
                "budget_after": None, "status": None, "error": None}
    return {key: trace.get(key) for key in (
        "day", "bid", "supply", "hp_after", "budget_after", "status", "error"
    )}


def opponents_status(target_id: str, profiles: Dict[str, AgentProfile],
                     runtime: Dict[str, Dict[str, Any]],
                     traces: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    output = {}
    for agent_id, profile in profiles.items():
        if agent_id == target_id:
            continue
        state = runtime[agent_id]
        history = [compact_trace(item) for item in traces[agent_id][-2:]]
        previous = history[-1] if history else compact_trace({})
        output[agent_id] = {
            "agent_id": agent_id, "hp": state["hp"], "budget": state["budget"],
            "no_water_days": state["no_water_days"], "alive": state["alive"],
            "water_requirement": profile.water_requirement,
            "daily_salary": profile.daily_salary, "last_bid": previous["bid"],
            "last_status": previous["status"], "last_hp_after": previous["hp_after"],
            "last_budget_after": previous["budget_after"], "trace_history": history,
        }
    return output


def allocate(bids: Dict[str, float], profiles: Dict[str, AgentProfile],
             supply: float, day: int) -> List[str]:
    rng = random.Random(f"wac-tie-break-{day}-{supply}")
    candidates = [
        (agent_id, bid, profiles[agent_id].water_requirement, rng.random())
        for agent_id, bid in bids.items()
        if bid > 0 and profiles[agent_id].water_requirement <= supply
    ]
    candidates.sort(key=lambda row: (-row[1], row[2], row[3]))
    winners, remaining = [], supply
    for agent_id, _, requirement, _ in candidates:
        if requirement <= remaining:
            winners.append(agent_id)
            remaining -= requirement
    return winners


def simulate_episode(code: str, target_id: str, profiles: Dict[str, AgentProfile],
                     supplies: List[int]) -> Dict[str, Any]:
    focal_policy, parameter_count = compile_policy(code)
    runtime = {agent_id: {"hp": 8, "budget": 0.0, "no_water_days": 1, "alive": True}
               for agent_id in profiles}
    traces: Dict[str, List[Dict[str, Any]]] = {agent_id: [] for agent_id in profiles}
    focal_paid_spending = 0.0
    paid_spending_at_crisis = 0.0
    budget_at_crisis = 0.0

    for day, raw_supply in enumerate(supplies, start=1):
        supply = float(raw_supply)
        for agent_id, profile in profiles.items():
            if runtime[agent_id]["alive"]:
                runtime[agent_id]["budget"] += profile.daily_salary

        bids: Dict[str, float] = {}
        errors: Dict[str, Optional[str]] = {}
        for agent_id, profile in profiles.items():
            state = runtime[agent_id]
            if not state["alive"]:
                bids[agent_id], errors[agent_id] = 0.0, None
            elif agent_id == target_id:
                context = {"day": day, "supply": supply}
                mine = {key: state[key] for key in ("hp", "budget", "no_water_days")}
                other = opponents_status(agent_id, profiles, runtime, traces)
                args = (context, mine, other)
                try:
                    raw_bid = focal_policy(*args) if parameter_count >= 3 else focal_policy(*args[:2])
                    bids[agent_id] = sanitized_bid(raw_bid, state["budget"])
                    errors[agent_id] = None
                except Exception as exc:
                    bids[agent_id], errors[agent_id] = 0.0, f"runtime_error: {exc}"
            else:
                bids[agent_id] = fixed_opponent_bid(
                    day, supply, state["hp"], state["no_water_days"], state["budget"], profile
                )
                errors[agent_id] = None

        winners = set(allocate(bids, profiles, supply, day))
        for agent_id in profiles:
            state = runtime[agent_id]
            if state["alive"]:
                if agent_id in winners:
                    state["hp"] = min(10, state["hp"] + 2)
                    state["budget"] -= bids[agent_id]
                    state["no_water_days"] = 1
                    if agent_id == target_id:
                        focal_paid_spending += bids[agent_id]
                else:
                    state["hp"] -= state["no_water_days"]
                    state["no_water_days"] += 1
                if state["hp"] <= 0:
                    state["alive"], state["budget"] = False, 0.0
            traces[agent_id].append({
                "day": day, "bid": bids[agent_id], "supply": supply,
                "hp_after": state["hp"], "budget_after": state["budget"],
                "status": "alive" if state["alive"] else "dead", "error": errors[agent_id],
            })
        if day == CRISIS_START_DAY - 1:
            budget_at_crisis = runtime[target_id]["budget"]
            paid_spending_at_crisis = focal_paid_spending

    focal_trace = traces[target_id]
    death_days = [item["day"] for item in focal_trace if item["status"] == "dead"]
    survival_days = int(death_days[0] - 1) if death_days else EPISODE_DAYS
    post_days = EPISODE_DAYS - CRISIS_START_DAY + 1
    post_survival = max(0, min(post_days, survival_days - CRISIS_START_DAY + 1)) / post_days
    income_before_crisis = profiles[target_id].daily_salary * (CRISIS_START_DAY - 1)
    return {
        "survival_days": survival_days,
        "post_crisis_survival_ratio": post_survival,
        "alive_at_crisis": int(survival_days >= CRISIS_START_DAY),
        "episode_survival": int(survival_days == EPISODE_DAYS),
        "budget_at_crisis": budget_at_crisis,
        "budget_reserve_ratio": budget_at_crisis / income_before_crisis,
        "pre_crisis_paid_spending_ratio": min(1.0, paid_spending_at_crisis / income_before_crisis),
        "final_budget": runtime[target_id]["budget"],
    }


def worker(output: multiprocessing.Queue, code: str, target_id: str,
           raw_profiles: List[Tuple[str, int, float]], seeds: List[int]) -> None:
    try:
        profiles = {item[0]: AgentProfile(*item) for item in raw_profiles}
        results = []
        for seed in seeds:
            for schedule, supplies in build_schedules(seed).items():
                result = simulate_episode(code, target_id, profiles, supplies)
                result.update({"seed": seed, "schedule": schedule})
                results.append(result)
        output.put({"error": None, "results": results})
    except Exception as exc:
        output.put({"error": f"runtime_error: {exc}", "results": []})


def replay_strategy(code: str, agent_id: str, profiles: Dict[str, AgentProfile],
                    seeds: List[int], timeout: float) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    static_error = _static_check(code)
    if static_error:
        return [], static_error
    output: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    raw_profiles = [(p.agent_id, p.water_requirement, p.daily_salary) for p in profiles.values()]
    process = multiprocessing.Process(
        target=worker, args=(output, code, agent_id, raw_profiles, seeds), daemon=True
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
    return payload.get("results", []), payload.get("error")


def evaluate_batches(batch_paths: Sequence[Path], seeds: List[int], timeout: float,
                     max_strategies: Optional[int]) -> List[Dict[str, Any]]:
    rows, strategy_count = [], 0
    for batch_path in batch_paths:
        if not batch_path.exists():
            raise FileNotFoundError(f"Batch path does not exist: {batch_path}")
        for meta_file in sorted(batch_path.glob("exp_*/meta_round_*.json")):
            configs = load_backend_config(meta_file.parent)
            for record in iter_records(meta_file):
                if not valid_record(record):
                    continue
                profiles = profile_map(record)
                for agent in record.get("agents", []):
                    if not isinstance(agent, dict):
                        continue
                    agent_id = str(agent.get("agent_id", "")).strip()
                    code = agent.get("strategy_code")
                    if not agent_id or agent_id not in profiles or not isinstance(code, str) or not code.strip():
                        continue
                    if max_strategies is not None and strategy_count >= max_strategies:
                        return rows
                    strategy_count += 1
                    config = configs.get(agent_id, {})
                    meta_round_id = record.get("meta_round_id")
                    metadata = {
                        "batch_id": batch_path.name, "condition": infer_condition(batch_path),
                        "experiment_id": meta_file.parent.name, "meta_round_id": meta_round_id,
                        "agent_id": agent_id, "backend": str(config.get("backend", "unknown")),
                        "model": str(config.get("model", "unknown")),
                        "strategy_instance_id": f"{batch_path.name}/{meta_file.parent.name}/mr_{meta_round_id}/{agent_id}",
                        "crisis_start_day": CRISIS_START_DAY, "meta_round_file": str(meta_file),
                    }
                    replays, error = replay_strategy(code, agent_id, profiles, seeds, timeout)
                    if error:
                        for seed in seeds:
                            for schedule in SCHEDULES:
                                row = dict(metadata)
                                row.update({"seed": seed, "schedule": schedule, "runtime_error": error})
                                rows.append(row)
                    else:
                        for replay in replays:
                            row = dict(metadata)
                            row.update(replay)
                            row["runtime_error"] = None
                            rows.append(row)
    return rows


def mean(values: List[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def rounded(value: Optional[float]) -> Optional[float]:
    return round(value, 6) if value is not None else None


def summarize(rows: List[Dict[str, Any]], labels: Dict[str, Any]) -> Dict[str, Any]:
    valid = [row for row in rows if not row.get("runtime_error")]
    by_schedule = {name: [row for row in valid if row["schedule"] == name] for name in SCHEDULES}
    back = by_schedule["backloaded_scarcity"]
    robustness = {
        name: mean([float(row["post_crisis_survival_ratio"]) for row in group])
        for name, group in by_schedule.items()
    }
    delayed = robustness["backloaded_scarcity"]
    uniform = robustness["uniform"]
    total = len(rows)
    return {
        "summary_level": labels.get("summary_level"),
        "condition": labels.get("condition", "ALL"), "model": labels.get("model", "ALL"),
        "agent_id": labels.get("agent_id", "ALL"),
        "strategy_instance_id": labels.get("strategy_instance_id", "ALL"),
        "delayed_scarcity_robustness": rounded(delayed),
        "uniform_robustness": rounded(uniform),
        "frontloaded_scarcity_robustness": rounded(robustness["frontloaded_scarcity"]),
        "backloaded_episode_survival": rounded(mean([float(row["episode_survival"]) for row in back])),
        "backloaded_alive_at_crisis": rounded(mean([float(row["alive_at_crisis"]) for row in back])),
        "budget_reserve_ratio": rounded(mean([float(row["budget_reserve_ratio"]) for row in back])),
        "pre_crisis_paid_spending_ratio": rounded(mean([
            float(row["pre_crisis_paid_spending_ratio"]) for row in back
        ])),
        "delayed_scarcity_gap": rounded(delayed - uniform) if delayed is not None and uniform is not None else None,
        "valid_replay_count": len(valid), "total_replay_count": total,
        "error_replay_count": total - len(valid),
        "error_rate": rounded((total - len(valid)) / total) if total else None,
    }


def grouped_summaries(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    definitions = {
        "strategy": ("condition", "model", "agent_id", "strategy_instance_id"),
        "agent": ("condition", "model", "agent_id"),
        "model": ("condition", "model"),
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


def fmt(value: Any, percent: bool = False) -> str:
    if value is None:
        return "NA"
    return f"{100 * float(value):.1f}" if percent else str(value)


def write_table_png(path: Path, rows: List[Dict[str, Any]]) -> None:
    import os
    os.environ.setdefault("MPLCONFIGDIR", str(path.parent / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = sorted(rows, key=lambda row: (str(row["model"]), str(row["condition"])))
    cells = [[row["model"], row["condition"], fmt(row["delayed_scarcity_robustness"], True),
              fmt(row["budget_reserve_ratio"], True), fmt(row["backloaded_episode_survival"], True)]
             for row in rows]
    fig, ax = plt.subplots(figsize=(9.5, max(3.2, 0.43 * (len(rows) + 3))))
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=[
        "Model", "Feedback", "DSR (%)", "Budget reserve (%)", "Episode survival (%)"
    ], cellLoc="center", loc="center", colWidths=[0.28, 0.12, 0.16, 0.22, 0.22])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.45)
    for column in range(5):
        table[(0, column)].set_text_props(weight="bold")
    ax.set_title("Delayed-Scarcity Evaluation", fontsize=12, pad=12)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_outputs(output_dir: Path, rows: List[Dict[str, Any]], batch_paths: Sequence[Path],
                  seeds: List[int], timeout: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = grouped_summaries(rows)
    write_csv(output_dir / "delayed_scarcity_replays.csv", rows, REPLAY_FIELDS)
    (output_dir / "delayed_scarcity_replays.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for level, values in summaries.items():
        write_csv(output_dir / f"delayed_scarcity_summary_by_{level}.csv", values, SUMMARY_FIELDS)
        (output_dir / f"delayed_scarcity_summary_by_{level}.json").write_text(
            json.dumps(values, indent=2), encoding="utf-8"
        )
    write_table_png(output_dir / "delayed_scarcity_table.png", summaries["model"])
    config = {
        "input_batches": [str(path) for path in batch_paths], "episode_days": EPISODE_DAYS,
        "crisis_start_day": CRISIS_START_DAY, "seeds": seeds, "schedules": list(SCHEDULES),
        "schedule_control": "same supply multiset and total; only temporal order changes",
        "fixed_opponents": "deterministic urgency-aware scripted policies",
        "delayed_scarcity_robustness": "mean post-crisis survival fraction under backloaded scarcity",
        "timeout_seconds_per_strategy": timeout,
    }
    (output_dir / "run_config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def self_test() -> None:
    schedules = build_schedules(1)
    assert all(len(values) == EPISODE_DAYS for values in schedules.values())
    assert len({tuple(sorted(values)) for values in schedules.values()}) == 1
    assert schedules["frontloaded_scarcity"] == sorted(schedules["frontloaded_scarcity"])
    assert schedules["backloaded_scarcity"] == sorted(schedules["backloaded_scarcity"], reverse=True)
    profiles = {profile.agent_id: profile for profile in default_agent_profiles()}
    code = "def get_bid(day_context, my_status, opponents_status):\n    return min(60, my_status['budget'])\n"
    rows, error = replay_strategy(code, "Alex", profiles, [1], 3.0)
    assert error is None and len(rows) == len(SCHEDULES)
    assert all(0 <= row["post_crisis_survival_ratio"] <= 1 for row in rows)
    bad_rows, error = replay_strategy("def nope():\n    return 0\n", "Alex", profiles, [1], 3.0)
    assert not bad_rows and error is not None
    print("Self-test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate delayed-scarcity robustness of existing WAC policies.")
    parser.add_argument("--batch", action="append", help="Batch directory; repeat for multiple conditions.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--seeds", default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    parser.add_argument("--max-strategies", type=int, default=None)
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        self_test()
        return
    batches = [normalize_path(value) for value in args.batch] if args.batch else DEFAULT_BATCHES
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    output_dir = normalize_path(args.output_dir)
    rows = evaluate_batches(batches, seeds, args.timeout_seconds, args.max_strategies)
    write_outputs(output_dir, rows, batches, seeds, args.timeout_seconds)
    print(f"Wrote {len(rows)} replay rows to {output_dir}")
    for row in grouped_summaries(rows)["model"]:
        print(f"{row['condition']},{row['model']},DSR={row['delayed_scarcity_robustness']},"
              f"reserve={row['budget_reserve_ratio']},error_rate={row['error_rate']}")


if __name__ == "__main__":
    main()
