#!/usr/bin/env python3
"""Rebuild the homogeneous-population appendix plot from packaged summaries."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = (
    ROOT
    / "reference_outputs"
    / "homogeneous_populations"
    / "five_model_test_v2_details.csv"
)
DEFAULT_OUTPUT = ROOT / "outputs" / "homogeneous_populations"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    grouped = defaultdict(list)
    for row in rows:
        round_id = int(str(row["Meta Round"]).replace("MR", ""))
        grouped[row["Model"]].append(
            (
                round_id,
                float(row["Avg Survival"]),
                float(row["Mortality Rate"].rstrip("%")),
            )
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharex=True)
    for model, values in sorted(grouped.items()):
        values.sort()
        rounds = [item[0] for item in values]
        axes[0].plot(rounds, [item[1] for item in values], marker="o", label=model)
        axes[1].plot(rounds, [item[2] for item in values], marker="o", label=model)
    axes[0].set_ylabel("Average survival days")
    axes[1].set_ylabel("Mortality (%)")
    for axis in axes:
        axis.set_xlabel("Meta-round")
        axis.set_xticks([1, 2, 3])
        axis.grid(alpha=0.25)
    axes[1].legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    path = args.output_dir / "homogeneous_population_trends.png"
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
