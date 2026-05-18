import argparse
import json
import os
import time

from datetime import datetime
from typing import Dict, List, Optional

import config
from agent_interface import AgentRunner, create_backend
from prompt_builder import PromptBuilder
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

        for agent in agents:
            agent_id = agent.get("agent_id", "unknown")
            traces = agent.get("daily_trace", [])

            if not traces:
                continue

            days = [
                trace.get("day")
                for trace in traces
            ]

            values = build_series(
                traces,
                spec["metric"],
            )

            plt.plot(
                days,
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
        ("adaptation_score", "Adaptation Score"),
        ("panic_score", "Panic Score"),
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

    extra_metric_keys = [
        "total_bid",
        "average_bid",
        "bid_variance",
        "bid_entropy",
        "adaptation_score",
        "panic_score",
        "opponent_awareness_score",
        "recovery_score",
        "supply_bid_correlation",
        "utility_score",
        "survival_efficiency",
        "strategy_complexity",
        "branch_count",
        "loop_count",
        "function_call_count",
        "compile_success",
        "runtime_success",
        "hallucinated_api_count",
    ]

    agent_stats = defaultdict(
        lambda: {
            "survival_days_list": [],
            "final_budgets_list": [],
            "all_bids": [],
            "death_count": 0,
            "rounds_played": 0,
            "metric_lists": defaultdict(list),
        }
    )

    for meta_round_key, meta_round_data in history.items():
        if not meta_round_key.startswith("meta_round"):
            continue

        for agent_id, info in meta_round_data.items():
            if not isinstance(info, dict):
                continue

            stats = agent_stats[agent_id]
            stats["rounds_played"] += 1

            survival_day = info.get("survival_day", 0)
            final_budget = info.get("budget", 0.0)
            final_hp = info.get("hp", 0)

            stats["survival_days_list"].append(survival_day)
            stats["final_budgets_list"].append(final_budget)

            if final_hp <= 0:
                stats["death_count"] += 1

            for metric_key in extra_metric_keys:
                value = info.get(metric_key)

                if isinstance(value, bool):
                    value = int(value)

                if isinstance(value, (int, float)):
                    stats["metric_lists"][metric_key].append(float(value))

            traces = info.get("recent_traces", [])

            for trace in traces:
                if not isinstance(trace, dict):
                    continue

                bid = trace.get("bid")

                if bid is not None:
                    stats["all_bids"].append(bid)

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
        rounds_played = stats["rounds_played"]

        if rounds_played == 0:
            continue

        average_survival_days = (
            sum(stats["survival_days_list"])
            / rounds_played
        )

        average_final_budget = (
            sum(stats["final_budgets_list"])
            / rounds_played
        )

        if stats["all_bids"]:
            average_daily_bid = (
                sum(stats["all_bids"])
                / len(stats["all_bids"])
            )
        else:
            average_daily_bid = 0.0

        mortality_rate = (
            stats["death_count"]
            / rounds_played
            * 100.0
        )

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

        extra_averages = {}

        for metric_key in extra_metric_keys:
            values = stats["metric_lists"].get(
                metric_key,
                [],
            )

            if values:
                extra_averages[f"avg_{metric_key}"] = round(
                    sum(values) / len(values),
                    4,
                )

        output_data["agent_averages"][agent_id] = {
            "developer_name": developer_name,
            "model_used": model_name,
            "avg_survival_days": round(
                average_survival_days,
                2,
            ),
            "avg_final_budget": round(
                average_final_budget,
                2,
            ),
            "avg_daily_bid": round(
                average_daily_bid,
                2,
            ),
            "mortality_rate": f"{mortality_rate:.1f}%",
            "death_count": f"{stats['death_count']}/{rounds_played}",
            **extra_averages,
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
    
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Water Allocation Challenge Programmatic Runner"
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default="medium",
        choices=sorted(
            SCENARIOS.keys()
        ),
        help="Scarcity scenario: low, medium, or high",
    )

    parser.add_argument(
        "--meta-rounds",
        type=int,
        default=10,
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
        "--no-plots",
        action="store_true",
        help="Skip generating daily and cross-meta line plots",
    )

    args = parser.parse_args()

    total_start_time = time.time()

    env = WACProgrammaticEnv(
        episode_days=10
    )

    profiles: List[AgentProfile] = default_agent_profiles()

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
            config.AGENT_BACKENDS.get(
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
                config.AGENT_BACKENDS.get(
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

            spec = config.AGENT_BACKENDS.get(
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

            opponent_code = {
                agent_id: code
                for agent_id, code in previous_codes.items()
                if agent_id != profile.agent_id
            }

            opponent_history = {}

            if history.get(
                "agent_summaries"
            ):
                opponent_history = {
                    agent_id: summary
                    for agent_id, summary in history[
                        "agent_summaries"
                    ].items()
                    if agent_id != profile.agent_id
                }

            print(
                "  Generating reasoning/code..."
            )

            reasoning_cot, strategy_code = runner.generate_strategy(
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
                    "opponent_summaries": opponent_history,
                },
            )

            print(
                "  Strategy generation complete."
            )

            submissions.append(
                AgentSubmission(
                    agent_id=profile.agent_id,
                    reasoning_cot=reasoning_cot,
                    strategy_code=strategy_code,
                )
            )

        record = env.build_meta_round_record(
            meta_round_id=meta_round_id,
            profiles=profiles,
            submissions=submissions,
            supply_list=supply_list,
            scenario=args.scenario,
            seed=seed_for_round,
        )

        log_path = env.save_meta_round_log(
            record,
            args.output_dir,
            experiment_id,
        )

        daily_plot_dir = os.path.join(
            exp_dir,
            "daily_metric_plots",
        )

        if not args.no_plots:
            save_daily_metric_plots_for_meta_round(
                record=record,
                output_dir=daily_plot_dir,
            )
        else:
            print("Skipping daily metric plots (--no-plots).")

        history = {
            "last_meta_round": meta_round_id,
            "log_path": log_path,
            "agent_summaries": {},
        }

        round_summary = {}

        for agent in record[
            "agents"
        ]:
            final_trace = agent[
                "daily_trace"
            ][
                -1
            ]

            metrics = agent[
                "metrics"
            ]

            # 🌟 [關鍵改動] 僅動態計算並打包最直觀、大模型最容易看懂的對手戰績指標
            valid_bids = [t["bid"] for t in agent["daily_trace"] if t.get("bid") is not None]
            max_bid_val = round(max(valid_bids), 2) if valid_bids else 0.0

            history[
                "agent_summaries"
            ][
                agent[
                    "agent_id"
                ]
            ] = {
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
                "max_bid": max_bid_val  # 👈 新增最高出價
            }

            round_summary[
                agent[
                    "agent_id"
                ]
            ] = {
                "hp": metrics["final_hp"],
                "survival_day": metrics["survival_days"],
                "budget": final_trace["budget_after"],

                "total_bid": metrics["total_bid"],
                "average_bid": metrics["average_bid"],
                "bid_variance": metrics["bid_variance"],
                "bid_entropy": metrics["bid_entropy"],

                "adaptation_score": metrics["adaptation_score"],
                "panic_score": metrics["panic_score"],
                "opponent_awareness_score": metrics["opponent_awareness_score"],
                "recovery_score": metrics["recovery_score"],
                "supply_bid_correlation": metrics["supply_bid_correlation"],

                "utility_score": metrics["utility_score"],
                "survival_efficiency": metrics["survival_efficiency"],

                "strategy_complexity": metrics["strategy_complexity"],
                "branch_count": metrics["branch_count"],
                "loop_count": metrics["loop_count"],
                "function_call_count": metrics["function_call_count"],

                "compile_success": int(metrics["compile_success"]),
                "runtime_success": int(metrics["runtime_success"]),
                "hallucinated_api_count": metrics["hallucinated_api_count"],

                "recent_traces": agent["daily_trace"],
            }

        all_meta_history[
            f"meta_round_{meta_round_id}"
        ] = round_summary

        previous_codes = {
            submission.agent_id: submission.strategy_code
            for submission in submissions
        }

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


if __name__ == "__main__":
    main()