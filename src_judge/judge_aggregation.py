from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple


SCORE_KEYS = [
    "strategy_quality_score",
    "survival_risk_management_score",
    "budget_efficiency_score",
    "opponent_supply_adaptation_score",
    "temporal_planning_score",
    "reasoning_code_trace_consistency_score",
    "implementation_quality_score",
    "judge_confidence",
]


def _safe_avg(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values)) / float(len(values))


def _group_key_model(record: Dict[str, Any]) -> str:
    return str(record.get("model_name", "unknown"))


def _group_key_condition(record: Dict[str, Any]) -> str:
    return str(record.get("condition", "unknown"))


def _group_key_model_condition(record: Dict[str, Any]) -> Tuple[str, str]:
    return (
        str(record.get("model_name", "unknown")),
        str(record.get("condition", "unknown")),
    )


def _aggregate_group(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    records = list(records)
    score_lists: Dict[str, List[float]] = defaultdict(list)
    valid_score_lists: Dict[str, List[float]] = defaultdict(list)
    failure_counter: Counter = Counter()
    primary_failure_counter: Counter = Counter()
    failure_severity_lists: Dict[str, List[float]] = defaultdict(list)

    valid_count = 0
    for record in records:
        judge = record.get("judge", {})
        is_valid_item = bool(record.get("is_valid_item", False))

        for key in SCORE_KEYS:
            value = judge.get(key)
            if isinstance(value, (int, float)):
                score_lists[key].append(float(value))
                if is_valid_item:
                    valid_score_lists[key].append(float(value))

        if is_valid_item:
            valid_count += 1

        labels = judge.get("failure_labels", [])
        if isinstance(labels, list):
            for label in labels:
                failure_counter[str(label)] += 1

        primary_failure_counter[str(judge.get("primary_failure_mode", "none"))] += 1

        annotations = judge.get("failure_annotations", [])
        if isinstance(annotations, list):
            for annotation in annotations:
                if not isinstance(annotation, dict):
                    continue
                label = str(annotation.get("label", "")).strip()
                severity = annotation.get("severity")
                if label and isinstance(severity, (int, float)):
                    failure_severity_lists[label].append(float(severity))

    output = {
        "count": len(records),
        "valid_item_count": valid_count,
        "valid_item_rate": (float(valid_count) / float(len(records))) if records else 0.0,
        "avg_scores": {key: round(_safe_avg(score_lists[key]), 4) for key in SCORE_KEYS},
        "avg_scores_valid_only": {
            key: (round(_safe_avg(valid_score_lists[key]), 4) if valid_score_lists[key] else None)
            for key in SCORE_KEYS
        },
        "failure_label_distribution": dict(failure_counter),
        "primary_failure_distribution": dict(primary_failure_counter),
        "avg_failure_severity": {
            label: round(_safe_avg(values), 4)
            for label, values in sorted(failure_severity_lists.items())
        },
    }

    return output


def aggregate_judge_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_model: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_condition: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_model_condition: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    global_failure_counter: Counter = Counter()

    for record in records:
        by_model[_group_key_model(record)].append(record)
        by_condition[_group_key_condition(record)].append(record)
        by_model_condition[_group_key_model_condition(record)].append(record)

        labels = record.get("judge", {}).get("failure_labels", [])
        if isinstance(labels, list):
            for label in labels:
                global_failure_counter[str(label)] += 1

    model_summary = {k: _aggregate_group(v) for k, v in sorted(by_model.items())}
    condition_summary = {k: _aggregate_group(v) for k, v in sorted(by_condition.items())}
    model_condition_summary = {
        f"{k[0]}__{k[1]}": _aggregate_group(v)
        for k, v in sorted(by_model_condition.items())
    }

    return {
        "total_items": len(records),
        "by_model": model_summary,
        "by_condition": condition_summary,
        "by_model_condition": model_condition_summary,
        "failure_label_distribution": dict(global_failure_counter),
    }
