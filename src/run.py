import argparse
import json
import os
import time

from datetime import datetime
from typing import Any, Dict, List, Optional

import config
from agent_interface import AgentRunner, create_backend
from prompt_builder import PromptBuilder, normalize_opponent_info_mode
from wac_programmatic import (
    SCENARIOS,
    AgentProfile,
    AgentSubmission,
    WACProgrammaticEnv,
    build_supply_list,
    default_agent_profiles,
)


def _build_backend_from_spec(
    spec: Dict[str, Optional[object]],
):
    backend_name = str(
        spec.get(
            "backend",
            "",
        )
    )

    model = spec.get(
        "model"
    )

    temperature = spec.get(
        "temperature"
    )

    base_url = spec.get(
        "base_url"
    )

    return create_backend(
        backend_name,
        model=model,
        temperature=temperature,
        base_url=base_url,
    )


def _build_game_state(
    scenario: str,
    supply_range: List[int],
    episode_days: int,
    meta_round_id: int,
) -> Dict[str, object]:
    return {
        "scenario": scenario,
        "supply_range": supply_range,
        "episode_days": episode_days,
        "meta_round_id": meta_round_id,
    }


def save_daily_metric_plots_for_meta_round(
    record: Dict[str, object],
    output_dir: str,
) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")

        import matplotlib.pyplot as plt

    except Exception as exc:
        print(f"Failed to import matplotlib/pyplot. Skip plots. Error: {exc}")
        return

    meta_round_id = record.get("meta_round_id", "unknown")
    agents = record.get("agents", [])

    if not agents:
        print(f"No agents found in meta_round_{meta_round_id}. Skip plots.")
        return

    os.makedirs(output_dir, exist_ok=True)

    def build_series(traces, metric_name):
        if metric_name == "hp_after":
            return [trace.get("hp_after") for trace in traces]

        if metric_name == "budget_after":
            return [trace.get("budget_after") for trace in traces]

        if metric_name == "bid":
            return [trace.get("bid") for trace in traces]

        if metric_name == "cumulative_bid":
            total_bid = 0.0
            values = []

            for trace in traces:
                bid = trace.get("bid") or 0.0
                total_bid += bid
                values.append(total_bid)

            return values

        if metric_name == "hp_change":
            values = []
            previous_hp = 8

            for trace in traces:
                current_hp = trace.get("hp_after", previous_hp)
                values.append(current_hp - previous_hp)
                previous_hp = current_hp

            return values

        if metric_name == "budget_change":
            values = []
            previous_budget = 0.0

            for trace in traces:
                current_budget = trace.get("budget_after", previous_budget)
                values.append(current_budget - previous_budget)
                previous_budget = current_budget

            return values

        if metric_name == "alive_status":
            return [
                0 if trace.get("status") == "dead" else 1
                for trace in traces
            ]

        if metric_name == "inferred_win":
            values = []
            previous_hp = 8

            for trace in traces:
                current_hp = trace.get("hp_after", previous_hp)
                status = trace.get("status")

                if status == "dead":
                    values.append(0)
                elif current_hp >= previous_hp:
                    values.append(1)
                else:
                    values.append(0)

                previous_hp = current_hp

            return values

        return [trace.get(metric_name) for trace in traces]

    plot_specs = [
        {
            "metric": "hp_after",
            "suffix": "hp",
            "title": f"HP Over Days - Meta Round {meta_round_id}",
            "ylabel": "HP",
            "marker": "o",
        },
        {
            "metric": "budget_after",
            "suffix": "budget",
            "title": f"Budget Over Days - Meta Round {meta_round_id}",
            "ylabel": "Budget",
            "marker": "s",
        },
        {
            "metric": "bid",
            "suffix": "bid",
            "title": f"Bid Over Days - Meta Round {meta_round_id}",
            "ylabel": "Bid",
            "marker": "^",
        },
        {
            "metric": "cumulative_bid",
            "suffix": "cumulative_bid",
            "title": f"Cumulative Bid Over Days - Meta Round {meta_round_id}",
            "ylabel": "Cumulative Bid",
            "marker": "D",
        },
        {
            "metric": "hp_change",
            "suffix": "hp_change",
            "title": f"HP Change Over Days - Meta Round {meta_round_id}",
            "ylabel": "HP Change",
            "marker": "o",
        },
        {
            "metric": "budget_change",
            "suffix": "budget_change",
            "title": f"Budget Change Over Days - Meta Round {meta_round_id}",
            "ylabel": "Budget Change",
            "marker": "s",
        },
        {
            "metric": "alive_status",
            "suffix": "alive_status",
            "title": f"Alive Status Over Days - Meta Round {meta_round_id}",
            "ylabel": "Alive Status",
            "marker": "o",
        },
        {
            "metric": "inferred_win",
            "suffix": "inferred_win",
            "title": f"Inferred Win Over Days - Meta Round {meta_round_id}",
            "ylabel": "Inferred Win",
            "marker": "o",
        },
    ]

    for spec in plot_specs:
        plt.figure(figsize=(9, 4.8))

        has_valid_trace = False

        visible_agents = [
            agent
            for agent in agents
            if agent.get("daily_trace")
        ]

        num_visible = len(visible_agents)

        for idx, agent in enumerate(visible_agents):
            agent_id = agent.get("agent_id", "unknown")
            traces = agent.get("daily_trace", [])

            days = [
                trace.get("day")
                for trace in traces
            ]
            
            if num_visible > 1:
                offset = (
                    idx
                    - (num_visible - 1) / 2
                ) * 0.08
            else:
                offset = 0.0

            days_shifted = [
                day + offset
                for day in days
            ]

            values = build_series(
                traces,
                spec["metric"],
            )

            plt.plot(
                days_shifted,
                values,
                marker=spec["marker"],
                linewidth=2,
                label=agent_id,
            )

            has_valid_trace = True

        if not has_valid_trace:
            print(
                f"No valid daily_trace found in meta_round_{meta_round_id}. "
                f"Skip {spec['suffix']} plot."
            )
            plt.close()
            continue

        if spec["metric"] == "bid":
            first_traces = agents[0].get("daily_trace", [])

            supply_days = [
                trace.get("day")
                for trace in first_traces
            ]

            supply_values = [
                trace.get("supply")
                for trace in first_traces
            ]

            plt.plot(
                supply_days,
                supply_values,
                linestyle="--",
                linewidth=2,
                label="Supply",
            )

        plt.title(spec["title"])
        plt.xlabel("Day")
        plt.ylabel(spec["ylabel"])
        plt.xticks(range(1, 11))
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(loc="best")
        plt.tight_layout()

        output_path = os.path.join(
            output_dir,
            f"meta_round_{meta_round_id}_{spec['suffix']}.png",
        )

        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"Saved plot: {output_path}")


