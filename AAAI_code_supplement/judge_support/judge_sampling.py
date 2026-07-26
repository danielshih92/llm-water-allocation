from collections import defaultdict, deque
from typing import Any, Dict, List, Tuple


def stratified_sample_items(items: List[Dict[str, Any]], max_items: int) -> List[Dict[str, Any]]:
    """Round-robin stratified sampling by condition and admission/outcome status."""
    if max_items <= 0 or len(items) <= max_items:
        return items

    buckets: Dict[Tuple[str, int, int], deque] = defaultdict(deque)
    for item in items:
        status = item.get("submission_status", {})
        key = (
            str(item.get("condition", "unknown")),
            int(status.get("admitted", 0)),
            int(status.get("outcome_valid", 0)),
        )
        buckets[key].append(item)

    ordered_keys = sorted(buckets.keys())
    sampled: List[Dict[str, Any]] = []

    while len(sampled) < max_items:
        progressed = False
        for key in ordered_keys:
            if len(sampled) >= max_items:
                break
            if buckets[key]:
                sampled.append(buckets[key].popleft())
                progressed = True
        if not progressed:
            break

    return sampled
