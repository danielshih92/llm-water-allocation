#!/usr/bin/env python3
"""Evaluate MR1->MR2 adaptation while freezing every opponent at its MR1 policy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import math
import multiprocessing as mp
import os
import queue
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
SRC_ROOT = HERE.parent
PROJECT_ROOT = SRC_ROOT.parent
sys.path.insert(0, str(SRC_ROOT))

import wac_programmatic as wac  # noqa: E402
from sandbox_executor import ALLOWED_BUILTINS, _static_check  # noqa: E402


DEFAULT_OF = PROJECT_ROOT / "log" / "batch_032_no_opp_info_c_med_20days"
DEFAULT_OPF = PROJECT_ROOT / "log" / "batch_031_full_code_access_c_med_20days"
DEFAULT_OUTPUT = PROJECT_ROOT / "compare_result" / "opponent-modeling"
DEFAULT_SEEDS = (10, 42, 98, 197, 666)
BOOTSTRAP_SEED = 20260714
BOOTSTRAP_REPLICATES = 2000
VALUE_TOLERANCE = 1e-12

PAIR_FIELDS = [
    "feedback", "batch", "experiment_id", "focal_agent", "model", "seed",
    "episode_days", "scenario", "baseline_stratum", "baseline_policy_hash",
    "adapted_policy_hash", "opponent_policy_hashes", "baseline_survival_days",
    "adapted_survival_days", "survival_gain", "baseline_dead", "adapted_dead",
    "mortality_change", "death_to_survival", "survival_to_death", "baseline_final_hp",
    "adapted_final_hp", "baseline_final_budget", "adapted_final_budget",
    "baseline_total_bid", "adapted_total_bid", "baseline_value", "adapted_value",
    "value_gain", "improved", "tied", "degraded",
]

SUMMARY_FIELDS = [
    "summary_level", "feedback", "model", "role", "baseline_stratum",
    "mean_survival_gain", "mean_value_gain", "improvement_rate", "tie_rate",
    "degradation_rate", "mortality_change", "death_to_survival_rate",
    "survival_to_death_rate", "mean_baseline_survival", "mean_adapted_survival",
    "valid_pair_count", "error_pair_count", "experiment_count", "expected_pair_count", "coverage",
    "mean_survival_gain_ci_low", "mean_survival_gain_ci_high",
    "mean_value_gain_ci_low", "mean_value_gain_ci_high",
    "improvement_rate_ci_low", "improvement_rate_ci_high",
    "mortality_change_ci_low", "mortality_change_ci_high",
]

ERROR_FIELDS = ["feedback", "batch", "experiment_id", "focal_agent", "seed", "stage", "error"]


def load_record(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise ValueError("expected a one-record JSON list")
        return payload[0]
    if isinstance(payload, dict):
        return payload
    raise ValueError("expected a JSON object or one-record list")


def load_model_map(exp_dir: Path) -> Dict[str, str]:
    with (exp_dir / "backend_config.json").open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("backend_config.json must contain an object")
    result = {}
    for role, spec in payload.items():
        if not isinstance(spec, dict) or not str(spec.get("model", "")).strip():
            raise ValueError(f"missing model mapping for {role}")
        result[str(role)] = str(spec["model"]).strip()
    return result


def record_profiles(record: Mapping[str, Any]) -> List[wac.AgentProfile]:
    players = record.get("environment", {}).get("players", [])
    if not isinstance(players, list) or not players:
        raise ValueError("record has no environment players")
    return [
        wac.AgentProfile(str(row["agent_id"]), int(row["water_requirement"]), float(row["daily_salary"]))
        for row in players
    ]


def policy_map(record: Mapping[str, Any]) -> Dict[str, str]:
    agents = record.get("agents", [])
    if not isinstance(agents, list):
        raise ValueError("record agents must be a list")
    result = {}
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        role = str(agent.get("agent_id", "")).strip()
        code = str(agent.get("strategy_code", "") or "")
        if role and code.strip():
            result[role] = code
    return result


def validate_compatibility(mr1: Mapping[str, Any], mr2: Mapping[str, Any]) -> Tuple[List[wac.AgentProfile], int, str]:
    env1 = mr1.get("environment", {})
    env2 = mr2.get("environment", {})
    profiles1, profiles2 = record_profiles(mr1), record_profiles(mr2)
    shape1 = [(p.agent_id, p.water_requirement, p.daily_salary) for p in profiles1]
    shape2 = [(p.agent_id, p.water_requirement, p.daily_salary) for p in profiles2]
    if shape1 != shape2:
        raise ValueError("MR1 and MR2 player profiles differ")
    days1, days2 = int(env1.get("episode_days", 0)), int(env2.get("episode_days", 0))
    if days1 <= 0 or days1 != days2:
        raise ValueError("MR1 and MR2 episode lengths differ or are invalid")
    scenario1, scenario2 = str(env1.get("scenario", "")), str(env2.get("scenario", ""))
    if scenario1 not in wac.SCENARIOS or scenario1 != scenario2:
        raise ValueError("MR1 and MR2 scenarios differ or are invalid")
    roles = {p.agent_id for p in profiles1}
    if set(policy_map(mr1)) != roles or set(policy_map(mr2)) != roles:
        raise ValueError("MR1 or MR2 does not contain exactly one non-empty policy per role")
    return profiles1, days1, scenario1


def code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def _episode_worker(
    output: mp.Queue,
    raw_profiles: List[Tuple[str, int, float]],
    codes: Dict[str, str],
    supplies: List[int],
    episode_days: int,
    focal_role: Optional[str],
) -> None:
    """Run one lineup in isolation, compiling each policy once per episode."""
    try:
        compiled: Dict[str, Tuple[Any, int]] = {}
        for role, code in codes.items():
            safe_globals: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
            exec(code, safe_globals, safe_globals)
            policy = safe_globals.get("get_bid")
            if not callable(policy):
                raise ValueError(f"{role}: missing_get_bid")
            compiled[code] = (policy, len(inspect.signature(policy).parameters))

        def cached_execute(strategy_code: str, day_context: Dict[str, Any],
                           my_status: Dict[str, Any], opponents_status: Optional[Dict[str, Any]] = None,
                           timeout_seconds: float = 1.0) -> Tuple[float, Optional[str]]:
            del timeout_seconds
            policy, parameter_count = compiled[strategy_code]
            try:
                raw = policy(day_context, my_status, opponents_status or {}) if parameter_count >= 3 else policy(day_context, my_status)
                bid = float(raw)
                if not math.isfinite(bid):
                    return 0.0, "invalid_bid_value"
                return bid, None
            except Exception as exc:
                return 0.0, f"runtime_error: {exc}"

        # run_episode resolves this module global. The whole episode is already isolated and timed.
        wac.execute_strategy = cached_execute
        profiles = [wac.AgentProfile(*row) for row in raw_profiles]
        submissions = [wac.AgentSubmission(p.agent_id, "", codes[p.agent_id]) for p in profiles]
        env = wac.WACProgrammaticEnv(episode_days=episode_days)
        result = env.run_episode(profiles, submissions, supplies)
        if focal_role is None:
            payload: Dict[str, Any] = {"episode_result": result}
        else:
            focal_profile = next(profile for profile in profiles if profile.agent_id == focal_role)
            payload = {
                "focal_outcome": extract_outcome(
                    result, focal_role, focal_profile.daily_salary, episode_days
                )
            }
        output.put({"result": payload, "error": None})
    except BaseException as exc:
        output.put({"result": None, "error": f"{type(exc).__name__}: {exc}"})


def run_isolated_episode(
    profiles: Sequence[wac.AgentProfile], codes: Dict[str, str], supplies: List[int],
    episode_days: int, timeout: float, focal_role: Optional[str] = None,
) -> Dict[str, Any]:
    for role, code in codes.items():
        error = _static_check(code)
        if error:
            raise RuntimeError(f"{role}: {error}")
    output: mp.Queue = mp.Queue(maxsize=1)
    raw_profiles = [(p.agent_id, p.water_requirement, p.daily_salary) for p in profiles]
    process = mp.Process(
        target=_episode_worker,
        args=(output, raw_profiles, codes, supplies, episode_days, focal_role),
        daemon=True,
    )
    process.start()
    deadline = time.monotonic() + timeout
    payload = None
    while payload is None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            process.terminate(); process.join()
            raise TimeoutError(f"policy_or_episode_timeout: exceeded {timeout:g} seconds")
        try:
            # Drain the pipe while the worker is alive. Waiting for process.join()
            # first can deadlock when a full episode result exceeds the pipe buffer.
            payload = output.get(timeout=min(0.1, remaining))
        except queue.Empty:
            if not process.is_alive():
                try:
                    payload = output.get(timeout=min(1.0, remaining))
                except queue.Empty as exc:
                    process.join()
                    raise RuntimeError("ipc_failure: episode worker exited without a payload") from exc
    process.join(1.0)
    if process.is_alive():
        # The complete focal result has already crossed the queue boundary.
        # Under high parallel load, a worker can remain alive briefly while
        # multiprocessing finalizers run; retaining the received payload is
        # safer than converting a successful deterministic replay into
        # missing data.
        process.terminate()
        process.join()
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return payload["result"]


def extract_outcome(result: Mapping[str, Any], role: str, salary: float, episode_days: int) -> Dict[str, float]:
    matches = [agent for agent in result.get("agents", []) if agent.get("agent_id") == role]
    if len(matches) != 1:
        raise ValueError(f"episode result missing unique focal agent {role}")
    agent = matches[0]
    trace = agent.get("daily_trace", [])
    trace_errors = [row.get("error") for row in trace if row.get("error") is not None]
    if trace_errors:
        raise RuntimeError(f"{role}: {trace_errors[0]}")
    metrics = agent.get("metrics", {})
    survival = float(metrics["survival_days"])
    final_hp = float(metrics["final_hp"])
    final_budget = float(trace[-1].get("budget_after", 0.0)) if trace else 0.0
    total_bid = float(metrics["total_bid"])
    dead = int(survival < episode_days)
    hp_quality = max(0.0, min(10.0, final_hp)) / 10.0
    max_budget = max(0.0, salary * episode_days)
    budget_quality = max(0.0, min(1.0, final_budget / max_budget)) if max_budget else 0.0
    value = survival + (0.5 * hp_quality + 0.5 * budget_quality) / (episode_days + 1.0)
    return {
        "survival_days": survival, "dead": float(dead), "final_hp": final_hp,
        "final_budget": final_budget, "total_bid": total_bid, "value": value,
    }


def baseline_stratum(survival: float, episode_days: int) -> str:
    if survival < 10:
        return "died_before_day_10"
    if survival < episode_days:
        return "survived_days_10_19"
    return "completed_20_days"


def make_pair_row(metadata: Dict[str, Any], baseline: Dict[str, float], adapted: Dict[str, float]) -> Dict[str, Any]:
    gain = adapted["value"] - baseline["value"]
    improved = int(gain > VALUE_TOLERANCE)
    degraded = int(gain < -VALUE_TOLERANCE)
    tied = int(not improved and not degraded)
    row = dict(metadata)
    row.update({
        "baseline_stratum": baseline_stratum(baseline["survival_days"], metadata["episode_days"]),
        "baseline_survival_days": baseline["survival_days"],
        "adapted_survival_days": adapted["survival_days"],
        "survival_gain": adapted["survival_days"] - baseline["survival_days"],
        "baseline_dead": int(baseline["dead"]), "adapted_dead": int(adapted["dead"]),
        "mortality_change": int(adapted["dead"] - baseline["dead"]),
        "death_to_survival": int(baseline["dead"] == 1 and adapted["dead"] == 0),
        "survival_to_death": int(baseline["dead"] == 0 and adapted["dead"] == 1),
        "baseline_final_hp": baseline["final_hp"], "adapted_final_hp": adapted["final_hp"],
        "baseline_final_budget": baseline["final_budget"], "adapted_final_budget": adapted["final_budget"],
        "baseline_total_bid": baseline["total_bid"], "adapted_total_bid": adapted["total_bid"],
        "baseline_value": baseline["value"], "adapted_value": adapted["value"],
        "value_gain": gain, "improved": improved, "tied": tied, "degraded": degraded,
    })
    return row


def evaluate_task(task: Dict[str, Any], timeout: float) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    try:
        profiles = task["profiles"]
        focal = task["focal_agent"]
        mr1_codes = task["mr1_codes"]
        adapted_codes = dict(mr1_codes)
        adapted_codes[focal] = task["mr2_codes"][focal]
        frozen = {role: code_hash(code) for role, code in mr1_codes.items() if role != focal}
        # This assertion documents and enforces the central intervention.
        if any(adapted_codes[role] != mr1_codes[role] for role in frozen):
            raise AssertionError("a frozen opponent policy changed")
        supplies = wac.build_supply_list(task["scenario"], task["episode_days"], task["seed"])
        baseline_payload = run_isolated_episode(
            profiles, mr1_codes, supplies, task["episode_days"], timeout, focal_role=focal
        )
        adapted_payload = run_isolated_episode(
            profiles, adapted_codes, supplies, task["episode_days"], timeout, focal_role=focal
        )
        baseline = baseline_payload["focal_outcome"]
        adapted = adapted_payload["focal_outcome"]
        metadata = {
            key: task[key] for key in (
                "feedback", "batch", "experiment_id", "focal_agent", "model", "seed",
                "episode_days", "scenario",
            )
        }
        metadata.update({
            "baseline_policy_hash": code_hash(mr1_codes[focal]),
            "adapted_policy_hash": code_hash(task["mr2_codes"][focal]),
            "opponent_policy_hashes": json.dumps(frozen, sort_keys=True),
        })
        return make_pair_row(metadata, baseline, adapted), None
    except Exception as exc:
        return None, {
            "feedback": task.get("feedback"), "batch": task.get("batch"),
            "experiment_id": task.get("experiment_id"), "focal_agent": task.get("focal_agent"),
            "seed": task.get("seed"), "stage": "replay", "error": f"{type(exc).__name__}: {exc}",
        }


def collect_tasks(batch_dir: Path, feedback: str, seeds: Sequence[int]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    tasks, errors = [], []
    exp_dirs = sorted(path for path in batch_dir.glob("exp_*") if path.is_dir())
    for exp_dir in exp_dirs:
        try:
            mr1 = load_record(exp_dir / "meta_round_1.json")
            mr2 = load_record(exp_dir / "meta_round_2.json")
            profiles, episode_days, scenario = validate_compatibility(mr1, mr2)
            models = load_model_map(exp_dir)
            roles = [p.agent_id for p in profiles]
            if set(models) != set(roles):
                raise ValueError("backend mappings do not exactly match player roles")
            mr1_codes, mr2_codes = policy_map(mr1), policy_map(mr2)
            for focal in roles:
                for seed in seeds:
                    tasks.append({
                        "feedback": feedback, "batch": batch_dir.name,
                        "experiment_id": exp_dir.name, "focal_agent": focal,
                        "model": models[focal], "seed": int(seed), "episode_days": episode_days,
                        "scenario": scenario, "profiles": profiles, "mr1_codes": mr1_codes,
                        "mr2_codes": mr2_codes,
                    })
        except Exception as exc:
            errors.append({
                "feedback": feedback, "batch": batch_dir.name, "experiment_id": exp_dir.name,
                "focal_agent": "", "seed": "", "stage": "load",
                "error": f"{type(exc).__name__}: {exc}",
            })
    return tasks, errors, len(exp_dirs)


def mean(rows: Sequence[Mapping[str, Any]], field: str) -> Optional[float]:
    values = [float(row[field]) for row in rows if row.get(field) is not None]
    return sum(values) / len(values) if values else None


def role_balanced_stat(rows: Sequence[Mapping[str, Any]], field: str) -> Optional[float]:
    by_role: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_role[str(row["focal_agent"])].append(row)
    role_means = [mean(items, field) for items in by_role.values()]
    valid = [value for value in role_means if value is not None]
    return sum(valid) / len(valid) if valid else None


STAT_FIELDS = {
    "mean_survival_gain": "survival_gain", "mean_value_gain": "value_gain",
    "improvement_rate": "improved", "tie_rate": "tied", "degradation_rate": "degraded",
    "mortality_change": "mortality_change", "death_to_survival_rate": "death_to_survival",
    "survival_to_death_rate": "survival_to_death",
    "mean_baseline_survival": "baseline_survival_days",
    "mean_adapted_survival": "adapted_survival_days",
}


def percentile(values: Sequence[float], q: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * q
    low, high = int(math.floor(position)), int(math.ceil(position))
    if low == high:
        return ordered[low]
    return ordered[low] * (high - position) + ordered[high] * (position - low)


def clustered_ci(rows: Sequence[Mapping[str, Any]], field: str, role_balanced: bool,
                 rng: random.Random, replicates: int) -> Tuple[Optional[float], Optional[float]]:
    clusters: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        clusters[str(row["experiment_id"])].append(row)
    keys = list(clusters)
    if not keys:
        return None, None
    estimates = []
    for _ in range(replicates):
        sampled = []
        for draw_index in range(len(keys)):
            key = rng.choice(keys)
            # Give duplicated clusters unique IDs; their rows still remain a joint block.
            for row in clusters[key]:
                copy = dict(row)
                copy["experiment_id"] = f"{draw_index}:{key}"
                sampled.append(copy)
        estimate = role_balanced_stat(sampled, field) if role_balanced else mean(sampled, field)
        if estimate is not None:
            estimates.append(estimate)
    return percentile(estimates, 0.025), percentile(estimates, 0.975)


def summarize_group(rows: Sequence[Mapping[str, Any]], labels: Dict[str, Any],
                    expected: int, role_balanced: bool, rng: random.Random,
                    bootstrap_replicates: int) -> Dict[str, Any]:
    result = {
        "summary_level": labels.get("summary_level"), "feedback": labels.get("feedback", "ALL"),
        "model": labels.get("model", "ALL"), "role": labels.get("role", "ALL"),
        "baseline_stratum": labels.get("baseline_stratum", "ALL"),
    }
    calculator = role_balanced_stat if role_balanced else mean
    for output_field, source_field in STAT_FIELDS.items():
        result[output_field] = calculator(rows, source_field)
    result.update({
        "valid_pair_count": len(rows),
        "error_pair_count": max(0, expected - len(rows)),
        "experiment_count": len({str(row["experiment_id"]) for row in rows}),
        "expected_pair_count": expected,
        "coverage": len(rows) / expected if expected else None,
    })
    for output_field in ("mean_survival_gain", "mean_value_gain", "improvement_rate", "mortality_change"):
        low, high = clustered_ci(
            rows, STAT_FIELDS[output_field], role_balanced, rng, bootstrap_replicates
        )
        result[f"{output_field}_ci_low"] = low
        result[f"{output_field}_ci_high"] = high
    return result


def grouped_summary(rows: List[Dict[str, Any]], level: str, seeds_per_pair: int,
                    bootstrap_replicates: int) -> List[Dict[str, Any]]:
    if level == "model":
        fields, role_balanced = ("feedback", "model"), True
    elif level == "role":
        fields, role_balanced = ("feedback", "model", "focal_agent"), False
    elif level == "baseline":
        fields, role_balanced = ("feedback", "model", "baseline_stratum"), True
    elif level == "agent":
        fields, role_balanced = ("feedback", "model", "experiment_id", "focal_agent"), False
    else:
        raise ValueError(f"unknown summary level: {level}")
    groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in fields)].append(row)
    output = []
    rng = random.Random(f"{BOOTSTRAP_SEED}:{level}")
    for key, items in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
        raw_labels = dict(zip(fields, key))
        labels = {
            "summary_level": level, "feedback": raw_labels.get("feedback", "ALL"),
            "model": raw_labels.get("model", "ALL"),
            "role": raw_labels.get("focal_agent", "ALL"),
            "baseline_stratum": raw_labels.get("baseline_stratum", "ALL"),
        }
        if level in ("model", "role"):
            expected = len({row["experiment_id"] for row in items}) * seeds_per_pair
        elif level == "agent":
            expected = seeds_per_pair
        else:
            # Strata are outcome-defined, so no pre-replay denominator exists.
            expected = len(items)
        output.append(summarize_group(
            items, labels, expected, role_balanced, rng,
            0 if level == "agent" else bootstrap_replicates,
        ))
    return output


def condition_differences(model_rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    by_model: Dict[str, Dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in model_rows:
        by_model[str(row["model"])][str(row["feedback"])] = row
    output = []
    for model, conditions in sorted(by_model.items()):
        if "OF" not in conditions or "OPF" not in conditions:
            continue
        of, opf = conditions["OF"], conditions["OPF"]
        output.append({
            "model": model,
            "delta_survival_gain": opf["mean_survival_gain"] - of["mean_survival_gain"],
            "delta_value_gain": opf["mean_value_gain"] - of["mean_value_gain"],
            "delta_improvement_rate": opf["improvement_rate"] - of["improvement_rate"],
            "delta_mortality_change": opf["mortality_change"] - of["mortality_change"],
            "of_valid_pairs": of["valid_pair_count"], "opf_valid_pairs": opf["valid_pair_count"],
        })
    return output


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Optional[Sequence[str]] = None) -> None:
    selected = list(fields or (list(rows[0]) if rows else []))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")


def pair_key(row: Mapping[str, Any]) -> Tuple[str, str, str, int]:
    return (
        str(row["feedback"]),
        str(row["experiment_id"]),
        str(row["focal_agent"]),
        int(row["seed"]),
    )


def load_existing_pairs(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = [pair_key(row) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError(f"duplicate paired replay keys in {path}")
    return rows


def configure_matplotlib(output_dir: Path) -> Any:
    os.environ.setdefault("MPLCONFIGDIR", str(output_dir / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def write_plots(output_dir: Path, model_rows: Sequence[Mapping[str, Any]],
                baseline_rows: Sequence[Mapping[str, Any]]) -> None:
    if not model_rows:
        return
    plt = configure_matplotlib(output_dir)
    ordered = sorted(model_rows, key=lambda row: (str(row["model"]), str(row["feedback"])))
    cells = [[
        row["model"], row["feedback"], f"{row['mean_survival_gain']:+.3f}",
        f"{100 * row['improvement_rate']:.1f}", f"{100 * row['degradation_rate']:.1f}",
        f"{100 * row['mortality_change']:+.1f}",
    ] for row in ordered]
    fig, ax = plt.subplots(figsize=(12, max(3.2, 0.43 * (len(cells) + 3))))
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=[
        "Model", "Feedback", "FOSG (days)", "FOIR (%)", "Degrade (%)", "Mortality Δ (pp)"
    ], cellLoc="center", loc="center")
    table.auto_set_font_size(False); table.set_fontsize(9); table.scale(1, 1.45)
    for col in range(6): table[(0, col)].set_text_props(weight="bold")
    ax.set_title("Frozen-Opponent Adaptation (MR1 to MR2)", pad=12)
    fig.tight_layout(); fig.savefig(output_dir / "opponent_modeling_table.png", dpi=300, bbox_inches="tight"); plt.close(fig)

    labels = [f"{row['model']}\n{row['feedback']}" for row in ordered]
    improved = [100 * row["improvement_rate"] for row in ordered]
    tied = [100 * row["tie_rate"] for row in ordered]
    degraded = [100 * row["degradation_rate"] for row in ordered]
    fig, ax = plt.subplots(figsize=(13, max(4.5, 0.45 * len(labels))))
    y = list(range(len(labels)))
    ax.barh(y, improved, label="Improved", color="#4C9F70")
    ax.barh(y, tied, left=improved, label="Tied", color="#BFC5CA")
    ax.barh(y, degraded, left=[a + b for a, b in zip(improved, tied)], label="Degraded", color="#D65F5F")
    ax.set_yticks(y, labels); ax.set_xlim(0, 100); ax.set_xlabel("Paired rollout outcomes (%)")
    ax.invert_yaxis(); ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, 1.01))
    fig.tight_layout(); fig.savefig(output_dir / "adaptation_outcomes.png", dpi=300, bbox_inches="tight"); plt.close(fig)

    strata_order = ["died_before_day_10", "survived_days_10_19", "completed_20_days"]
    models = sorted({str(row["model"]) for row in baseline_rows})
    conditions = ("OF", "OPF")
    fig, axes = plt.subplots(len(models), 1, figsize=(11, max(4, 2.5 * len(models))), sharex=True)
    if len(models) == 1: axes = [axes]
    lookup = {(row["model"], row["feedback"], row["baseline_stratum"]): row for row in baseline_rows}
    width = 0.36
    for ax, model in zip(axes, models):
        x = list(range(len(strata_order)))
        for offset, condition in zip((-width / 2, width / 2), conditions):
            values = [lookup.get((model, condition, stratum), {}).get("mean_survival_gain", float("nan")) for stratum in strata_order]
            ax.bar([value + offset for value in x], values, width, label=condition)
        ax.axhline(0, color="black", linewidth=0.7); ax.set_ylabel("FOSG"); ax.set_title(model)
    axes[-1].set_xticks(range(3), ["Died <10", "Survived 10–19", "Completed 20"])
    axes[0].legend(); fig.tight_layout(); fig.savefig(output_dir / "gain_by_baseline.png", dpi=300, bbox_inches="tight"); plt.close(fig)


def logged_focal_outcome(record: Mapping[str, Any], role: str) -> Dict[str, Any]:
    agent = next(item for item in record["agents"] if item["agent_id"] == role)
    trace = agent["daily_trace"]
    return {
        "survival_days": float(agent["metrics"]["survival_days"]),
        "final_hp": float(agent["metrics"]["final_hp"]),
        "trace": [
            (row["day"], float(row["bid"]), float(row["hp_after"]), float(row["budget_after"]), row["status"])
            for row in trace
        ],
    }


def parity_check(batch_dirs: Sequence[Path], timeout: float, max_experiments: Optional[int]) -> None:
    checked = 0
    for batch_dir in batch_dirs:
        for exp_dir in sorted(batch_dir.glob("exp_*")):
            if max_experiments is not None and checked >= max_experiments:
                print(f"Parity check passed for {checked} experiments.")
                return
            record = load_record(exp_dir / "meta_round_1.json")
            profiles = record_profiles(record); codes = policy_map(record)
            env = record["environment"]; days = int(env["episode_days"])
            supplies = list(env["supply_list"])
            result = run_isolated_episode(profiles, codes, supplies, days, timeout)["episode_result"]
            for profile in profiles:
                actual = extract_outcome(result, profile.agent_id, profile.daily_salary, days)
                expected = logged_focal_outcome(record, profile.agent_id)
                replay_agent = next(item for item in result["agents"] if item["agent_id"] == profile.agent_id)
                replay_trace = [
                    (row["day"], float(row["bid"]), float(row["hp_after"]), float(row["budget_after"]), row["status"])
                    for row in replay_agent["daily_trace"]
                ]
                assert actual["survival_days"] == expected["survival_days"]
                assert actual["final_hp"] == expected["final_hp"]
                assert replay_trace == expected["trace"]
            checked += 1
    print(f"Parity check passed for {checked} experiments.")


def self_test() -> None:
    profiles = wac.default_agent_profiles()
    days, seed = 20, 42
    fixed = "def get_bid(day_context, my_status, opponents_status):\n    return min(60.0, my_status['budget'])\n"
    weak = "def get_bid(day_context, my_status, opponents_status):\n    return 0.0\n"
    strong = "def get_bid(day_context, my_status, opponents_status):\n    return my_status['budget']\n"
    codes = {p.agent_id: fixed for p in profiles}
    supplies = wac.build_supply_list("medium", days, seed)
    result1 = run_isolated_episode(profiles, codes, supplies, days, 10.0)["episode_result"]
    result2 = run_isolated_episode(profiles, codes, supplies, days, 10.0)["episode_result"]
    assert result1 == result2
    focal = profiles[0]
    outcome = extract_outcome(result1, focal.agent_id, focal.daily_salary, days)
    metadata = {
        "feedback": "TEST", "batch": "test", "experiment_id": "exp_001",
        "focal_agent": focal.agent_id, "model": "test", "seed": seed,
        "episode_days": days, "scenario": "medium", "baseline_policy_hash": code_hash(fixed),
        "adapted_policy_hash": code_hash(fixed), "opponent_policy_hashes": "{}",
    }
    tie = make_pair_row(metadata, outcome, outcome)
    assert tie["survival_gain"] == 0 and tie["value_gain"] == 0 and tie["tied"] == 1
    synthetic_low = {"survival_days": 3.0, "dead": 1.0, "final_hp": 0.0, "final_budget": 0.0, "total_bid": 0.0, "value": 3.0}
    synthetic_high = {"survival_days": 20.0, "dead": 0.0, "final_hp": 10.0, "final_budget": 100.0, "total_bid": 50.0, "value": 20.02}
    assert make_pair_row(metadata, synthetic_low, synthetic_high)["improved"] == 1
    assert make_pair_row(metadata, synthetic_high, synthetic_low)["degraded"] == 1
    changed = dict(codes); changed[focal.agent_id] = weak
    assert all(changed[p.agent_id] == codes[p.agent_id] for p in profiles if p.agent_id != focal.agent_id)
    changed[focal.agent_id] = strong
    assert code_hash(changed[focal.agent_id]) != code_hash(codes[focal.agent_id])
    print("Self-test passed.")


def write_outputs(output_dir: Path, rows: List[Dict[str, Any]], errors: List[Dict[str, Any]],
                  args: argparse.Namespace, task_count: int, experiment_counts: Dict[str, int]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = {
        level: grouped_summary(rows, level, len(args.seeds), args.bootstrap_replicates)
        for level in ("model", "role", "baseline", "agent")
    }
    differences = condition_differences(summaries["model"])
    write_csv(output_dir / "frozen_opponent_pairs.csv", rows, PAIR_FIELDS)
    write_json(output_dir / "frozen_opponent_pairs.json", rows)
    for level, values in summaries.items():
        name = "summary_by_experiment_agent" if level == "agent" else f"summary_by_{level}"
        write_csv(output_dir / f"{name}.csv", values, SUMMARY_FIELDS)
        write_json(output_dir / f"{name}.json", values)
    write_csv(output_dir / "opf_minus_of.csv", differences)
    write_json(output_dir / "opf_minus_of.json", differences)
    write_csv(output_dir / "replay_errors.csv", errors, ERROR_FIELDS)
    write_json(output_dir / "replay_errors.json", errors)
    config = {
        "input_batches": {"OF": str(args.of_dir), "OPF": str(args.opf_dir)},
        "meta_round_transition": "MR1->MR2", "seeds": list(args.seeds),
        "workers": args.workers, "episode_timeout_seconds": args.timeout_seconds,
        "bootstrap_replicates": args.bootstrap_replicates,
        "bootstrap_seed": BOOTSTRAP_SEED, "bootstrap_cluster": "experiment_id",
        "aggregation": "mean within role, then equal-weight mean across observed roles for model summaries",
        "value": "survival_days + (0.5*(clamped_final_hp/10) + 0.5*(final_budget/(salary*T)))/(T+1)",
        "foir": "fraction of paired seeds with adapted value strictly greater than baseline value",
        "baseline_strata": ["died_before_day_10", "survived_days_10_19", "completed_20_days"],
        "experiment_counts": experiment_counts, "expected_task_count": task_count,
        "valid_pair_count": len(rows), "error_count": len(errors),
    }
    write_json(output_dir / "run_config.json", config)
    if not args.skip_plots:
        write_plots(output_dir, summaries["model"], summaries["baseline"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--of-dir", type=Path, default=DEFAULT_OF)
    parser.add_argument("--opf-dir", type=Path, default=DEFAULT_OPF)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    parser.add_argument("--max-tasks", type=int, default=None, help="Smoke-test limit after task discovery.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--parity-check", action="store_true")
    parser.add_argument("--parity-max-experiments", type=int, default=None)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Reuse valid rows already present in frozen_opponent_pairs.csv and evaluate only missing pairs.",
    )
    parser.add_argument("--skip-plots", action="store_true", help="Write numeric outputs without importing matplotlib.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.of_dir = args.of_dir.resolve(); args.opf_dir = args.opf_dir.resolve()
    args.output_dir = args.output_dir.resolve()
    if args.self_test:
        self_test()
        return
    if args.parity_check:
        parity_check((args.of_dir, args.opf_dir), args.timeout_seconds, args.parity_max_experiments)
        return
    tasks, errors, counts = [], [], {}
    for feedback, path in (("OF", args.of_dir), ("OPF", args.opf_dir)):
        batch_tasks, batch_errors, count = collect_tasks(path, feedback, args.seeds)
        tasks.extend(batch_tasks); errors.extend(batch_errors); counts[feedback] = count
    expected_task_count = len(tasks)
    rows = []
    if args.resume:
        rows = load_existing_pairs(args.output_dir / "frozen_opponent_pairs.csv")
        completed = {pair_key(row) for row in rows}
        tasks = [task for task in tasks if pair_key(task) not in completed]
        print(f"Resuming with {len(rows)} existing pairs; {len(tasks)} pairs remain.")
    if args.max_tasks is not None:
        tasks = tasks[:args.max_tasks]
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
        for row, error in executor.map(lambda item: evaluate_task(item, args.timeout_seconds), tasks):
            if row is not None: rows.append(row)
            if error is not None: errors.append(error)
    rows.sort(key=lambda row: (
        str(row["feedback"]), str(row["model"]), str(row["experiment_id"]),
        str(row["focal_agent"]), int(row["seed"])
    ))
    write_outputs(args.output_dir, rows, errors, args, expected_task_count, counts)
    print(f"Wrote {len(rows)} valid paired rollouts and {len(errors)} errors to {args.output_dir}")
    for row in grouped_summary(rows, "model", len(args.seeds), 0):
        print(
            f"{row['feedback']},{row['model']},FOSG={row['mean_survival_gain']:.4f},"
            f"FOIR={row['improvement_rate']:.4f},degrade={row['degradation_rate']:.4f},"
            f"mortality_delta={row['mortality_change']:.4f},n={row['valid_pair_count']}"
        )


if __name__ == "__main__":
    main()