def build_compact_meta_round_record(
    record: Dict[str, Any],
) -> Dict[str, Any]:
    if not isinstance(record, dict):
        return record

    compact_agents = []

    for agent in record.get("agents", []):
        if not isinstance(agent, dict):
            continue

        compact_agents.append(
            {
                "agent_id": agent.get("agent_id"),
                "reasoning_cot": agent.get("reasoning_cot", ""),
                "strategy_code": agent.get("strategy_code", ""),
                "daily_trace": agent.get("daily_trace", []),
                "metrics": agent.get("metrics"),
                "admitted": agent.get("admitted", 0),
                "outcome_valid": agent.get("outcome_valid", 0),
                "generation_stats": agent.get("generation_stats", {}),
            }
        )

    return {
        "meta_round_id": record.get("meta_round_id"),
        "evaluation_mode": record.get("evaluation_mode"),
        "all_agents_admitted": record.get("all_agents_admitted"),
        "invalid_agents": record.get("invalid_agents", []),
        "outcome_valid": record.get("outcome_valid", 0),
        "debug_invalid_agents_allowed": record.get("debug_invalid_agents_allowed", 0),
        "official_outcome": record.get("official_outcome", 1),
        "environment": record.get("environment", {}),
        "agents": compact_agents,
    }
        
def save_cross_meta_metric_plots(
    history: Dict[str, object],
    output_dir: str,
) -> None:
    try:
        import re
        import matplotlib

        matplotlib.use("Agg")

        import matplotlib.pyplot as plt

    except Exception as exc:
        print(f"Failed to import matplotlib/pyplot. Skip cross-meta plots. Error: {exc}")
        return

    from collections import defaultdict

    os.makedirs(output_dir, exist_ok=True)

    mr_keys = sorted(
        [
            key
            for key in history.keys()
            if key.startswith("meta_round")
        ],
        key=lambda key: int(re.findall(r"\d+", key)[0]) if re.findall(r"\d+", key) else 0,
    )

    if not mr_keys:
        return

    meta_round_nums = [
        int(re.findall(r"\d+", key)[0])
        for key in mr_keys
    ]

    metric_specs = [
        ("hp", "Final HP"),
        ("survival_day", "Survival Days"),
        ("budget", "Final Budget"),
        ("total_bid", "Total Bid"),
        ("average_bid", "Average Bid"),
        ("bid_variance", "Bid Variance"),
        ("bid_entropy", "Bid Entropy"),
        ("bid_supply_sensitivity", "Bid-Supply Sensitivity"),
        ("opponent_awareness_score", "Opponent Awareness Score"),
        ("recovery_score", "Recovery Score"),
        ("supply_bid_correlation", "Supply-Bid Correlation"),
        ("utility_score", "Utility Score"),
        ("survival_efficiency", "Survival Efficiency"),
        ("strategy_complexity", "Strategy Complexity"),
        ("branch_count", "Branch Count"),
        ("loop_count", "Loop Count"),
        ("function_call_count", "Function Call Count"),
        ("compile_success", "Compile Success"),
        ("runtime_success", "Runtime Success"),
        ("hallucinated_api_count", "Hallucinated API Count"),
    ]

    for metric_key, metric_title in metric_specs:
        trends = defaultdict(list)

        for mr_key in mr_keys:
            round_data = history[mr_key]

            for agent_id, info in round_data.items():
                if not isinstance(info, dict):
                    continue

                value = info.get(metric_key, 0)

                if isinstance(value, bool):
                    value = int(value)

                if value is None:
                    value = 0

                trends[agent_id].append(value)

        if not trends:
            continue

        plt.figure(figsize=(9, 4.8))

        for agent_id, trend in trends.items():
            plt.plot(
                meta_round_nums,
                trend,
                marker="o",
                linewidth=2,
                label=agent_id,
            )

        plt.title(f"{metric_title} Across Meta-Rounds")
        plt.xlabel("Meta-Round")
        plt.ylabel(metric_title)
        plt.xticks(meta_round_nums)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.legend(loc="best")
        plt.tight_layout()

        output_path = os.path.join(
            output_dir,
            f"meta_rounds_{metric_key}.png",
        )

        plt.savefig(output_path, dpi=300)
        plt.close()

        print(f"Saved cross-meta plot: {output_path}")


