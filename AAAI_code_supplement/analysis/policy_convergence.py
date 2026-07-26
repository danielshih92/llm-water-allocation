#!/usr/bin/env python3
"""Probe submitted policies and estimate OF/OPF convergence across meta-rounds."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import inspect
import itertools
import json
import math
import os
import signal
import sys
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

os.environ.setdefault("MPLCONFIGDIR", "/tmp/wacbench-matplotlib")
import matplotlib.pyplot as plt
import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_ROOT = PROJECT_ROOT / "wacbench"
sys.path.insert(0, str(SRC_ROOT))

from sandbox_executor import ALLOWED_BUILTINS, _static_check  # noqa: E402
from wac_programmatic import AgentProfile, default_agent_profiles  # noqa: E402
from package_paths import package_relative  # noqa: E402


DEFAULT_BATCHES = (
    PROJECT_ROOT / "data" / "paper_intermediates" / "logs" / "OF",
    PROJECT_ROOT / "data" / "paper_intermediates" / "logs" / "OPF",
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "policy_convergence"
CONDITION_ORDER = ("OF", "OPF")
CONDITION_COLORS = {"OF": "#377EB8", "OPF": "#E68613"}
CONDITION_MARKERS = {"OF": "o", "OPF": "s"}
ANALYSIS_VERSION = 1

DAYS = (3, 10, 18)
SUPPLIES = (16.0, 20.0, 24.0)
BUDGETS = (150.0, 400.0)
RISK_STATES = (
    ("safe", 10, 1),
    ("low_hp", 4, 1),
    ("drought", 7, 3),
    ("joint_risk", 4, 3),
)
PRESSURES = {
    "low": (0.20, 0.30),
    "high": (0.80, 1.00),
}


@dataclass(frozen=True)
class PolicyInstance:
    condition: str
    batch: str
    experiment_id: str
    meta_round: int
    agent_id: str
    model: str
    code: str
    profiles: Mapping[str, AgentProfile]

    @property
    def instance_id(self) -> str:
        return (
            f"{self.condition}/{self.batch}/{self.experiment_id}/"
            f"MR{self.meta_round}/{self.agent_id}"
        )

    @property
    def source_hash(self) -> str:
        profiles = [
            {
                "agent_id": profile.agent_id,
                "water_requirement": profile.water_requirement,
                "daily_salary": profile.daily_salary,
            }
            for profile in sorted(self.profiles.values(), key=lambda item: item.agent_id)
        ]
        payload = json.dumps(
            {"code": self.code, "profiles": profiles}, sort_keys=True
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def iter_records(path: Path) -> Iterable[Mapping[str, Any]]:
    payload = load_json(path)
    if isinstance(payload, list):
        yield from (item for item in payload if isinstance(item, dict))
    elif isinstance(payload, dict):
        yield payload


def infer_condition(batch: Path) -> str:
    name = batch.name.lower()
    if name == "opf":
        return "OPF"
    if name == "of":
        return "OF"
    if "full_code_access" in name:
        return "OPF"
    if "no_opp_info" in name or "no_opponent_info" in name:
        return "OF"
    raise ValueError(f"Cannot infer OF/OPF condition from batch name: {batch.name}")


def profile_map(record: Mapping[str, Any]) -> Dict[str, AgentProfile]:
    environment = record.get("environment", {})
    players = environment.get("players", []) if isinstance(environment, dict) else []
    profiles: Dict[str, AgentProfile] = {}
    for item in players if isinstance(players, list) else []:
        if not isinstance(item, dict):
            continue
        agent_id = str(item.get("agent_id", "")).strip()
        if not agent_id:
            continue
        profiles[agent_id] = AgentProfile(
            agent_id=agent_id,
            water_requirement=int(item.get("water_requirement", 0) or 0),
            daily_salary=float(item.get("daily_salary", 0.0) or 0.0),
        )
    return profiles or {profile.agent_id: profile for profile in default_agent_profiles()}


def load_model_map(exp_dir: Path) -> Dict[str, str]:
    payload = load_json(exp_dir / "backend_config.json")
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid backend_config.json: {exp_dir}")
    return {
        str(agent_id): str(spec.get("model", "unknown"))
        for agent_id, spec in payload.items()
        if isinstance(spec, dict)
    }


def load_policy_instances(
    batches: Sequence[Path], meta_rounds: Sequence[int]
) -> List[PolicyInstance]:
    requested = set(meta_rounds)
    instances: List[PolicyInstance] = []
    for batch in batches:
        if not batch.is_dir():
            raise FileNotFoundError(batch)
        condition = infer_condition(batch)
        for exp_dir in sorted(batch.glob("exp_[0-9][0-9][0-9]")):
            model_map = load_model_map(exp_dir)
            for path in sorted(exp_dir.glob("meta_round_*.json")):
                for record in iter_records(path):
                    meta_round = int(record.get("meta_round_id", 0) or 0)
                    if meta_round not in requested:
                        continue
                    if record.get("all_agents_admitted") != 1 or record.get("outcome_valid") != 1:
                        raise ValueError(f"Invalid source round cannot be probed: {path}")
                    profiles = profile_map(record)
                    for agent in record.get("agents", []):
                        if not isinstance(agent, dict) or agent.get("admitted") != 1:
                            continue
                        agent_id = str(agent.get("agent_id", "")).strip()
                        code = agent.get("strategy_code")
                        if not agent_id or not isinstance(code, str) or not code.strip():
                            raise ValueError(f"Missing admitted strategy code: {path} / {agent_id}")
                        instances.append(
                            PolicyInstance(
                                condition=condition,
                                batch=batch.name,
                                experiment_id=exp_dir.name,
                                meta_round=meta_round,
                                agent_id=agent_id,
                                model=model_map.get(agent_id, "unknown"),
                                code=code,
                                profiles=profiles,
                            )
                        )
    return instances


def validate_design(
    instances: Sequence[PolicyInstance], meta_rounds: Sequence[int]
) -> Tuple[List[str], List[str], List[str]]:
    experiments = sorted(
        {item.experiment_id for item in instances},
        key=lambda value: int(value.split("_")[-1]),
    )
    roles = sorted({item.agent_id for item in instances})
    models = sorted({item.model for item in instances})
    expected = {
        (condition, experiment, meta_round, role)
        for condition in CONDITION_ORDER
        for experiment in experiments
        for meta_round in meta_rounds
        for role in roles
    }
    observed = [
        (item.condition, item.experiment_id, item.meta_round, item.agent_id)
        for item in instances
    ]
    counts = Counter(observed)
    observed_set = set(observed)
    duplicates = [key for key, count in counts.items() if count != 1]
    if expected != observed_set or duplicates:
        raise ValueError(
            "Incomplete policy design; "
            f"missing={sorted(expected - observed_set)[:10]}, "
            f"extra={sorted(observed_set - expected)[:10]}, duplicates={duplicates[:10]}"
        )
    if "unknown" in models:
        raise ValueError("At least one strategy lacks a model mapping")
    return experiments, roles, models


def make_opponents_status(
    focal_agent: str,
    profiles: Mapping[str, AgentProfile],
    day: int,
    supply: float,
    budget: float,
    pressure: str,
) -> Dict[str, Dict[str, Any]]:
    factors = PRESSURES[pressure]
    output: Dict[str, Dict[str, Any]] = {}
    for agent_id in sorted(profiles):
        if agent_id == focal_agent:
            continue
        profile = profiles[agent_id]
        bids = [min(budget, profile.daily_salary * factor) for factor in factors]
        history_days = (max(1, day - 2), max(1, day - 1))
        history = [
            {
                "day": history_day,
                "bid": float(bid),
                "supply": supply,
                "hp_after": 8,
                "budget_after": budget,
                "status": "alive",
                "error": None,
            }
            for history_day, bid in zip(history_days, bids)
        ]
        output[agent_id] = {
            "agent_id": agent_id,
            "hp": 8,
            "budget": budget,
            "no_water_days": 1,
            "alive": True,
            "water_requirement": profile.water_requirement,
            "daily_salary": profile.daily_salary,
            "last_bid": float(bids[-1]),
            "last_status": "alive",
            "last_hp_after": 8,
            "last_budget_after": budget,
            "trace_history": history,
        }
    return output


def build_probe_cases(
    agent_id: str, profiles: Mapping[str, AgentProfile]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    cases: List[Dict[str, Any]] = []
    manifest: List[Dict[str, Any]] = []
    focal = profiles[agent_id]
    for day, supply, budget, (risk_name, hp, no_water_days), pressure in itertools.product(
        DAYS, SUPPLIES, BUDGETS, RISK_STATES, PRESSURES
    ):
        opponents = make_opponents_status(
            agent_id, profiles, day, supply, budget, pressure
        )
        cases.append(
            {
                "day_context": {"day": day, "supply": supply},
                "my_status": {
                    "agent_id": agent_id,
                    "hp": hp,
                    "budget": budget,
                    "no_water_days": no_water_days,
                    "water_requirement": focal.water_requirement,
                    "daily_salary": focal.daily_salary,
                },
                "opponents_status": opponents,
            }
        )
        manifest.append(
            {
                "case_index": len(manifest),
                "day": day,
                "supply": supply,
                "budget": budget,
                "risk_state": risk_name,
                "hp": hp,
                "no_water_days": no_water_days,
                "opponent_pressure": pressure,
            }
        )
    return cases, manifest


def execute_policy(
    code: str, cases: Sequence[Mapping[str, Any]], timeout_seconds: float
) -> Tuple[List[Optional[float]], List[Optional[str]]]:
    static_error = _static_check(code)
    if static_error:
        return [None] * len(cases), [static_error] * len(cases)

    def alarm_handler(signum: int, frame: Any) -> None:
        del signum, frame
        raise TimeoutError("runtime_timeout")

    previous_handler = signal.signal(signal.SIGALRM, alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        namespace: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
        exec(code, namespace, namespace)
        policy = namespace.get("get_bid")
        if not callable(policy):
            return [None] * len(cases), ["missing_get_bid"] * len(cases)
        parameter_count = len(inspect.signature(policy).parameters)
        bids: List[Optional[float]] = []
        errors: List[Optional[str]] = []
        for case in cases:
            try:
                args = (
                    deepcopy(case["day_context"]),
                    deepcopy(case["my_status"]),
                    deepcopy(case["opponents_status"]),
                )
                raw = policy(*args) if parameter_count >= 3 else policy(*args[:2])
                bid = float(raw)
                if not math.isfinite(bid):
                    raise ValueError("invalid_bid_value")
                budget = float(case["my_status"]["budget"])
                bids.append(min(budget, max(0.0, bid)) / budget)
                errors.append(None)
            except TimeoutError:
                raise
            except Exception as exc:
                bids.append(None)
                errors.append(f"runtime_error: {exc}")
        return bids, errors
    except TimeoutError:
        return [None] * len(cases), ["runtime_timeout"] * len(cases)
    except Exception as exc:
        return [None] * len(cases), [f"compile_error: {exc}"] * len(cases)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)


def ast_ngrams(code: str, n: int = 3) -> List[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    tokens = [type(node).__name__ for node in ast.walk(tree)]
    if len(tokens) < n:
        return ["|".join(tokens)] if tokens else []
    return sorted({"|".join(tokens[index : index + n]) for index in range(len(tokens) - n + 1)})


def probe_config(meta_rounds: Sequence[int], batches: Sequence[Path]) -> Dict[str, Any]:
    payload = {
        "analysis_version": ANALYSIS_VERSION,
        "batches": [package_relative(path) for path in batches],
        "meta_rounds": list(meta_rounds),
        "days": list(DAYS),
        "supplies": list(SUPPLIES),
        "budgets": list(BUDGETS),
        "risk_states": [list(value) for value in RISK_STATES],
        "pressures": {key: list(value) for key, value in PRESSURES.items()},
        "bid_normalization": "clamp bid to [0, budget], then divide by budget",
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    payload["config_hash"] = hashlib.sha256(encoded).hexdigest()[:16]
    return payload


def load_checkpoint(path: Path) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    if not path.is_file():
        return records
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid checkpoint line {line_number}: {path}") from exc
            records[str(row["instance_id"])] = row
    return records


def run_probes(
    instances: Sequence[PolicyInstance],
    checkpoint_path: Path,
    timeout_seconds: float,
    resume: bool,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    completed = load_checkpoint(checkpoint_path) if resume else {}
    mode = "a" if resume else "w"
    case_manifest: List[Dict[str, Any]] = []
    with checkpoint_path.open(mode, encoding="utf-8") as handle:
        for index, instance in enumerate(instances, start=1):
            previous = completed.get(instance.instance_id)
            if previous is not None and previous.get("source_hash") == instance.source_hash:
                continue
            cases, manifest = build_probe_cases(instance.agent_id, instance.profiles)
            if not case_manifest:
                case_manifest = manifest
            bids, errors = execute_policy(instance.code, cases, timeout_seconds)
            row = {
                "instance_id": instance.instance_id,
                "source_hash": instance.source_hash,
                "condition": instance.condition,
                "batch": instance.batch,
                "experiment_id": instance.experiment_id,
                "meta_round": instance.meta_round,
                "agent_id": instance.agent_id,
                "model": instance.model,
                "normalized_bids": bids,
                "valid_case_count": sum(error is None for error in errors),
                "total_case_count": len(errors),
                "error_counts": dict(Counter(error for error in errors if error is not None)),
                "ast_ngrams": ast_ngrams(instance.code),
            }
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            handle.flush()
            completed[instance.instance_id] = row
            if index % 100 == 0 or index == len(instances):
                print(f"Probed {index}/{len(instances)} policies")
    if not case_manifest and instances:
        _, case_manifest = build_probe_cases(instances[0].agent_id, instances[0].profiles)
    return list(completed.values()), case_manifest


def pairwise_rmse(left: Sequence[Any], right: Sequence[Any]) -> Optional[float]:
    pairs = [
        (float(a), float(b))
        for a, b in zip(left, right)
        if a is not None and b is not None and math.isfinite(float(a)) and math.isfinite(float(b))
    ]
    if len(pairs) < 0.9 * min(len(left), len(right)):
        return None
    return math.sqrt(sum((a - b) ** 2 for a, b in pairs) / len(pairs))


def jaccard(left: Sequence[str], right: Sequence[str]) -> Optional[float]:
    a, b = set(left), set(right)
    if not a or not b:
        return None
    return len(a & b) / len(a | b)


def build_cluster_rows(
    records: Sequence[Mapping[str, Any]],
    experiments: Sequence[str],
    meta_rounds: Sequence[int],
) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str, int], List[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        grouped[(str(row["condition"]), str(row["experiment_id"]), int(row["meta_round"]))].append(row)
    output: List[Dict[str, Any]] = []
    for condition in CONDITION_ORDER:
        for experiment in experiments:
            for meta_round in meta_rounds:
                policies = grouped[(condition, experiment, meta_round)]
                if len(policies) != 5:
                    raise ValueError(
                        f"Expected five policies: {condition}/{experiment}/MR{meta_round}; got {len(policies)}"
                    )
                behavior_values: List[float] = []
                structure_values: List[float] = []
                for left, right in itertools.combinations(policies, 2):
                    behavior = pairwise_rmse(left["normalized_bids"], right["normalized_bids"])
                    structure = jaccard(left["ast_ngrams"], right["ast_ngrams"])
                    if behavior is not None:
                        behavior_values.append(behavior)
                    if structure is not None:
                        structure_values.append(structure)
                output.append(
                    {
                        "condition": condition,
                        "experiment_id": experiment,
                        "meta_round": meta_round,
                        "behavioral_distance": (
                            float(np.mean(behavior_values)) if behavior_values else math.nan
                        ),
                        "structural_similarity": (
                            float(np.mean(structure_values)) if structure_values else math.nan
                        ),
                        "valid_behavior_pairs": len(behavior_values),
                        "valid_structure_pairs": len(structure_values),
                        "total_pairs": 10,
                    }
                )
    return output


def percentile_interval(values: np.ndarray) -> Tuple[float, float]:
    low, high = np.percentile(values, [2.5, 97.5])
    return float(low), float(high)


def transition_pairs(meta_rounds: Sequence[int]) -> List[Tuple[int, int]]:
    pairs = [(meta_rounds[index - 1], meta_rounds[index]) for index in range(1, len(meta_rounds))]
    overall = (meta_rounds[0], meta_rounds[-1])
    if len(meta_rounds) > 2 and overall not in pairs:
        pairs.append(overall)
    return pairs


def summarize_clusters(
    rows: Sequence[Mapping[str, Any]],
    experiments: Sequence[str],
    meta_rounds: Sequence[int],
    bootstrap_samples: int,
    bootstrap_seed: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    lookup = {
        (str(row["condition"]), str(row["experiment_id"]), int(row["meta_round"])): row
        for row in rows
    }
    rng = np.random.default_rng(bootstrap_seed)
    weights = rng.multinomial(
        len(experiments),
        np.full(len(experiments), 1.0 / len(experiments)),
        size=bootstrap_samples,
    ).astype(float)
    estimates: Dict[Tuple[str, str, int], float] = {}
    distributions: Dict[Tuple[str, str, int], np.ndarray] = {}
    summary_rows: List[Dict[str, Any]] = []
    metrics = (
        ("Behavioral distance", "behavioral_distance", "lower means more similar"),
        ("Structural similarity", "structural_similarity", "higher means more similar"),
    )
    for condition in CONDITION_ORDER:
        for metric, field, direction in metrics:
            for meta_round in meta_rounds:
                values = np.array(
                    [float(lookup[(condition, exp, meta_round)][field]) for exp in experiments]
                )
                if np.any(~np.isfinite(values)):
                    raise ValueError(f"Non-finite {field}: {condition}/MR{meta_round}")
                point = float(np.mean(values))
                boot = (weights @ values) / len(experiments)
                low, high = percentile_interval(boot)
                estimates[(condition, metric, meta_round)] = point
                distributions[(condition, metric, meta_round)] = boot
                summary_rows.append(
                    {
                        "condition": condition,
                        "meta_round": meta_round,
                        "metric": metric,
                        "estimate": point,
                        "ci95_low": low,
                        "ci95_high": high,
                        "interpretation": direction,
                        "bootstrap_samples": bootstrap_samples,
                    }
                )

    change_rows: List[Dict[str, Any]] = []
    contrast_rows: List[Dict[str, Any]] = []
    for start, end in transition_pairs(meta_rounds):
        transition = f"MR{end}-MR{start}"
        for metric, _, direction in metrics:
            changes: Dict[str, Tuple[float, np.ndarray]] = {}
            for condition in CONDITION_ORDER:
                point = estimates[(condition, metric, end)] - estimates[(condition, metric, start)]
                boot = distributions[(condition, metric, end)] - distributions[(condition, metric, start)]
                low, high = percentile_interval(boot)
                changes[condition] = point, boot
                change_rows.append(
                    {
                        "condition": condition,
                        "transition": transition,
                        "metric": metric,
                        "estimate": point,
                        "ci95_low": low,
                        "ci95_high": high,
                        "interpretation": direction,
                        "bootstrap_samples": bootstrap_samples,
                    }
                )
            point = changes["OPF"][0] - changes["OF"][0]
            boot = changes["OPF"][1] - changes["OF"][1]
            low, high = percentile_interval(boot)
            contrast_rows.append(
                {
                    "contrast": "OPF-minus-OF change",
                    "transition": transition,
                    "metric": metric,
                    "estimate": point,
                    "ci95_low": low,
                    "ci95_high": high,
                    "interpretation": direction,
                    "bootstrap_samples": bootstrap_samples,
                }
            )
    return summary_rows, change_rows, contrast_rows


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def rounded_rows(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {key: round(value, 6) if isinstance(value, float) else value for key, value in row.items()}
        for row in rows
    ]


def plot_metric_trajectory(
    rows: Sequence[Mapping[str, Any]],
    meta_rounds: Sequence[int],
    metric: str,
    _title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    """Render one metric at AAAI single-column dimensions."""
    lookup = {
        (str(row["condition"]), str(row["metric"]), int(row["meta_round"])): row
        for row in rows
    }
    fig, ax = plt.subplots(figsize=(3.0, 1.72))
    for condition in CONDITION_ORDER:
        items = [lookup[(condition, metric, meta_round)] for meta_round in meta_rounds]
        points = np.array([float(item["estimate"]) for item in items])
        lows = np.array([float(item["ci95_low"]) for item in items])
        highs = np.array([float(item["ci95_high"]) for item in items])
        ax.plot(
            meta_rounds, points, color=CONDITION_COLORS[condition],
            marker=CONDITION_MARKERS[condition], linewidth=1.3,
            markersize=3.5, label=condition,
        )
        ax.fill_between(
            meta_rounds, lows, highs,
            color=CONDITION_COLORS[condition], alpha=0.16, linewidth=0,
        )
    # The paper caption carries the full title; omitting it here saves
    # vertical space at single-column scale.
    ax.set_xlabel("Meta-round", fontsize=6.8, labelpad=2)
    ax.set_ylabel(ylabel, fontsize=6.8, labelpad=2)
    ax.set_xticks(meta_rounds, [f"MR{value}" for value in meta_rounds])
    ax.tick_params(axis="both", labelsize=6.5, pad=1.5, length=2.5)
    ax.grid(axis="y", color="#D5D5D5", linewidth=0.55, alpha=0.7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(
        loc="lower center", bbox_to_anchor=(0.5, 1.015), ncol=2,
        frameon=False, fontsize=6.7, handlelength=1.7,
        columnspacing=1.2, borderaxespad=0,
    )
    fig.tight_layout(pad=0.35)
    fig.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def write_summary(
    path: Path,
    summary_rows: Sequence[Mapping[str, Any]],
    contrast_rows: Sequence[Mapping[str, Any]],
    meta_rounds: Sequence[int],
) -> None:
    lookup = {
        (str(row["condition"]), str(row["metric"]), int(row["meta_round"])): row
        for row in summary_rows
    }
    lines = [
        "# Policy convergence summary",
        "",
        "Behavioral distance is the experiment-level mean pairwise RMSE between the five",
        "policies' normalized bids over the same 144 controlled states. Lower is more similar.",
        "Structural similarity is a normalized-AST 3-gram Jaccard robustness diagnostic.",
        "All intervals use matched experiment-cluster bootstrap samples.",
        "",
        "| Condition | MR | Behavioral distance (95% CI) | Structural similarity (95% CI) |",
        "| --- | ---: | ---: | ---: |",
    ]
    for condition in CONDITION_ORDER:
        for meta_round in meta_rounds:
            behavior = lookup[(condition, "Behavioral distance", meta_round)]
            structure = lookup[(condition, "Structural similarity", meta_round)]
            lines.append(
                f"| {condition} | {meta_round} | "
                f"{behavior['estimate']:.4f} [{behavior['ci95_low']:.4f}, {behavior['ci95_high']:.4f}] | "
                f"{structure['estimate']:.4f} [{structure['ci95_low']:.4f}, {structure['ci95_high']:.4f}] |"
            )
    lines.extend(
        [
            "",
            "## Baseline-adjusted OPF-minus-OF changes",
            "",
            "| Transition | Metric | Difference in change (95% CI) |",
            "| --- | --- | ---: |",
        ]
    )
    for row in contrast_rows:
        lines.append(
            f"| {row['transition']} | {row['metric']} | "
            f"{row['estimate']:+.4f} [{row['ci95_low']:+.4f}, {row['ci95_high']:+.4f}] |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", nargs="+", type=Path, default=list(DEFAULT_BATCHES))
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--meta-rounds", nargs="+", type=int, default=[1, 2, 3])
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--bootstrap-samples", type=int, default=5000)
    parser.add_argument("--bootstrap-seed", type=int, default=42)
    parser.add_argument(
        "--resume", action=argparse.BooleanOptionalAction, default=True,
        help="Resume the per-policy JSONL checkpoint (default: true).",
    )
    args = parser.parse_args()
    if sorted(set(args.meta_rounds)) != args.meta_rounds or len(args.meta_rounds) < 2:
        parser.error("--meta-rounds must be unique, increasing integers")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.bootstrap_samples < 100:
        parser.error("--bootstrap-samples must be at least 100")
    return args


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    batches = [path.resolve() for path in args.batches]
    config = probe_config(args.meta_rounds, batches)
    config_path = output_dir / "probe_config.json"
    if args.resume and config_path.is_file():
        existing = load_json(config_path)
        if existing.get("config_hash") != config["config_hash"]:
            raise ValueError(
                "Existing probe checkpoint uses a different configuration; "
                "choose a new --output-dir or use --no-resume."
            )
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    instances = load_policy_instances(batches, args.meta_rounds)
    experiments, roles, models = validate_design(instances, args.meta_rounds)
    records, case_manifest = run_probes(
        instances,
        output_dir / "policy_probe_records.jsonl",
        args.timeout_seconds,
        args.resume,
    )
    if len(records) != len(instances):
        raise ValueError(f"Checkpoint contains {len(records)} records; expected {len(instances)}")
    (output_dir / "probe_case_manifest.json").write_text(
        json.dumps(case_manifest, indent=2) + "\n", encoding="utf-8"
    )

    cluster_rows = build_cluster_rows(records, experiments, args.meta_rounds)
    summary_rows, change_rows, contrast_rows = summarize_clusters(
        cluster_rows,
        experiments,
        args.meta_rounds,
        args.bootstrap_samples,
        args.bootstrap_seed,
    )
    cluster_rows = rounded_rows(cluster_rows)
    summary_rows = rounded_rows(summary_rows)
    change_rows = rounded_rows(change_rows)
    contrast_rows = rounded_rows(contrast_rows)
    write_csv(output_dir / "experiment_level_convergence.csv", cluster_rows)
    write_csv(output_dir / "policy_convergence_by_round.csv", summary_rows)
    write_csv(output_dir / "policy_convergence_changes.csv", change_rows)
    write_csv(output_dir / "opf_minus_of_convergence_change.csv", contrast_rows)
    plot_metric_trajectory(
        summary_rows,
        args.meta_rounds,
        "Behavioral distance",
        "Behavioral policy distance",
        "Pairwise RMSE",
        output_dir / "policy_convergence.png",
    )
    plot_metric_trajectory(
        summary_rows,
        args.meta_rounds,
        "Structural similarity",
        "Normalized AST similarity",
        "Jaccard similarity",
        output_dir / "policy_structure_similarity.png",
    )
    write_summary(
        output_dir / "policy_convergence_summary.md",
        summary_rows,
        contrast_rows,
        args.meta_rounds,
    )

    error_counts = Counter()
    valid_cases = total_cases = 0
    for row in records:
        valid_cases += int(row["valid_case_count"])
        total_cases += int(row["total_case_count"])
        error_counts.update(row.get("error_counts", {}))
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "analysis_version": ANALYSIS_VERSION,
        "batches": [package_relative(path) for path in batches],
        "experiments": len(experiments),
        "policies": len(records),
        "meta_rounds": args.meta_rounds,
        "roles": roles,
        "models": models,
        "probe_cases_per_policy": len(case_manifest),
        "valid_probe_cases": valid_cases,
        "total_probe_cases": total_cases,
        "probe_coverage": valid_cases / total_cases if total_cases else 0.0,
        "error_counts": dict(error_counts),
        "behavior_metric": "within-experiment mean pairwise RMSE over normalized bid signatures",
        "structure_metric": "within-experiment mean pairwise Jaccard over AST node-type 3-grams",
        "bootstrap": {
            "method": "matched experiment-cluster percentile bootstrap",
            "samples": args.bootstrap_samples,
            "seed": args.bootstrap_seed,
            "confidence_level": 0.95,
        },
        "files": [
            "probe_config.json",
            "probe_case_manifest.json",
            "policy_probe_records.jsonl",
            "experiment_level_convergence.csv",
            "policy_convergence_by_round.csv",
            "policy_convergence_changes.csv",
            "opf_minus_of_convergence_change.csv",
            "policy_convergence.png",
            "policy_structure_similarity.png",
            "policy_convergence_summary.md",
        ],
    }
    (output_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        f"Wrote policy convergence for {len(records)} policies to {output_dir}; "
        f"probe coverage={manifest['probe_coverage']:.2%}"
    )


if __name__ == "__main__":
    main()
