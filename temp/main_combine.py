#!/usr/bin/env python3
"""Replay OF/OPF strategies over fixed supply seeds and build the main table.

Each replay unit is one (condition, experiment, meta-round, supply-seed) block.
A block is committed only when all five agent traces are valid.  ``--resume``
keeps complete blocks from replay_details.csv and reruns only missing or partial
blocks, which prevents a late agent failure from leaving biased partial data.
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
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
import wac_programmatic  # noqa: E402
from sandbox_executor import _execute_strategy_no_timeout, _static_check  # noqa: E402


DEFAULT_OF = PROJECT_ROOT / "log" / "batch_032_no_opp_info_c_med_20days"
DEFAULT_OPF = PROJECT_ROOT / "log" / "batch_031_full_code_access_c_med_20days"
DEFAULT_OUTPUT = PROJECT_ROOT / "compare_result" / "main_table"
DEFAULT_SEEDS = (10, 42, 98, 197, 666)
DEFAULT_META_ROUNDS = (2, 3)
DEFAULT_TABLE_META_ROUNDS = (2, 3)
EPISODE_DAYS = 20
SCENARIO = "medium"

DETAIL_FIELDS = [
    "feedback", "batch", "exp_id", "meta_round", "seed", "role", "model",
    "survival_days", "final_hp", "dead",
]
ERROR_FIELDS = [
    "feedback", "exp_id", "meta_round", "seed", "attempts", "error", "recorded_at",
]


def trusted_fast_execute_strategy(
    strategy_code, day_context, my_status, opponents_status=None, timeout_seconds=1.0,
):
    """Replay previously validated code without a subprocess per bid."""
    error = _static_check(strategy_code)
    if error:
        return 0.0, error
    return _execute_strategy_no_timeout(
        strategy_code, day_context, my_status, opponents_status
    )


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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


def read_csv(path):
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def block_key(row):
    return (
        str(row["feedback"]),
        str(row["exp_id"]),
        int(row["meta_round"]),
        int(row["seed"]),
    )


def exp_sort_value(exp_id):
    try:
        return int(str(exp_id).rsplit("_", 1)[1])
    except (IndexError, ValueError):
        return sys.maxsize


def row_sort_key(row, role_order):
    feedback_order = {"OF": 0, "OPF": 1}
    return (
        feedback_order.get(str(row["feedback"]), 99),
        exp_sort_value(row["exp_id"]),
        int(row["meta_round"]),
        int(row["seed"]),
        role_order.get(str(row["role"]), 99),
    )


def expected_blocks(batch_specs, seeds, meta_rounds):
    expected = set()
    for feedback, batch_dir in batch_specs:
        if not batch_dir.is_dir():
            raise FileNotFoundError(f"Batch directory not found: {batch_dir}")
        for exp_dir in sorted(batch_dir.glob("exp_*")):
            if exp_dir.is_dir():
                for meta_round in meta_rounds:
                    for seed in seeds:
                        expected.add((feedback, exp_dir.name, meta_round, seed))
    return expected


def retain_complete_blocks(rows, requested_keys, expected_roles):
    """Return only requested blocks containing every expected role exactly once."""
    grouped = defaultdict(list)
    invalid_rows = 0
    for row in rows:
        try:
            key = block_key(row)
        except (KeyError, TypeError, ValueError):
            invalid_rows += 1
            continue
        if key in requested_keys:
            grouped[key].append(row)
        else:
            invalid_rows += 1

    role_set = set(expected_roles)
    complete_rows = []
    complete_keys = set()
    partial_keys = set()
    for key, items in grouped.items():
        roles = [str(item.get("role", "")) for item in items]
        if len(items) == len(expected_roles) and set(roles) == role_set and len(set(roles)) == len(roles):
            complete_rows.extend(items)
            complete_keys.add(key)
        else:
            partial_keys.add(key)
    return complete_rows, complete_keys, partial_keys, invalid_rows


def load_submissions(exp_dir, meta_round, expected_roles):
    source = load_single_record(exp_dir / f"meta_round_{meta_round}.json")
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
    return submissions


def run_episode_block(feedback, batch_dir, exp_dir, meta_round, seed, env, profiles, model_map, submissions):
    """Build a complete five-row block in memory; never return partial rows."""
    expected_roles = [profile.agent_id for profile in profiles]
    result = env.run_episode(
        profiles,
        submissions,
        build_supply_list(SCENARIO, EPISODE_DAYS, seed),
    )
    agents = result.get("agents", [])
    by_role = {}
    for agent in agents:
        role = agent.get("agent_id")
        if role in by_role:
            raise ValueError(f"duplicate replay agent: {role}")
        by_role[role] = agent
    if set(by_role) != set(expected_roles):
        missing = sorted(set(expected_roles) - set(by_role))
        extra = sorted(set(by_role) - set(expected_roles))
        raise ValueError(f"invalid replay agents; missing={missing}, extra={extra}")

    # Validate all traces before constructing any output row.  A failure by the
    # fifth agent therefore cannot leave the first four agents in the dataset.
    for role in expected_roles:
        trace_errors = [
            item.get("error")
            for item in by_role[role].get("daily_trace", [])
            if isinstance(item, dict) and item.get("error") is not None
        ]
        if trace_errors:
            raise RuntimeError(f"{role} strategy error: {trace_errors[0]}")

    block_rows = []
    for role in expected_roles:
        metrics = by_role[role].get("metrics") or {}
        survival = float(metrics["survival_days"])
        final_hp = float(metrics["final_hp"])
        block_rows.append({
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
    return block_rows


def replay_one_block(
    feedback, batch_dir, exp_dir, meta_round, seed, env, profiles,
    model_map, submissions, max_attempts,
):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            block_rows = run_episode_block(
                feedback, batch_dir, exp_dir, meta_round, seed,
                env, profiles, model_map, submissions,
            )
        except Exception as exc:
            last_error = exc
            print(
                f"[{feedback} {exp_dir.name} MR{meta_round} seed={seed}] "
                f"attempt {attempt}/{max_attempts} failed: {exc}",
                flush=True,
            )
        else:
            print(
                f"[{feedback} {exp_dir.name} MR{meta_round} seed={seed}] "
                f"completed ({attempt} attempt{'s' if attempt != 1 else ''})",
                flush=True,
            )
            return block_rows, None
    return None, {
        "feedback": feedback,
        "exp_id": exp_dir.name,
        "meta_round": meta_round,
        "seed": seed,
        "attempts": max_attempts,
        "error": f"replay: {last_error}",
        "recorded_at": utc_now(),
    }


def replay_batch(
    feedback, batch_dir, seeds, meta_rounds, env, profiles, target_keys, max_attempts,
    workers=1, on_block_complete=None,
):
    rows = []
    errors = []
    expected_roles = [profile.agent_id for profile in profiles]

    for exp_dir in sorted(batch_dir.glob("exp_*")):
        if not exp_dir.is_dir():
            continue
        exp_targets = [key for key in target_keys if key[0] == feedback and key[1] == exp_dir.name]
        if not exp_targets:
            continue

        try:
            model_map = load_model_map(exp_dir)
        except Exception as exc:
            for _, _, meta_round, seed in sorted(exp_targets):
                errors.append({
                    "feedback": feedback, "exp_id": exp_dir.name, "meta_round": meta_round,
                    "seed": seed, "attempts": 0, "error": f"backend_config: {exc}",
                    "recorded_at": utc_now(),
                })
            continue

        for meta_round in meta_rounds:
            target_seeds = [
                seed for seed in seeds
                if (feedback, exp_dir.name, meta_round, seed) in target_keys
            ]
            if not target_seeds:
                continue
            try:
                submissions = load_submissions(exp_dir, meta_round, expected_roles)
            except Exception as exc:
                for seed in target_seeds:
                    errors.append({
                        "feedback": feedback, "exp_id": exp_dir.name, "meta_round": meta_round,
                        "seed": seed, "attempts": 0, "error": f"source: {exc}",
                        "recorded_at": utc_now(),
                    })
                continue

            with ThreadPoolExecutor(max_workers=min(workers, len(target_seeds))) as executor:
                futures = {
                    executor.submit(
                        replay_one_block,
                        feedback, batch_dir, exp_dir, meta_round, seed, env, profiles,
                        model_map, submissions, max_attempts,
                    ): seed
                    for seed in target_seeds
                }
                for future in as_completed(futures):
                    block_rows, error = future.result()
                    if block_rows is not None:
                        rows.extend(block_rows)
                        if on_block_complete is not None:
                            on_block_complete(block_rows)
                    if error is not None:
                        errors.append(error)
    return rows, errors


def paired_rows(rows, expected_roles):
    """Use only experiment/round/seed units complete in both OF and OPF."""
    grouped = defaultdict(list)
    for row in rows:
        grouped[block_key(row)].append(row)
    role_set = set(expected_roles)
    complete = {
        key for key, items in grouped.items()
        if len(items) == len(expected_roles)
        and {str(item["role"]) for item in items} == role_set
    }
    coordinates = defaultdict(set)
    for feedback, exp_id, meta_round, seed in complete:
        coordinates[(exp_id, meta_round, seed)].add(feedback)
    paired_coordinates = {coord for coord, conditions in coordinates.items() if conditions == {"OF", "OPF"}}
    return [
        row for row in rows
        if (str(row["exp_id"]), int(row["meta_round"]), int(row["seed"])) in paired_coordinates
    ], len(paired_coordinates)


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["feedback"], row["model"])].append(row)

    stats = {}
    for key, items in grouped.items():
        role_survival = defaultdict(list)
        role_mortality = defaultdict(list)
        for item in items:
            role_survival[item["role"]].append(float(item["survival_days"]))
            role_mortality[item["role"]].append(int(item["dead"]))
        survival_means = [sum(values) / len(values) for values in role_survival.values()]
        mortality_means = [sum(values) / len(values) for values in role_mortality.values()]
        wac_score = 100.0 * (sum(survival_means) / len(survival_means)) / EPISODE_DAYS
        mortality = 100.0 * sum(mortality_means) / len(mortality_means)
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
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
    temporary.replace(path)


def merge_error_history(old_history, old_current_errors, new_errors):
    history = []
    seen = set()
    for row in [*old_history, *old_current_errors, *new_errors]:
        normalized = {field: row.get(field, "") for field in ERROR_FIELDS}
        if not normalized["recorded_at"]:
            normalized["recorded_at"] = "legacy"
        fingerprint = tuple(normalized[field] for field in ERROR_FIELDS)
        if fingerprint not in seen:
            history.append(normalized)
            seen.add(fingerprint)
    return history


def write_table_png(path, rows):
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
    for col in range(len(display_headers)):
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
    parser.add_argument(
        "--meta-rounds", nargs="+", type=int, default=list(DEFAULT_META_ROUNDS),
        help="Meta-round strategies to replay and retain in replay_details.csv.",
    )
    parser.add_argument(
        "--table-meta-rounds", nargs="+", type=int, default=list(DEFAULT_TABLE_META_ROUNDS),
        help="Subset of replayed meta-rounds used to calculate main_table.csv.",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Keep complete blocks in replay_details.csv and replay only missing/partial blocks.",
    )
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument(
        "--workers", type=int, default=1,
        help="Parallel local episode replays per experiment (no API calls).",
    )
    parser.add_argument(
        "--strategy-timeout", type=float, default=1.0,
        help="Per-bid sandbox wall-time limit; increase when using parallel workers.",
    )
    parser.add_argument(
        "--trusted-fast-replay", action="store_true",
        help=(
            "Skip per-bid subprocess startup for strategies already validated in the source logs; "
            "static checks and restricted builtins remain active."
        ),
    )
    parser.add_argument(
        "--checkpoint-every", type=int, default=25,
        help="Flush completed blocks to replay_details.csv after this many blocks.",
    )
    args = parser.parse_args()
    if args.max_attempts < 1:
        parser.error("--max-attempts must be at least 1")
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.strategy_timeout <= 0:
        parser.error("--strategy-timeout must be positive")
    if args.checkpoint_every < 1:
        parser.error("--checkpoint-every must be at least 1")
    if len(set(args.seeds)) != len(args.seeds):
        parser.error("--seeds must not contain duplicates")
    if not args.meta_rounds or any(value < 1 for value in args.meta_rounds):
        parser.error("--meta-rounds must contain positive integers")
    if len(set(args.meta_rounds)) != len(args.meta_rounds):
        parser.error("--meta-rounds must not contain duplicates")
    if not args.table_meta_rounds:
        parser.error("--table-meta-rounds must not be empty")
    if not set(args.table_meta_rounds).issubset(args.meta_rounds):
        parser.error("--table-meta-rounds must be a subset of --meta-rounds")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    # wac_programmatic imported execute_strategy directly. Adjust only its
    # optional timeout default for this replay process; the simulator default
    # remains unchanged for all other entry points.
    executor_defaults = list(wac_programmatic.execute_strategy.__defaults__ or ())
    if not executor_defaults:
        raise RuntimeError("execute_strategy has no configurable timeout default")
    executor_defaults[-1] = args.strategy_timeout
    wac_programmatic.execute_strategy.__defaults__ = tuple(executor_defaults)
    if args.trusted_fast_replay:
        wac_programmatic.execute_strategy = trusted_fast_execute_strategy
    profiles = default_agent_profiles()
    expected_roles = [profile.agent_id for profile in profiles]
    role_order = {role: index for index, role in enumerate(expected_roles)}
    env = WACProgrammaticEnv(episode_days=EPISODE_DAYS)
    batch_specs = (("OF", args.of_dir), ("OPF", args.opf_dir))
    requested_keys = expected_blocks(batch_specs, args.seeds, args.meta_rounds)

    details_path = args.output_dir / "replay_details.csv"
    old_current_errors = read_csv(args.output_dir / "replay_errors.csv")
    old_history = read_csv(args.output_dir / "replay_error_history.csv")
    existing_rows = read_csv(details_path) if args.resume else []
    kept_rows, completed_before, partial_keys, invalid_rows = retain_complete_blocks(
        existing_rows, requested_keys, expected_roles,
    )
    target_keys = requested_keys - completed_before
    checkpoint_rows = list(kept_rows)
    blocks_since_checkpoint = 0

    def checkpoint_block(block_rows):
        nonlocal blocks_since_checkpoint
        checkpoint_rows.extend(block_rows)
        blocks_since_checkpoint += 1
        if blocks_since_checkpoint >= args.checkpoint_every:
            checkpoint_rows.sort(key=lambda row: row_sort_key(row, role_order))
            write_csv(details_path, checkpoint_rows, DETAIL_FIELDS)
            blocks_since_checkpoint = 0

    print(
        f"Requested {len(requested_keys)} blocks ({len(requested_keys) * len(expected_roles)} agent rows); "
        f"keeping {len(completed_before)} complete blocks and replaying {len(target_keys)}.",
        flush=True,
    )
    if partial_keys or invalid_rows:
        print(
            f"Discarded {len(partial_keys)} partial blocks and {invalid_rows} invalid/out-of-scope rows "
            "from the previous checkpoint.",
            flush=True,
        )

    new_rows = []
    new_errors = []
    for feedback, batch_dir in batch_specs:
        rows, errors = replay_batch(
            feedback, batch_dir, args.seeds, args.meta_rounds,
            env, profiles, target_keys, args.max_attempts,
            args.workers, checkpoint_block,
        )
        new_rows.extend(rows)
        new_errors.extend(errors)

    candidate_rows = kept_rows + new_rows
    all_rows, completed_after, still_partial, invalid_after = retain_complete_blocks(
        candidate_rows, requested_keys, expected_roles,
    )
    if still_partial or invalid_after:
        raise RuntimeError("internal error: replay produced a partial or invalid block")
    all_rows.sort(key=lambda row: row_sort_key(row, role_order))
    remaining_keys = requested_keys - completed_after

    # Keep only errors that correspond to blocks still absent after this run.
    remaining_errors = []
    error_keys = set()
    for error in new_errors:
        try:
            key = (
                str(error["feedback"]), str(error["exp_id"]),
                int(error["meta_round"]), int(error["seed"]),
            )
        except (KeyError, TypeError, ValueError):
            remaining_errors.append(error)
            continue
        if key in remaining_keys:
            remaining_errors.append(error)
            error_keys.add(key)
    for key in sorted(remaining_keys - error_keys):
        feedback, exp_id, meta_round, seed = key
        remaining_errors.append({
            "feedback": feedback, "exp_id": exp_id, "meta_round": meta_round,
            "seed": seed, "attempts": 0, "error": "missing block after replay",
            "recorded_at": utc_now(),
        })

    table_input_rows = [
        row for row in all_rows if int(row["meta_round"]) in args.table_meta_rounds
    ]
    analysis_rows, paired_count = paired_rows(table_input_rows, expected_roles)
    table_rows = summarize(analysis_rows)
    if not table_rows:
        raise SystemExit("No paired OF/OPF model results were produced; inspect replay_errors.csv")

    write_csv(args.output_dir / "main_table.csv", table_rows)
    write_csv(details_path, all_rows, DETAIL_FIELDS)
    write_csv(args.output_dir / "replay_errors.csv", remaining_errors, ERROR_FIELDS)
    history = merge_error_history(old_history, old_current_errors, new_errors)
    write_csv(args.output_dir / "replay_error_history.csv", history, ERROR_FIELDS)
    write_table_png(args.output_dir / "main_table.png", table_rows)

    report = {
        "of_batch": str(args.of_dir.resolve()),
        "opf_batch": str(args.opf_dir.resolve()),
        "seeds": args.seeds,
        "replayed_meta_rounds": args.meta_rounds,
        "table_meta_rounds": args.table_meta_rounds,
        "parallel_workers": args.workers,
        "strategy_timeout_seconds": args.strategy_timeout,
        "trusted_fast_replay": args.trusted_fast_replay,
        "expected_roles": expected_roles,
        "expected_blocks": len(requested_keys),
        "expected_agent_rows": len(requested_keys) * len(expected_roles),
        "complete_blocks_before_resume": len(completed_before),
        "blocks_targeted_this_run": len(target_keys),
        "complete_blocks_after_run": len(completed_after),
        "complete_agent_rows_after_run": len(all_rows),
        "remaining_failed_blocks": len(remaining_keys),
        "paired_condition_units_used_for_table": paired_count,
        "generated_at": utc_now(),
    }
    with (args.output_dir / "replay_run_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(
        f"Wrote {len(all_rows)}/{len(requested_keys) * len(expected_roles)} complete agent rows; "
        f"remaining failed blocks: {len(remaining_keys)}. Output: {args.output_dir}",
        flush=True,
    )


if __name__ == "__main__":
    main()
