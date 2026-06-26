import argparse
import itertools
import json
import os
import re
import time
from datetime import datetime

import config
import run as run_module

AGENTS = config.AGENTS
MODELS = config.BATCH_MODELS

META_ROUND_PATTERN = re.compile(r"^meta_round_(\d+)\.json$")


def aggregate_batch_results(batch_folder, batch_manifest=None):
    """
    Scan all agent_averages.json files under a batch folder and build
    global model-level and agent-level performance summaries.
    """
    import os
    import json
    import re
    import time
    from collections import defaultdict

    PERFORMANCE_METRIC_FIELDS = [
        ("avg_survival_days", "survival_days", 2),
        ("avg_final_budget", "final_budget", 2),
        ("avg_daily_bid", "daily_bid", 2),
        ("avg_total_bid", "total_bid", 2),
        ("avg_average_bid", "metric_average_bid", 2),
        ("avg_bid_variance", "bid_variance", 4),
        ("avg_bid_entropy", "bid_entropy", 4),
        ("avg_bid_supply_sensitivity", "bid_supply_sensitivity", 4),
        ("avg_opponent_awareness_score", "opponent_awareness_score", 4),
        ("avg_recovery_score", "recovery_score", 4),
        ("avg_supply_bid_correlation", "supply_bid_correlation", 4),
        ("avg_utility_score", "utility_score", 4),
        ("avg_survival_efficiency", "survival_efficiency", 6),
        ("avg_strategy_complexity", "strategy_complexity", 4),
        ("avg_branch_count", "branch_count", 4),
        ("avg_loop_count", "loop_count", 4),
        ("avg_function_call_count", "function_call_count", 4),
    ]

    RELIABILITY_METRIC_FIELDS = [
        ("admission_rate", "admission_rate", 4),
        ("outcome_valid_rate", "outcome_valid_rate", 4),
        ("one_shot_json_valid_rate", "one_shot_json_valid_rate", 4),
        ("one_shot_code_extracted_rate", "one_shot_code_extracted_rate", 4),
        ("one_shot_compile_success_rate", "one_shot_compile_success_rate", 4),
        ("one_shot_runtime_success_rate", "one_shot_runtime_success_rate", 4),
        ("one_shot_strict_success_rate", "one_shot_strict_success_rate", 4),
        ("repair_used_rate", "repair_used_rate", 4),
        ("json_repair_success_rate", "json_repair_success_rate", 4),
        ("code_repair_success_rate", "code_repair_success_rate", 4),
        ("json_repair_success_given_used", "json_repair_success_given_used", 4),
        ("code_repair_success_given_used", "code_repair_success_given_used", 4),
        ("post_repair_strict_success_rate", "post_repair_strict_success_rate", 4),
        ("avg_repair_attempts", "repair_attempts", 4),
        ("avg_compile_success", "compile_success", 4),
        ("avg_runtime_success", "runtime_success", 4),
        ("avg_strict_success_rate", "strict_success_rate", 4),
        ("avg_hallucinated_api_count", "hallucinated_api_count", 4),
        ("json_parse_fail_rate", "json_parse_fail_rate", 4),
        ("default_code_usage_rate", "default_code_usage_rate", 4),
        ("valid_round_rate", "valid_round_rate", 4),
    ]

    def new_pool_item():
        return {
            "performance_weighted_sums": defaultdict(float),
            "reliability_weighted_sums": defaultdict(float),
            "deaths": 0,
            "valid_rounds": 0,
            "attempted_rounds": 0,
            "agent_observations": 0,
            "experiments": set(),
        }

    model_pool = defaultdict(new_pool_item)
    agent_pool = defaultdict(new_pool_item)

    def parse_death_count(death_text):
        death_count = 0
        round_count = 0

        match = re.match(
            r"(\d+)/(\d+)",
            str(death_text),
        )

        if match:
            death_count = int(match.group(1))
            round_count = int(match.group(2))

        return death_count, round_count

    def parse_round_counts(stats, death_count, round_count):
        attempted_rounds = stats.get("attempted_meta_rounds")
        valid_rounds = stats.get("valid_meta_rounds")

        if not isinstance(attempted_rounds, int) or attempted_rounds < 0:
            attempted_rounds = round_count

        if not isinstance(valid_rounds, int) or valid_rounds < 0:
            valid_rounds = round_count

        if valid_rounds > attempted_rounds:
            valid_rounds = attempted_rounds

        if death_count > valid_rounds:
            death_count = valid_rounds

        return attempted_rounds, valid_rounds, death_count

    def add_stats(pool, group_name, stats, attempted_rounds, valid_rounds, death_count, experiment_id):
        item = pool[group_name]

        item["deaths"] += death_count
        item["valid_rounds"] += valid_rounds
        item["attempted_rounds"] += attempted_rounds
        item["agent_observations"] += 1
        item["experiments"].add(experiment_id)

        for source_key, report_key, _ in PERFORMANCE_METRIC_FIELDS:
            value = stats.get(source_key)
            if isinstance(value, bool):
                value = int(value)

            if isinstance(value, (int, float)) and valid_rounds > 0:
                item["performance_weighted_sums"][report_key] += float(value) * valid_rounds

        for source_key, report_key, _ in RELIABILITY_METRIC_FIELDS:
            value = stats.get(source_key)
            if isinstance(value, bool):
                value = int(value)

            if isinstance(value, (int, float)) and attempted_rounds > 0:
                item["reliability_weighted_sums"][report_key] += float(value) * attempted_rounds

    for root, _, files in os.walk(batch_folder):
        if "agent_averages.json" not in files:
            continue

        summary_path = os.path.join(
            root,
            "agent_averages.json",
        )

        experiment_id = os.path.relpath(
            root,
            batch_folder,
        )

        with open(
            summary_path,
            "r",
            encoding="utf-8",
        ) as handle:
            try:
                exp_data = json.load(handle)
            except Exception:
                continue

        averages = exp_data.get(
            "agent_averages",
            {},
        )

        for agent_id, stats in averages.items():
            model_name = stats.get(
                "model_used",
                "Unknown Model",
            )

            agent_name = stats.get(
                "developer_name",
                agent_id,
            )

            death_count, round_count = parse_death_count(
                stats.get(
                    "death_count",
                    "0/0",
                )
            )

            attempted_rounds, valid_rounds, death_count = parse_round_counts(
                stats,
                death_count,
                round_count,
            )

            if attempted_rounds == 0:
                continue

            add_stats(
                pool=model_pool,
                group_name=model_name,
                stats=stats,
                attempted_rounds=attempted_rounds,
                valid_rounds=valid_rounds,
                death_count=death_count,
                experiment_id=experiment_id,
            )

            add_stats(
                pool=agent_pool,
                group_name=agent_name,
                stats=stats,
                attempted_rounds=attempted_rounds,
                valid_rounds=valid_rounds,
                death_count=death_count,
                experiment_id=experiment_id,
            )

    def finalize_pool(pool):
        output = {}

        for group_name, data in pool.items():
            valid_rounds = data["valid_rounds"]
            attempted_rounds = data["attempted_rounds"]

            if attempted_rounds == 0:
                continue

            if valid_rounds > 0:
                global_mortality_rate = f"{(data['deaths'] / valid_rounds) * 100:.1f}%"
            else:
                global_mortality_rate = "N/A"

            row = {
                "global_mortality_rate": global_mortality_rate,
                "total_valid_meta_rounds": valid_rounds,
                "total_attempted_meta_rounds": attempted_rounds,
                "total_outcome_valid_agent_rounds": round(
                    data["reliability_weighted_sums"].get("outcome_valid_rate", 0.0)
                ),
                "total_outcome_valid_meta_rounds": round(
                    data["reliability_weighted_sums"].get("outcome_valid_rate", 0.0)
                ),
                "outcome_valid_rate": round(
                    data["reliability_weighted_sums"].get("outcome_valid_rate", 0.0) / attempted_rounds,
                    4,
                ) if attempted_rounds > 0 else None,
                "total_agent_observations": data["agent_observations"],
                "total_experiments": len(data["experiments"]),
            }

            for _, report_key, decimals in PERFORMANCE_METRIC_FIELDS:
                weighted_sum = data["performance_weighted_sums"].get(report_key)
                if weighted_sum is None or valid_rounds == 0:
                    row[f"grand_avg_{report_key}"] = None
                else:
                    row[f"grand_avg_{report_key}"] = round(weighted_sum / valid_rounds, decimals)

            for _, report_key, decimals in RELIABILITY_METRIC_FIELDS:
                weighted_sum = data["reliability_weighted_sums"].get(report_key)
                if weighted_sum is None or attempted_rounds == 0:
                    row[f"grand_avg_{report_key}"] = None
                else:
                    row[f"grand_avg_{report_key}"] = round(weighted_sum / attempted_rounds, decimals)

            output[group_name] = row

        return output

    global_report = {
        "report_metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_batch": batch_folder,
        },
        "batch_execution_manifest": batch_manifest or {},
        "performance_by_model": finalize_pool(model_pool),
        "performance_by_agent": finalize_pool(agent_pool),
    }

    report_path = os.path.join(
        batch_folder,
        "global_batch_report.json",
    )

    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(
            global_report,
            handle,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\nGlobal batch report saved to: {report_path}")


def load_meta_rounds(exp_dir):
    meta_rounds = []

    for entry in os.listdir(exp_dir):
        match = META_ROUND_PATTERN.match(entry)
        if not match:
            continue

        meta_path = os.path.join(exp_dir, entry)
        if not os.path.isfile(meta_path):
            continue

        try:
            with open(meta_path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue

        if not isinstance(data, list) or not data:
            continue

        payload = data[0]
        meta_round_id = payload.get("meta_round_id")
        if not isinstance(meta_round_id, int):
            try:
                meta_round_id = int(match.group(1))
            except Exception:
                continue

        meta_rounds.append((meta_round_id, payload))

    meta_rounds.sort(key=lambda item: item[0])
    return meta_rounds


def wrap_code_block(code_text):
    if code_text is None:
        code_text = ""

    if "\"\"\"" in code_text:
        code_text = code_text.replace("\"\"\"", "\\\"\\\"\\\"")

    return f"\"\"\"\n{code_text}\n\"\"\""


def build_code_py(exp_id, source_log, agent_id, meta_rounds):
    lines = []
    lines.append("# ============================================================")
    lines.append(f"# Experiment: {exp_id}")
    lines.append(f"# Agent: {agent_id}")
    lines.append(f"# Source: {source_log}")
    lines.append("# ============================================================")
    lines.append("")

    for meta_round_id, payload in meta_rounds:
        lines.append("# ============================================================")
        lines.append(f"# Meta Round {meta_round_id}")
        lines.append("# ============================================================")
        lines.append("")

        strategy_code = ""
        for agent_entry in payload.get("agents", []):
            if agent_entry.get("agent_id") == agent_id:
                strategy_code = agent_entry.get("strategy_code") or ""
                break

        block = wrap_code_block(strategy_code)
        lines.append(f"META_ROUND_{meta_round_id}_CODE = {block}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_inference_for_experiment(exp_dir, source_log_dir):
    meta_rounds = load_meta_rounds(exp_dir)
    if not meta_rounds:
        return

    inference_dir = os.path.join(exp_dir, "inference")
    os.makedirs(inference_dir, exist_ok=True)

    first_payload = meta_rounds[0][1]
    agent_ids = [
        agent.get("agent_id")
        for agent in first_payload.get("agents", [])
        if agent.get("agent_id")
    ]

    exp_id = os.path.basename(exp_dir)
    source_log = os.path.relpath(exp_dir, source_log_dir).replace(os.sep, "/")

    for agent_id in agent_ids:
        cot_history = []

        for meta_round_id, payload in meta_rounds:
            reasoning_cot = ""
            for agent_entry in payload.get("agents", []):
                if agent_entry.get("agent_id") == agent_id:
                    reasoning_cot = agent_entry.get("reasoning_cot") or ""
                    break

            cot_history.append({
                "meta_round_id": meta_round_id,
                "reasoning_cot": reasoning_cot,
            })

        agent_dir = os.path.join(inference_dir, agent_id)
        os.makedirs(agent_dir, exist_ok=True)

        cot_path = os.path.join(agent_dir, "cot.json")
        with open(cot_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "experiment_id": exp_id,
                    "agent_id": agent_id,
                    "source_log": source_log,
                    "cot_history": cot_history,
                },
                handle,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")

        code_path = os.path.join(agent_dir, "code.py")
        code_text = build_code_py(
            exp_id,
            source_log,
            agent_id,
            meta_rounds,
        )
        with open(code_path, "w", encoding="utf-8") as handle:
            handle.write(code_text)

def main():
    parser = argparse.ArgumentParser(description="Run permutation experiments.")
    parser.add_argument(
        "--batch-name",
        type=str,
        default=None,
        help="Use an existing batch folder name (e.g., batch_YYYYMMDD_HHMMSS).",
    )
    parser.add_argument(
        "--slice-start",
        type=int,
        default=1,
        help="1-based start index (inclusive) for permutations.",
    )
    parser.add_argument(
        "--slice-end",
        type=int,
        default=30,
        help="1-based end index (inclusive) for permutations.",
    )
    parser.add_argument(
        "--meta-rounds",
        type=int,
        default=3,
        help="Number of meta-rounds to run for each experiment.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="low",
        choices=["low", "medium", "high"],
        help="Scarcity scenario used for all experiments in this batch.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base random seed forwarded to run.py (default: None for random supply).",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating plots when calling run.py for each permutation.",
    )
    parser.add_argument(
        "--opponent-info-mode",
        type=str,
        default=None,
        choices=[
            "full_code_access",
            "outcome_only",
            "no_opponent_info",
        ],
        help="Opponent info exposure across meta-rounds (optional).",
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
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    batch_id = args.batch_name or datetime.now().strftime("batch_%Y%m%d_%H%M%S")
    batch_dir = os.path.join(project_root, "log", batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    slice_start = args.slice_start
    slice_end = args.slice_end
    if slice_start < 1:
        raise SystemExit("--slice-start must be >= 1")
    if slice_end < slice_start:
        raise SystemExit("--slice-end must be >= --slice-start")

    all_permutations = list(itertools.permutations(MODELS))
    start_index = slice_start - 1
    end_index = min(slice_end, len(all_permutations))
    if start_index >= len(all_permutations):
        raise SystemExit("--slice-start exceeds total permutations")
    permutations_slice = all_permutations[start_index:end_index]
    print(f"Total experiments: {len(permutations_slice)}")

    batch_start_time = time.time()
    experiment_summary = []

    for offset, perm in enumerate(permutations_slice):
        experiment_start_time = time.time()
        exp_index = slice_start + offset
        backend_config = {}

        for agent, model_spec in zip(AGENTS, perm):
            backend_config[agent] = {
                "backend": model_spec["backend"],
                "model": model_spec["model"],
                "temperature": 0.1,
            }

        experiment_id = os.path.join(batch_id, f"exp_{exp_index:03d}")

        print("\n================================================")
        print(f"Experiment {offset+1}/{len(permutations_slice)}")
        print(f"Experiment ID: {experiment_id}")
        for agent in AGENTS:
            print(f"{agent}: {backend_config[agent]['model']}")
        print("================================================\n")

        run_args = argparse.Namespace(
            scenario=args.scenario,
            meta_rounds=args.meta_rounds,
            seed=args.seed,
            backend_mode="per-agent",
            backend=None,
            backend_model=None,
            backend_temperature=None,
            backend_base_url=None,
            output_dir=os.path.join(project_root, "log"),
            experiment_id=experiment_id,
            opponent_info_mode=(args.opponent_info_mode or config.OPPONENT_INFO_MODE),
            no_plots=args.no_plots,
            compact_meta_log=True,
            evaluation_mode=args.evaluation_mode,
            max_json_repair_attempts=args.max_json_repair_attempts,
            max_code_repair_attempts=args.max_code_repair_attempts,
            allow_invalid_agents_for_debug=False,
        )

        try:
            run_module.run_experiment(run_args, backend_overrides=backend_config)
        except Exception as exc:
            print(f"[WARN] run.py failed for {experiment_id}: {exc}. Skipping inference build.")
            continue

        exp_dir = os.path.join(batch_dir, f"exp_{exp_index:03d}")
        build_inference_for_experiment(exp_dir, batch_dir)

        experiment_elapsed = time.time() - experiment_start_time
        print(f"\nExperiment runtime: {experiment_elapsed:.2f} sec")

        experiment_summary.append({
            "experiment_id": experiment_id,
            "runtime_sec": round(experiment_elapsed, 2),
            "backend_config": backend_config,
        })

    batch_elapsed = time.time() - batch_start_time

    manifest_data = {
        "batch_id": batch_id,
        "scenario": args.scenario,
        "evaluation_mode": args.evaluation_mode,
        "max_json_repair_attempts": args.max_json_repair_attempts,
        "max_code_repair_attempts": args.max_code_repair_attempts,
        "total_experiments": len(all_permutations),
        "total_runtime_sec": round(batch_elapsed, 2),
        "experiments": experiment_summary,
    }

    print("\n================================================")
    print("All experiments complete.")
    print(f"Batch directory: {batch_dir}")
    print(f"Total batch runtime: {batch_elapsed:.2f} sec")
    print("================================================")

    aggregate_batch_results(batch_dir, batch_manifest=manifest_data)


if __name__ == '__main__':
    main()