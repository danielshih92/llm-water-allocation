#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
from typing import Dict, List, Tuple


META_ROUND_PATTERN = re.compile(r"^meta_round_(\d+)\.json$")


def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        if isinstance(value, str) and value.strip().upper() == "N/A":
            return default
        return float(value)
    except Exception:
        return default


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _iter_meta_round_files(exp_dir: str):
    for name in sorted(os.listdir(exp_dir)):
        match = META_ROUND_PATTERN.match(name)
        if not match:
            continue
        path = os.path.join(exp_dir, name)
        if os.path.isfile(path):
            yield int(match.group(1)), path


def _collect_round_records(batch_dir: str) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []

    for entry in sorted(os.listdir(batch_dir)):
        if not entry.startswith("exp_"):
            continue

        exp_dir = os.path.join(batch_dir, entry)
        if not os.path.isdir(exp_dir):
            continue

        for meta_round_id, meta_path in _iter_meta_round_files(exp_dir):
            try:
                with open(meta_path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
            except Exception:
                continue

            if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
                continue

            round_payload = payload[0]
            record_outcome_valid = int(_safe_float(round_payload.get("outcome_valid"), 0) or 0)
            agents = round_payload.get("agents", [])
            if not isinstance(agents, list):
                continue

            for agent in agents:
                if not isinstance(agent, dict):
                    continue

                generation_stats = agent.get("generation_stats", {})
                if not isinstance(generation_stats, dict):
                    generation_stats = {}

                admitted = int(
                    _safe_float(agent.get("admitted", generation_stats.get("admitted", 0)), 0)
                    or 0
                )
                outcome_valid = int(
                    _safe_float(agent.get("outcome_valid", record_outcome_valid), record_outcome_valid)
                    or 0
                )
                metrics = agent.get("metrics")
                if not isinstance(metrics, dict):
                    metrics = None

                records.append(
                    {
                        "exp_id": entry,
                        "meta_round_id": meta_round_id,
                        "admitted": admitted,
                        "outcome_valid": outcome_valid,
                        "performance_valid": bool(admitted == 1 and outcome_valid == 1 and metrics is not None),
                        "strategy_code": str(agent.get("strategy_code", "") or ""),
                        "survival_days": _safe_float(metrics.get("survival_days"), None) if metrics else None,
                        "final_hp": _safe_float(metrics.get("final_hp"), None) if metrics else None,
                        "average_bid": _safe_float(metrics.get("average_bid"), None) if metrics else None,
                        "opponent_awareness_score": _safe_float(metrics.get("opponent_awareness_score"), None) if metrics else None,
                        "strategy_complexity": _safe_float(metrics.get("strategy_complexity"), None) if metrics else None,
                    }
                )

    return records


def _mean_metric(records: List[Dict[str, object]], key: str):
    values = [
        _safe_float(row.get(key), None)
        for row in records
        if bool(row.get("performance_valid", False))
    ]
    values = [value for value in values if value is not None]
    if not values:
        return None
    return sum(values) / len(values)


def _format_number(value, decimals: int) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _format_percent(value, decimals: int) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def _mortality_rate(records: List[Dict[str, object]]):
    valid_records = [row for row in records if bool(row.get("performance_valid", False))]
    if not valid_records:
        return None

    deaths = 0
    for row in valid_records:
        final_hp = _safe_float(row.get("final_hp"), 1.0)
        if final_hp is not None and final_hp <= 0:
            deaths += 1
    return deaths / len(valid_records) * 100.0


def _batch_short_label(batch_name: str) -> str:
    match = re.search(r"batch_(\d+)", batch_name)
    prefix = match.group(1) if match else batch_name
    if "no_opp" in batch_name or "no-opponent" in batch_name:
        suffix = "noopp"
    elif "full_code" in batch_name:
        suffix = "full"
    else:
        suffix = ""
    return f"{prefix} {suffix}".strip()


def _trace_last_counts(records: List[Dict[str, object]]) -> str:
    trace_count = sum(
        1 for row in records if re.search(r"trace_history", str(row.get("strategy_code", "") or ""))
    )
    last_bid_count = sum(
        1 for row in records if re.search(r"last_bid", str(row.get("strategy_code", "") or ""))
    )
    return f"{trace_count} / {last_bid_count}"


def _build_comparison_rows(batch_specs: List[Tuple[str, str]]) -> List[Dict[str, str]]:
    records_by_batch: List[Tuple[str, List[Dict[str, object]]]] = []
    all_round_ids = set()

    for batch_name, batch_dir in batch_specs:
        records = _collect_round_records(batch_dir)
        records_by_batch.append((batch_name, records))
        all_round_ids.update(int(row.get("meta_round_id", 0) or 0) for row in records)

    records_by_batch = sorted(records_by_batch, key=lambda item: _batch_short_label(item[0]))

    rows: List[Dict[str, str]] = []
    for round_id in sorted(all_round_ids):
        for batch_name, records in records_by_batch:
            round_records = [
                row for row in records if int(row.get("meta_round_id", 0) or 0) == round_id
            ]
            if not round_records:
                continue

            mortality_rate = _mortality_rate(round_records)
            rows.append(
                {
                    "round": f"R{round_id}",
                    "batch": _batch_short_label(batch_name),
                    "avg survival": _format_number(_mean_metric(round_records, "survival_days"), 2),
                    "mortality rate": _format_percent(mortality_rate, 1),
                    "avg bid": _format_number(_mean_metric(round_records, "average_bid"), 1),
                    "opp awareness": _format_number(
                        _mean_metric(round_records, "opponent_awareness_score"),
                        2,
                    ),
                    "complexity": _format_number(_mean_metric(round_records, "strategy_complexity"), 1),
                    "trace / last bid": _trace_last_counts(round_records),
                }
            )

    return rows


def _write_csv(rows: List[Dict[str, str]], path: str) -> None:
    if not rows:
        return

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _estimate_col_widths(rows: List[Dict[str, str]]) -> List[float]:
    headers = list(rows[0].keys())
    lengths = []
    for header in headers:
        max_len = max([len(str(header))] + [len(str(row.get(header, ""))) for row in rows])
        lengths.append(max_len)
    total = float(sum(lengths)) or 1.0
    return [max(0.08, length / total) for length in lengths]


def _write_png(rows: List[Dict[str, str]], path: str, title: str) -> bool:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        print(f"Skipping PNG output because matplotlib is unavailable: {exc}")
        return False

    if not rows:
        return False

    headers = list(rows[0].keys())
    cell_text = [[row.get(header, "") for header in headers] for row in rows]
    fig_height = max(3.0, 0.55 * (len(rows) + 1))
    fig_width = 12.0
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")
    table = ax.table(
        cellText=cell_text,
        colLabels=headers,
        cellLoc="center",
        loc="center",
        colWidths=_estimate_col_widths(rows),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.4)
    ax.set_title(title, fontsize=12, pad=12)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare round-level summary tables for two batches.")
    parser.add_argument("--log-dir", type=str, default="log", help="Root log directory.")
    parser.add_argument("--batch-a", type=str, required=True, help="First batch folder name.")
    parser.add_argument("--batch-b", type=str, required=True, help="Second batch folder name.")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output folder. Defaults to PROJECT_ROOT/compare_result.",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="batch_round_comparison_table",
        help="Output filename prefix for CSV and PNG.",
    )
    args = parser.parse_args()

    batch_a_dir = os.path.join(args.log_dir, args.batch_a)
    batch_b_dir = os.path.join(args.log_dir, args.batch_b)
    if not os.path.isdir(batch_a_dir):
        raise SystemExit(f"batch-a not found: {batch_a_dir}")
    if not os.path.isdir(batch_b_dir):
        raise SystemExit(f"batch-b not found: {batch_b_dir}")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = args.output_dir or os.path.join(project_root, "compare_result")
    _ensure_dir(output_dir)

    rows = _build_comparison_rows(
        [
            (args.batch_a, batch_a_dir),
            (args.batch_b, batch_b_dir),
        ]
    )
    if not rows:
        raise SystemExit("No comparable meta-round records found.")

    csv_path = os.path.join(output_dir, f"{args.output_prefix}.csv")
    png_path = os.path.join(output_dir, f"{args.output_prefix}.png")
    _write_csv(rows, csv_path)
    wrote_png = _write_png(rows, png_path, "Batch Round Comparison Summary")

    print(f"Wrote CSV: {csv_path}")
    if wrote_png:
        print(f"Wrote PNG: {png_path}")


if __name__ == "__main__":
    main()
