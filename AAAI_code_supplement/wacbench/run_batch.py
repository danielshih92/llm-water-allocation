import argparse
import itertools
import json
import os
import re
import time
from datetime import datetime

try:
    from . import config
    from . import run as run_module
    from .prompt_builder import normalize_opponent_info_mode
except ImportError:  # Direct script execution.
    import config
    import run as run_module
    from prompt_builder import normalize_opponent_info_mode

def aggregate_batch_results(batch_folder, batch_manifest=None):
    """
    Scan all agent_averages.json files under a batch folder and build
    global model-level and agent-level performance summaries.
    """
    import os
    import json
    import re
    import ast
    import statistics
    import time
    from collections import defaultdict

    PERFORMANCE_METRIC_FIELDS = [
        ("avg_survival_days", "survival_days", 2),
        ("avg_final_budget", "final_budget", 2),
        ("avg_daily_bid", "daily_bid", 2),
        ("avg_total_bid", "total_bid", 2),
        ("avg_average_bid", "metric_average_bid", 2),
        ("avg_bid_variance", "bid_variance", 4),
        ("avg_bid_supply_sensitivity", "bid_supply_sensitivity", 4),
        ("avg_recovery_score", "recovery_score", 4),
        ("avg_supply_bid_correlation", "supply_bid_correlation", 4),
        ("avg_utility_score", "utility_score", 4),
        ("avg_strategy_complexity", "strategy_complexity", 4),
        ("avg_branch_count", "branch_count", 4),
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

    OPP_CODE_PATTERNS = [
        "opponents_status",
        "opponent",
        "opp",
        "other",
        "rival",
        "competitor",
        "last_bid",
        "last_status",
        "last_hp_after",
        "last_budget_after",
        "water_requirement",
        "daily_salary",
        "trace_history",
    ]

    REASONING_OPP_PATTERNS = [
        "opponent",
        "opponents",
        "competition",
        "competitor",
        "rival",
        "other agents",
        "their bid",
        "last bid",
        "aggressive",
        "conservative",
    ]

    TOKEN_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?")

    def strip_get_bid_signature(code_text):
        if not isinstance(code_text, str):
            return ""

        lines = code_text.splitlines()

        for index, line in enumerate(lines):
            if line.lstrip().startswith("def get_bid"):
                return "\n".join(lines[index + 1:])

        return code_text

    def count_pattern_occurrences(text, patterns):
        if not isinstance(text, str) or not text:
            return 0

        lowered = text.lower()
        return sum(lowered.count(pattern.lower()) for pattern in patterns)

    def compute_opp_code_aware_score(strategy_code):
        return count_pattern_occurrences(
            strip_get_bid_signature(strategy_code),
            OPP_CODE_PATTERNS,
        )

    def uses_opponent_status(strategy_code):
        if not isinstance(strategy_code, str) or not strategy_code.strip():
            return False

        try:
            tree = ast.parse(strategy_code)
        except Exception:
            return compute_opp_code_aware_score(strategy_code) > 0

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Name)
                and node.id == "opponents_status"
                and isinstance(node.ctx, ast.Load)
            ):
                return True

        return False

    def compute_reasoning_opp_aware_score(agent_entry):
        generation_stats = agent_entry.get("generation_stats") or {}
        reasoning_text = (
            generation_stats.get("final_reasoning")
            or generation_stats.get("one_shot_reasoning")
            or agent_entry.get("reasoning_cot")
            or ""
        )
        return count_pattern_occurrences(reasoning_text, REASONING_OPP_PATTERNS)

    def tokenize_code(strategy_code):
        if not isinstance(strategy_code, str):
            return set()

        return set(TOKEN_PATTERN.findall(strategy_code.lower()))

    def compute_strategy_revision_score(previous_code, current_code):
        previous_tokens = tokenize_code(previous_code)
        current_tokens = tokenize_code(current_code)

        union = previous_tokens | current_tokens
        if not union:
            return 0.0

        intersection = previous_tokens & current_tokens
        return 1.0 - (len(intersection) / len(union))

    def get_numeric(mapping, key):
        value = mapping.get(key)
        if isinstance(value, bool):
            value = int(value)
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def new_round_item():
        return {
            "opp_code_aware_sum": 0.0,
            "opp_code_used_sum": 0.0,
            "code_count": 0,
            "reasoning_opp_aware_sum": 0.0,
            "reasoning_count": 0,
            "survival_days_sum": 0.0,
            "utility_score_sum": 0.0,
            "performance_count": 0,
            "death_count": 0,
            "strategy_revision_sum": 0.0,
            "strategy_revision_count": 0,
        }

    def new_pool_item():
        return {
            "performance_weighted_sums": defaultdict(float),
            "reliability_weighted_sums": defaultdict(float),
            "deaths": 0,
            "valid_rounds": 0,
            "attempted_rounds": 0,
            "agent_observations": 0,
            "experiments": set(),
            "round_metrics": defaultdict(new_round_item),
            "opp_code_aware_sum": 0.0,
            "opp_code_used_sum": 0.0,
            "code_count": 0,
            "reasoning_opp_aware_sum": 0.0,
            "reasoning_count": 0,
            "strategy_revision_sum": 0.0,
            "strategy_revision_count": 0,
            "role_survival_sums": defaultdict(float),
            "role_survival_counts": defaultdict(int),
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

    def add_code_observation(pool, group_name, meta_round_id, opp_score, opp_used, reasoning_score):
        item = pool[group_name]
        round_item = item["round_metrics"][meta_round_id]

        round_item["opp_code_aware_sum"] += opp_score
        round_item["opp_code_used_sum"] += 1.0 if opp_used else 0.0
        round_item["code_count"] += 1
        round_item["reasoning_opp_aware_sum"] += reasoning_score
        round_item["reasoning_count"] += 1

        item["opp_code_aware_sum"] += opp_score
        item["opp_code_used_sum"] += 1.0 if opp_used else 0.0
        item["code_count"] += 1
        item["reasoning_opp_aware_sum"] += reasoning_score
        item["reasoning_count"] += 1

    def add_meta_performance(pool, group_name, meta_round_id, survival_days, utility_score, dead):
        item = pool[group_name]
        round_item = item["round_metrics"][meta_round_id]

        round_item["survival_days_sum"] += survival_days
        round_item["utility_score_sum"] += utility_score
        round_item["performance_count"] += 1
        round_item["death_count"] += 1 if dead else 0

    def add_strategy_revision(pool, group_name, meta_round_id, revision_score):
        item = pool[group_name]
        round_item = item["round_metrics"][meta_round_id]

        round_item["strategy_revision_sum"] += revision_score
        round_item["strategy_revision_count"] += 1
        item["strategy_revision_sum"] += revision_score
        item["strategy_revision_count"] += 1

    def add_role_survival(model_name, agent_id, survival_days):
        item = model_pool[model_name]
        item["role_survival_sums"][agent_id] += survival_days
        item["role_survival_counts"][agent_id] += 1

    def add_meta_round_stats(exp_dir, averages):
        meta_rounds = load_meta_rounds(exp_dir)
        previous_code_by_agent = {}

        for meta_round_id, payload in meta_rounds:
            agents = payload.get("agents", [])
            if not isinstance(agents, list):
                continue

            for agent_entry in agents:
                if not isinstance(agent_entry, dict):
                    continue

                agent_id = agent_entry.get("agent_id")
                if not agent_id:
                    continue

                stats = averages.get(agent_id) or {}
                model_name = stats.get("model_used", "Unknown Model")
                agent_name = stats.get("developer_name", agent_id)
                strategy_code = agent_entry.get("strategy_code") or ""

                opp_score = compute_opp_code_aware_score(strategy_code)
                opp_used = uses_opponent_status(strategy_code)
                reasoning_score = compute_reasoning_opp_aware_score(agent_entry)

                add_code_observation(
                    pool=model_pool,
                    group_name=model_name,
                    meta_round_id=meta_round_id,
                    opp_score=opp_score,
                    opp_used=opp_used,
                    reasoning_score=reasoning_score,
                )
                add_code_observation(
                    pool=agent_pool,
                    group_name=agent_name,
                    meta_round_id=meta_round_id,
                    opp_score=opp_score,
                    opp_used=opp_used,
                    reasoning_score=reasoning_score,
                )

                metrics = agent_entry.get("metrics") or {}
                admitted = int(agent_entry.get("admitted", 0) or 0) == 1
                outcome_valid = int(agent_entry.get("outcome_valid", 0) or 0) == 1
                survival_days = get_numeric(metrics, "survival_days")
                utility_score = get_numeric(metrics, "utility_score")
                final_hp = get_numeric(metrics, "final_hp")

                if admitted and outcome_valid and survival_days is not None and utility_score is not None:
                    dead = bool(final_hp is not None and final_hp <= 0)
                    add_meta_performance(
                        pool=model_pool,
                        group_name=model_name,
                        meta_round_id=meta_round_id,
                        survival_days=survival_days,
                        utility_score=utility_score,
                        dead=dead,
                    )
                    add_meta_performance(
                        pool=agent_pool,
                        group_name=agent_name,
                        meta_round_id=meta_round_id,
                        survival_days=survival_days,
                        utility_score=utility_score,
                        dead=dead,
                    )
                    add_role_survival(
                        model_name=model_name,
                        agent_id=agent_name,
                        survival_days=survival_days,
                    )

                if agent_id in previous_code_by_agent:
                    revision_score = compute_strategy_revision_score(
                        previous_code_by_agent[agent_id],
                        strategy_code,
                    )
                    add_strategy_revision(
                        pool=model_pool,
                        group_name=model_name,
                        meta_round_id=meta_round_id,
                        revision_score=revision_score,
                    )
                    add_strategy_revision(
                        pool=agent_pool,
                        group_name=agent_name,
                        meta_round_id=meta_round_id,
                        revision_score=revision_score,
                    )

                previous_code_by_agent[agent_id] = strategy_code

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

        add_meta_round_stats(root, averages)

    def finalize_meta_round_fields(row, data):
        all_round_ids = sorted(data["round_metrics"].keys())

        for meta_round_id in all_round_ids:
            round_item = data["round_metrics"][meta_round_id]
            prefix = f"meta_round_{meta_round_id}"

            code_count = round_item["code_count"]
            reasoning_count = round_item["reasoning_count"]
            performance_count = round_item["performance_count"]
            revision_count = round_item["strategy_revision_count"]

            row[f"{prefix}_opp_code_aware_score"] = (
                round(round_item["opp_code_aware_sum"] / code_count, 4)
                if code_count > 0 else None
            )
            row[f"{prefix}_opp_code_use_rate"] = (
                round(round_item["opp_code_used_sum"] / code_count, 4)
                if code_count > 0 else None
            )
            row[f"{prefix}_reasoning_opp_aware_score"] = (
                round(round_item["reasoning_opp_aware_sum"] / reasoning_count, 4)
                if reasoning_count > 0 else None
            )
            row[f"{prefix}_avg_survival_days"] = (
                round(round_item["survival_days_sum"] / performance_count, 2)
                if performance_count > 0 else None
            )
            row[f"{prefix}_avg_utility_score"] = (
                round(round_item["utility_score_sum"] / performance_count, 4)
                if performance_count > 0 else None
            )
            row[f"{prefix}_mortality_rate"] = (
                f"{(round_item['death_count'] / performance_count) * 100:.1f}%"
                if performance_count > 0 else "N/A"
            )

            if meta_round_id > 1:
                row[f"{prefix}_strategy_revision_score"] = (
                    round(round_item["strategy_revision_sum"] / revision_count, 4)
                    if revision_count > 0 else None
                )

        code_count = data["code_count"]
        reasoning_count = data["reasoning_count"]
        revision_count = data["strategy_revision_count"]

        row["grand_avg_opp_code_aware_score"] = (
            round(data["opp_code_aware_sum"] / code_count, 4)
            if code_count > 0 else None
        )
        row["grand_avg_opp_code_use_rate"] = (
            round(data["opp_code_used_sum"] / code_count, 4)
            if code_count > 0 else None
        )
        row["grand_avg_reasoning_opp_aware_score"] = (
            round(data["reasoning_opp_aware_sum"] / reasoning_count, 4)
            if reasoning_count > 0 else None
        )

        if (
            row["grand_avg_reasoning_opp_aware_score"] is not None
            and row["grand_avg_opp_code_aware_score"] is not None
        ):
            row["grand_avg_opp_awareness_gap"] = round(
                row["grand_avg_reasoning_opp_aware_score"]
                - row["grand_avg_opp_code_aware_score"],
                4,
            )
        else:
            row["grand_avg_opp_awareness_gap"] = None

        row["grand_avg_strategy_revision_score"] = (
            round(data["strategy_revision_sum"] / revision_count, 4)
            if revision_count > 0 else None
        )

        first_round = data["round_metrics"].get(1)
        third_round = data["round_metrics"].get(3)

        if first_round and third_round:
            first_performance_count = first_round["performance_count"]
            third_performance_count = third_round["performance_count"]
            first_code_count = first_round["code_count"]
            third_code_count = third_round["code_count"]

            row["survival_delta_mr3_mr1"] = (
                round(
                    (third_round["survival_days_sum"] / third_performance_count)
                    - (first_round["survival_days_sum"] / first_performance_count),
                    2,
                )
                if first_performance_count > 0 and third_performance_count > 0 else None
            )
            row["utility_delta_mr3_mr1"] = (
                round(
                    (third_round["utility_score_sum"] / third_performance_count)
                    - (first_round["utility_score_sum"] / first_performance_count),
                    4,
                )
                if first_performance_count > 0 and third_performance_count > 0 else None
            )
            row["opp_code_aware_delta_mr3_mr1"] = (
                round(
                    (third_round["opp_code_aware_sum"] / third_code_count)
                    - (first_round["opp_code_aware_sum"] / first_code_count),
                    4,
                )
                if first_code_count > 0 and third_code_count > 0 else None
            )
        else:
            row["survival_delta_mr3_mr1"] = None
            row["utility_delta_mr3_mr1"] = None
            row["opp_code_aware_delta_mr3_mr1"] = None

    def finalize_role_fields(row, data):
        role_averages = {}

        for role, total in data["role_survival_sums"].items():
            count = data["role_survival_counts"].get(role, 0)
            if count > 0:
                role_averages[role] = total / count

        if not role_averages:
            row["role_sensitivity_score"] = None
            row["best_role_survival_days"] = None
            row["worst_role_survival_days"] = None
            row["best-worst_gap"] = None
            return

        values = list(role_averages.values())
        row["role_sensitivity_score"] = (
            round(statistics.pstdev(values), 4)
            if len(values) > 1 else 0.0
        )
        row["best_role_survival_days"] = round(max(values), 2)
        row["worst_role_survival_days"] = round(min(values), 2)
        row["best-worst_gap"] = round(max(values) - min(values), 2)

    def finalize_pool(pool, include_role_metrics=False):
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

            finalize_meta_round_fields(row, data)

            if include_role_metrics:
                finalize_role_fields(row, data)

            output[group_name] = row

        return output

    global_report = {
        "report_metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "source_batch": os.path.basename(os.path.normpath(batch_folder)),
        },
        "batch_execution_manifest": batch_manifest or {},
        "performance_by_model": finalize_pool(model_pool, include_role_metrics=True),
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
        match = re.match(r"^meta_round_(\d+)\.json$", entry)
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
            meta_round_id = int(match.group(1))
        meta_rounds.append((meta_round_id, payload))
    meta_rounds.sort(key=lambda item: item[0])
    return meta_rounds


def main():
    parser = argparse.ArgumentParser(
        description="Run config-driven OF/OPF permutation experiments."
    )
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    parser.add_argument(
        "--config",
        default=os.path.join(project_root, "configs", "paper.json"),
        help="JSON experiment configuration.",
    )
    parser.add_argument(
        "--condition",
        required=True,
        choices=["OF", "OPF"],
        help=(
            "OF exposes prior self-policy and survival outcomes; OPF additionally "
            "exposes prior opponent policies."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(project_root, "generated_outputs"),
        help="Root directory for generated batches.",
    )
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
        default=None,
        help="1-based end index (inclusive); default runs all permutations.",
    )
    parser.add_argument(
        "--meta-rounds",
        type=int,
        default=None,
        help="Override the configured meta-round count.",
    )
    parser.add_argument(
        "--episode-days",
        type=int,
        default=None,
        help="Override the configured number of days.",
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        choices=["low", "medium", "high"],
        help="Override the configured scarcity scenario.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Random seed forwarded to run.py. The same seed is reused for every "
            "meta-round (default: None for random supply)."
        ),
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip generating plots when calling run.py for each permutation.",
    )
    parser.add_argument(
        "--evaluation-mode",
        type=str,
        default=None,
        choices=["one_shot", "repair_assisted"],
    )
    parser.add_argument(
        "--max-json-repair-attempts",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--max-code-repair-attempts",
        type=int,
        default=None,
    )
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as handle:
        run_config = json.load(handle)

    agents = run_config.get("agents")
    models = run_config.get("models")
    experiment_config = run_config.get("experiment", {})
    conditions = run_config.get("conditions", {})
    if not isinstance(agents, list) or len(agents) != 5:
        raise SystemExit("The configuration must define exactly five agents.")
    if not isinstance(models, list) or len(models) != 5:
        raise SystemExit("The configuration must define exactly five models.")
    if sorted(agents) != sorted(config.AGENTS):
        raise SystemExit(
            "Configured agents must be the five benchmark roles: "
            + ", ".join(config.AGENTS)
        )

    legacy_mode = conditions.get(args.condition)
    expected_mode = {
        "OF": "no_opponent_info",
        "OPF": "full_code_access",
    }[args.condition]
    if legacy_mode != expected_mode:
        raise SystemExit(
            f"Condition {args.condition} must map to legacy mode {expected_mode!r}."
        )
    effective_opponent_info_mode = normalize_opponent_info_mode(legacy_mode)

    scenario = args.scenario or experiment_config.get("scenario")
    meta_rounds = (
        args.meta_rounds
        if args.meta_rounds is not None
        else int(experiment_config.get("meta_rounds", 3))
    )
    episode_days = (
        args.episode_days
        if args.episode_days is not None
        else int(experiment_config.get("episode_days", 20))
    )
    seed = args.seed if args.seed is not None else experiment_config.get("seed")
    evaluation_mode = (
        args.evaluation_mode
        or experiment_config.get("evaluation_mode", "repair_assisted")
    )
    max_json_repair_attempts = (
        args.max_json_repair_attempts
        if args.max_json_repair_attempts is not None
        else int(experiment_config.get("max_json_repair_attempts", 1))
    )
    max_code_repair_attempts = (
        args.max_code_repair_attempts
        if args.max_code_repair_attempts is not None
        else int(experiment_config.get("max_code_repair_attempts", 1))
    )

    batch_id = args.batch_name or datetime.now().strftime("batch_%Y%m%d_%H%M%S")
    batch_dir = os.path.join(os.path.abspath(args.output_dir), batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    slice_start = args.slice_start
    slice_end = args.slice_end
    if slice_start < 1:
        raise SystemExit("--slice-start must be >= 1")
    all_permutations = list(itertools.permutations(models))
    slice_end = args.slice_end or len(all_permutations)
    if slice_end < slice_start:
        raise SystemExit("--slice-end must be >= --slice-start")
    if episode_days <= 0:
        raise SystemExit("--episode-days must be a positive integer")

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

        for agent, model_spec in zip(agents, perm):
            backend_config[agent] = {
                "backend": model_spec["backend"],
                "model": model_spec["model"],
                "temperature": model_spec.get("temperature", 0.1),
            }
            if model_spec.get("base_url"):
                backend_config[agent]["base_url"] = model_spec["base_url"]

        experiment_id = os.path.join(batch_id, f"exp_{exp_index:03d}")

        print("\n================================================")
        print(f"Experiment {offset+1}/{len(permutations_slice)}")
        print(f"Experiment ID: {experiment_id}")
        for agent in agents:
            print(f"{agent}: {backend_config[agent]['model']}")
        print("================================================\n")

        run_args = argparse.Namespace(
            scenario=scenario,
            meta_rounds=meta_rounds,
            episode_days=episode_days,
            seed=seed,
            backend_mode="per-agent",
            backend=None,
            backend_model=None,
            backend_temperature=None,
            backend_base_url=None,
            output_dir=os.path.abspath(args.output_dir),
            experiment_id=experiment_id,
            opponent_info_mode=effective_opponent_info_mode,
            no_plots=args.no_plots,
            compact_meta_log=True,
            evaluation_mode=evaluation_mode,
            max_json_repair_attempts=max_json_repair_attempts,
            max_code_repair_attempts=max_code_repair_attempts,
            allow_invalid_agents_for_debug=False,
        )

        try:
            run_module.run_experiment(run_args, backend_overrides=backend_config)
        except Exception as exc:
            print(f"[WARN] run.py failed for {experiment_id}: {exc}. Skipping inference build.")
            continue

        experiment_elapsed = time.time() - experiment_start_time
        print(f"\nExperiment runtime: {experiment_elapsed:.2f} sec")

        experiment_summary.append({
            "experiment_id": experiment_id,
            "runtime_sec": round(experiment_elapsed, 2),
            "backend_config": backend_config,
        })

    batch_elapsed = time.time() - batch_start_time

    new_manifest_data = {
        "batch_id": batch_id,
        "condition": args.condition,
        "legacy_mode": effective_opponent_info_mode,
        "scenario": scenario,
        "episode_days": episode_days,
        "meta_rounds": meta_rounds,
        "seed": seed,
        "evaluation_mode": evaluation_mode,
        "max_json_repair_attempts": max_json_repair_attempts,
        "max_code_repair_attempts": max_code_repair_attempts,
        "total_experiments": len(all_permutations),
        "total_runtime_sec": round(batch_elapsed, 2),
        "experiments": experiment_summary,
    }

    manifest_path = os.path.join(batch_dir, "batch_manifest.json")
    previous_manifest = {}
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as handle:
            previous_manifest = json.load(handle)
        for field in (
            "condition",
            "legacy_mode",
            "scenario",
            "episode_days",
            "meta_rounds",
            "seed",
            "evaluation_mode",
        ):
            prior = previous_manifest.get(field)
            current = new_manifest_data.get(field)
            if prior is not None and prior != current:
                raise SystemExit(
                    f"Existing batch manifest has incompatible {field}: "
                    f"{prior!r} != {current!r}"
                )

    merged_experiments = {
        item["experiment_id"]: item
        for item in previous_manifest.get("experiments", [])
        if isinstance(item, dict) and item.get("experiment_id")
    }
    merged_experiments.update(
        {
            item["experiment_id"]: item
            for item in experiment_summary
            if item.get("experiment_id")
        }
    )
    manifest_data = dict(new_manifest_data)
    manifest_data["total_runtime_sec"] = round(
        float(previous_manifest.get("total_runtime_sec", 0.0)) + batch_elapsed,
        2,
    )
    manifest_data["completed_experiments"] = len(merged_experiments)
    manifest_data["experiments"] = [
        merged_experiments[key] for key in sorted(merged_experiments)
    ]
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest_data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print("\n================================================")
    print("All experiments complete.")
    print(f"Batch directory: {batch_dir}")
    print(f"Total batch runtime: {batch_elapsed:.2f} sec")
    print("================================================")

    aggregate_batch_results(batch_dir, batch_manifest=manifest_data)


if __name__ == '__main__':
    main()
