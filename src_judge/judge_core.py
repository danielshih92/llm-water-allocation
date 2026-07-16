import glob
import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from judge_aggregation import aggregate_judge_records
from judge_parser import parse_judge_response
from judge_prompt import build_judge_prompt
from judge_sampling import stratified_sample_items


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_backend_config(exp_dir: str) -> Dict[str, Any]:
    path = os.path.join(exp_dir, "backend_config.json")
    if not os.path.isfile(path):
        return {}
    try:
        data = _load_json(path)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _extract_model_name(backend_cfg: Dict[str, Any], agent_id: str) -> Optional[str]:
    spec = backend_cfg.get(agent_id)
    if not isinstance(spec, dict):
        return None
    model_name = spec.get("model")
    if model_name is None:
        return None
    return str(model_name)


def _build_item_id(batch_name: str, exp_id: str, meta_round_id: Any, agent_id: str) -> str:
    return f"{batch_name}::{exp_id}::meta_{meta_round_id}::{agent_id}"


def _safe_generation_stats(agent: Dict[str, Any]) -> Dict[str, Any]:
    stats = agent.get("generation_stats")
    if isinstance(stats, dict):
        return stats
    return {}


def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        return float(value)
    except Exception:
        return default


def _round_or_none(value: Any, digits: int = 4) -> Optional[float]:
    value = _safe_float(value)
    if value is None:
        return None
    return round(value, digits)


