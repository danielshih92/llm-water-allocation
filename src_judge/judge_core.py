import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from judge_aggregation import aggregate_judge_records
from judge_backend import JudgeBackend
from judge_parser import parse_judge_response
from judge_prompt import build_judge_prompt
from judge_sampling import stratified_sample_items
from judge_table_plot import generate_judge_tables


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
            "scenario": record.get("environment", {}).get("scenario"),
            "supply_range": record.get("environment", {}).get("supply_range"),
            "episode_days": record.get("environment", {}).get("episode_days"),
            "supply_list": record.get("environment", {}).get("supply_list"),
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
        },
        "is_valid_item": bool(admitted == 1 and outcome_valid == 1 and has_daily_trace),
    }


def _iter_meta_round_paths(log_dir: str, batch_name: str) -> Iterable[Tuple[str, str]]:
    pattern = os.path.join(log_dir, batch_name, "exp_*", "meta_round_*.json")
    for path in sorted(glob.glob(pattern)):
        exp_id = os.path.basename(os.path.dirname(path))
        yield exp_id, path


def scan_judge_items(
    log_dir: str,
    batches: List[str],
    condition_labels: List[str],
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for batch_name, condition_label in zip(batches, condition_labels):
        batch_root = os.path.join(log_dir, batch_name)
        if not os.path.isdir(batch_root):
            continue

        for exp_id, meta_path in _iter_meta_round_paths(log_dir, batch_name):
            exp_dir = os.path.dirname(meta_path)
            backend_cfg = _read_backend_config(exp_dir)

            try:
                payload = _load_json(meta_path)
            except Exception:
                continue

            if not isinstance(payload, list) or not payload:
                continue

            record = payload[0]
            if not isinstance(record, dict):
                continue

            agents = record.get("agents", [])
            if not isinstance(agents, list):
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


def _append_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return

    with open(path, "a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_judge_records(path: str) -> List[Dict[str, Any]]:
    if not os.path.isfile(path):
        return []

    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


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
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)

    items = scan_judge_items(log_dir=log_dir, batches=batches, condition_labels=condition_labels)
    if judge_valid_only:
        items = [item for item in items if item.get("is_valid_item", False)]

    records_path = os.path.join(output_dir, "judge_records.jsonl")
    existing_ids = _load_existing_item_ids(records_path) if resume else set()

    pending_items = [item for item in items if item.get("item_id") not in existing_ids]
    if max_items > 0:
        pending_items = stratified_sample_items(pending_items, max_items)

    backend = JudgeBackend(
        backend_name=judge_backend,
        model=judge_model,
        temperature=judge_temperature,
    )

    new_rows: List[Dict[str, Any]] = []
    for item in pending_items:
        prompt = build_judge_prompt(item, blind_model_names=blind_model_names)
        raw_response = backend.generate(prompt)
        judge_json = parse_judge_response(raw_response)

        new_rows.append(
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
                "judge_model": judge_model,
                "judge_backend": judge_backend,
                "judged_at": datetime.utcnow().isoformat() + "Z",
            }
        )

    _append_jsonl(records_path, new_rows)

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

    generate_judge_tables(aggregation=aggregation, output_dir=output_dir)

    return {
        "total_scanned_items": len(items),
        "new_judged_items": len(new_rows),
        "total_judged_items": len(all_records),
        "output_dir": output_dir,
    }
