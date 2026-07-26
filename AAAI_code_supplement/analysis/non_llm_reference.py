#!/usr/bin/env python3
"""Evaluate a fixed non-LLM policy through matched focal-policy replacement.

For every OF/OPF experiment, meta-round, role, and replay seed, the evaluator
keeps the four opponent policy programs fixed and replaces only the focal LLM
program with the risk-aware pacing heuristic. No model API is called.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import math
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
WACBENCH_ROOT = PROJECT_ROOT / "wacbench"
sys.path.insert(0, str(WACBENCH_ROOT))
sys.path.insert(0, str(HERE))

import wac_programmatic as wac  # noqa: E402
from reference_policy import POLICY_NAME, RoleParameters, build_policy_code  # noqa: E402
from sandbox_executor import ALLOWED_BUILTINS, _static_check  # noqa: E402
from strategy_validator import validate_strategy_code  # noqa: E402
from package_paths import package_relative  # noqa: E402


DEFAULT_OF = PROJECT_ROOT / "data" / "paper_intermediates" / "logs" / "OF"
DEFAULT_OPF = PROJECT_ROOT / "data" / "paper_intermediates" / "logs" / "OPF"
DEFAULT_ORIGINAL = (
    PROJECT_ROOT / "data" / "paper_intermediates" / "main_table" / "replay_details.csv"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "non_llm_reference"
DEFAULT_SEEDS = (10, 42, 98, 197, 666)
DEFAULT_ROUNDS = (1, 2, 3)
BOOTSTRAP_SEED = 20260722

PAIR_FIELDS = [
    "feedback", "batch", "experiment_id", "meta_round", "seed", "role", "model",
    "original_survival_days", "reference_survival_days", "survival_difference",
    "original_wac_contribution", "reference_wac_contribution", "wac_difference",
    "original_dead", "reference_dead", "mortality_difference",
    "original_final_hp", "reference_final_hp", "reference_final_budget",
    "original_policy_hash", "reference_policy_hash",
]

METRIC_FIELDS = (
    "original_wac", "reference_wac", "wac_difference",
    "original_mortality", "reference_mortality", "mortality_difference",
)


def load_record(path: Path) -> Dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise ValueError(f"{path}: expected one record")
        return payload[0]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"{path}: expected a JSON object or one-record list")


def record_profiles(record: Mapping[str, Any]) -> List[wac.AgentProfile]:
    players = record.get("environment", {}).get("players", [])
    if not isinstance(players, list) or not players:
        raise ValueError("record has no player profiles")
    return [
        wac.AgentProfile(
            str(row["agent_id"]), int(row["water_requirement"]), float(row["daily_salary"])
        )
        for row in players
    ]


def policy_map(record: Mapping[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for agent in record.get("agents", []):
        role = str(agent.get("agent_id", "")).strip()
        code = str(agent.get("strategy_code", "") or "")
        if role and code.strip():
            result[role] = code
    return result


def load_model_map(path: Path) -> Dict[str, str]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return {str(role): str(spec["model"]) for role, spec in payload.items()}


def code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]


def original_key(
    feedback: str, batch: str, experiment_id: str, meta_round: int, seed: int, role: str
) -> Tuple[str, str, str, int, int, str]:
    return feedback, batch, experiment_id, int(meta_round), int(seed), role


def load_original_outcomes(path: Path) -> Dict[Tuple[str, str, str, int, int, str], Dict[str, Any]]:
    outcomes: Dict[Tuple[str, str, str, int, int, str], Dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = original_key(
                row["feedback"], row["batch"], row["exp_id"], int(row["meta_round"]),
                int(row["seed"]), row["role"],
            )
            if key in outcomes:
                raise ValueError(f"duplicate original outcome: {key}")
            outcomes[key] = {
                "model": row["model"],
                "survival_days": float(row["survival_days"]),
                "final_hp": float(row["final_hp"]),
                "dead": int(row["dead"]),
            }
    return outcomes


def validate_policy_family(profiles: Sequence[wac.AgentProfile], episode_days: int) -> None:
    for profile in profiles:
        code = build_policy_code(
            RoleParameters(profile.agent_id, profile.daily_salary, profile.water_requirement),
            episode_days,
        )
        result = validate_strategy_code(code)
        if not result.admitted:
            raise RuntimeError(
                f"reference policy failed validation for {profile.agent_id}: "
                f"{result.error_message}"
            )


def collect_group_tasks(
    batch_dir: Path,
    feedback: str,
    meta_rounds: Sequence[int],
    seeds: Sequence[int],
    originals: Mapping[Tuple[str, str, str, int, int, str], Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    tasks: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    exp_dirs = sorted(path for path in batch_dir.glob("exp_*") if path.is_dir())
    for exp_dir in exp_dirs:
        try:
            models = load_model_map(exp_dir / "backend_config.json")
            for meta_round in meta_rounds:
                record = load_record(exp_dir / f"meta_round_{meta_round}.json")
                if not int(record.get("official_outcome", 1)):
                    raise ValueError(f"MR{meta_round} is not an official outcome")
                profiles = record_profiles(record)
                codes = policy_map(record)
                roles = [profile.agent_id for profile in profiles]
                if set(codes) != set(roles) or set(models) != set(roles):
                    raise ValueError(f"MR{meta_round} roles, policies, and models do not match")
                environment = record.get("environment", {})
                episode_days = int(environment.get("episode_days", 0))
                scenario = str(environment.get("scenario", ""))
                if episode_days <= 0 or scenario not in wac.SCENARIOS:
                    raise ValueError(f"MR{meta_round} has an invalid environment")
                originals_for_group: Dict[str, Dict[str, Any]] = {}
                for role in roles:
                    for seed in seeds:
                        key = original_key(
                            feedback, batch_dir.name, exp_dir.name, meta_round, seed, role
                        )
                        if key not in originals:
                            raise ValueError(f"missing original replay outcome: {key}")
                        outcome = originals[key]
                        if outcome["model"] != models[role]:
                            raise ValueError(f"model mismatch for {key}")
                        originals_for_group[f"{role}|{seed}"] = outcome
                tasks.append({
                    "feedback": feedback,
                    "batch": batch_dir.name,
                    "experiment_id": exp_dir.name,
                    "meta_round": int(meta_round),
                    "episode_days": episode_days,
                    "scenario": scenario,
                    "profiles": [
                        (profile.agent_id, profile.water_requirement, profile.daily_salary)
                        for profile in profiles
                    ],
                    "models": models,
                    "codes": codes,
                    "seeds": [int(seed) for seed in seeds],
                    "originals": originals_for_group,
                })
        except Exception as exc:
            errors.append({
                "feedback": feedback,
                "batch": batch_dir.name,
                "experiment_id": exp_dir.name,
                "meta_round": "",
                "seed": "",
                "role": "",
                "stage": "load",
                "error": f"{type(exc).__name__}: {exc}",
            })
    return tasks, errors


def _compile_policies(codes: Iterable[str]) -> Dict[str, Tuple[Any, int]]:
    compiled: Dict[str, Tuple[Any, int]] = {}
    for code in set(codes):
        error = _static_check(code)
        if error:
            raise RuntimeError(error)
        namespace: Dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS, "math": math}
        exec(code, namespace, namespace)
        policy = namespace.get("get_bid")
        if not callable(policy):
            raise ValueError("missing_get_bid")
        compiled[code] = (policy, len(inspect.signature(policy).parameters))
    return compiled


def _extract_reference_outcome(
    result: Mapping[str, Any], role: str, episode_days: int
) -> Dict[str, float]:
    matches = [agent for agent in result.get("agents", []) if agent.get("agent_id") == role]
    if len(matches) != 1:
        raise ValueError(f"missing unique focal outcome for {role}")
    agent = matches[0]
    trace = agent.get("daily_trace", [])
    trace_errors = [row.get("error") for row in trace if row.get("error")]
    if trace_errors:
        raise RuntimeError(str(trace_errors[0]))
    survival = float(agent["metrics"]["survival_days"])
    return {
        "survival_days": survival,
        "dead": float(survival < episode_days),
        "final_hp": float(agent["metrics"]["final_hp"]),
        "final_budget": float(trace[-1].get("budget_after", 0.0)) if trace else 0.0,
    }


def _evaluate_group(task: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    profiles = [wac.AgentProfile(*raw) for raw in task["profiles"]]
    reference_codes = {
        profile.agent_id: build_policy_code(
            RoleParameters(profile.agent_id, profile.daily_salary, profile.water_requirement),
            int(task["episode_days"]),
        )
        for profile in profiles
    }
    try:
        compiled = _compile_policies(
            list(task["codes"].values()) + list(reference_codes.values())
        )

        def cached_execute(
            strategy_code: str,
            day_context: Dict[str, Any],
            my_status: Dict[str, Any],
            opponents_status: Optional[Dict[str, Any]] = None,
            timeout_seconds: float = 1.0,
        ) -> Tuple[float, Optional[str]]:
            del timeout_seconds
            policy, parameter_count = compiled[strategy_code]
            try:
                if parameter_count >= 3:
                    raw_bid = policy(day_context, my_status, opponents_status or {})
                else:
                    raw_bid = policy(day_context, my_status)
                bid = float(raw_bid)
                if not math.isfinite(bid):
                    return 0.0, "invalid_bid_value"
                return bid, None
            except Exception as exc:
                return 0.0, f"runtime_error: {exc}"

        wac.execute_strategy = cached_execute
        profile_by_role = {profile.agent_id: profile for profile in profiles}
        for role in profile_by_role:
            lineup = dict(task["codes"])
            lineup[role] = reference_codes[role]
            if any(
                lineup[other] != task["codes"][other]
                for other in profile_by_role if other != role
            ):
                raise AssertionError("an opponent policy changed during focal replacement")
            submissions = [
                wac.AgentSubmission(profile.agent_id, "", lineup[profile.agent_id])
                for profile in profiles
            ]
            for seed in task["seeds"]:
                try:
                    supplies = wac.build_supply_list(
                        str(task["scenario"]), int(task["episode_days"]), int(seed)
                    )
                    env = wac.WACProgrammaticEnv(episode_days=int(task["episode_days"]))
                    result = env.run_episode(profiles, submissions, supplies)
                    reference = _extract_reference_outcome(
                        result, role, int(task["episode_days"])
                    )
                    original = task["originals"][f"{role}|{seed}"]
                    scale = 100.0 / float(task["episode_days"])
                    survival_difference = (
                        float(original["survival_days"]) - reference["survival_days"]
                    )
                    mortality_difference = int(original["dead"]) - int(reference["dead"])
                    rows.append({
                        "feedback": task["feedback"],
                        "batch": task["batch"],
                        "experiment_id": task["experiment_id"],
                        "meta_round": int(task["meta_round"]),
                        "seed": int(seed),
                        "role": role,
                        "model": task["models"][role],
                        "original_survival_days": float(original["survival_days"]),
                        "reference_survival_days": reference["survival_days"],
                        "survival_difference": survival_difference,
                        "original_wac_contribution": float(original["survival_days"]) * scale,
                        "reference_wac_contribution": reference["survival_days"] * scale,
                        "wac_difference": survival_difference * scale,
                        "original_dead": int(original["dead"]),
                        "reference_dead": int(reference["dead"]),
                        "mortality_difference": mortality_difference,
                        "original_final_hp": float(original["final_hp"]),
                        "reference_final_hp": reference["final_hp"],
                        "reference_final_budget": reference["final_budget"],
                        "original_policy_hash": code_hash(task["codes"][role]),
                        "reference_policy_hash": code_hash(reference_codes[role]),
                    })
                except Exception as exc:
                    errors.append({
                        "feedback": task["feedback"], "batch": task["batch"],
                        "experiment_id": task["experiment_id"],
                        "meta_round": task["meta_round"], "seed": seed, "role": role,
                        "stage": "replay", "error": f"{type(exc).__name__}: {exc}",
                    })
    except Exception as exc:
        errors.append({
            "feedback": task["feedback"], "batch": task["batch"],
            "experiment_id": task["experiment_id"], "meta_round": task["meta_round"],
            "seed": "", "role": "", "stage": "compile",
            "error": f"{type(exc).__name__}: {exc}",
        })
    return rows, errors


def _analysis_items(rows: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[str, str, str], List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["experiment_id"]), str(row["role"]), str(row["model"]))].append(row)
    items: List[Dict[str, Any]] = []
    for (experiment_id, role, model), group in grouped.items():
        items.append({
            "experiment_id": experiment_id,
            "role": role,
            "model": model,
            "original_wac": float(np.mean([float(row["original_wac_contribution"]) for row in group])),
            "reference_wac": float(np.mean([float(row["reference_wac_contribution"]) for row in group])),
            "wac_difference": float(np.mean([float(row["wac_difference"]) for row in group])),
            "original_mortality": 100.0 * float(np.mean([float(row["original_dead"]) for row in group])),
            "reference_mortality": 100.0 * float(np.mean([float(row["reference_dead"]) for row in group])),
            "mortality_difference": 100.0 * float(np.mean([float(row["mortality_difference"]) for row in group])),
        })
    return items


def _role_balanced_distribution(
    items: Sequence[Mapping[str, Any]], field: str, bootstrap_replicates: int, seed: int
) -> Tuple[float, float, float]:
    experiments = sorted({str(item["experiment_id"]) for item in items})
    roles = sorted({str(item["role"]) for item in items})
    if not experiments or not roles:
        return float("nan"), float("nan"), float("nan")
    experiment_index = {value: index for index, value in enumerate(experiments)}
    role_index = {value: index for index, value in enumerate(roles)}
    matrix = np.full((len(roles), len(experiments)), np.nan, dtype=float)
    for item in items:
        row = role_index[str(item["role"])]
        column = experiment_index[str(item["experiment_id"])]
        if np.isfinite(matrix[row, column]):
            raise ValueError(f"duplicate analysis cell for {field}: {item}")
        matrix[row, column] = float(item[field])

    def estimate(weights: np.ndarray) -> np.ndarray:
        valid = np.isfinite(matrix).astype(float)
        values = np.nan_to_num(matrix, nan=0.0)
        numerators = (values[None, :, :] * weights[:, None, :]).sum(axis=2)
        denominators = (valid[None, :, :] * weights[:, None, :]).sum(axis=2)
        role_means = np.full(numerators.shape, np.nan, dtype=float)
        np.divide(numerators, denominators, out=role_means, where=denominators > 0)
        return np.nanmean(role_means, axis=1)

    point = float(estimate(np.ones((1, len(experiments)), dtype=float))[0])
    if bootstrap_replicates <= 0:
        return point, float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    weights = rng.multinomial(
        len(experiments), np.full(len(experiments), 1.0 / len(experiments)),
        size=bootstrap_replicates,
    ).astype(float)
    distribution = estimate(weights)
    low, high = np.nanpercentile(distribution, [2.5, 97.5])
    return point, float(low), float(high)


def summarize_rows(
    rows: Sequence[Mapping[str, Any]], labels: Mapping[str, Any], bootstrap_replicates: int
) -> Dict[str, Any]:
    items = _analysis_items(rows)
    result: Dict[str, Any] = dict(labels)
    result.update({
        "experiment_count": len({str(row["experiment_id"]) for row in rows}),
        "role_count": len({str(row["role"]) for row in rows}),
        "paired_replay_count": len(rows),
    })
    for offset, field in enumerate(METRIC_FIELDS):
        point, low, high = _role_balanced_distribution(
            items, field, bootstrap_replicates, BOOTSTRAP_SEED + offset
        )
        result[field] = point
        result[f"{field}_ci_low"] = low
        result[f"{field}_ci_high"] = high
    return result


def grouped_summaries(
    rows: Sequence[Dict[str, Any]], group_fields: Sequence[str], bootstrap_replicates: int
) -> List[Dict[str, Any]]:
    groups: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[field] for field in group_fields)].append(row)
    output: List[Dict[str, Any]] = []
    for key, group in sorted(groups.items(), key=lambda item: tuple(map(str, item[0]))):
        output.append(summarize_rows(
            group, dict(zip(group_fields, key)), bootstrap_replicates
        ))
    return output


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Optional[Sequence[str]] = None) -> None:
    selected = list(fields or (list(rows[0]) if rows else []))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=selected, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_paper_outputs(
    output_dir: Path,
    rows: Sequence[Dict[str, Any]],
    by_round: Sequence[Mapping[str, Any]],
    bootstrap_replicates: int,
) -> None:
    revised = [row for row in rows if int(row["meta_round"]) in (2, 3)]
    revised_by_condition = grouped_summaries(revised, ("feedback",), bootstrap_replicates)
    lookup = {str(row["feedback"]): row for row in revised_by_condition}
    if set(lookup) == {"OF", "OPF"}:
        wac_values = [float(lookup[key]["reference_wac"]) for key in ("OF", "OPF")]
        mortality_values = [
            float(lookup[key]["reference_mortality"]) for key in ("OF", "OPF")
        ]
        cells = [
            "Risk-aware heuristic",
            f"{wac_values[0]:.2f}",
            f"{wac_values[1]:.2f}",
            f"{np.mean(wac_values):.2f}",
            f"{mortality_values[0]:.2f}",
            f"{mortality_values[1]:.2f}",
            f"{np.mean(mortality_values):.2f}",
        ]
        latex_row = " & ".join(cells) + " " + r"\\" + "\n"
        (output_dir / "reference_revised_row.tex").write_text(latex_row, encoding="utf-8")

    lines = [
        "% Generated by src/non-llm-reference/evaluate_reference.py",
        "\\begin{tabular}{llrrrr}",
        "    \\toprule",
        "    Feedback & Round & Ref. WAC & Ref. Mort. & LLM$-$Ref. WAC & LLM$-$Ref. Mort. \\\\",
        "    \\midrule",
    ]
    for row in by_round:
        lines.append(
            f"    {row['feedback']} & MR{row['meta_round']} & "
            f"{row['reference_wac']:.2f} & {row['reference_mortality']:.2f} & "
            f"{row['wac_difference']:+.2f} & {row['mortality_difference']:+.2f} \\\\" 
        )
    lines.extend(["    \\bottomrule", "\\end{tabular}"])
    (output_dir / "reference_by_round_table.tex").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def write_summary_markdown(
    path: Path, by_round: Sequence[Mapping[str, Any]], by_model: Sequence[Mapping[str, Any]]
) -> None:
    lines = [
        "# Non-LLM reference-policy evaluation",
        "",
        f"Reference: **{POLICY_NAME}**. Positive WAC differences and negative mortality differences favor the LLM policy.",
        "",
        "## Overall by feedback condition and meta-round",
        "",
        "| Feedback | Round | Original WAC | Reference WAC | LLM−Ref WAC | Original mortality | Reference mortality | LLM−Ref mortality |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in by_round:
        lines.append(
            f"| {row['feedback']} | MR{row['meta_round']} | {row['original_wac']:.2f} | "
            f"{row['reference_wac']:.2f} | {row['wac_difference']:+.2f} | "
            f"{row['original_mortality']:.2f}% | {row['reference_mortality']:.2f}% | "
            f"{row['mortality_difference']:+.2f} pp |"
        )
    lines.extend([
        "",
        "## Model-level paired differences",
        "",
        "| Feedback | Round | Model | LLM−Ref WAC | LLM−Ref mortality |",
        "| --- | ---: | --- | ---: | ---: |",
    ])
    for row in by_model:
        lines.append(
            f"| {row['feedback']} | MR{row['meta_round']} | {row['model']} | "
            f"{row['wac_difference']:+.2f} | {row['mortality_difference']:+.2f} pp |"
        )
    lines.extend([
        "",
        "The heuristic is fixed across rounds. Changes in its absolute outcomes reflect the round-specific opponent policy pool, not heuristic adaptation.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def self_test() -> None:
    profiles = wac.default_agent_profiles()
    validate_policy_family(profiles, 20)
    codes = {
        profile.agent_id: build_policy_code(
            RoleParameters(profile.agent_id, profile.daily_salary, profile.water_requirement), 20
        )
        for profile in profiles
    }
    compiled = _compile_policies(codes.values())
    assert len(compiled) == len(profiles)
    for profile in profiles:
        code = codes[profile.agent_id]
        policy, _ = compiled[code]
        safe = policy(
            {"day": 1, "supply": 20},
            {"hp": 8, "budget": profile.daily_salary, "no_water_days": 1},
            {},
        )
        critical = policy(
            {"day": 10, "supply": 20},
            {"hp": 2, "budget": 300.0, "no_water_days": 2},
            {"Other": {"alive": True, "last_bid": 120.0}},
        )
        assert 0.0 <= safe <= profile.daily_salary
        assert safe < critical <= 300.0
    print("Self-test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--of-dir", type=Path, default=DEFAULT_OF)
    parser.add_argument("--opf-dir", type=Path, default=DEFAULT_OPF)
    parser.add_argument("--original-replays", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--meta-rounds", nargs="+", type=int, default=list(DEFAULT_ROUNDS))
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--bootstrap-replicates", type=int, default=2000)
    parser.add_argument("--max-groups", type=int, default=None, help="Limit experiment-round groups for a smoke test.")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.self_test:
        self_test()
        return
    if sorted(set(args.meta_rounds)) != args.meta_rounds:
        raise ValueError("--meta-rounds must be unique and increasing")
    if sorted(set(args.seeds)) != args.seeds:
        raise ValueError("--seeds must be unique and increasing")
    if args.workers <= 0 or args.bootstrap_replicates < 0:
        raise ValueError("workers must be positive and bootstrap replicates non-negative")

    of_dir = args.of_dir.resolve()
    opf_dir = args.opf_dir.resolve()
    original_path = args.original_replays.resolve()
    output_dir = args.output_dir.resolve()
    originals = load_original_outcomes(original_path)

    tasks: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for feedback, batch_dir in (("OF", of_dir), ("OPF", opf_dir)):
        batch_tasks, batch_errors = collect_group_tasks(
            batch_dir, feedback, args.meta_rounds, args.seeds, originals
        )
        tasks.extend(batch_tasks)
        errors.extend(batch_errors)
    if args.max_groups is not None:
        tasks = tasks[: args.max_groups]

    if tasks:
        first_profiles = [wac.AgentProfile(*raw) for raw in tasks[0]["profiles"]]
        validate_policy_family(first_profiles, int(tasks[0]["episode_days"]))

    rows: List[Dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        for group_rows, group_errors in executor.map(_evaluate_group, tasks, chunksize=1):
            rows.extend(group_rows)
            errors.extend(group_errors)
    rows.sort(key=lambda row: (
        row["feedback"], row["experiment_id"], row["meta_round"], row["role"], row["seed"]
    ))

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "paired_replacements.csv", rows, PAIR_FIELDS)
    write_json(output_dir / "replay_errors.json", errors)
    write_csv(
        output_dir / "replay_errors.csv", errors,
        ("feedback", "batch", "experiment_id", "meta_round", "seed", "role", "stage", "error"),
    )

    by_round = grouped_summaries(rows, ("feedback", "meta_round"), args.bootstrap_replicates)
    by_model = grouped_summaries(
        rows, ("feedback", "meta_round", "model"), args.bootstrap_replicates
    )
    by_role = grouped_summaries(
        rows, ("feedback", "meta_round", "role"), args.bootstrap_replicates
    )
    write_csv(output_dir / "summary_by_round.csv", by_round)
    write_csv(output_dir / "summary_by_model_round.csv", by_model)
    write_csv(output_dir / "summary_by_role_round.csv", by_role)
    write_json(output_dir / "summary_by_round.json", by_round)
    write_json(output_dir / "summary_by_model_round.json", by_model)
    write_json(output_dir / "summary_by_role_round.json", by_role)
    write_paper_outputs(output_dir, rows, by_round, args.bootstrap_replicates)
    write_summary_markdown(output_dir / "summary.md", by_round, by_model)

    profiles = [wac.AgentProfile(*raw) for raw in tasks[0]["profiles"]] if tasks else []
    policy_codes = {
        profile.agent_id: build_policy_code(
            RoleParameters(profile.agent_id, profile.daily_salary, profile.water_requirement),
            int(tasks[0]["episode_days"]),
        )
        for profile in profiles
    }
    write_json(output_dir / "reference_policy_codes.json", policy_codes)
    write_json(output_dir / "run_config.json", {
        "policy_name": POLICY_NAME,
        "input_batches": {
            "OF": package_relative(of_dir),
            "OPF": package_relative(opf_dir),
        },
        "original_replays": package_relative(original_path),
        "meta_rounds": args.meta_rounds,
        "seeds": args.seeds,
        "workers": args.workers,
        "bootstrap_replicates": args.bootstrap_replicates,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "intervention": "replace one focal LLM policy; keep four opponent policy codes fixed",
        "aggregation": "average seeds within experiment-role, then equal-weight roles; bootstrap experiments",
        "expected_group_count": len(tasks),
        "expected_pair_count": len(tasks) * 5 * len(args.seeds),
        "valid_pair_count": len(rows),
        "error_count": len(errors),
    })

    print(
        f"Wrote {len(rows)} paired replacements from {len(tasks)} experiment-round groups "
        f"with {len(errors)} errors to {output_dir}"
    )
    for row in by_round:
        print(
            f"{row['feedback']},MR{row['meta_round']},"
            f"reference_wac={row['reference_wac']:.2f},"
            f"reference_mortality={row['reference_mortality']:.2f},"
            f"llm_minus_reference_wac={row['wac_difference']:+.2f},"
            f"llm_minus_reference_mortality={row['mortality_difference']:+.2f}"
        )


if __name__ == "__main__":
    main()
