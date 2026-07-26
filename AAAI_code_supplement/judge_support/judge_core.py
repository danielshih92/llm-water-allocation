import fcntl
import glob
import hashlib
import inspect
import json
import os
import re
import time
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Iterable, List, Optional, Tuple

from judge_aggregation import aggregate_judge_records
from judge_evidence import reconstruct_record_evidence
from judge_parser import parse_judge_response
from judge_prompt import JUDGE_PROMPT_VERSION, build_judge_prompt
from judge_sampling import stratified_sample_items


@contextmanager
def _exclusive_output_lock(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    lock_path = os.path.join(output_dir, ".judge_pipeline.lock")
    lock_handle = open(lock_path, "a+", encoding="utf-8")
    lock_acquired = False
    try:
        try:
            fcntl.flock(
                lock_handle.fileno(),
                fcntl.LOCK_EX | fcntl.LOCK_NB,
            )
            lock_acquired = True
        except BlockingIOError as exc:
            raise RuntimeError(
                "Another judge process is already using this "
                f"--output-dir: {os.path.abspath(output_dir)}. "
                "Use a different output directory for parallel tmux runs."
            ) from exc
        yield
    finally:
        try:
            if lock_acquired:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        finally:
            lock_handle.close()


def _lock_output_directory(function):
    signature = inspect.signature(function)

    @wraps(function)
    def wrapped(*args, **kwargs):
        bound = signature.bind(*args, **kwargs)
        output_dir = str(bound.arguments["output_dir"])
        with _exclusive_output_lock(output_dir):
            return function(*args, **kwargs)

    return wrapped


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
    record_evidence: Optional[Dict[str, Any]] = None,
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
    environment = (
        record.get("environment", {})
        if isinstance(record.get("environment"), dict)
        else {}
    )
    if record_evidence is None:
        record_evidence = reconstruct_record_evidence(record)
    agent_evidence = (
        record_evidence.get("agents", {}).get(str(agent_id), {})
        if isinstance(record_evidence, dict)
        else {}
    )
    evidence_summary = (
        agent_evidence.get("summary", {})
        if isinstance(agent_evidence, dict)
        else {}
    )
    daily_evidence = (
        agent_evidence.get("daily_evidence", [])
        if isinstance(agent_evidence, dict)
        else []
    )
    has_daily_evidence = (
        isinstance(daily_evidence, list) and len(daily_evidence) > 0
    )
    reconstruction_valid = bool(
        evidence_summary.get("reconstruction_valid", False)
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
            "evidence_summary": evidence_summary,
            "daily_evidence": daily_evidence,
        },
        "is_valid_item": bool(
            admitted == 1
            and outcome_valid == 1
            and has_daily_evidence
            and reconstruction_valid
        ),
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

                record_evidence = reconstruct_record_evidence(record)
                if not record_evidence.get("reconstruction_valid", False):
                    mismatches = record_evidence.get(
                        "validation_mismatches", []
                    )
                    preview = ", ".join(str(value) for value in mismatches[:3])
                    print(
                        "Warning: evidence reconstruction validation failed "
                        f"for {meta_path}: {preview}"
                    )

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
                            record_evidence=record_evidence,
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


def _prepare_run_config(
    output_dir: str,
    records_path: str,
    batches: List[str],
    condition_labels: List[str],
    judge_backend: str,
    judge_model: Optional[str],
    judge_temperature: float,
    blind_model_names: bool,
    judge_valid_only: bool,
) -> Dict[str, Any]:
    config_path = os.path.join(output_dir, "judge_run_config.json")
    current = {
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "judge_backend": judge_backend,
        "judge_model": judge_model,
        "judge_temperature": judge_temperature,
        "blind_model_names": blind_model_names,
        "judge_valid_only": judge_valid_only,
        "batch_condition_mapping": [
            {
                "batch": batch,
                "condition": condition,
            }
            for batch, condition in zip(batches, condition_labels)
        ],
    }

    if os.path.isfile(config_path):
        existing = _load_json(config_path)
        if not isinstance(existing, dict):
            raise ValueError(
                f"Invalid judge run config: {config_path}"
            )
        mismatched_keys = [
            key
            for key, value in current.items()
            if existing.get(key) != value
        ]
        if mismatched_keys:
            mismatch_text = ", ".join(mismatched_keys)
            raise ValueError(
                "The output directory already contains results from a "
                "different judge configuration "
                f"({mismatch_text}). Use a new --output-dir."
            )
        return existing

    if os.path.isfile(records_path) and os.path.getsize(records_path) > 0:
        raise ValueError(
            "The output directory contains legacy judge records without "
            "judge_run_config.json. Use a new --output-dir so old and new "
            "evaluation protocols are not mixed."
        )

    _write_json(config_path, current)
    return current


@_lock_output_directory
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
    if judge_backend != "mock" and not judge_model:
        raise ValueError(
            "--judge-model must be specified explicitly so the judge run "
            "is reproducible."
        )
    os.makedirs(output_dir, exist_ok=True)
    records_path = os.path.join(output_dir, "judge_records.jsonl")
    errors_path = os.path.join(output_dir, "judge_errors.jsonl")
    _prepare_run_config(
        output_dir=output_dir,
        records_path=records_path,
        batches=batches,
        condition_labels=condition_labels,
        judge_backend=judge_backend,
        judge_model=judge_model,
        judge_temperature=judge_temperature,
        blind_model_names=blind_model_names,
        judge_valid_only=judge_valid_only,
    )

    items = scan_judge_items(
        log_dir=log_dir,
        batches=batches,
        condition_labels=condition_labels,
        exp_start=exp_start,
        exp_end=exp_end,
    )
    if judge_valid_only:
        items = [item for item in items if item.get("is_valid_item", False)]

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
        prompt_sha256 = hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest()
        last_error: Optional[Exception] = None
        raw_response: Optional[str] = None
        judge_json: Optional[Dict[str, Any]] = None
        attempts_used = 0
        for attempt in range(1, max_attempts + 1):
            attempts_used = attempt
            try:
                raw_response = backend.generate(prompt)
                judge_json = parse_judge_response(raw_response)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print(
                    f"Warning: judge attempt failed for {item.get('item_id')} "
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
                    "judge_temperature": judge_temperature,
                    "blind_model_names": blind_model_names,
                    "judge_prompt_version": JUDGE_PROMPT_VERSION,
                    "judge_prompt_sha256": prompt_sha256,
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
                "judge_response_format_valid": True,
                "judge_model": judge_model,
                "judge_backend": judge_backend,
                "judge_temperature": judge_temperature,
                "blind_model_names": blind_model_names,
                "judge_prompt_version": JUDGE_PROMPT_VERSION,
                "judge_prompt_sha256": prompt_sha256,
                "raw_judge_response": raw_response,
                "judge_attempts": attempts_used,
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

    current_item_ids = {
        str(item.get("item_id"))
        for item in items
        if item.get("item_id")
    }
    current_success_count = sum(
        1
        for record in all_records
        if str(record.get("item_id")) in current_item_ids
    )
    result = {
        "total_scanned_items": len(items),
        "matched_experiments": experiment_count,
        "planned_api_calls": len(pending_items),
        "new_judged_items": success_count,
        "failed_items": failure_count,
        "remaining_failed_items": failure_count,
        "skipped_existing_items": skipped_count,
        "total_judged_items": len(all_records),
        "current_range_successful_items": current_success_count,
        "current_range_coverage_rate": (
            round(current_success_count / len(items), 6)
            if items
            else 0.0
        ),
        "batches": list(batches),
        "condition_labels": list(condition_labels),
        "exp_start": exp_start,
        "exp_end": exp_end,
        "max_items": max_items,
        "judge_valid_only": judge_valid_only,
        "resume": resume,
        "max_attempts": max_attempts,
        "retry_base_seconds": retry_base_seconds,
        "judge_prompt_version": JUDGE_PROMPT_VERSION,
        "completed_at": datetime.utcnow().isoformat() + "Z",
        "log_dir": os.path.abspath(log_dir),
        "output_dir": os.path.abspath(output_dir),
    }
    _write_json(
        os.path.join(output_dir, "judge_run_report.json"),
        result,
    )
    return result
