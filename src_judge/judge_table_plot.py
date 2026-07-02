import os
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _save_markdown_table(df: pd.DataFrame, path: str) -> None:
    headers = list(df.columns)
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join([str(row[col]) for col in headers]) + " |")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def _save_table_png(df: pd.DataFrame, path: str, title: str) -> None:
    fig_height = max(2.8, 0.44 * (len(df) + 1))
    fig, ax = plt.subplots(figsize=(12, fig_height))
    ax.axis("off")
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.3)
    ax.set_title(title, fontsize=12, pad=10)
    plt.tight_layout()
    plt.savefig(path, dpi=300)
    plt.close(fig)


def _to_pct(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value) * 100.0:.2f}%"
    except Exception:
        return "N/A"


def _to_score(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.3f}"
    except Exception:
        return "N/A"


def _summary_rows(summary: Dict[str, Dict[str, Any]], key_name: str) -> List[Dict[str, Any]]:
    rows = []
    for key, stats in sorted(summary.items()):
        avg = stats.get("avg_scores", {})
        rows.append(
            {
                key_name: key,
                "Count": int(stats.get("count", 0)),
                "Valid Item Rate": _to_pct(stats.get("valid_item_rate")),
                "Strategy Quality": _to_score(avg.get("strategy_quality_score")),
                "Survival Risk": _to_score(avg.get("survival_risk_management_score")),
                "Budget Efficiency": _to_score(avg.get("budget_efficiency_score")),
                "Opponent/Supply Adaptation": _to_score(avg.get("opponent_supply_adaptation_score")),
                "Temporal Planning": _to_score(avg.get("temporal_planning_score")),
                "Reasoning-Code-Trace": _to_score(avg.get("reasoning_code_trace_consistency_score")),
                "Implementation Quality": _to_score(avg.get("implementation_quality_score")),
                "Judge Confidence": _to_score(avg.get("judge_confidence")),
            }
        )
    return rows


def generate_judge_tables(aggregation: Dict[str, Any], output_dir: str) -> None:
    _ensure_dir(output_dir)

    model_rows = _summary_rows(aggregation.get("by_model", {}), "Model")
    if model_rows:
        model_df = pd.DataFrame(model_rows)
        _save_markdown_table(model_df, os.path.join(output_dir, "judge_model_summary_table.md"))
        _save_table_png(model_df, os.path.join(output_dir, "judge_model_summary_table.png"), "Judge Summary by Model")

    condition_rows = _summary_rows(aggregation.get("by_condition", {}), "Condition")
    if condition_rows:
        condition_df = pd.DataFrame(condition_rows)
        _save_markdown_table(condition_df, os.path.join(output_dir, "judge_condition_summary_table.md"))
        _save_table_png(condition_df, os.path.join(output_dir, "judge_condition_summary_table.png"), "Judge Summary by Condition")

    mc_rows = _summary_rows(aggregation.get("by_model_condition", {}), "Model__Condition")
    if mc_rows:
        mc_df = pd.DataFrame(mc_rows)
        _save_markdown_table(mc_df, os.path.join(output_dir, "judge_model_condition_table.md"))
        _save_table_png(mc_df, os.path.join(output_dir, "judge_model_condition_table.png"), "Judge Summary by Model and Condition")
