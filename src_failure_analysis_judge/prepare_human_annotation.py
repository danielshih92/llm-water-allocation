#!/usr/bin/env python3
"""Prepare a blinded, reproducible human-validation subset.

The public packet stores the exact prompt supplied to the LLM judges. A
separate private mapping preserves model, condition, source, and LLM-judge
labels for later agreement analysis and must not be shared with annotators.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_JUDGE_DIR = PROJECT_ROOT / "src_judge"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_JUDGE_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_JUDGE_DIR))

from judge_core import scan_judge_items

from src_failure_analysis_judge.prompt import build_failure_prompt
from src_failure_analysis_judge.taxonomy import (
    ATTRIBUTION_STATUSES,
    FAILURE_MODES,
    PROMPT_VERSION,
)


DEFAULT_INPUT_DIR = (
    PROJECT_ROOT / "judge_result" / "failure_analysis_full_gpt_deepseek_v3"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "appendix" / "human"
DEFAULT_LOG_DIR = PROJECT_ROOT / "log"
MODEL_ORDER = (
    "gemini-3.5-flash",
    "claude-sonnet-5",
    "gpt-5.4",
    "deepseek-v4-flash",
    "gpt-5.4-nano",
)
MODEL_NAME_LEAK_PATTERNS = (
    "gemini",
    "claude",
    "gpt",
    "deepseek",
    "gemini-3.5-flash",
    "gemini 3.5 flash",
    "claude-sonnet-5",
    "claude sonnet 5",
    "gpt-5.4",
    "gpt 5.4",
    "deepseek-v4-flash",
    "deepseek v4 flash",
    "gpt-5.4-nano",
    "gpt 5.4 nano",
)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl_by_id(path: Path) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if isinstance(row, dict) and row.get("item_id"):
                rows[str(row["item_id"])] = row
    return rows


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def is_death_item(item: Mapping[str, Any]) -> bool:
    trajectory = item.get("trajectory", {})
    summary = trajectory.get("evidence_summary", {}) if isinstance(trajectory, dict) else {}
    return bool(
        item.get("is_valid_item", False)
        and isinstance(summary, dict)
        and summary.get("final_status") == "dead"
    )


def prompt_contains_model_name(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(pattern in lowered for pattern in MODEL_NAME_LEAK_PATTERNS)


def judge_payload(record: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = record.get("judge", {})
    return payload if isinstance(payload, dict) else {}


def compact_judge_labels(record: Mapping[str, Any]) -> Dict[str, Any]:
    payload = judge_payload(record)
    primary = payload.get("primary_failure_mode")
    contributing = payload.get("contributing_failure_modes", [])
    modes = []
    if primary in FAILURE_MODES:
        modes.append(str(primary))
    if isinstance(contributing, list):
        modes.extend(
            str(label)
            for label in contributing
            if label in FAILURE_MODES and label not in modes
        )
    return {
        "attribution_status": payload.get("attribution_status"),
        "primary_failure_mode": primary,
        "contributing_failure_modes": contributing,
        "any_failure_modes": modes,
    }


def select_cases(
    items: Iterable[Dict[str, Any]],
    paired_ids: set[str],
    conditions: Sequence[str],
    per_model_condition: int,
    seed: int,
) -> Tuple[List[Tuple[Dict[str, Any], str]], Dict[str, int]]:
    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for item in items:
        item_id = str(item.get("item_id", ""))
        model = str(item.get("model_name", ""))
        condition = str(item.get("condition", ""))
        if (
            item_id in paired_ids
            and model in MODEL_ORDER
            and condition in conditions
            and is_death_item(item)
        ):
            buckets[(model, condition)].append(item)

    selected: List[Tuple[Dict[str, Any], str]] = []
    skipped_for_leak: Dict[str, int] = {}
    for model_index, model in enumerate(MODEL_ORDER):
        for condition_index, condition in enumerate(conditions):
            key = (model, condition)
            candidates = sorted(
                buckets.get(key, []), key=lambda row: str(row.get("item_id", ""))
            )
            rng = random.Random(seed + model_index * 101 + condition_index * 1009)
            rng.shuffle(candidates)
            chosen: List[Tuple[Dict[str, Any], str]] = []
            leak_count = 0
            for item in candidates:
                prompt = build_failure_prompt(item, blind_model_names=True)
                if prompt_contains_model_name(prompt):
                    leak_count += 1
                    continue
                chosen.append((item, prompt))
                if len(chosen) == per_model_condition:
                    break
            if len(chosen) != per_model_condition:
                raise ValueError(
                    f"Need {per_model_condition} blinded cases for {model}/{condition}, "
                    f"but found {len(chosen)} after model-name leakage checks."
                )
            selected.extend(chosen)
            skipped_for_leak[f"{model}::{condition}"] = leak_count

    presentation_rng = random.Random(seed + 999_983)
    presentation_rng.shuffle(selected)
    return selected, skipped_for_leak


def response_template(case_ids: Sequence[str]) -> Dict[str, Any]:
    return {
        "annotator_id": "",
        "annotation_version": "wac-human-failure-validation-v1",
        "annotations": [
            {
                "case_id": case_id,
                "attribution_status": None,
                "failure_modes": [],
                "confidence": None,
                "notes": "",
            }
            for case_id in case_ids
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    parser.add_argument("--seed", type=int, default=2027)
    parser.add_argument("--per-model-condition", type=int, default=5)
    args = parser.parse_args()
    if args.per_model_condition <= 0:
        parser.error("--per-model-condition must be positive")
    return args


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = load_json(input_dir / "failure_run_config.json")
    mappings = config.get("batch_condition_mapping", [])
    batches = [str(row["batch"]) for row in mappings if isinstance(row, dict)]
    conditions = [str(row["condition"]) for row in mappings if isinstance(row, dict)]
    if len(batches) != 2 or set(conditions) != {"OF", "OPF"}:
        raise ValueError("Expected one OF and one OPF batch in failure_run_config.json")

    paired = load_jsonl_by_id(input_dir / "paired_judge_records.jsonl")
    judge_1 = load_jsonl_by_id(input_dir / "judge_1_records.jsonl")
    judge_2 = load_jsonl_by_id(input_dir / "judge_2_records.jsonl")
    paired_ids = set(paired)
    items = scan_judge_items(
        log_dir=str(args.log_dir.resolve()),
        batches=batches,
        condition_labels=conditions,
        exp_start=1,
        exp_end=120,
    )
    selected, skipped_for_leak = select_cases(
        items=items,
        paired_ids=paired_ids,
        conditions=conditions,
        per_model_condition=args.per_model_condition,
        seed=args.seed,
    )

    public_cases: List[Dict[str, Any]] = []
    private_mapping: List[Dict[str, Any]] = []
    stratum_counts: Counter[Tuple[str, str]] = Counter()
    for index, (item, prompt) in enumerate(selected, start=1):
        case_id = f"case_{index:03d}"
        item_id = str(item["item_id"])
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        public_cases.append(
            {
                "case_id": case_id,
                "prompt_version": PROMPT_VERSION,
                "prompt_sha256": prompt_hash,
                "llm_judge_prompt": prompt,
            }
        )
        model = str(item["model_name"])
        condition = str(item["condition"])
        stratum_counts[(model, condition)] += 1
        private_mapping.append(
            {
                "case_id": case_id,
                "source_item_id": item_id,
                "batch_name": item.get("batch_name"),
                "condition": condition,
                "experiment_id": item.get("experiment_id"),
                "meta_round_id": item.get("meta_round_id"),
                "agent_id": item.get("agent_id"),
                "model_name": model,
                "prompt_sha256": prompt_hash,
                "judge_1": compact_judge_labels(judge_1[item_id]),
                "judge_2": compact_judge_labels(judge_2[item_id]),
            }
        )

    case_ids = [row["case_id"] for row in public_cases]
    write_json(
        output_dir / "human_annotation_cases.json",
        {
            "annotation_version": "wac-human-failure-validation-v1",
            "prompt_version": PROMPT_VERSION,
            "case_count": len(public_cases),
            "cases": public_cases,
        },
    )
    write_json(
        output_dir / "annotator_1_response.json", response_template(case_ids)
    )
    write_json(
        output_dir / "annotator_2_response.json", response_template(case_ids)
    )
    write_json(
        output_dir / "PRIVATE_case_mapping_do_not_share.json",
        {
            "warning": "DO NOT SHARE WITH ANNOTATORS.",
            "cases": private_mapping,
        },
    )
    write_json(
        output_dir / "sampling_manifest.json",
        {
            "annotation_version": "wac-human-failure-validation-v1",
            "source_result_dir": str(input_dir),
            "sampling_seed": args.seed,
            "sampling_rule": (
                "Five paired death cases per model-condition stratum, sampled "
                "without consulting either judge's labels; presentation order "
                "is independently shuffled."
            ),
            "case_count": len(public_cases),
            "model_count": len(MODEL_ORDER),
            "conditions": sorted(set(conditions)),
            "per_model_condition": args.per_model_condition,
            "stratum_counts_private_check": {
                f"{model}::{condition}": stratum_counts[(model, condition)]
                for model in MODEL_ORDER
                for condition in sorted(set(conditions))
            },
            "model_name_leak_candidates_skipped": skipped_for_leak,
            "allowed_attribution_statuses": ATTRIBUTION_STATUSES,
            "allowed_failure_modes": FAILURE_MODES,
            "all_cases_have_paired_llm_judgments": all(
                row["source_item_id"] in paired_ids for row in private_mapping
            ),
        },
    )

    print(f"Output directory: {output_dir}")
    print(f"Cases: {len(public_cases)}")
    for model in MODEL_ORDER:
        counts = ", ".join(
            f"{condition}={stratum_counts[(model, condition)]}"
            for condition in sorted(set(conditions))
        )
        print(f"{model}: {counts}")


if __name__ == "__main__":
    main()
