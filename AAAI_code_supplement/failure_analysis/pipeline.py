"""Checkpointed two-judge failure-analysis pipeline."""

import fcntl
import hashlib
import json
import os
import sys
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .aggregation import (
    aggregate_paired_records,
    load_jsonl_records,
    pair_judge_records,
    write_attribution_csv,
    write_contextual_contributors_csv,
    write_distribution_csv,
    write_paired_jsonl,
)
from .backend import FailureJudgeBackend
from .parser import FailureJudgeParseError, parse_failure_response
from .prompt import build_failure_prompt, derive_failure_evidence
from .taxonomy import PROMPT_VERSION


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_JUDGE_DIR = os.path.join(PROJECT_ROOT, "judge_support")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _is_non_retryable_quota_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return "insufficient_quota" in message or (
        "exceeded your current quota" in message
        and ("429" in message or "quota" in message)
    )


@contextmanager
def _output_lock(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, ".failure_analysis.lock")
    handle = open(path, "a+", encoding="utf-8")
    acquired = False
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError as exc:
            raise RuntimeError(
                "Another failure-analysis process is using this output directory. "
                "Use a different --output-dir for parallel runs."
            ) from exc
        yield
    finally:
        if acquired:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def _append_jsonl(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _scan_items(
    log_dir: str,
    batches: List[str],
    condition_labels: List[str],
    exp_start: Optional[int],
    exp_end: Optional[int],
) -> List[Dict[str, Any]]:
    if SRC_JUDGE_DIR not in sys.path:
        sys.path.insert(0, SRC_JUDGE_DIR)
    from judge_core import scan_judge_items

    return scan_judge_items(
        log_dir=log_dir,
        batches=batches,
        condition_labels=condition_labels,
        exp_start=exp_start,
        exp_end=exp_end,
    )


def _eligible_items(items: Iterable[Dict[str, Any]], death_only: bool) -> List[Dict[str, Any]]:
    eligible: List[Dict[str, Any]] = []
    for item in items:
        if not item.get("is_valid_item", False):
            continue
        summary = item.get("trajectory", {}).get("evidence_summary", {})
        if death_only and summary.get("final_status") != "dead":
            continue
        eligible.append(item)
    return eligible


def _stratified_sample(items: Sequence[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
    if max_items <= 0 or len(items) <= max_items:
        return list(items)
    buckets: Dict[Tuple[str, str], deque] = defaultdict(deque)
    for item in items:
        key = (str(item.get("condition", "unknown")), str(item.get("model_name", "unknown")))
        buckets[key].append(item)
    result: List[Dict[str, Any]] = []
    keys = sorted(buckets)
    while len(result) < max_items:
        progressed = False
        for key in keys:
            if len(result) >= max_items:
                break
            if buckets[key]:
                result.append(buckets[key].popleft())
                progressed = True
        if not progressed:
            break
    return result


def _existing_ids(path: str) -> set:
    return {str(row["item_id"]) for row in load_jsonl_records(path) if row.get("item_id")}


def _validate_response_against_item(
    parsed: Dict[str, Any], item: Dict[str, Any]
) -> None:
    """Reject labels whose required trajectory-side evidence is absent."""
    derived = derive_failure_evidence(item)
    bridge_candidates = derived["winner_curse_bridge_candidates"]
    critical_misses = derived["critical_affordable_threshold_misses"]
    miss_supported = derived["repeated_or_lethal_affordable_miss_supported"]
    checks = parsed.get("boundary_checks", {})
    primary = parsed.get("primary_failure_mode")
    attribution_status = parsed.get("attribution_status")
    mixed_attribution = attribution_status == "mixed_policy_and_context"

    if checks.get("winner_curse_bridge_supported") and not bridge_candidates:
        raise FailureJudgeParseError(
            "boundary_checks.winner_curse_bridge_supported=true but the "
            "derived evidence contains no winner_curse_bridge_candidate."
        )
    if primary == "winners_curse_overpayment" and not bridge_candidates:
        raise FailureJudgeParseError(
            "winners_curse_overpayment requires a derived winner-curse bridge."
        )
    if primary == "fatal_undercommitment":
        required_miss_evidence = bool(critical_misses) if mixed_attribution else miss_supported
        if not required_miss_evidence:
            qualifier = (
                "at least one critical affordable miss"
                if mixed_attribution
                else (
                    "repeated critical misses, a lethal same-day miss, or a "
                    "critical miss immediately preceding death"
                )
            )
            raise FailureJudgeParseError(
                f"fatal_undercommitment requires {qualifier}."
            )
    if primary == "competitive_threshold_miscalibration":
        required_miss_evidence = bool(critical_misses) if mixed_attribution else miss_supported
        if not required_miss_evidence:
            qualifier = (
                "at least one critical affordable miss"
                if mixed_attribution
                else (
                    "repeated critical misses, a lethal same-day miss, or a "
                    "critical miss immediately preceding death"
                )
            )
            raise FailureJudgeParseError(
                f"competitive_threshold_miscalibration requires {qualifier}."
            )


def _prepare_config(
    output_dir: str,
    batches: List[str],
    condition_labels: List[str],
    judge_specs: Sequence[Dict[str, Any]],
    temperature: float,
    blind_model_names: bool,
    death_only: bool,
) -> Dict[str, Any]:
    path = os.path.join(output_dir, "failure_run_config.json")
    current = {
        "prompt_version": PROMPT_VERSION,
        "judge_specs": list(judge_specs),
        "temperature": temperature,
        "blind_model_names": blind_model_names,
        "death_only": death_only,
        "batch_condition_mapping": [
            {"batch": batch, "condition": condition}
            for batch, condition in zip(batches, condition_labels)
        ],
        "categorical_aggregation": (
            "Each judge contributes 0.5 attribution-status vote and 0.5 "
            "primary-mode vote per item; contributing/contextual modes are "
            "reported as independent prevalence scores."
        ),
    }
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            existing = json.load(handle)
        mismatches = [key for key, value in current.items() if existing.get(key) != value]
        if mismatches:
            raise ValueError(
                "Output directory contains a different failure-analysis configuration "
                f"({', '.join(mismatches)}). Use a new --output-dir."
            )
        return existing
    _write_json(path, current)
    return current


def _run_one_judge(
    judge_index: int,
    spec: Dict[str, Any],
    items: Sequence[Dict[str, Any]],
    output_dir: str,
    temperature: float,
    blind_model_names: bool,
    max_attempts: int,
    retry_base_seconds: float,
) -> Dict[str, int]:
    records_path = os.path.join(output_dir, f"judge_{judge_index}_records.jsonl")
    errors_path = os.path.join(output_dir, f"judge_{judge_index}_errors.jsonl")
    completed = _existing_ids(records_path)
    pending = [item for item in items if str(item.get("item_id")) not in completed]
    if not pending:
        return {"planned": 0, "successful": 0, "failed": 0, "skipped": len(items)}

    backend = FailureJudgeBackend(
        backend_name=str(spec["backend"]),
        model=str(spec["model"]),
        temperature=temperature,
    )
    successful = 0
    failed = 0
    aborted_reason: Optional[str] = None

    for item in pending:
        prompt = build_failure_prompt(item, blind_model_names=blind_model_names)
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        response: Optional[str] = None
        parsed: Optional[Dict[str, Any]] = None
        last_error: Optional[Exception] = None
        attempts = 0
        for attempt in range(1, max_attempts + 1):
            attempts = attempt
            try:
                response = backend.generate(prompt)
                parsed = parse_failure_response(response)
                _validate_response_against_item(parsed, item)
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                print(
                    f"Warning: judge {judge_index} failed for {item.get('item_id')} "
                    f"({attempt}/{max_attempts}): {exc}"
                )
                if _is_non_retryable_quota_error(exc):
                    aborted_reason = "non_retryable_insufficient_quota"
                    break
                if attempt < max_attempts:
                    time.sleep(retry_base_seconds * (2 ** (attempt - 1)))

        if last_error is not None or parsed is None or response is None:
            failed += 1
            _append_jsonl(
                errors_path,
                {
                    "item_id": item.get("item_id"),
                    "judge_index": judge_index,
                    "judge_backend": spec["backend"],
                    "judge_model": spec["model"],
                    "attempts": attempts,
                    "error_type": type(last_error).__name__ if last_error else "UnknownError",
                    "error_message": str(last_error) if last_error else "No response",
                    "raw_response_excerpt": response[:2000] if response else None,
                    "prompt_sha256": prompt_hash,
                    "failed_at": _utc_now(),
                },
            )
            if aborted_reason:
                print(
                    f"Stopping judge {judge_index}: API quota is exhausted. "
                    "Successful checkpoints are preserved."
                )
                break
            continue

        summary = item.get("trajectory", {}).get("evidence_summary", {})
        _append_jsonl(
            records_path,
            {
                "item_id": item.get("item_id"),
                "batch_name": item.get("batch_name"),
                "condition": item.get("condition"),
                "experiment_id": item.get("experiment_id"),
                "meta_round_id": item.get("meta_round_id"),
                "agent_id": item.get("agent_id"),
                "model_name": item.get("model_name"),
                "death_day": summary.get("death_day"),
                "judge_index": judge_index,
                "judge_backend": spec["backend"],
                "judge_model": spec["model"],
                "judge_temperature": temperature,
                "blind_model_names": blind_model_names,
                "prompt_version": PROMPT_VERSION,
                "prompt_sha256": prompt_hash,
                "judge": parsed,
                "raw_judge_response": response,
                "judge_attempts": attempts,
                "judged_at": _utc_now(),
            },
        )
        successful += 1

    attempted_items = successful + failed
    return {
        "planned": len(pending),
        "successful": successful,
        "failed": failed,
        "skipped": len(items) - len(pending),
        "unattempted_due_to_abort": max(0, len(pending) - attempted_items),
        "aborted_reason": aborted_reason,
    }


def run_failure_analysis(
    log_dir: str,
    batches: List[str],
    condition_labels: List[str],
    judge_specs: Sequence[Dict[str, Any]],
    output_dir: str,
    temperature: float = 0.0,
    blind_model_names: bool = True,
    death_only: bool = True,
    exp_start: Optional[int] = None,
    exp_end: Optional[int] = None,
    max_items: int = 0,
    max_attempts: int = 3,
    retry_base_seconds: float = 1.0,
    judge_run_order: Sequence[int] = (1, 2),
) -> Dict[str, Any]:
    if len(judge_specs) != 2:
        raise ValueError("Exactly two judge specifications are required.")
    if len(batches) != len(condition_labels):
        raise ValueError("condition_labels length must equal batches length.")
    if sorted(judge_run_order) != [1, 2]:
        raise ValueError("judge_run_order must contain judge indices 1 and 2 once each.")

    with _output_lock(output_dir):
        _prepare_config(
            output_dir,
            batches,
            condition_labels,
            judge_specs,
            temperature,
            blind_model_names,
            death_only,
        )
        scanned = _scan_items(log_dir, batches, condition_labels, exp_start, exp_end)
        eligible = _eligible_items(scanned, death_only=death_only)

        paths = [
            os.path.join(output_dir, "judge_1_records.jsonl"),
            os.path.join(output_dir, "judge_2_records.jsonl"),
        ]
        existing_sets = [_existing_ids(path) for path in paths]
        candidates = [
            item
            for item in eligible
            if any(str(item.get("item_id")) not in ids for ids in existing_sets)
        ]
        selected_pending = _stratified_sample(candidates, max_items)
        selected_ids = {str(item.get("item_id")) for item in selected_pending}
        selected = [
            item
            for item in eligible
            if str(item.get("item_id")) in selected_ids
            or all(str(item.get("item_id")) in ids for ids in existing_sets)
        ]

        print(f"Output directory: {os.path.abspath(output_dir)}")
        print(f"Scanned policy-rounds: {len(scanned)}")
        print(f"Eligible failure-analysis items: {len(eligible)}")
        print(f"New items selected this run: {len(selected_pending)}")
        planned_calls = sum(
            sum(str(item.get("item_id")) not in ids for item in selected_pending)
            for ids in existing_sets
        )
        print(f"Planned API calls across two judges: {planned_calls}")

        judge_reports = []
        for index in judge_run_order:
            spec = judge_specs[index - 1]
            judge_report = _run_one_judge(
                    judge_index=index,
                    spec=dict(spec),
                    items=selected,
                    output_dir=output_dir,
                    temperature=temperature,
                    blind_model_names=blind_model_names,
                    max_attempts=max_attempts,
                    retry_base_seconds=retry_base_seconds,
                )
            judge_reports.append(judge_report)
            if judge_report.get("aborted_reason"):
                break

        records_1 = load_jsonl_records(paths[0])
        records_2 = load_jsonl_records(paths[1])
        paired = pair_judge_records(records_1, records_2)
        aggregation = aggregate_paired_records(paired)

        write_paired_jsonl(os.path.join(output_dir, "paired_judge_records.jsonl"), paired)
        _write_json(os.path.join(output_dir, "failure_summary_overall.json"), aggregation["overall"])
        _write_json(os.path.join(output_dir, "failure_summary_by_model.json"), aggregation["by_model"])
        _write_json(
            os.path.join(output_dir, "failure_summary_by_condition.json"),
            aggregation["by_condition"],
        )
        _write_json(
            os.path.join(output_dir, "failure_summary_by_model_condition.json"),
            aggregation["by_model_condition"],
        )
        _write_json(
            os.path.join(output_dir, "judge_agreement.json"),
            {
                "overall": {
                    key: aggregation["overall"][key]
                    for key in (
                        "paired_item_count",
                        "primary_agreement_count",
                        "primary_agreement_rate",
                        "cohen_kappa",
                        "attribution_status_agreement_count",
                        "attribution_status_agreement_rate",
                        "attribution_status_cohen_kappa",
                    )
                },
                "by_model": {
                    model: {
                        key: summary[key]
                        for key in (
                            "paired_item_count",
                            "primary_agreement_count",
                            "primary_agreement_rate",
                            "cohen_kappa",
                            "attribution_status_agreement_count",
                            "attribution_status_agreement_rate",
                            "attribution_status_cohen_kappa",
                        )
                    }
                    for model, summary in aggregation["by_model"].items()
                },
            },
        )
        write_distribution_csv(
            os.path.join(output_dir, "failure_mode_distribution.csv"), aggregation
        )
        write_attribution_csv(
            os.path.join(output_dir, "attribution_status_distribution.csv"),
            aggregation,
        )
        write_contextual_contributors_csv(
            os.path.join(output_dir, "contextual_contributor_distribution.csv"),
            aggregation,
        )

        report = {
            "scanned_policy_rounds": len(scanned),
            "eligible_items": len(eligible),
            "selected_new_items": len(selected_pending),
            "planned_api_calls": planned_calls,
            "judge_reports": judge_reports,
            "judge_run_order": list(judge_run_order),
            "judge_1_total_success": len(records_1),
            "judge_2_total_success": len(records_2),
            "paired_total": len(paired),
            "death_only": death_only,
            "exp_start": exp_start,
            "exp_end": exp_end,
            "completed_at": _utc_now(),
        }
        _write_json(os.path.join(output_dir, "failure_run_report.json"), report)
        return report
