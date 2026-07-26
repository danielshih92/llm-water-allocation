#!/usr/bin/env python3
"""Build the minimal, identity-free analysis data shipped with the supplement."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable


SAFE_TOP_LEVEL_FIELDS = (
    "meta_round_id",
    "evaluation_mode",
    "all_agents_admitted",
    "invalid_agents",
    "outcome_valid",
    "debug_invalid_agents_allowed",
    "official_outcome",
    "environment",
)
SAFE_AGENT_FIELDS = (
    "agent_id",
    "strategy_code",
    "daily_trace",
    "metrics",
    "admitted",
    "outcome_valid",
)
SAFE_GENERATION_FIELDS = (
    "admitted",
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
    "final_error_type",
    "json_parse_failed",
    "default_code_used",
    "generation_success",
    "raw_json_valid",
    "raw_code_extracted",
    "code_extraction_failed",
)


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")


def sanitize_backend_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for agent_id, spec in payload.items():
        if not isinstance(spec, dict):
            continue
        result[agent_id] = {
            "backend": spec.get("backend"),
            "model": spec.get("model"),
            "temperature": spec.get("temperature"),
        }
    return result


def sanitize_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    record = {key: payload.get(key) for key in SAFE_TOP_LEVEL_FIELDS}
    agents = []
    for source_agent in payload.get("agents", []):
        if not isinstance(source_agent, dict):
            continue
        agent = {key: source_agent.get(key) for key in SAFE_AGENT_FIELDS}
        stats = source_agent.get("generation_stats")
        if isinstance(stats, dict):
            agent["generation_stats"] = {
                key: stats.get(key)
                for key in SAFE_GENERATION_FIELDS
                if key in stats
            }
        agents.append(agent)
    record["agents"] = agents
    return record


def iter_experiment_dirs(batch: Path) -> Iterable[Path]:
    return sorted(
        path
        for path in batch.glob("exp_*")
        if path.is_dir() and path.name[4:].isdigit()
    )


def sanitize_batch(source: Path, destination: Path, condition: str) -> Dict[str, int]:
    experiments = 0
    meta_rounds = 0
    agent_records = 0
    for source_exp in iter_experiment_dirs(source):
        target_exp = destination / source_exp.name
        backend_path = source_exp / "backend_config.json"
        if not backend_path.is_file():
            raise FileNotFoundError(backend_path)
        write_json(
            target_exp / "backend_config.json",
            sanitize_backend_config(read_json(backend_path)),
        )
        experiments += 1
        for source_round in sorted(source_exp.glob("meta_round_*.json")):
            raw = read_json(source_round)
            if not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], dict):
                raise ValueError(f"Unexpected meta-round format: {source_round}")
            clean = sanitize_record(raw[0])
            write_json(target_exp / source_round.name, [clean])
            meta_rounds += 1
            agent_records += len(clean["agents"])

    write_json(
        destination / "condition_manifest.json",
        {
            "condition": condition,
            "experiments": experiments,
            "meta_rounds": meta_rounds,
            "agent_records": agent_records,
            "contains_reasoning": False,
            "contains_raw_responses": False,
        },
    )
    return {
        "experiments": experiments,
        "meta_rounds": meta_rounds,
        "agent_records": agent_records,
    }


def condition_from_row(row: Dict[str, str]) -> str:
    condition = row.get("feedback") or row.get("condition") or ""
    if condition in {"OF", "OPF"}:
        return condition
    batch = row.get("batch") or row.get("batch_name") or ""
    if "032" in batch or "no_opp" in batch:
        return "OF"
    if "031" in batch or "full_code" in batch:
        return "OPF"
    return condition


def sanitize_csv(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source.open(newline="", encoding="utf-8") as src:
        reader = csv.DictReader(src)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {source}")
        with destination.open("w", newline="", encoding="utf-8") as dst:
            writer = csv.DictWriter(dst, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                condition = condition_from_row(row)
                if "batch" in row:
                    row["batch"] = condition
                if "batch_name" in row:
                    row["batch_name"] = condition
                if "item_id" in row and "::" in row["item_id"]:
                    row["item_id"] = condition + "::" + row["item_id"].split("::", 1)[1]
                writer.writerow(row)
                count += 1
    return count


def sanitize_paired_jsonl(source: Path, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with source.open(encoding="utf-8") as src, destination.open(
        "w", encoding="utf-8"
    ) as dst:
        for line in src:
            if not line.strip():
                continue
            row = json.loads(line)
            condition = condition_from_row(row)
            row["batch_name"] = condition
            if isinstance(row.get("item_id"), str) and "::" in row["item_id"]:
                row["item_id"] = condition + "::" + row["item_id"].split("::", 1)[1]
            dst.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    return count


def copy_small_reference_files(source_root: Path, destination: Path) -> None:
    mappings = {
        "main_table/main_table.csv": "main_table/main_table.csv",
        "adaptation_dynamics/meta_round_summary.csv": "adaptation/meta_round_summary.csv",
        "adaptation_dynamics/meta_round_changes.csv": "adaptation/meta_round_changes.csv",
        "objective_outcomes/objective_performance.csv": "objective/objective_performance.csv",
        "objective_outcomes/objective_performance_ci_table.tex": "objective/objective_performance_ci_table.tex",
        "policy_convergence/policy_convergence_by_round.csv": "policy_convergence/policy_convergence_by_round.csv",
        "policy_convergence/policy_convergence_changes.csv": "policy_convergence/policy_convergence_changes.csv",
        "policy_convergence/opf_minus_of_convergence_change.csv": "policy_convergence/opf_minus_of_convergence_change.csv",
        "policy_convergence/experiment_level_convergence.csv": "policy_convergence/experiment_level_convergence.csv",
        "policy_convergence/policy_convergence_summary.md": "policy_convergence/policy_convergence_summary.md",
        "non-llm-reference/summary_by_model_round.csv": "non_llm_reference/summary_by_model_round.csv",
        "non-llm-reference/reference_by_round_table.tex": "non_llm_reference/reference_by_round_table.tex",
        "opponent-modeling/aggregate_fosg.csv": "opponent_modeling/aggregate_fosg.csv",
        "opponent-modeling/summary_by_model.csv": "opponent_modeling/summary_by_model.csv",
        "risk-sensitive-decision-making/risk_summary_by_model.csv": "risk_response/risk_summary_by_model.csv",
        "risk-sensitive-decision-making/risk_sensitivity_table.md": "risk_response/risk_sensitivity_table.md",
        "long-term-planning/counterfactual-rollout/counterfactual_summary_by_model.csv": "counterfactual_planning/counterfactual_summary_by_model.csv",
        "meta_round/five_model_test_v2.csv": "homogeneous_populations/five_model_test_v2.csv",
        "meta_round/five_model_test_v2_details.csv": "homogeneous_populations/five_model_test_v2_details.csv",
    }
    for source_rel, destination_rel in mappings.items():
        source = source_root / source_rel
        if source.is_file():
            target = destination / destination_rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--of-source", type=Path, required=True)
    parser.add_argument("--opf-source", type=Path, required=True)
    parser.add_argument("--results-source", type=Path, required=True)
    parser.add_argument("--failure-source", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    data_root = args.output_root / "data" / "paper_intermediates"
    reference_root = args.output_root / "reference_outputs"
    counts: Dict[str, Any] = {
        "OF": sanitize_batch(args.of_source, data_root / "logs" / "OF", "OF"),
        "OPF": sanitize_batch(args.opf_source, data_root / "logs" / "OPF", "OPF"),
    }
    counts["replay_records"] = sanitize_csv(
        args.results_source / "main_table" / "replay_details.csv",
        data_root / "main_table" / "replay_details.csv",
    )
    counts["reference_replacements"] = sanitize_csv(
        args.results_source / "non-llm-reference" / "paired_replacements.csv",
        data_root / "non_llm_reference" / "paired_replacements.csv",
    )
    counts["frozen_opponent_pairs"] = sanitize_csv(
        args.results_source / "opponent-modeling" / "frozen_opponent_pairs.csv",
        data_root / "opponent_modeling" / "frozen_opponent_pairs.csv",
    )
    failure_target = data_root / "failure_analysis"
    counts["paired_failure_judgments"] = sanitize_paired_jsonl(
        args.failure_source / "paired_judge_records.jsonl",
        failure_target / "paired_judge_records.jsonl",
    )
    for name in (
        "attribution_status_distribution.csv",
        "contextual_contributor_distribution.csv",
        "failure_mode_distribution.csv",
    ):
        sanitize_csv(args.failure_source / name, failure_target / name)
    for name in (
        "failure_summary_by_condition.json",
        "failure_summary_by_model.json",
        "failure_summary_by_model_condition.json",
        "failure_summary_overall.json",
        "judge_agreement.json",
    ):
        shutil.copyfile(args.failure_source / name, failure_target / name)
    write_json(
        failure_target / "failure_run_config.json",
        {
            "prompt_version": "wac-failure-analysis-v3-causal-attribution",
            "judge_specs": [
                {"backend": "openai", "model": "gpt-5.4"},
                {"backend": "deepseek", "model": "deepseek-v4-flash"},
            ],
            "temperature": 0.0,
            "blind_model_names": True,
            "death_only": True,
            "batch_condition_mapping": [
                {"batch": "OPF", "condition": "OPF"},
                {"batch": "OF", "condition": "OF"},
            ],
            "categorical_aggregation": (
                "Each judge contributes 0.5 attribution-status vote and 0.5 "
                "primary-mode vote per item; contributing and contextual modes "
                "are independent prevalence scores."
            ),
        },
    )
    plot_data = args.failure_source / "figures" / "failure_analysis_plot_data.csv"
    if plot_data.is_file():
        sanitize_csv(plot_data, failure_target / plot_data.name)

    copy_small_reference_files(args.results_source, reference_root)
    write_json(
        data_root / "DATA_MANIFEST.json",
        {
            "schema_version": 1,
            "description": "Minimal sanitized records required for offline paper analyses.",
            "counts": counts,
            "excluded": [
                "API responses",
                "model reasoning",
                "generation prompts",
                "machine paths",
                "repository metadata",
                "human annotations",
            ],
        },
    )


if __name__ == "__main__":
    main()
