#!/usr/bin/env python3
"""Replay OF/OPF strategies over fixed supply seeds and build the main table."""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from wac_programmatic import (  # noqa: E402
    AgentSubmission,
    WACProgrammaticEnv,
    build_supply_list,
    default_agent_profiles,
)


DEFAULT_OF = PROJECT_ROOT / "log" / "batch_032_no_opp_info_c_med_20days"
DEFAULT_OPF = PROJECT_ROOT / "log" / "batch_031_full_code_access_c_med_20days"
DEFAULT_OUTPUT = PROJECT_ROOT / "compare_result" / "main_table"
DEFAULT_SEEDS = (10, 42, 98, 197, 666)
META_ROUNDS = (2, 3)
EPISODE_DAYS = 20
SCENARIO = "medium"


def load_single_record(path: Path):
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        if not payload or not isinstance(payload[0], dict):
            raise ValueError("expected a non-empty JSON list containing an object")
        return payload[0]
    if isinstance(payload, dict):
        return payload
    raise ValueError("expected a JSON object or list containing an object")


def load_model_map(exp_dir: Path):
    with (exp_dir / "backend_config.json").open(encoding="utf-8") as handle:
        config = json.load(handle)
    return {
        role: str(spec.get("model", "")).strip()
        for role, spec in config.items()
        if isinstance(spec, dict) and str(spec.get("model", "")).strip()
    }


def replay_batch(feedback, batch_dir, seeds, env, profiles):
    rows = []
    errors = []
    expected_roles = [profile.agent_id for profile in profiles]

    if not batch_dir.is_dir():
        raise FileNotFoundError(f"Batch directory not found: {batch_dir}")

    for exp_dir in sorted(batch_dir.glob("exp_*")):
        if not exp_dir.is_dir():
            continue
        try:
            model_map = load_model_map(exp_dir)
        except Exception as exc:
            errors.append({"feedback": feedback, "exp_id": exp_dir.name, "meta_round": "", "seed": "", "error": f"backend_config: {exc}"})
            continue

        for meta_round in META_ROUNDS:
            source_path = exp_dir / f"meta_round_{meta_round}.json"
            try:
                source = load_single_record(source_path)
                agents = source.get("agents", [])
                by_role = {agent.get("agent_id"): agent for agent in agents if isinstance(agent, dict)}
                missing = [role for role in expected_roles if role not in by_role]
                if missing:
                    raise ValueError(f"missing agents: {', '.join(missing)}")
                submissions = []
                for role in expected_roles:
                    code = str(by_role[role].get("strategy_code", "") or "")
                    if not code.strip():
                        raise ValueError(f"empty strategy_code for {role}")
                    submissions.append(AgentSubmission(role, "", code))
            except Exception as exc:
                errors.append({"feedback": feedback, "exp_id": exp_dir.name, "meta_round": meta_round, "seed": "", "error": f"source: {exc}"})
                continue

            for seed in seeds:
                try:
                    result = env.run_episode(
                        profiles,
                        submissions,
                        build_supply_list(SCENARIO, EPISODE_DAYS, seed),
                    )
                    for agent in result["agents"]:
                        role = agent["agent_id"]
                        metrics = agent.get("metrics") or {}
                        survival = float(metrics["survival_days"])
                        final_hp = float(metrics["final_hp"])
                        trace_errors = [
                            item.get("error") for item in agent.get("daily_trace", [])
                            if item.get("error") is not None
                        ]
                        if trace_errors:
                            raise RuntimeError(f"{role} strategy error: {trace_errors[0]}")
                        rows.append({
                            "feedback": feedback,
                            "batch": batch_dir.name,
                            "exp_id": exp_dir.name,
                            "meta_round": meta_round,
                            "seed": seed,
                            "role": role,
                            "model": model_map.get(role, "Unknown Model"),
                            "survival_days": survival,
                            "final_hp": final_hp,
                            "dead": int(final_hp <= 0),
                        })
                except Exception as exc:
                    errors.append({"feedback": feedback, "exp_id": exp_dir.name, "meta_round": meta_round, "seed": seed, "error": f"replay: {exc}"})

    return rows, errors


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["feedback"], row["model"])].append(row)

    stats = {}
    for key, items in grouped.items():
        role_values = defaultdict(list)
        for item in items:
            role_values[item["role"]].append(float(item["survival_days"]))
        role_means = [sum(values) / len(values) for values in role_values.values()]
        wac_score = 100.0 * (sum(role_means) / len(role_means)) / EPISODE_DAYS
        mortality = 100.0 * sum(int(item["dead"]) for item in items) / len(items)
        stats[key] = {"wac_score": wac_score, "mortality": mortality, "n": len(items)}

    models = sorted({model for _, model in stats})
    table = []
    for model in models:
        of = stats.get(("OF", model))
        opf = stats.get(("OPF", model))
        if of is None or opf is None:
            continue
        table.append({
            "Model": model,
            "OF WACScore": round(of["wac_score"], 2),
            "OF Mortality (%)": round(of["mortality"], 2),
            "OPF WACScore": round(opf["wac_score"], 2),
            "OPF Mortality (%)": round(opf["mortality"], 2),
            "Δ Survival": round(opf["wac_score"] - of["wac_score"], 2),
            "Δ Mortality (pp)": round(opf["mortality"] - of["mortality"], 2),
        })
    table.sort(key=lambda row: row["OPF WACScore"], reverse=True)
    return table