def save_agent_average_summary(
    history: Dict[str, object],
    agent_runner: AgentRunner,
    agent_profiles: List[AgentProfile],
    output_filename: str,
    enable_plots: bool = True,
) -> None:
    from collections import defaultdict

    PERFORMANCE_METRIC_KEYS = [
        "total_bid",
        "average_bid",
        "bid_variance",
        "bid_entropy",
        "bid_supply_sensitivity",
        "opponent_awareness_score",
        "recovery_score",
        "supply_bid_correlation",
        "utility_score",
        "survival_efficiency",
        "strategy_complexity",
        "branch_count",
        "loop_count",
        "function_call_count",
    ]

    RELIABILITY_METRIC_KEYS = [
        "admitted",
        "outcome_valid",
        "one_shot_json_valid",
        "one_shot_code_extracted",
        "one_shot_compile_success",
        "one_shot_runtime_success",
        "one_shot_strict_success",
        "repair_used",
        "json_repair_used",
        "json_repair_success",
        "code_repair_used",
        "code_repair_success",
        "repair_attempts",
        "post_repair_compile_success",
        "post_repair_runtime_success",
        "post_repair_strict_success",
        "strict_success_rate",
        "compile_success",
        "runtime_success",
        "hallucinated_api_count",
        "json_parse_failed",
        "default_code_used",
    ]

    agent_stats = defaultdict(
        lambda: {
            "attempted_meta_rounds": 0,
            "valid_meta_rounds": 0,
            "valid_survival_days_list": [],
            "valid_final_budgets_list": [],
            "valid_total_bid_list": [],
            "valid_all_bids": [],
            "valid_death_count": 0,
            "performance_metric_lists": defaultdict(list),
            "reliability_metric_lists": defaultdict(list),
        }
    )

    for meta_round_key, meta_round_data in history.items():
        if not meta_round_key.startswith("meta_round"):
            continue

        for agent_id, info in meta_round_data.items():
            if not isinstance(info, dict):
                continue

            stats = agent_stats[agent_id]
            stats["attempted_meta_rounds"] += 1

            outcome_valid = int(info.get("outcome_valid", 0)) == 1
            admitted = int(info.get("admitted", 0)) == 1
            strict_success = int(info.get("strict_success_rate", 0)) == 1
            performance_valid = outcome_valid and admitted and strict_success

            for metric_key in RELIABILITY_METRIC_KEYS:
                value = info.get(metric_key, 0)
                if isinstance(value, bool):
                    value = int(value)
                if isinstance(value, (int, float)):
                    stats["reliability_metric_lists"][metric_key].append(float(value))
                else:
                    stats["reliability_metric_lists"][metric_key].append(0.0)

            if not performance_valid:
                continue

            stats["valid_meta_rounds"] += 1

            survival_day = info.get("survival_day")
            final_budget = info.get("budget")
            final_hp = info.get("hp")
            total_bid = info.get("total_bid")

            if isinstance(survival_day, (int, float)):
                stats["valid_survival_days_list"].append(float(survival_day))

            if isinstance(final_budget, (int, float)):
                stats["valid_final_budgets_list"].append(float(final_budget))

            if isinstance(total_bid, (int, float)):
                stats["valid_total_bid_list"].append(float(total_bid))

            if isinstance(final_hp, (int, float)) and float(final_hp) <= 0:
                stats["valid_death_count"] += 1

            for metric_key in PERFORMANCE_METRIC_KEYS:
                value = info.get(metric_key)
                if isinstance(value, bool):
                    value = int(value)
                if isinstance(value, (int, float)):
                    stats["performance_metric_lists"][metric_key].append(float(value))

            traces = info.get("daily_traces", [])
            for trace in traces:
                if not isinstance(trace, dict):
                    continue
                bid = trace.get("bid")
                if isinstance(bid, (int, float)):
                    stats["valid_all_bids"].append(float(bid))

    output_data = {
        "experiment_metadata": {
            "total_meta_rounds": len(
                [
                    key
                    for key in history.keys()
                    if key.startswith("meta_round")
                ]
            ),
            "description": "Water Allocation Challenge Agent Average Summary",
        },
        "agent_averages": {},
    }

    for agent_id, stats in agent_stats.items():
        rounds_played = stats["attempted_meta_rounds"]
        valid_rounds_played = stats["valid_meta_rounds"]

        if rounds_played == 0:
            continue

        if valid_rounds_played > 0 and stats["valid_survival_days_list"]:
            average_survival_days = round(sum(stats["valid_survival_days_list"]) / len(stats["valid_survival_days_list"]), 2)
        else:
            average_survival_days = None

        if valid_rounds_played > 0 and stats["valid_final_budgets_list"]:
            average_final_budget = round(sum(stats["valid_final_budgets_list"]) / len(stats["valid_final_budgets_list"]), 2)
        else:
            average_final_budget = None

        if valid_rounds_played > 0 and stats["valid_all_bids"]:
            average_daily_bid = round(sum(stats["valid_all_bids"]) / len(stats["valid_all_bids"]), 2)
        else:
            average_daily_bid = None

        if valid_rounds_played > 0 and stats["valid_total_bid_list"]:
            average_total_bid = round(sum(stats["valid_total_bid_list"]) / len(stats["valid_total_bid_list"]), 2)
        else:
            average_total_bid = None

        if valid_rounds_played > 0:
            mortality_rate = f"{(stats['valid_death_count'] / valid_rounds_played) * 100.0:.1f}%"
        else:
            mortality_rate = "N/A"

        developer_name = agent_id

        for profile in agent_profiles:
            if profile.agent_id == agent_id:
                developer_name = profile.agent_id
                break

        model_name = "Unknown Model"

        try:
            backend = agent_runner._select_backend(agent_id)

            if hasattr(backend, "model") and backend.model:
                model_name = backend.model
            else:
                model_name = backend.__class__.__name__

        except Exception:
            pass

        performance_averages = {}
        for metric_key in PERFORMANCE_METRIC_KEYS:
            values = stats["performance_metric_lists"].get(metric_key, [])
            if valid_rounds_played > 0 and values:
                performance_averages[f"avg_{metric_key}"] = round(sum(values) / len(values), 4)
            else:
                performance_averages[f"avg_{metric_key}"] = None

        reliability_averages = {}
        for metric_key in RELIABILITY_METRIC_KEYS:
            values = stats["reliability_metric_lists"].get(metric_key, [])
            reliability_averages[f"avg_{metric_key}"] = round(sum(values) / rounds_played, 4) if rounds_played > 0 else 0.0

        avg_admitted = round(sum(stats["reliability_metric_lists"].get("admitted", [])) / rounds_played, 4)
        avg_outcome_valid = round(sum(stats["reliability_metric_lists"].get("outcome_valid", [])) / rounds_played, 4)
        avg_one_shot_json_valid = round(sum(stats["reliability_metric_lists"].get("one_shot_json_valid", [])) / rounds_played, 4)
        avg_one_shot_code_extracted = round(sum(stats["reliability_metric_lists"].get("one_shot_code_extracted", [])) / rounds_played, 4)
        avg_one_shot_compile_success = round(sum(stats["reliability_metric_lists"].get("one_shot_compile_success", [])) / rounds_played, 4)
        avg_one_shot_runtime_success = round(sum(stats["reliability_metric_lists"].get("one_shot_runtime_success", [])) / rounds_played, 4)
        avg_one_shot_strict_success = round(sum(stats["reliability_metric_lists"].get("one_shot_strict_success", [])) / rounds_played, 4)
        avg_repair_used = round(sum(stats["reliability_metric_lists"].get("repair_used", [])) / rounds_played, 4)
        avg_json_repair_success = round(sum(stats["reliability_metric_lists"].get("json_repair_success", [])) / rounds_played, 4)
        avg_code_repair_success = round(sum(stats["reliability_metric_lists"].get("code_repair_success", [])) / rounds_played, 4)
        avg_post_repair_strict_success = round(sum(stats["reliability_metric_lists"].get("post_repair_strict_success", [])) / rounds_played, 4)
        avg_repair_attempts = round(sum(stats["reliability_metric_lists"].get("repair_attempts", [])) / rounds_played, 4)
        json_repair_used_count = sum(stats["reliability_metric_lists"].get("json_repair_used", []))
        json_repair_success_count = sum(stats["reliability_metric_lists"].get("json_repair_success", []))
        code_repair_used_count = sum(stats["reliability_metric_lists"].get("code_repair_used", []))
        code_repair_success_count = sum(stats["reliability_metric_lists"].get("code_repair_success", []))

        json_repair_success_given_used = (
            round(json_repair_success_count / json_repair_used_count, 4)
            if json_repair_used_count > 0
            else None
        )
        code_repair_success_given_used = (
            round(code_repair_success_count / code_repair_used_count, 4)
            if code_repair_used_count > 0
            else None
        )

        output_data["agent_averages"][agent_id] = {
            "developer_name": developer_name,
            "model_used": model_name,
            "attempted_meta_rounds": rounds_played,
            "valid_meta_rounds": valid_rounds_played,
            "invalid_meta_rounds": rounds_played - valid_rounds_played,
            "valid_round_rate": round(valid_rounds_played / rounds_played, 4),
            "avg_survival_days": average_survival_days,
            "avg_final_budget": average_final_budget,
            "avg_daily_bid": average_daily_bid,
            "avg_total_bid": average_total_bid,
            "mortality_rate": mortality_rate,
            "death_count": f"{stats['valid_death_count']}/{valid_rounds_played}",
            "json_parse_fail_rate": round(sum(stats["reliability_metric_lists"].get("json_parse_failed", [])) / rounds_played, 4),
            "default_code_usage_rate": round(sum(stats["reliability_metric_lists"].get("default_code_used", [])) / rounds_played, 4),
            "admission_rate": avg_admitted,
            "outcome_valid_rate": avg_outcome_valid,
            "one_shot_json_valid_rate": avg_one_shot_json_valid,
            "one_shot_code_extracted_rate": avg_one_shot_code_extracted,
            "one_shot_compile_success_rate": avg_one_shot_compile_success,
            "one_shot_runtime_success_rate": avg_one_shot_runtime_success,
            "one_shot_strict_success_rate": avg_one_shot_strict_success,
            "repair_used_rate": avg_repair_used,
            "json_repair_success_rate": avg_json_repair_success,
            "code_repair_success_rate": avg_code_repair_success,
            "json_repair_success_given_used": json_repair_success_given_used,
            "code_repair_success_given_used": code_repair_success_given_used,
            "post_repair_strict_success_rate": avg_post_repair_strict_success,
            "avg_repair_attempts": avg_repair_attempts,
            **performance_averages,
            **reliability_averages,
        }

    with open(
        output_filename,
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            output_data,
            handle,
            indent=2,
            ensure_ascii=False,
        )

    print(
        f"Saved agent average summary: {output_filename}"
    )

    if enable_plots:
        cross_meta_plot_dir = os.path.join(
            os.path.dirname(output_filename) or ".",
            "cross_meta_metric_plots",
        )

        save_cross_meta_metric_plots(
            history=history,
            output_dir=cross_meta_plot_dir,
        )
    else:
        print("Skipping cross-meta plots (--no-plots).")
    
