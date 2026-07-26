#!/usr/bin/env python3
"""Summarize aggregate frozen-opponent survival gains from paired replays.

Replay seeds are averaged within each focal policy first. The five agents are
then kept together as one experiment cluster, and OF/OPF confidence intervals
are obtained by jointly resampling matched experiment IDs.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DEFAULT_INPUT = PROJECT_ROOT / "outputs" / "opponent_modeling" / "frozen_opponent_pairs.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "opponent_modeling"
DEFAULT_BOOTSTRAP_SEED = 20260714
DEFAULT_BOOTSTRAP_REPLICATES = 50_000
CONDITIONS = ("OF", "OPF")


def percentile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot compute a percentile of an empty sequence")
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def load_policy_means(path: Path) -> Tuple[Dict[Tuple[str, str], float], Dict[str, int], int]:
    grouped: Dict[Tuple[str, str, str], List[float]] = defaultdict(list)
    seed_counts: Dict[str, int] = defaultdict(int)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            condition = row["feedback"]
            if condition not in CONDITIONS:
                continue
            key = (condition, row["experiment_id"], row["focal_agent"])
            grouped[key].append(float(row["survival_gain"]))
            seed_counts[condition] += 1

    experiment_values: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for (condition, experiment_id, _focal_agent), values in grouped.items():
        experiment_values[(condition, experiment_id)].append(statistics.mean(values))

    cluster_means: Dict[Tuple[str, str], float] = {}
    for key, values in experiment_values.items():
        cluster_means[key] = statistics.mean(values)
    return cluster_means, dict(seed_counts), len(grouped)


def summarize(
    cluster_means: Mapping[Tuple[str, str], float],
    seed_counts: Mapping[str, int],
    policy_count: int,
    bootstrap_seed: int,
    bootstrap_replicates: int,
) -> List[Dict[str, object]]:
    ids_by_condition = {
        condition: {experiment_id for current, experiment_id in cluster_means if current == condition}
        for condition in CONDITIONS
    }
    if ids_by_condition["OF"] != ids_by_condition["OPF"]:
        raise ValueError("OF and OPF do not contain the same experiment IDs")
    experiment_ids = sorted(ids_by_condition["OF"])
    if not experiment_ids:
        raise ValueError("no matched experiment clusters found")

    estimates = {
        condition: statistics.mean(cluster_means[(condition, experiment_id)]
                                   for experiment_id in experiment_ids)
        for condition in CONDITIONS
    }
    estimates["OPF-minus-OF"] = estimates["OPF"] - estimates["OF"]

    rng = random.Random(f"{bootstrap_seed}:aggregate-fosg")
    samples: Dict[str, List[float]] = {
        "OF": [], "OPF": [], "OPF-minus-OF": []
    }
    for _ in range(bootstrap_replicates):
        sampled_ids = [rng.choice(experiment_ids) for _ in experiment_ids]
        condition_estimates = {
            condition: statistics.mean(
                cluster_means[(condition, experiment_id)]
                for experiment_id in sampled_ids
            )
            for condition in CONDITIONS
        }
        samples["OF"].append(condition_estimates["OF"])
        samples["OPF"].append(condition_estimates["OPF"])
        samples["OPF-minus-OF"].append(
            condition_estimates["OPF"] - condition_estimates["OF"]
        )

    output: List[Dict[str, object]] = []
    policy_counts = {
        condition: sum(
            1 for current, _experiment_id in cluster_means if current == condition
        ) * 5
        for condition in CONDITIONS
    }
    for label in ("OF", "OPF", "OPF-minus-OF"):
        valid_seed_replays = (
            seed_counts["OF"] + seed_counts["OPF"]
            if label == "OPF-minus-OF"
            else seed_counts[label]
        )
        focal_policy_count = (
            policy_count
            if label == "OPF-minus-OF"
            else policy_counts[label]
        )
        output.append({
            "condition_or_contrast": label,
            "fosg_days": estimates[label],
            "ci95_low": percentile(samples[label], 0.025),
            "ci95_high": percentile(samples[label], 0.975),
            "experiment_count": len(experiment_ids),
            "focal_policy_count": focal_policy_count,
            "valid_seed_replays": valid_seed_replays,
            "bootstrap_replicates": bootstrap_replicates,
            "bootstrap_seed": bootstrap_seed,
        })
    return output


def write_outputs(output_dir: Path, rows: Iterable[Mapping[str, object]]) -> None:
    materialized = list(rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "aggregate_fosg.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(materialized[0]))
        writer.writeheader()
        writer.writerows(materialized)
    (output_dir / "aggregate_fosg.json").write_text(
        json.dumps(materialized, indent=2), encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bootstrap-seed", type=int, default=DEFAULT_BOOTSTRAP_SEED)
    parser.add_argument(
        "--bootstrap-replicates",
        type=int,
        default=DEFAULT_BOOTSTRAP_REPLICATES,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cluster_means, seed_counts, policy_count = load_policy_means(args.input)
    rows = summarize(
        cluster_means,
        seed_counts,
        policy_count,
        args.bootstrap_seed,
        args.bootstrap_replicates,
    )
    write_outputs(args.output_dir, rows)
    for row in rows:
        print(
            f"{row['condition_or_contrast']}: "
            f"{row['fosg_days']:.4f} "
            f"[{row['ci95_low']:.4f}, {row['ci95_high']:.4f}]"
        )


if __name__ == "__main__":
    main()
