"""Pair two independent judges and average their categorical votes."""

import csv
import json
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .taxonomy import (
    ALLOWED_PRIMARY_LABELS,
    ATTRIBUTION_STATUSES,
    CONTEXTUAL_CONTRIBUTORS,
    FAILURE_MODES,
    NO_PRIMARY_FAILURE_LABEL,
)


def load_jsonl_records(path: str) -> List[Dict[str, Any]]:
    rows_by_id: Dict[str, Dict[str, Any]] = {}
    try:
        handle = open(path, "r", encoding="utf-8")
    except FileNotFoundError:
        return []
    with handle:
        for line in handle:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not isinstance(row, dict) or not row.get("item_id"):
                continue
            rows_by_id[str(row["item_id"])] = row
    return list(rows_by_id.values())


def _judge_payload(record: Mapping[str, Any]) -> Mapping[str, Any]:
    value = record.get("judge", {})
    return value if isinstance(value, dict) else {}


def pair_judge_records(
    judge_1_records: Sequence[Dict[str, Any]],
    judge_2_records: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    left = {str(row["item_id"]): row for row in judge_1_records if row.get("item_id")}
    right = {str(row["item_id"]): row for row in judge_2_records if row.get("item_id")}
    paired: List[Dict[str, Any]] = []

    for item_id in sorted(set(left).intersection(right)):
        row_1 = left[item_id]
        row_2 = right[item_id]
        judge_1 = _judge_payload(row_1)
        judge_2 = _judge_payload(row_2)
        primary_1 = judge_1.get("primary_failure_mode")
        primary_2 = judge_2.get("primary_failure_mode")
        label_1 = str(primary_1) if primary_1 in FAILURE_MODES else NO_PRIMARY_FAILURE_LABEL
        label_2 = str(primary_2) if primary_2 in FAILURE_MODES else NO_PRIMARY_FAILURE_LABEL
        status_1 = str(judge_1.get("attribution_status", "insufficient_evidence"))
        status_2 = str(judge_2.get("attribution_status", "insufficient_evidence"))
        vote_weights = {label: 0.0 for label in ALLOWED_PRIMARY_LABELS}
        vote_weights[label_1] = vote_weights.get(label_1, 0.0) + 0.5
        vote_weights[label_2] = vote_weights.get(label_2, 0.0) + 0.5
        reasoning_mismatch_1 = bool(judge_1.get("reasoning_policy_mismatch"))
        reasoning_mismatch_2 = bool(judge_2.get("reasoning_policy_mismatch"))
        trajectory_mismatch_1 = bool(judge_1.get("policy_trajectory_mismatch"))
        trajectory_mismatch_2 = bool(judge_2.get("policy_trajectory_mismatch"))
        modes_1 = {
            label_1,
            *judge_1.get("contributing_failure_modes", []),
        }.intersection(FAILURE_MODES)
        modes_2 = {
            label_2,
            *judge_2.get("contributing_failure_modes", []),
        }.intersection(FAILURE_MODES)
        any_mode_scores = {
            label: (float(label in modes_1) + float(label in modes_2)) / 2.0
            for label in FAILURE_MODES
        }
        context_1 = set(judge_1.get("contextual_contributors", [])).intersection(
            CONTEXTUAL_CONTRIBUTORS
        )
        context_2 = set(judge_2.get("contextual_contributors", [])).intersection(
            CONTEXTUAL_CONTRIBUTORS
        )
        contextual_scores = {
            label: (float(label in context_1) + float(label in context_2)) / 2.0
            for label in CONTEXTUAL_CONTRIBUTORS
        }

        paired.append(
            {
                "item_id": item_id,
                "batch_name": row_1.get("batch_name"),
                "condition": row_1.get("condition"),
                "experiment_id": row_1.get("experiment_id"),
                "meta_round_id": row_1.get("meta_round_id"),
                "agent_id": row_1.get("agent_id"),
                "model_name": row_1.get("model_name"),
                "death_day": row_1.get("death_day"),
                "judge_1_attribution_status": status_1,
                "judge_2_attribution_status": status_2,
                "attribution_status_agreement": status_1 == status_2,
                "judge_1_primary": label_1,
                "judge_2_primary": label_2,
                "primary_agreement": label_1 == label_2,
                "averaged_primary_vote": vote_weights,
                "averaged_any_failure_mode_score": any_mode_scores,
                "averaged_contextual_contributor_score": contextual_scores,
                "judge_1_reasoning_policy_mismatch": reasoning_mismatch_1,
                "judge_2_reasoning_policy_mismatch": reasoning_mismatch_2,
                "reasoning_policy_mismatch_agreement": (
                    reasoning_mismatch_1 == reasoning_mismatch_2
                ),
                "reasoning_policy_mismatch_score": (
                    float(reasoning_mismatch_1) + float(reasoning_mismatch_2)
                )
                / 2.0,
                "judge_1_policy_trajectory_mismatch": trajectory_mismatch_1,
                "judge_2_policy_trajectory_mismatch": trajectory_mismatch_2,
                "policy_trajectory_mismatch_agreement": (
                    trajectory_mismatch_1 == trajectory_mismatch_2
                ),
                "policy_trajectory_mismatch_score": (
                    float(trajectory_mismatch_1) + float(trajectory_mismatch_2)
                )
                / 2.0,
                "mean_confidence": (
                    float(judge_1.get("confidence", 0))
                    + float(judge_2.get("confidence", 0))
                )
                / 2.0,
            }
        )
    return paired


def _cohen_kappa(
    rows: Sequence[Dict[str, Any]],
    left_key: str = "judge_1_primary",
    right_key: str = "judge_2_primary",
    agreement_key: str = "primary_agreement",
    labels: Sequence[str] = ALLOWED_PRIMARY_LABELS,
) -> Optional[float]:
    if not rows:
        return None
    observed = sum(bool(row.get(agreement_key)) for row in rows) / len(rows)
    left = Counter(str(row.get(left_key)) for row in rows)
    right = Counter(str(row.get(right_key)) for row in rows)
    expected = sum((left[label] / len(rows)) * (right[label] / len(rows)) for label in labels)
    if expected >= 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _group_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(rows)
    weighted = {label: 0.0 for label in ALLOWED_PRIMARY_LABELS}
    status_weighted = {status: 0.0 for status in ATTRIBUTION_STATUSES}
    any_mode_weighted = {label: 0.0 for label in FAILURE_MODES}
    contextual_weighted = {label: 0.0 for label in CONTEXTUAL_CONTRIBUTORS}
    judge_1 = Counter()
    judge_2 = Counter()
    judge_1_status = Counter()
    judge_2_status = Counter()
    for row in rows:
        for label, weight in row.get("averaged_primary_vote", {}).items():
            weighted[str(label)] = weighted.get(str(label), 0.0) + float(weight)
        judge_1[str(row.get("judge_1_primary"))] += 1
        judge_2[str(row.get("judge_2_primary"))] += 1
        status_1 = str(row.get("judge_1_attribution_status"))
        status_2 = str(row.get("judge_2_attribution_status"))
        status_weighted[status_1] = status_weighted.get(status_1, 0.0) + 0.5
        status_weighted[status_2] = status_weighted.get(status_2, 0.0) + 0.5
        judge_1_status[status_1] += 1
        judge_2_status[status_2] += 1
        for label, score in row.get("averaged_any_failure_mode_score", {}).items():
            any_mode_weighted[str(label)] += float(score)
        for label, score in row.get(
            "averaged_contextual_contributor_score", {}
        ).items():
            contextual_weighted[str(label)] += float(score)

    attributable_weight = sum(
        status_weighted.get(status, 0.0)
        for status in ("dominant_policy_failure", "mixed_policy_and_context")
    )
    rates_all = {
        label: round(weighted.get(label, 0.0) / n, 6) if n else 0.0
        for label in ALLOWED_PRIMARY_LABELS
    }
    rates_attributable = {
        label: (
            round(weighted.get(label, 0.0) / attributable_weight, 6)
            if attributable_weight > 0.0
            else 0.0
        )
        for label in ALLOWED_PRIMARY_LABELS
        if label != NO_PRIMARY_FAILURE_LABEL
    }

    agreement_count = sum(bool(row.get("primary_agreement")) for row in rows)
    status_agreement_count = sum(
        bool(row.get("attribution_status_agreement")) for row in rows
    )
    kappa = _cohen_kappa(rows)
    status_kappa = _cohen_kappa(
        rows,
        left_key="judge_1_attribution_status",
        right_key="judge_2_attribution_status",
        agreement_key="attribution_status_agreement",
        labels=ATTRIBUTION_STATUSES,
    )
    return {
        "paired_item_count": n,
        "policy_attributable_vote_weight": round(attributable_weight, 4),
        "policy_attribution_coverage_rate": (
            round(attributable_weight / n, 6) if n else 0.0
        ),
        "averaged_attribution_status_counts": {
            status: round(status_weighted.get(status, 0.0), 4)
            for status in ATTRIBUTION_STATUSES
        },
        "averaged_attribution_status_rates": {
            status: round(status_weighted.get(status, 0.0) / n, 6) if n else 0.0
            for status in ATTRIBUTION_STATUSES
        },
        "judge_1_attribution_status_counts": dict(judge_1_status),
        "judge_2_attribution_status_counts": dict(judge_2_status),
        "attribution_status_agreement_count": status_agreement_count,
        "attribution_status_agreement_rate": (
            round(status_agreement_count / n, 6) if n else 0.0
        ),
        "attribution_status_cohen_kappa": (
            round(status_kappa, 6) if status_kappa is not None else None
        ),
        "averaged_primary_counts": {
            label: round(weighted.get(label, 0.0), 4)
            for label in ALLOWED_PRIMARY_LABELS
        },
        "averaged_primary_rates_all_items": rates_all,
        "averaged_primary_rates_attributable": rates_attributable,
        "averaged_any_failure_mode_counts": {
            label: round(any_mode_weighted.get(label, 0.0), 4)
            for label in FAILURE_MODES
        },
        "averaged_any_failure_mode_rates_all_items": {
            label: round(any_mode_weighted.get(label, 0.0) / n, 6) if n else 0.0
            for label in FAILURE_MODES
        },
        "averaged_contextual_contributor_counts": {
            label: round(contextual_weighted.get(label, 0.0), 4)
            for label in CONTEXTUAL_CONTRIBUTORS
        },
        "averaged_contextual_contributor_rates_all_items": {
            label: round(contextual_weighted.get(label, 0.0) / n, 6) if n else 0.0
            for label in CONTEXTUAL_CONTRIBUTORS
        },
        "judge_1_primary_counts": dict(judge_1),
        "judge_2_primary_counts": dict(judge_2),
        "primary_agreement_count": agreement_count,
        "primary_agreement_rate": round(agreement_count / n, 6) if n else 0.0,
        "cohen_kappa": round(kappa, 6) if kappa is not None else None,
        "reasoning_policy_mismatch_rate": round(
            _mean(float(row.get("reasoning_policy_mismatch_score", 0.0)) for row in rows),
            6,
        ),
        "policy_trajectory_mismatch_rate": round(
            _mean(float(row.get("policy_trajectory_mismatch_score", 0.0)) for row in rows),
            6,
        ),
        "reasoning_policy_mismatch_agreement_rate": round(
            _mean(
                float(bool(row.get("reasoning_policy_mismatch_agreement")))
                for row in rows
            ),
            6,
        ),
        "policy_trajectory_mismatch_agreement_rate": round(
            _mean(
                float(bool(row.get("policy_trajectory_mismatch_agreement")))
                for row in rows
            ),
            6,
        ),
        "mean_judge_confidence": round(
            _mean(float(row.get("mean_confidence", 0.0)) for row in rows),
            4,
        ),
    }


def aggregate_paired_records(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    by_model: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_condition: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    by_model_condition: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)

    for row in rows:
        model = str(row.get("model_name", "unknown"))
        condition = str(row.get("condition", "unknown"))
        by_model[model].append(row)
        by_condition[condition].append(row)
        by_model_condition[(model, condition)].append(row)

    return {
        "overall": _group_summary(rows),
        "by_model": {key: _group_summary(value) for key, value in sorted(by_model.items())},
        "by_condition": {
            key: _group_summary(value) for key, value in sorted(by_condition.items())
        },
        "by_model_condition": {
            f"{key[0]}__{key[1]}": _group_summary(value)
            for key, value in sorted(by_model_condition.items())
        },
    }


def write_paired_jsonl(path: str, rows: Sequence[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_distribution_csv(path: str, aggregation: Mapping[str, Any]) -> None:
    fields = [
        "group_level",
        "model",
        "condition",
        "failure_mode",
        "averaged_count",
        "rate_all_items",
        "rate_attributable",
        "any_mode_count",
        "any_mode_rate_all_items",
        "paired_item_count",
    ]
    group_rows: List[Tuple[str, str, str, Mapping[str, Any]]] = [
        ("overall", "ALL", "ALL", aggregation.get("overall", {}))
    ]
    group_rows.extend(
        ("model", model, "ALL", summary)
        for model, summary in aggregation.get("by_model", {}).items()
    )
    group_rows.extend(
        ("condition", "ALL", condition, summary)
        for condition, summary in aggregation.get("by_condition", {}).items()
    )
    for key, summary in aggregation.get("by_model_condition", {}).items():
        model, condition = key.split("__", 1)
        group_rows.append(("model_condition", model, condition, summary))

    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for level, model, condition, summary in group_rows:
            for label in FAILURE_MODES:
                writer.writerow(
                    {
                        "group_level": level,
                        "model": model,
                        "condition": condition,
                        "failure_mode": label,
                        "averaged_count": summary.get("averaged_primary_counts", {}).get(label, 0.0),
                        "rate_all_items": summary.get(
                            "averaged_primary_rates_all_items", {}
                        ).get(label, 0.0),
                        "rate_attributable": summary.get(
                            "averaged_primary_rates_attributable", {}
                        ).get(label, ""),
                        "any_mode_count": summary.get(
                            "averaged_any_failure_mode_counts", {}
                        ).get(label, 0.0),
                        "any_mode_rate_all_items": summary.get(
                            "averaged_any_failure_mode_rates_all_items", {}
                        ).get(label, 0.0),
                        "paired_item_count": summary.get("paired_item_count", 0),
                    }
                )


def _iter_group_rows(
    aggregation: Mapping[str, Any]
) -> List[Tuple[str, str, str, Mapping[str, Any]]]:
    rows: List[Tuple[str, str, str, Mapping[str, Any]]] = [
        ("overall", "ALL", "ALL", aggregation.get("overall", {}))
    ]
    rows.extend(
        ("model", model, "ALL", summary)
        for model, summary in aggregation.get("by_model", {}).items()
    )
    rows.extend(
        ("condition", "ALL", condition, summary)
        for condition, summary in aggregation.get("by_condition", {}).items()
    )
    for key, summary in aggregation.get("by_model_condition", {}).items():
        model, condition = key.split("__", 1)
        rows.append(("model_condition", model, condition, summary))
    return rows


def write_attribution_csv(path: str, aggregation: Mapping[str, Any]) -> None:
    fields = [
        "group_level",
        "model",
        "condition",
        "attribution_status",
        "averaged_count",
        "rate",
        "paired_item_count",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for level, model, condition, summary in _iter_group_rows(aggregation):
            for status in ATTRIBUTION_STATUSES:
                writer.writerow(
                    {
                        "group_level": level,
                        "model": model,
                        "condition": condition,
                        "attribution_status": status,
                        "averaged_count": summary.get(
                            "averaged_attribution_status_counts", {}
                        ).get(status, 0.0),
                        "rate": summary.get(
                            "averaged_attribution_status_rates", {}
                        ).get(status, 0.0),
                        "paired_item_count": summary.get("paired_item_count", 0),
                    }
                )


def write_contextual_contributors_csv(
    path: str, aggregation: Mapping[str, Any]
) -> None:
    fields = [
        "group_level",
        "model",
        "condition",
        "contextual_contributor",
        "averaged_count",
        "rate_all_items",
        "paired_item_count",
    ]
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for level, model, condition, summary in _iter_group_rows(aggregation):
            for contributor in CONTEXTUAL_CONTRIBUTORS:
                writer.writerow(
                    {
                        "group_level": level,
                        "model": model,
                        "condition": condition,
                        "contextual_contributor": contributor,
                        "averaged_count": summary.get(
                            "averaged_contextual_contributor_counts", {}
                        ).get(contributor, 0.0),
                        "rate_all_items": summary.get(
                            "averaged_contextual_contributor_rates_all_items", {}
                        ).get(contributor, 0.0),
                        "paired_item_count": summary.get("paired_item_count", 0),
                    }
                )