def write_csv(path, rows, fieldnames=None):
    if fieldnames is None:
        fieldnames = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_table_png(path, rows):
    headers = list(rows[0])
    display_headers = [
        "Model", "OF\nWACScore", "OF\nMortality", "OPF\nWACScore",
        "OPF\nMortality", "Delta\nSurvival", "Delta\nMortality",
    ]
    cells = []
    for row in rows:
        cells.append([
            row["Model"], f'{row["OF WACScore"]:.2f}', f'{row["OF Mortality (%)"]:.2f}%',
            f'{row["OPF WACScore"]:.2f}', f'{row["OPF Mortality (%)"]:.2f}%',
            f'{row["Δ Survival"]:+.2f}', f'{row["Δ Mortality (pp)"]:+.2f} pp',
        ])
    fig, ax = plt.subplots(figsize=(14, max(3.0, 0.58 * (len(rows) + 2))))
    ax.axis("off")
    table = ax.table(cellText=cells, colLabels=display_headers, cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.55)
    for col in range(len(headers)):
        table[(0, col)].set_facecolor("#D9EAF7")
        table[(0, col)].set_text_props(weight="bold")
    ax.set_title("Outcome Feedback vs. Outcome-and-Policy Feedback", fontsize=14, pad=14)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--of-dir", type=Path, default=DEFAULT_OF)
    parser.add_argument("--opf-dir", type=Path, default=DEFAULT_OPF)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    profiles = default_agent_profiles()
    env = WACProgrammaticEnv(episode_days=EPISODE_DAYS)
    all_rows, all_errors = [], []

    batch_specs = (("OF", args.of_dir), ("OPF", args.opf_dir))
    for feedback, batch_dir in batch_specs:
        rows, errors = replay_batch(feedback, batch_dir, args.seeds, env, profiles)
        all_rows.extend(rows)
        all_errors.extend(errors)

    table_rows = summarize(all_rows)
    if not table_rows:
        raise SystemExit("No paired OF/OPF model results were produced; inspect replay_errors.csv")

    write_csv(args.output_dir / "main_table.csv", table_rows)
    write_csv(args.output_dir / "replay_details.csv", all_rows)
    write_csv(
        args.output_dir / "replay_errors.csv",
        all_errors,
        ["feedback", "exp_id", "meta_round", "seed", "error"],
    )
    write_table_png(args.output_dir / "main_table.png", table_rows)
    print(f"Wrote {len(all_rows)} valid agent replays and {len(all_errors)} errors to {args.output_dir}")


if __name__ == "__main__":
    main()