def _find_agent_profile(environment: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
    players = environment.get("players", [])
    if not isinstance(players, list):
        return {}
    for player in players:
        if isinstance(player, dict) and str(player.get("agent_id")) == str(agent_id):
            return dict(player)
    return {}


def _compact_trace_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        compact.append(
            {
                "day": row.get("day"),
                "bid": _round_or_none(row.get("bid"), 3),
                "supply": row.get("supply"),
                "hp_after": row.get("hp_after"),
                "budget_after": _round_or_none(row.get("budget_after"), 3),
                "status": row.get("status"),
                "error": row.get("error"),
            }
        )
    return compact


def _build_evidence_summary(
    record: Dict[str, Any],
    agent: Dict[str, Any],
    agent_id: str,
    admitted: int,
    outcome_valid: int,
    daily_trace: Any,
) -> Dict[str, Any]:
    trace = daily_trace if isinstance(daily_trace, list) else []
    environment = record.get("environment", {}) if isinstance(record.get("environment"), dict) else {}
    metrics = agent.get("metrics") if isinstance(agent.get("metrics"), dict) else {}
    profile = _find_agent_profile(environment, str(agent_id))

    death_index: Optional[int] = None
    for idx, row in enumerate(trace):
        if isinstance(row, dict) and row.get("status") == "dead":
            death_index = idx
            break

    final_row = trace[-1] if trace and isinstance(trace[-1], dict) else {}
    death_row = trace[death_index] if death_index is not None and isinstance(trace[death_index], dict) else {}
    reference_index = death_index if death_index is not None else len(trace) - 1
    evidence_window = []
    if reference_index >= 0:
        start = max(0, reference_index - 3)
        evidence_window = _compact_trace_rows(trace[start : reference_index + 1])

    bids = [
        _safe_float(row.get("bid"))
        for row in trace
        if isinstance(row, dict) and _safe_float(row.get("bid")) is not None
    ]
    hp_values = [
        _safe_float(row.get("hp_after"))
        for row in trace
        if isinstance(row, dict) and _safe_float(row.get("hp_after")) is not None
    ]
    budgets = [
        _safe_float(row.get("budget_after"))
        for row in trace
        if isinstance(row, dict) and _safe_float(row.get("budget_after")) is not None
    ]

    salary = _safe_float(profile.get("daily_salary"))
    water_requirement = _safe_float(profile.get("water_requirement"))
    total_bid = _safe_float(metrics.get("total_bid"), sum(bids) if bids else 0.0)
    avg_bid = _safe_float(metrics.get("average_bid"), (sum(bids) / len(bids)) if bids else 0.0)
    final_budget = _safe_float(final_row.get("budget_after"), budgets[-1] if budgets else None)
    budget_at_death = _safe_float(death_row.get("budget_after")) if death_row else None

    early_count = max(1, len(bids) // 3) if bids else 0
    early_total_bid = sum(bids[:early_count]) if early_count else 0.0

    low_hp_days = [
        row.get("day")
        for row in trace
        if isinstance(row, dict)
        and _safe_float(row.get("hp_after")) is not None
        and (_safe_float(row.get("hp_after")) or 0.0) <= 3.0
    ]

    high_budget_at_death = False
    if budget_at_death is not None and salary and salary > 0:
        high_budget_at_death = budget_at_death >= 2.0 * salary

    early_overspending = False
    if salary and salary > 0 and early_total_bid > 0:
        early_overspending = early_total_bid >= 2.0 * salary * max(1, early_count)

    return {
        "valid_for_strategy_judging": bool(admitted == 1 and outcome_valid == 1 and len(trace) > 0),
        "agent_profile": profile,
        "episode_days": environment.get("episode_days"),
        "trace_days_observed": len(trace),
        "survival_days": metrics.get("survival_days"),
        "death_day": death_row.get("day") if death_row else None,
        "final_status": final_row.get("status"),
        "final_hp": metrics.get("final_hp", final_row.get("hp_after")),
        "final_budget": _round_or_none(final_budget, 3),
        "budget_at_death": _round_or_none(budget_at_death, 3),
        "budget_at_death_in_salary_units": (
            round(budget_at_death / salary, 3)
            if budget_at_death is not None and salary and salary > 0
            else None
        ),
        "high_budget_at_death_flag": high_budget_at_death,
        "total_bid": _round_or_none(total_bid, 3),
        "average_bid": _round_or_none(avg_bid, 3),
        "average_bid_salary_ratio": (
            round(avg_bid / salary, 4)
            if avg_bid is not None and salary and salary > 0
            else None
        ),
        "early_total_bid": round(early_total_bid, 3),
        "early_overspending_flag": early_overspending,
        "min_hp_after": _round_or_none(min(hp_values), 3) if hp_values else None,
        "low_hp_days": low_hp_days[:10],
        "bid_entropy": metrics.get("bid_entropy"),
        "bid_variance": metrics.get("bid_variance"),
        "bid_supply_sensitivity": metrics.get("bid_supply_sensitivity"),
        "supply_bid_correlation": metrics.get("supply_bid_correlation"),
        "static_policy": metrics.get("static_policy"),
        "strategy_complexity": metrics.get("strategy_complexity"),
        "branch_count": metrics.get("branch_count"),
        "loop_count": metrics.get("loop_count"),
        "function_call_count": metrics.get("function_call_count"),
        "water_requirement": water_requirement,
        "daily_salary": salary,
        "evidence_window_around_death_or_final": evidence_window,
    }


def build_judge_item(
    batch_name: str,
    condition_label: str,
    exp_id: str,
    record: Dict[str, Any],
    agent: Dict[str, Any],
    model_name: Optional[str],
) -> Dict[str, Any]:
    generation_stats = _safe_generation_stats(agent)
    meta_round_id = record.get("meta_round_id")
    agent_id = agent.get("agent_id", "unknown")

    one_shot_reasoning = generation_stats.get("one_shot_reasoning", agent.get("reasoning_cot", ""))
    one_shot_code = generation_stats.get("one_shot_code", agent.get("strategy_code", ""))
    final_reasoning = generation_stats.get("final_reasoning", agent.get("reasoning_cot", ""))
    final_code = generation_stats.get("final_code", agent.get("strategy_code", ""))

    admitted = int(agent.get("admitted", generation_stats.get("admitted", 0)))
    outcome_valid = int(agent.get("outcome_valid", record.get("outcome_valid", 0)))
    daily_trace = agent.get("daily_trace", [])
    has_daily_trace = isinstance(daily_trace, list) and len(daily_trace) > 0
    environment = record.get("environment", {}) if isinstance(record.get("environment"), dict) else {}
    evidence_summary = _build_evidence_summary(
        record=record,
        agent=agent,
        agent_id=str(agent_id),
        admitted=admitted,
        outcome_valid=outcome_valid,
        daily_trace=daily_trace,
    )

    return {
        "item_id": _build_item_id(batch_name, exp_id, meta_round_id, str(agent_id)),
        "batch_name": batch_name,
        "condition": condition_label,
        "experiment_id": exp_id,
        "meta_round_id": meta_round_id,
        "agent_id": agent_id,
        "model_name": model_name,
        "evaluation_mode": record.get("evaluation_mode"),
        "environment": {
            "scenario": environment.get("scenario"),
            "supply_range": environment.get("supply_range"),
            "episode_days": environment.get("episode_days"),
            "supply_list": environment.get("supply_list"),
            "players": environment.get("players"),
        },
        "submission_status": {
            "admitted": admitted,
            "outcome_valid": outcome_valid,
            "one_shot_strict_success": int(generation_stats.get("one_shot_strict_success", 0)),
            "post_repair_strict_success": int(generation_stats.get("post_repair_strict_success", 0)),
            "strict_success_rate": int(generation_stats.get("strict_success_rate", 0)),
            "repair_used": int(generation_stats.get("repair_used", 0)),
            "json_repair_used": int(generation_stats.get("json_repair_used", 0)),
            "code_repair_used": int(generation_stats.get("code_repair_used", 0)),
            "final_error_type": generation_stats.get("final_error_type"),
            "final_error_message": generation_stats.get("final_error_message"),
            "json_repair_error": generation_stats.get("json_repair_error"),
            "code_repair_error": generation_stats.get("code_repair_error"),
            "validation_test_results": generation_stats.get("validation_test_results", []),
        },
        "policy": {
            "one_shot_reasoning": one_shot_reasoning,
            "one_shot_code": one_shot_code,
            "final_reasoning": final_reasoning,
            "final_code": final_code,
        },
        "trajectory": {
            "daily_trace": daily_trace,
            "metrics": agent.get("metrics"),
            "evidence_summary": evidence_summary,
        },
        "is_valid_item": bool(admitted == 1 and outcome_valid == 1 and has_daily_trace),
    }


def _parse_exp_number(exp_id: str) -> Optional[int]:
    match = re.fullmatch(r"exp_(\d+)", exp_id)
    if not match:
        return None
    return int(match.group(1))


def _in_exp_range(exp_number: int, exp_start: Optional[int], exp_end: Optional[int]) -> bool:
    if exp_start is not None and exp_number < exp_start:
        return False
    if exp_end is not None and exp_number > exp_end:
        return False
    return True


def _iter_experiment_dirs(
    log_dir: str,
    batch_name: str,
    exp_start: Optional[int],
    exp_end: Optional[int],
) -> Iterable[Tuple[str, int, str]]:
    pattern = os.path.join(log_dir, batch_name, "exp_*")
    experiments: List[Tuple[int, str, str]] = []
    for exp_dir in glob.glob(pattern):
        if not os.path.isdir(exp_dir):
            continue
        exp_id = os.path.basename(exp_dir)
        exp_number = _parse_exp_number(exp_id)
        if exp_number is None or not _in_exp_range(exp_number, exp_start, exp_end):
            continue
        experiments.append((exp_number, exp_id, exp_dir))

    for exp_number, exp_id, exp_dir in sorted(experiments):
        yield exp_id, exp_number, exp_dir


def scan_judge_items(
    log_dir: str,
    batches: List[str],
    condition_labels: List[str],
    exp_start: Optional[int] = None,
    exp_end: Optional[int] = None,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for batch_name, condition_label in zip(batches, condition_labels):
        batch_root = os.path.join(log_dir, batch_name)
        if not os.path.isdir(batch_root):
            print(f"Warning: batch directory not found: {batch_root}")
            continue

        experiment_dirs = list(
            _iter_experiment_dirs(log_dir, batch_name, exp_start, exp_end)
        )
        found_numbers = {number for _, number, _ in experiment_dirs}
        if exp_start is not None and exp_end is not None:
            missing = [
                number
                for number in range(exp_start, exp_end + 1)
                if number not in found_numbers
            ]
            if missing:
                missing_text = ", ".join(f"exp_{number:03d}" for number in missing[:20])
                suffix = " ..." if len(missing) > 20 else ""
                print(f"Warning: missing experiment directories in {batch_name}: {missing_text}{suffix}")

        if not experiment_dirs:
            print(f"Warning: no experiments matched the requested range in {batch_name}")

        for exp_id, _, exp_dir in experiment_dirs:
            backend_cfg = _read_backend_config(exp_dir)
            meta_paths = sorted(glob.glob(os.path.join(exp_dir, "meta_round_*.json")))
            if not meta_paths:
                print(f"Warning: no meta-round files found in {exp_dir}")
                continue

            for meta_path in meta_paths:
                try:
                    payload = _load_json(meta_path)
                except Exception as exc:
                    print(f"Warning: could not read {meta_path}: {exc}")
                    continue

                if not isinstance(payload, list) or not payload:
                    print(f"Warning: invalid or empty meta-round payload: {meta_path}")
                    continue

                record = payload[0]
                if not isinstance(record, dict):
                    print(f"Warning: first meta-round record is not an object: {meta_path}")
                    continue

                agents = record.get("agents", [])
                if not isinstance(agents, list):
                    print(f"Warning: agents is not a list: {meta_path}")
                    continue

                for agent in agents:
                    if not isinstance(agent, dict):
                        continue
                    agent_id = str(agent.get("agent_id", "unknown"))
                    model_name = _extract_model_name(backend_cfg, agent_id)
                    items.append(
                        build_judge_item(
                            batch_name=batch_name,
                            condition_label=condition_label,
                            exp_id=exp_id,
                            record=record,
                            agent=agent,
                            model_name=model_name,
                        )
                    )

    return items


def _load_existing_item_ids(records_path: str) -> set:
    if not os.path.isfile(records_path):
        return set()

    item_ids = set()
    with open(records_path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            item_id = payload.get("item_id")
            if item_id:
                item_ids.add(str(item_id))

    return item_ids


def _append_jsonl_row(path: str, row: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _load_judge_records(path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        return []

    rows_by_id: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            item_id = row.get("item_id")
            if item_id:
                rows_by_id[str(item_id)] = row
    return list(rows_by_id.values())


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def run_judge_pipeline(
    log_dir: str,
    batches: List[str],
    condition_labels: List[str],
    judge_backend: str,
    judge_model: Optional[str],
    judge_temperature: float,
    output_dir: str,
    max_items: int = 0,
    judge_valid_only: bool = False,
    resume: bool = False,
    blind_model_names: bool = True,
    exp_start: Optional[int] = None,
    exp_end: Optional[int] = None,
    max_attempts: int = 3,
    retry_base_seconds: float = 1.0,
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)

    items = scan_judge_items(
        log_dir=log_dir,
        batches=batches,
        condition_labels=condition_labels,
        exp_start=exp_start,
        exp_end=exp_end,
    )
    if judge_valid_only:
        items = [item for item in items if item.get("is_valid_item", False)]

    records_path = os.path.join(output_dir, "judge_records.jsonl")
    errors_path = os.path.join(output_dir, "judge_errors.jsonl")
    existing_ids = _load_existing_item_ids(records_path)

    pending_items = [item for item in items if item.get("item_id") not in existing_ids]
    if max_items > 0:
        pending_items = stratified_sample_items(pending_items, max_items)

    experiment_count = len({(item.get("batch_name"), item.get("experiment_id")) for item in items})
    skipped_count = len(items) - len(
        [item for item in items if item.get("item_id") not in existing_ids]
    )
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print(f"Matched experiments: {experiment_count}")
    print(f"Scanned judge items: {len(items)}")
    print(f"Already completed items: {skipped_count}")
    print(f"Planned API calls: {len(pending_items)}")
    if resume:
        print("Resume mode: successful existing items are skipped; failed items are retried.")

    if not pending_items:
        backend = None
    else:
        from judge_backend import JudgeBackend

        backend = JudgeBackend(
            backend_name=judge_backend,
            model=judge_model,
            temperature=judge_temperature,
        )

    success_count = 0
    failure_count = 0
    for item in pending_items:
        prompt = build_judge_prompt(item, blind_model_names=blind_model_names)
        last_error: Optional[Exception] = None
        raw_response: Optional[str] = None
        judge_json: Optional[Dict[str, Any]] = None
        attempts_used = 0
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            try:
                raw_response = backend.generate(prompt)
                judge_json = parse_judge_response(raw_response)
                if judge_json.get("primary_failure_mode") == "format_failure":
                    raise ValueError(judge_json.get("short_diagnosis"))
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print(
                    f"Warning: judge API failed for {item.get('item_id')} "
                    f"(attempt {attempt}/{max_attempts}): {exc}"
                )
                if attempt < max_attempts:
                    time.sleep(retry_base_seconds * (2 ** (attempt - 1)))

        if last_error is not None or raw_response is None or judge_json is None:
            failure_count += 1
            _append_jsonl_row(
                errors_path,
                {
                    "item_id": item.get("item_id"),
                    "batch_name": item.get("batch_name"),
                    "condition": item.get("condition"),
                    "experiment_id": item.get("experiment_id"),
                    "meta_round_id": item.get("meta_round_id"),
                    "agent_id": item.get("agent_id"),
                    "judge_model": judge_model,
                    "judge_backend": judge_backend,
                    "attempts": attempts_used,
                    "error_type": type(last_error).__name__ if last_error else "UnknownError",
                    "error_message": str(last_error) if last_error else "No response returned",
                    "raw_response_excerpt": (
                        raw_response[:2000] if isinstance(raw_response, str) else None
                    ),
                    "failed_at": datetime.utcnow().isoformat() + "Z",
                },
            )
            continue

        _append_jsonl_row(
            records_path,
            {
                "item_id": item.get("item_id"),
                "batch_name": item.get("batch_name"),
                "condition": item.get("condition"),
                "experiment_id": item.get("experiment_id"),
                "meta_round_id": item.get("meta_round_id"),
                "agent_id": item.get("agent_id"),
                "model_name": item.get("model_name"),
                "is_valid_item": bool(item.get("is_valid_item", False)),
                "submission_status": item.get("submission_status", {}),
                "judge": judge_json,
                "judge_response_format_valid": (
                    judge_json.get("primary_failure_mode") != "format_failure"
                ),
                "judge_model": judge_model,
                "judge_backend": judge_backend,
                "judged_at": datetime.utcnow().isoformat() + "Z",
            },
        )
        success_count += 1

    all_records = _load_judge_records(records_path)
    aggregation = aggregate_judge_records(all_records)

    _write_json(os.path.join(output_dir, "judge_summary_by_model.json"), aggregation.get("by_model", {}))
    _write_json(os.path.join(output_dir, "judge_summary_by_condition.json"), aggregation.get("by_condition", {}))
    _write_json(
        os.path.join(output_dir, "judge_summary_by_model_condition.json"),
        aggregation.get("by_model_condition", {}),
    )
    _write_json(
        os.path.join(output_dir, "judge_failure_label_distribution.json"),
        aggregation.get("failure_label_distribution", {}),
    )

    from judge_table_plot import generate_judge_tables

    generate_judge_tables(aggregation=aggregation, output_dir=output_dir)

    return {
        "total_scanned_items": len(items),
        "matched_experiments": experiment_count,
        "planned_api_calls": len(pending_items),
        "new_judged_items": success_count,
        "failed_items": failure_count,
        "remaining_failed_items": failure_count,
        "skipped_existing_items": skipped_count,
        "total_judged_items": len(all_records),
        "output_dir": os.path.abspath(output_dir),
    }
