import itertools
import json
import subprocess
import os
import time
from datetime import datetime

AGENTS = ["Alex", "Bob", "Cindy", "David", "Eric"]

MODELS = [
    {"backend": "openai", "model": "gpt-5.4"},
    {"backend": "openai", "model": "gpt-5.4-nano"},
    {"backend": "gemini", "model": "gemini-2.5-flash"},
    {"backend": "gemini", "model": "gemini-3.1-flash-lite-preview"},
    {"backend": "deepseek", "model": "deepseek-v4-flash"},
    # {"backend": "deepseek", "model": "deepseek-v4-flash"},
    # {"backend": "deepseek", "model": "deepseek-v4-flash"},
    # {"backend": "deepseek", "model": "deepseek-v4-flash"},
    # {"backend": "deepseek", "model": "deepseek-v4-flash"},
    # {"backend": "deepseek", "model": "deepseek-v4-flash"},

]


# ============================================================================
# 🌟 全域大匯總模組（已整合原本的 experiment_summary 執行紀錄）
# ============================================================================
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

    metric_fields = [
        ("avg_survival_days", "survival_days", 2),
        ("avg_final_budget", "final_budget", 2),
        ("avg_daily_bid", "daily_bid", 2),

        ("avg_total_bid", "total_bid", 2),
        ("avg_average_bid", "metric_average_bid", 2),
        ("avg_bid_variance", "bid_variance", 4),
        ("avg_bid_entropy", "bid_entropy", 4),

        ("avg_adaptation_score", "adaptation_score", 4),
        ("avg_panic_score", "panic_score", 4),
        ("avg_opponent_awareness_score", "opponent_awareness_score", 4),
        ("avg_recovery_score", "recovery_score", 4),
        ("avg_supply_bid_correlation", "supply_bid_correlation", 4),

        ("avg_utility_score", "utility_score", 4),
        ("avg_survival_efficiency", "survival_efficiency", 6),

        ("avg_strategy_complexity", "strategy_complexity", 4),
        ("avg_branch_count", "branch_count", 4),
        ("avg_loop_count", "loop_count", 4),
        ("avg_function_call_count", "function_call_count", 4),

        ("avg_compile_success", "compile_success", 4),
        ("avg_runtime_success", "runtime_success", 4),
        ("avg_hallucinated_api_count", "hallucinated_api_count", 4),
    ]

    def new_pool_item():
        return {
            "weighted_sums": defaultdict(float),
            "deaths": 0,
            "rounds": 0,
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

    def add_stats(pool, group_name, stats, round_count, death_count, experiment_id):
        item = pool[group_name]

        item["deaths"] += death_count
        item["rounds"] += round_count
        item["agent_observations"] += 1
        item["experiments"].add(experiment_id)

        for source_key, report_key, _ in metric_fields:
            value = stats.get(source_key)

            if isinstance(value, bool):
                value = int(value)

            if isinstance(value, (int, float)):
                item["weighted_sums"][report_key] += float(value) * round_count

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

            if round_count == 0:
                continue

            add_stats(
                pool=model_pool,
                group_name=model_name,
                stats=stats,
                round_count=round_count,
                death_count=death_count,
                experiment_id=experiment_id,
            )

            add_stats(
                pool=agent_pool,
                group_name=agent_name,
                stats=stats,
                round_count=round_count,
                death_count=death_count,
                experiment_id=experiment_id,
            )

    def finalize_pool(pool):
        output = {}

        for group_name, data in pool.items():
            rounds = data["rounds"]

            if rounds == 0:
                continue

            row = {
                "global_mortality_rate": f"{(data['deaths'] / rounds) * 100:.1f}%",
                "total_evaluated_meta_rounds": rounds,
                "total_agent_observations": data["agent_observations"],
                "total_experiments": len(data["experiments"]),
            }

            for _, report_key, decimals in metric_fields:
                weighted_sum = data["weighted_sums"].get(
                    report_key,
                    None,
                )

                if weighted_sum is None:
                    continue

                row[
                    f"grand_avg_{report_key}"
                ] = round(
                    weighted_sum / rounds,
                    decimals,
                )

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

# ============================================================
# 🚀 主執行流程區
# ============================================================
def main():
    batch_id = datetime.now().strftime("batch_%Y%m%d_%H%M%S")
    batch_dir = os.path.join("log", batch_id)
    os.makedirs(batch_dir, exist_ok=True)

    # 這裡可以自由選擇切片（例如 [:1] 或拿掉跑全排列）
    all_permutations = list(itertools.permutations(MODELS))[:30]
    print(f"Total experiments: {len(all_permutations)}")

    batch_start_time = time.time()
    experiment_summary = []

    for exp_idx, perm in enumerate(all_permutations):
        experiment_start_time = time.time()
        backend_config = {}

        for agent, model_spec in zip(AGENTS, perm):
            backend_config[agent] = {
                "backend": model_spec["backend"],
                "model": model_spec["model"],
                "temperature": 0.6,
            }

        temp_config_path = "temp_backend_config.json"
        with open(temp_config_path, "w", encoding="utf-8") as f:
            json.dump(backend_config, f, indent=2)

        experiment_id = os.path.join(batch_id, f"exp_{exp_idx:03d}")

        print("\n================================================")
        print(f"Experiment {exp_idx+1}/{len(all_permutations)}")
        print(f"Experiment ID: {experiment_id}")
        for agent in AGENTS:
            print(f"{agent}: {backend_config[agent]['model']}")
        print("================================================\n")

        subprocess.run([
            "python", "src/run.py",
            "--scenario", "medium",
            "--meta-rounds", "10",  
            "--backend-mode", "per-agent",
            "--experiment-id", experiment_id,
        ])

        experiment_elapsed = time.time() - experiment_start_time
        print(f"\nExperiment runtime: {experiment_elapsed:.2f} sec")

        experiment_summary.append({
            "experiment_id": experiment_id,
            "runtime_sec": round(experiment_elapsed, 2),
            "backend_config": backend_config,
        })

    batch_elapsed = time.time() - batch_start_time

    # 🛠️ 關鍵改動：不再單獨寫出 experiment_summary.json 實體檔案
    # 改為將記憶體中的 Dict 資料打包，當作參數直接送進全域統計模組中合併！
    manifest_data = {
        "batch_id": batch_id,
        "total_experiments": len(all_permutations),
        "total_runtime_sec": round(batch_elapsed, 2),
        "experiments": experiment_summary,
    }

    print("\n================================================")
    print("All experiments complete.")
    print(f"Batch directory: {batch_dir}")
    print(f"Total batch runtime: {batch_elapsed:.2f} sec")
    print("================================================")

    # 🌟 呼叫升級後的統計模組，把 manifest_data 餵進去
    aggregate_batch_results(batch_dir, batch_manifest=manifest_data)


if __name__ == '__main__':
    main()