def run_experiment(
    args: argparse.Namespace,
    backend_overrides: Optional[Dict[str, Dict[str, object]]] = None,
) -> None:
    total_start_time = time.time()

    env = WACProgrammaticEnv(
        episode_days=10
    )

    profiles: List[AgentProfile] = default_agent_profiles()
    per_agent_backends = backend_overrides or config.AGENT_BACKENDS

    experiment_id = (
        args.experiment_id
        or datetime.now().strftime(
            "exp_%Y%m%d_%H%M%S"
        )
    )

    exp_dir = os.path.join(
        args.output_dir,
        experiment_id,
    )

    os.makedirs(
        exp_dir,
        exist_ok=True,
    )

    backend_record = {}

    for profile in profiles:
        spec = dict(
            config.PER_AGENT_DEFAULT
        )

        spec.update(
            per_agent_backends.get(
                profile.agent_id,
                {},
            )
        )

        backend_record[
            profile.agent_id
        ] = {
            "backend": spec.get(
                "backend"
            ),
            "model": spec.get(
                "model"
            ),
            "temperature": spec.get(
                "temperature"
            ),
            "base_url": spec.get(
                "base_url"
            ),
        }

    with open(
        os.path.join(
            exp_dir,
            "backend_config.json",
        ),
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            backend_record,
            handle,
            indent=2,
        )

    prompt_builder = PromptBuilder()
    opponent_info_mode = normalize_opponent_info_mode(args.opponent_info_mode)

    if args.backend_mode == "per-agent":
        backend_map = {}

        default_spec = dict(
            config.PER_AGENT_DEFAULT
        )

        for profile in profiles:
            spec = dict(
                default_spec
            )

            spec.update(
                per_agent_backends.get(
                    profile.agent_id,
                    {},
                )
            )

            backend_map[
                profile.agent_id
            ] = _build_backend_from_spec(
                spec
            )

        default_backend = _build_backend_from_spec(
            default_spec
        )

        runner = AgentRunner(
            backend=default_backend,
            backend_map=backend_map,
            prompt_builder=prompt_builder,
        )

    else:
        uniform_spec = {
            "backend": args.backend or config.UNIFORM_BACKEND,
            "model": (
                args.backend_model
                if args.backend_model is not None
                else config.UNIFORM_MODEL
            ),
            "temperature": (
                args.backend_temperature
                if args.backend_temperature is not None
                else config.UNIFORM_TEMPERATURE
            ),
            "base_url": (
                args.backend_base_url
                if args.backend_base_url is not None
                else config.UNIFORM_BASE_URL
            ),
        }

        backend = _build_backend_from_spec(
            uniform_spec
        )

        runner = AgentRunner(
            backend=backend,
            prompt_builder=prompt_builder,
        )

    previous_codes: Dict[str, str] = {}

    history: Dict[str, object] = {}

    all_meta_history: Dict[str, object] = {}

    for meta_round_id in range(
        1,
        args.meta_rounds + 1,
    ):
        meta_round_start_time = time.time()

        if args.seed is None:
            seed_for_round = None
        else:
            seed_for_round = args.seed + meta_round_id

        supply_list = build_supply_list(
            scenario=args.scenario,
            days=env.episode_days,
            seed=seed_for_round,
        )

        game_state = _build_game_state(
            args.scenario,
            list(
                SCENARIOS[
                    args.scenario
                ]
            ),
            env.episode_days,
            meta_round_id,
        )

        submissions: List[AgentSubmission] = []
        generation_stats_by_agent: Dict[str, Dict[str, bool]] = {}

        total_agents = len(
            profiles
        )

        for index, profile in enumerate(
            profiles,
            start=1,
        ):
            print(
                f"\n[Meta-Round {meta_round_id}/{args.meta_rounds}] "
                f"[Agent {index}/{total_agents}] "
                f"{profile.agent_id}"
            )

            spec = per_agent_backends.get(
                profile.agent_id,
                {},
            )

            backend_name = spec.get(
                "backend",
                "default",
            )

            model_name = spec.get(
                "model",
                "default",
            )

            print(
                f"  Backend: {backend_name}"
            )

            print(
                f"  Model: {model_name}"
            )

            if opponent_info_mode == "full_code_access":
                opponent_code = {
                    agent_id: code
                    for agent_id, code in previous_codes.items()
                    if agent_id != profile.agent_id
                }
            else:
                opponent_code = {}

            print(
                "  Generating reasoning/code..."
            )

            reasoning_cot, strategy_code, generation_stats = runner.generate_validated_strategy(
                agent_profile={
                    "agent_id": profile.agent_id,
                    "water_requirement": profile.water_requirement,
                    "daily_salary": profile.daily_salary,
                },
                game_state=game_state,
                opponent_code=opponent_code,
                history={
                    "last_meta_round": history.get(
                        "last_meta_round"
                    ),
                },
                opponent_info_mode=opponent_info_mode,
                show_opponent_code=(
                    opponent_info_mode == "full_code_access"
                    and config.REVEAL_OPPONENT_CODE
                ),
                evaluation_mode=args.evaluation_mode,
                max_json_repair_attempts=args.max_json_repair_attempts,
                max_code_repair_attempts=args.max_code_repair_attempts,
            )

            print(
                "  Strategy generation complete."
            )

            reasoning_cot = generation_stats.get("final_reasoning", reasoning_cot)
            strategy_code = generation_stats.get("final_code", strategy_code)

            generation_stats_by_agent[profile.agent_id] = generation_stats

            submissions.append(
                AgentSubmission(
                    agent_id=profile.agent_id,
                    reasoning_cot=reasoning_cot,
                    strategy_code=strategy_code,
                )
            )

        invalid_agents = [
            agent_id
            for agent_id, stats in generation_stats_by_agent.items()
            if int(stats.get("admitted", 0)) != 1
        ]
        all_agents_admitted = len(invalid_agents) == 0

        if all_agents_admitted or args.allow_invalid_agents_for_debug:
            record = env.build_meta_round_record(
                meta_round_id=meta_round_id,
                profiles=profiles,
                submissions=submissions,
                supply_list=supply_list,
                scenario=args.scenario,
                seed=seed_for_round,
            )

            record["evaluation_mode"] = args.evaluation_mode
            record["all_agents_admitted"] = int(all_agents_admitted)
            record["invalid_agents"] = [] if all_agents_admitted else invalid_agents
            record["outcome_valid"] = int(all_agents_admitted)
            record["debug_invalid_agents_allowed"] = int(args.allow_invalid_agents_for_debug and (not all_agents_admitted))
            record["official_outcome"] = int(all_agents_admitted)

            for agent in record.get("agents", []):
                agent_id = agent.get("agent_id")
                stats = generation_stats_by_agent.get(agent_id, {})
                admitted = int(stats.get("admitted", 0))
                agent["admitted"] = admitted
                agent["outcome_valid"] = int(all_agents_admitted)
                agent["generation_stats"] = stats

        else:
            record = {
                "meta_round_id": meta_round_id,
                "evaluation_mode": args.evaluation_mode,
                "all_agents_admitted": 0,
                "invalid_agents": invalid_agents,
                "outcome_valid": 0,
                "debug_invalid_agents_allowed": 0,
                "official_outcome": 0,
                "environment": {
                    "scenario": args.scenario,
                    "supply_range": SCENARIOS[args.scenario],
                    "seed": seed_for_round,
                    "episode_days": env.episode_days,
                    "players": [
                        {
                            "agent_id": p.agent_id,
                            "water_requirement": p.water_requirement,
                            "daily_salary": p.daily_salary,
                        }
                        for p in profiles
                    ],
                    "supply_list": supply_list,
                },
                "agents": [
                    {
                        "agent_id": submission.agent_id,
                        "reasoning_cot": submission.reasoning_cot,
                        "strategy_code": submission.strategy_code,
                        "daily_trace": [],
                        "metrics": None,
                        "admitted": int(generation_stats_by_agent[submission.agent_id].get("admitted", 0)),
                        "outcome_valid": 0,
                        "generation_stats": generation_stats_by_agent[submission.agent_id],
                    }
                    for submission in submissions
                ],
            }

        record_for_log = (
            build_compact_meta_round_record(record)
            if args.compact_meta_log
            else record
        )

        log_path = env.save_meta_round_log(
            record_for_log,
            args.output_dir,
            experiment_id,
        )

        daily_plot_dir = os.path.join(
            exp_dir,
            "daily_metric_plots",
        )

        if not args.no_plots and int(record.get("outcome_valid", 0)) == 1:
            save_daily_metric_plots_for_meta_round(
                record=record,
                output_dir=daily_plot_dir,
            )
        else:
            print("Skipping daily metric plots (--no-plots or outcome_valid=0).")

        history = {
            "last_meta_round": meta_round_id,
            "log_path": log_path,
            "agent_summaries": {},
        }

        round_summary = {}

        for agent in record[
            "agents"
        ]:
            agent_id = agent["agent_id"]
            generation_stats = generation_stats_by_agent.get(agent_id, {})
            metrics = agent.get("metrics")
            outcome_valid = int(record.get("outcome_valid", 0))
            admitted = int(generation_stats.get("admitted", 0))

            common_reliability = {
                "admitted": admitted,
                "outcome_valid": outcome_valid,
                "one_shot_json_valid": int(generation_stats.get("one_shot_json_valid", 0)),
                "one_shot_code_extracted": int(generation_stats.get("one_shot_code_extracted", 0)),
                "one_shot_compile_success": int(generation_stats.get("one_shot_compile_success", 0)),
                "one_shot_runtime_success": int(generation_stats.get("one_shot_runtime_success", 0)),
                "one_shot_strict_success": int(generation_stats.get("one_shot_strict_success", 0)),
                "repair_used": int(generation_stats.get("repair_used", 0)),
                "json_repair_used": int(generation_stats.get("json_repair_used", 0)),
                "json_repair_success": int(generation_stats.get("json_repair_success", 0)),
                "code_repair_used": int(generation_stats.get("code_repair_used", 0)),
                "code_repair_success": int(generation_stats.get("code_repair_success", 0)),
                "repair_attempts": int(generation_stats.get("repair_attempts", 0)),
                "post_repair_compile_success": int(generation_stats.get("post_repair_compile_success", 0)),
                "post_repair_runtime_success": int(generation_stats.get("post_repair_runtime_success", 0)),
                "post_repair_strict_success": int(generation_stats.get("post_repair_strict_success", 0)),
                "strict_success_rate": int(generation_stats.get("strict_success_rate", 0)),
                "compile_success": int(generation_stats.get("post_repair_compile_success", 0)),
                "runtime_success": int(generation_stats.get("post_repair_runtime_success", 0)),
                "json_parse_failed": int(generation_stats.get("json_parse_failed", 0)),
                "default_code_used": 0,
                "generation_success": int(generation_stats.get("generation_success", 0)),
                "final_error_type": generation_stats.get("final_error_type"),
                "final_error_message": generation_stats.get("final_error_message"),
            }

            performance_valid = (
                outcome_valid == 1
                and admitted == 1
                and metrics is not None
            )

            # Keep only the compact per-agent summary for the next meta-round.
            valid_bids = [
                t.get("bid")
                for t in agent.get("daily_trace", [])
                if isinstance(t, dict) and t.get("bid") is not None
            ]
            max_bid_val = round(max(valid_bids), 2) if valid_bids else 0.0

            if performance_valid:
                final_trace = agent["daily_trace"][-1]
                history[
                    "agent_summaries"
                ][
                    agent_id
                ] = {
                    "valid": True,
                    "final_hp": metrics[
                        "final_hp"
                    ],
                    "survival_days": metrics[
                        "survival_days"
                    ],
                    "average_bid": metrics[
                        "average_bid"
                    ],
                    "final_budget": final_trace[
                        "budget_after"
                    ],
                    "max_bid": max_bid_val
                }
            else:
                history[
                    "agent_summaries"
                ][
                    agent_id
                ] = {
                    "valid": False,
                    "failure": {
                        "admitted": admitted,
                        "outcome_valid": outcome_valid,
                        "one_shot_json_valid": int(generation_stats.get("one_shot_json_valid", 0)),
                        "one_shot_code_extracted": int(generation_stats.get("one_shot_code_extracted", 0)),
                        "one_shot_runtime_success": int(generation_stats.get("one_shot_runtime_success", 0)),
                        "one_shot_strict_success": int(generation_stats.get("one_shot_strict_success", 0)),
                        "repair_used": int(generation_stats.get("repair_used", 0)),
                        "post_repair_strict_success": int(generation_stats.get("post_repair_strict_success", 0)),
                        "strict_success_rate": int(generation_stats.get("strict_success_rate", 0)),
                        "final_error_type": generation_stats.get("final_error_type"),
                        "final_error_message": generation_stats.get("final_error_message"),
                    },
                }

            if performance_valid:
                final_trace = agent["daily_trace"][-1]
                performance_block = {
                    "hp": metrics["final_hp"],
                    "survival_day": metrics["survival_days"],
                    "budget": final_trace["budget_after"],
                    "total_bid": metrics["total_bid"],
                    "average_bid": metrics["average_bid"],
                    "bid_variance": metrics["bid_variance"],
                    "bid_entropy": metrics["bid_entropy"],
                    "bid_supply_sensitivity": metrics["bid_supply_sensitivity"],
                    "opponent_awareness_score": metrics["opponent_awareness_score"],
                    "recovery_score": metrics["recovery_score"],
                    "supply_bid_correlation": metrics["supply_bid_correlation"],
                    "utility_score": metrics["utility_score"],
                    "survival_efficiency": metrics["survival_efficiency"],
                    "strategy_complexity": metrics["strategy_complexity"],
                    "branch_count": metrics["branch_count"],
                    "loop_count": metrics["loop_count"],
                    "function_call_count": metrics["function_call_count"],
                    "hallucinated_api_count": metrics["hallucinated_api_count"],
                    "daily_traces": agent.get("daily_trace", []),
                }
            else:
                performance_block = {
                    "hp": None,
                    "survival_day": None,
                    "budget": None,
                    "total_bid": None,
                    "average_bid": None,
                    "bid_variance": None,
                    "bid_entropy": None,
                    "bid_supply_sensitivity": None,
                    "opponent_awareness_score": None,
                    "recovery_score": None,
                    "supply_bid_correlation": None,
                    "utility_score": None,
                    "survival_efficiency": None,
                    "strategy_complexity": None,
                    "branch_count": None,
                    "loop_count": None,
                    "function_call_count": None,
                    "hallucinated_api_count": None,
                    "daily_traces": [],
                }

            round_summary[agent_id] = {
                **performance_block,
                **common_reliability,
            }

        all_meta_history[
            f"meta_round_{meta_round_id}"
        ] = round_summary

        if int(record.get("outcome_valid", 0)) == 1:
            previous_codes = {
                submission.agent_id: submission.strategy_code
                for submission in submissions
            }
        else:
            previous_codes = {}

        meta_round_elapsed = (
            time.time()
            - meta_round_start_time
        )

        print(
            f"Meta-round {meta_round_id} complete "
            f"({meta_round_elapsed:.2f} sec). "
            f"Log: {log_path}"
        )

    total_elapsed = time.time() - total_start_time

    print(
        "\n=================================================="
    )

    print(
        "All meta-rounds complete."
    )

    print(
        f"Total execution time: {total_elapsed:.2f} sec"
    )

    print(
        "=================================================="
    )

    save_agent_average_summary(
        history=all_meta_history,
        agent_runner=runner,
        agent_profiles=profiles,
        output_filename=os.path.join(
            exp_dir,
            "agent_averages.json",
        ),
        enable_plots=not args.no_plots,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Water Allocation Challenge Programmatic Runner"
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default="low",
        choices=sorted(
            SCENARIOS.keys()
        ),
        help="Scarcity scenario: low, medium, or high",
    )

    parser.add_argument(
        "--meta-rounds",
        type=int,
        default=3,
        help="Number of meta-rounds to run",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base random seed for deterministic supply generation",
    )

    parser.add_argument(
        "--backend-mode",
        type=str,
        default=config.BACKEND_MODE,
        choices=[
            "uniform",
            "per-agent",
        ],
        help="Backend mode: uniform or per-agent",
    )

    parser.add_argument(
        "--backend",
        type=str,
        default=None,
        choices=[
            "mock",
            "openai",
            "gemini",
            "ollama",
            "deepseek",
        ],
        help="LLM backend for uniform mode",
    )

    parser.add_argument(
        "--backend-model",
        type=str,
        default=None,
        help="Model name for uniform mode",
    )

    parser.add_argument(
        "--backend-temperature",
        type=float,
        default=None,
        help="Temperature for uniform mode",
    )

    parser.add_argument(
        "--backend-base-url",
        type=str,
        default=None,
        help="Base URL for uniform mode",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="log",
        help="Directory to write meta-round logs",
    )

    parser.add_argument(
        "--experiment-id",
        type=str,
        default=None,
        help="Optional experiment ID suffix for log naming",
    )

    parser.add_argument(
        "--opponent-info-mode",
        type=str,
        default=config.OPPONENT_INFO_MODE,
        help="Opponent info exposure across meta-rounds",
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating daily and cross-meta line plots",
    )

    parser.add_argument(
        "--compact-meta-log",
        action="store_true",
        help="Save compact meta-round logs (omit metrics)",
    )

    parser.add_argument(
        "--evaluation-mode",
        type=str,
        default="repair_assisted",
        choices=["one_shot", "repair_assisted"],
    )

    parser.add_argument(
        "--max-json-repair-attempts",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--max-code-repair-attempts",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--allow-invalid-agents-for-debug",
        action="store_true",
    )

    args = parser.parse_args()
    run_experiment(args)


if __name__ == "__main__":
    main()