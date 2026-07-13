import argparse
import csv
import inspect
import json
import math
import multiprocessing
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SRC_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC_ROOT))

from sandbox_executor import ALLOWED_BUILTINS, _static_check, execute_strategy
from wac_programmatic import AgentProfile, default_agent_profiles


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BATCH = REPO_ROOT / "log" / "batch_031_full_code_access_c_med_20days"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "compare_result" / "long-term-planning"

PAIR_FIELDS = [
    "batch_id",
    "condition",
    "experiment_id",
    "meta_round_id",
    "agent_id",
    "backend",
    "model",
    "template_name",
    "early_day",
    "late_day",
    "hp",
    "no_water_days",
    "budget",
    "supply",
    "early_bid",
    "late_bid",
    "bid_delta",
    "horizon_awareness",
    "valid_pair",
    "early_error",
    "late_error",
    "meta_round_file",
]

SUMMARY_FIELDS = [
    "condition",
    "model",
    "agent_id",
    "meta_round_id",
    "horizon_awareness",
    "mean_bid_delta",
    "valid_pair_count",
    "total_pair_count",
    "error_pair_count",
    "error_rate",
]

TEMPLATES = [
    {
        "name": "neutral_mid",
        "hp": 8,
        "no_water_days": 1,
        "budget": 300.0,
        "supply": 20.0,
    },
    {
        "name": "scarce_mild_risk",
        "hp": 6,
        "no_water_days": 2,
        "budget": 300.0,
        "supply": 16.0,
    },
    {
        "name": "critical_survival",
        "hp": 3,
        "no_water_days": 2,
        "budget": 300.0,
        "supply": 18.0,
    },
    {
        "name": "safe_high_budget",
        "hp": 10,
        "no_water_days": 1,
        "budget": 600.0,
        "supply": 24.0,
    },
]


def infer_condition(batch_path: Path) -> str:
    name = batch_path.name.lower()
    if "full_code_access" in name:
        return "OPF"
    if "no_opp_info" in name or "no_opponent_info" in name:
        return "OF"
    return "unknown"


def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_records(path: Path) -> Iterable[Dict[str, Any]]:
    payload = load_json_file(path)
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
    elif isinstance(payload, dict):
        yield payload


def normalize_batch_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def load_backend_config(exp_dir: Path) -> Dict[str, Dict[str, Any]]:
    path = exp_dir / "backend_config.json"
    if not path.exists():
        return {}
    payload = load_json_file(path)
    if isinstance(payload, dict):
        return {
            str(agent_id): config
            for agent_id, config in payload.items()
            if isinstance(config, dict)
        }
    return {}


def is_valid_record(record: Dict[str, Any]) -> bool:
    return (
        record.get("all_agents_admitted") == 1
        and record.get("outcome_valid") == 1
    )


def build_profile_map(record: Dict[str, Any]) -> Dict[str, AgentProfile]:
    players = (
        record.get("environment", {})
        if isinstance(record.get("environment"), dict)
        else {}
    ).get("players", [])

    profiles: Dict[str, AgentProfile] = {}
    if isinstance(players, list):
        for item in players:
            if not isinstance(item, dict):
                continue
            agent_id = str(item.get("agent_id", "")).strip()
            if not agent_id:
                continue
            profiles[agent_id] = AgentProfile(
                agent_id=agent_id,
                water_requirement=int(item.get("water_requirement", 0) or 0),
                daily_salary=float(item.get("daily_salary", 0.0) or 0.0),
            )

    if profiles:
        return profiles

    return {
        profile.agent_id: profile
        for profile in default_agent_profiles()
    }


def sanitize_bid(bid: Any, budget: float) -> float:
    try:
        value = float(bid)
    except Exception:
        return 0.0
    if not math.isfinite(value):
        return 0.0
    if value < 0.0:
        value = 0.0
    if value > budget:
        value = budget
    return float(value)


def synthetic_opponents_status(
    target_agent_id: str,
    profiles: Dict[str, AgentProfile],
    template: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    status: Dict[str, Dict[str, Any]] = {}
    supply = float(template["supply"])

    for agent_id in sorted(profiles):
        if agent_id == target_agent_id:
            continue

        profile = profiles[agent_id]
        first_bid = min(120.0, round(profile.daily_salary * 0.70, 4))
        last_bid = min(120.0, round(profile.daily_salary * 0.80, 4))
        budget_after = max(0.0, 300.0 - first_bid - last_bid)

        trace_history = [
            {
                "day": 1,
                "bid": first_bid,
                "supply": supply,
                "hp_after": 8,
                "budget_after": round(300.0 - first_bid, 4),
                "status": "alive",
                "error": None,
            },
            {
                "day": 2,
                "bid": last_bid,
                "supply": supply,
                "hp_after": 8,
                "budget_after": round(budget_after, 4),
                "status": "alive",
                "error": None,
            },
        ]

        status[agent_id] = {
            "agent_id": agent_id,
            "hp": 8,
            "budget": round(budget_after, 4),
            "no_water_days": 1,
            "alive": True,
            "water_requirement": profile.water_requirement,
            "daily_salary": profile.daily_salary,
            "last_bid": last_bid,
            "last_status": "alive",
            "last_hp_after": 8,
            "last_budget_after": round(budget_after, 4),
            "trace_history": trace_history,
        }

    return status


def execute_synthetic_bid(
    strategy_code: str,
    day: int,
    template: Dict[str, Any],
    opponents_status: Dict[str, Dict[str, Any]],
) -> Tuple[float, Optional[str]]:
    budget = float(template["budget"])
    day_context = {
        "day": int(day),
        "supply": float(template["supply"]),
    }
    my_status = {
        "hp": int(template["hp"]),
        "budget": budget,
        "no_water_days": int(template["no_water_days"]),
    }

    raw_bid, error = execute_strategy(
        strategy_code,
        day_context,
        my_status,
        opponents_status,
    )
    return sanitize_bid(raw_bid, budget), error


def _strategy_cases_worker(
    queue: multiprocessing.Queue,
    strategy_code: str,
    cases: List[Dict[str, Any]],
) -> None:
    safe_globals: Dict[str, Any] = {
        "__builtins__": ALLOWED_BUILTINS,
        "math": math,
    }

    try:
        exec(strategy_code, safe_globals, safe_globals)
    except Exception as exc:
        queue.put({
            "global_error": f"compile_error: {exc}",
            "results": [],
        })
        return

    get_bid = safe_globals.get("get_bid")
    if not callable(get_bid):
        queue.put({
            "global_error": "missing_get_bid",
            "results": [],
        })
        return

    try:
        signature = inspect.signature(get_bid)
        param_count = len(signature.parameters)
    except Exception as exc:
        queue.put({
            "global_error": f"signature_error: {exc}",
            "results": [],
        })
        return

    results = []
    for case in cases:
        try:
            if param_count >= 3:
                raw_bid = get_bid(
                    case["day_context"],
                    case["my_status"],
                    case["opponents_status"],
                )
            else:
                raw_bid = get_bid(
                    case["day_context"],
                    case["my_status"],
                )

            bid = float(raw_bid)
            if not math.isfinite(bid):
                results.append({
                    "bid": 0.0,
                    "error": "invalid_bid_value",
                })
            else:
                results.append({
                    "bid": bid,
                    "error": None,
                })
        except Exception as exc:
            results.append({
                "bid": 0.0,
                "error": f"runtime_error: {exc}",
            })

    queue.put({
        "global_error": None,
        "results": results,
    })


def execute_strategy_cases(
    strategy_code: str,
    cases: List[Dict[str, Any]],
    timeout_seconds: float,
) -> List[Tuple[float, Optional[str]]]:
    static_error = _static_check(strategy_code)
    if static_error:
        return [
            (0.0, static_error)
            for _ in cases
        ]

    queue: multiprocessing.Queue = multiprocessing.Queue(maxsize=1)
    process = multiprocessing.Process(
        target=_strategy_cases_worker,
        args=(queue, strategy_code, cases),
        daemon=True,
    )

    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return [
            (0.0, "runtime_timeout")
            for _ in cases
        ]

    if queue.empty():
        return [
            (0.0, "runtime_error: no_result")
            for _ in cases
        ]

    try:
        payload = queue.get_nowait()
    except Exception:
        return [
            (0.0, "runtime_error: no_result")
            for _ in cases
        ]

    global_error = payload.get("global_error")
    if global_error:
        return [
            (0.0, global_error)
            for _ in cases
        ]

    raw_results = payload.get("results", [])
    results: List[Tuple[float, Optional[str]]] = []
    for index, case in enumerate(cases):
        item = raw_results[index] if index < len(raw_results) else {}
        budget = float(case["my_status"].get("budget", 0.0))
        results.append(
            (
                sanitize_bid(item.get("bid", 0.0), budget),
                item.get("error", "runtime_error: missing_case_result"),
            )
        )

    return results


def make_pair_row(
    *,
    batch_id: str,
    condition: str,
    experiment_id: str,
    meta_round_id: Any,
    agent_id: str,
    backend: str,
    model: str,
    template: Dict[str, Any],
    early_day: int,
    late_day: int,
    early_bid: float,
    late_bid: float,
    early_error: Optional[str],
    late_error: Optional[str],
    meta_round_file: Path,
) -> Dict[str, Any]:
    valid_pair = early_error is None and late_error is None
    bid_delta = late_bid - early_bid if valid_pair else None
    horizon_awareness = (
        int(late_bid >= early_bid)
        if valid_pair
        else None
    )

    return {
        "batch_id": batch_id,
        "condition": condition,
        "experiment_id": experiment_id,
        "meta_round_id": meta_round_id,
        "agent_id": agent_id,
        "backend": backend,
        "model": model,
        "template_name": template["name"],
        "early_day": early_day,
        "late_day": late_day,
        "hp": template["hp"],
        "no_water_days": template["no_water_days"],
        "budget": template["budget"],
        "supply": template["supply"],
        "early_bid": round(early_bid, 6),
        "late_bid": round(late_bid, 6),
        "bid_delta": round(bid_delta, 6) if bid_delta is not None else None,
        "horizon_awareness": horizon_awareness,
        "valid_pair": int(valid_pair),
        "early_error": early_error,
        "late_error": late_error,
        "meta_round_file": str(meta_round_file),
    }


def evaluate_batch(
    batch_path: Path,
    early_day: int,
    late_day: int,
    timeout_seconds: float,
    max_files: Optional[int] = None,
    max_strategies: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if not batch_path.exists():
        raise FileNotFoundError(f"Batch path does not exist: {batch_path}")

    condition = infer_condition(batch_path)
    batch_id = batch_path.name
    rows: List[Dict[str, Any]] = []
    strategy_count = 0

    meta_round_files = sorted(batch_path.glob("exp_*/meta_round_*.json"))
    if max_files is not None:
        meta_round_files = meta_round_files[:max_files]

    for meta_round_file in meta_round_files:
        exp_dir = meta_round_file.parent
        experiment_id = exp_dir.name
        backend_config = load_backend_config(exp_dir)

        for record in iter_records(meta_round_file):
            if not is_valid_record(record):
                continue

            meta_round_id = record.get("meta_round_id")
            profiles = build_profile_map(record)
            agents = record.get("agents", [])
            if not isinstance(agents, list):
                continue

            for agent in agents:
                if not isinstance(agent, dict):
                    continue

                strategy_code = agent.get("strategy_code")
                if not isinstance(strategy_code, str) or not strategy_code.strip():
                    continue

                agent_id = str(agent.get("agent_id", "")).strip()
                if not agent_id:
                    continue

                if max_strategies is not None and strategy_count >= max_strategies:
                    return rows
                strategy_count += 1

                agent_backend_config = backend_config.get(agent_id, {})
                backend = str(agent_backend_config.get("backend", "unknown"))
                model = str(agent_backend_config.get("model", "unknown"))

                cases: List[Dict[str, Any]] = []
                for template in TEMPLATES:
                    opponents_status = synthetic_opponents_status(
                        target_agent_id=agent_id,
                        profiles=profiles,
                        template=template,
                    )
                    budget = float(template["budget"])
                    my_status = {
                        "hp": int(template["hp"]),
                        "budget": budget,
                        "no_water_days": int(template["no_water_days"]),
                    }
                    cases.append(
                        {
                            "template": template["name"],
                            "day": early_day,
                            "day_context": {
                                "day": int(early_day),
                                "supply": float(template["supply"]),
                            },
                            "my_status": my_status,
                            "opponents_status": opponents_status,
                        }
                    )
                    cases.append(
                        {
                            "template": template["name"],
                            "day": late_day,
                            "day_context": {
                                "day": int(late_day),
                                "supply": float(template["supply"]),
                            },
                            "my_status": my_status,
                            "opponents_status": opponents_status,
                        }
                    )

                case_results = execute_strategy_cases(
                    strategy_code=strategy_code,
                    cases=cases,
                    timeout_seconds=timeout_seconds,
                )

                for template_index, template in enumerate(TEMPLATES):
                    early_index = template_index * 2
                    late_index = early_index + 1
                    early_bid, early_error = case_results[early_index]
                    late_bid, late_error = case_results[late_index]

                    rows.append(
                        make_pair_row(
                            batch_id=batch_id,
                            condition=condition,
                            experiment_id=experiment_id,
                            meta_round_id=meta_round_id,
                            agent_id=agent_id,
                            backend=backend,
                            model=model,
                            template=template,
                            early_day=early_day,
                            late_day=late_day,
                            early_bid=early_bid,
                            late_bid=late_bid,
                            early_error=early_error,
                            late_error=late_error,
                            meta_round_file=meta_round_file,
                        )
                    )

    return rows


def summarize_group(rows: List[Dict[str, Any]], key: Tuple[Any, ...]) -> Dict[str, Any]:
    valid_rows = [
        row
        for row in rows
        if row["valid_pair"] == 1
    ]
    error_count = len(rows) - len(valid_rows)

    if valid_rows:
        awareness = sum(
            float(row["horizon_awareness"])
            for row in valid_rows
        ) / len(valid_rows)
        mean_delta = sum(
            float(row["bid_delta"])
            for row in valid_rows
        ) / len(valid_rows)
    else:
        awareness = None
        mean_delta = None

    condition, model, agent_id, meta_round_id = key
    return {
        "condition": condition,
        "model": model,
        "agent_id": agent_id,
        "meta_round_id": meta_round_id,
        "horizon_awareness": round(awareness, 6) if awareness is not None else None,
        "mean_bid_delta": round(mean_delta, 6) if mean_delta is not None else None,
        "valid_pair_count": len(valid_rows),
        "total_pair_count": len(rows),
        "error_pair_count": error_count,
        "error_rate": round(error_count / len(rows), 6) if rows else None,
    }


def summarize_pairs(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["condition"],
            row["model"],
            row["agent_id"],
            row["meta_round_id"],
        )
        grouped[key].append(row)

    return [
        summarize_group(group_rows, key)
        for key, group_rows in sorted(grouped.items(), key=lambda item: item[0])
    ]


def summarize_for_console(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            row["condition"],
            row["model"],
            "ALL",
            "ALL",
        )
        grouped[key].append(row)

    return [
        summarize_group(group_rows, key)
        for key, group_rows in sorted(grouped.items(), key=lambda item: item[0])
    ]


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                field: row.get(field)
                for field in fields
            })


def format_table_value(value: Any, digits: int = 4) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    try:
        float_value = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{float_value:.{digits}f}"


def estimate_col_widths(rows: List[Dict[str, str]]) -> List[float]:
    if not rows:
        return []

    headers = list(rows[0].keys())
    lengths = []
    for header in headers:
        max_len = max(
            [len(str(header))]
            + [
                len(str(row.get(header, "")))
                for row in rows
            ]
        )
        lengths.append(max_len)

    total = float(sum(lengths)) or 1.0
    return [
        max(0.08, length / total)
        for length in lengths
    ]


def write_summary_table_png(
    path: Path,
    console_rows: List[Dict[str, Any]],
) -> None:
    os.environ.setdefault(
        "MPLCONFIGDIR",
        str(path.parent / ".matplotlib"),
    )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = sorted(
        console_rows,
        key=lambda row: (
            str(row.get("condition", "")),
            str(row.get("model", "")),
        ),
    )

    table_rows = [
        {
            "condition": row.get("condition", ""),
            "model": row.get("model", ""),
            "horizon awareness": format_table_value(row.get("horizon_awareness")),
            "mean delta": format_table_value(row.get("mean_bid_delta")),
            "valid pairs": str(row.get("valid_pair_count", "")),
            "error rate": format_table_value(row.get("error_rate")),
        }
        for row in rows
    ]

    if not table_rows:
        return

    headers = list(table_rows[0].keys())
    cell_text = [
        [
            row.get(header, "")
            for header in headers
        ]
        for row in table_rows
    ]

    fig_height = max(3.0, 0.55 * (len(table_rows) + 1))
    fig, ax = plt.subplots(figsize=(12.0, fig_height))
    ax.axis("off")
    table = ax.table(
        cellText=cell_text,
        colLabels=headers,
        cellLoc="center",
        loc="center",
        colWidths=estimate_col_widths(table_rows),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.4)
    ax.set_title(
        "Horizon Awareness Summary",
        fontsize=12,
        pad=12,
    )
    plt.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


def write_outputs(
    output_dir: Path,
    pair_rows: List[Dict[str, Any]],
    summary_rows: List[Dict[str, Any]],
    console_rows: List[Dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    write_csv(
        output_dir / "horizon_awareness_pairs.csv",
        pair_rows,
        PAIR_FIELDS,
    )
    write_csv(
        output_dir / "horizon_awareness_summary.csv",
        summary_rows,
        SUMMARY_FIELDS,
    )

    payload = {
        "summary_by_condition_model_agent_meta_round": summary_rows,
        "summary_by_condition_model": console_rows,
    }
    with (output_dir / "horizon_awareness_summary.json").open(
        "w",
        encoding="utf-8",
    ) as handle:
        json.dump(payload, handle, indent=2)

    write_summary_table_png(
        output_dir / "horizon_awareness_table.png",
        console_rows,
    )


def print_console_summary(rows: List[Dict[str, Any]]) -> None:
    print("condition,model,horizon_awareness,mean_bid_delta,valid_pair_count,error_rate")
    for row in rows:
        print(
            f"{row['condition']},"
            f"{row['model']},"
            f"{row['horizon_awareness']},"
            f"{row['mean_bid_delta']},"
            f"{row['valid_pair_count']},"
            f"{row['error_rate']}"
        )


def run_self_test() -> None:
    profiles = {
        profile.agent_id: profile
        for profile in default_agent_profiles()
    }
    template = TEMPLATES[0]
    opponents_status = synthetic_opponents_status("Alex", profiles, template)

    cases = [
        (
            "constant",
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    return 100\n",
            1,
            0.0,
        ),
        (
            "day_aware",
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    return int(day_context.get('day', 1)) * 10\n",
            1,
            150.0,
        ),
        (
            "reverse_day",
            "def get_bid(day_context, my_status, opponents_status):\n"
            "    return 300 - int(day_context.get('day', 1)) * 10\n",
            0,
            -150.0,
        ),
    ]

    for name, code, expected_awareness, expected_delta in cases:
        early_bid, early_error = execute_synthetic_bid(code, 3, template, opponents_status)
        late_bid, late_error = execute_synthetic_bid(code, 18, template, opponents_status)
        if early_error or late_error:
            raise AssertionError(f"{name} failed with errors: {early_error}, {late_error}")

        awareness = int(late_bid >= early_bid)
        delta = late_bid - early_bid
        if awareness != expected_awareness:
            raise AssertionError(
                f"{name} awareness mismatch: {awareness} != {expected_awareness}"
            )
        if abs(delta - expected_delta) > 1e-6:
            raise AssertionError(
                f"{name} delta mismatch: {delta} != {expected_delta}"
            )

    print("Self-test passed.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate horizon awareness from existing WAC strategy code logs.",
    )
    parser.add_argument(
        "--batch",
        default=str(DEFAULT_BATCH),
        help="Batch log directory containing exp_*/meta_round_*.json.",
    )
    parser.add_argument(
        "--early-day",
        type=int,
        default=3,
        help="Early day used in synthetic state pairs.",
    )
    parser.add_argument(
        "--late-day",
        type=int,
        default=18,
        help="Late day used in synthetic state pairs.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Base directory for CSV/JSON/PNG outputs.",
    )
    parser.add_argument(
        "--output-folder",
        default=None,
        help=(
            "Optional subfolder under --output-dir. For example, "
            "--output-folder batch_031 writes to "
            "compare_result/long-term-planning/batch_031."
        ),
    )
    parser.add_argument(
        "--metric",
        choices=["late_ge_early"],
        default="late_ge_early",
        help="Horizon awareness metric.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=8.0,
        help="Per-strategy sandbox timeout for all synthetic calls.",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Optional debug limit on meta_round files to scan.",
    )
    parser.add_argument(
        "--max-strategies",
        type=int,
        default=None,
        help="Optional debug limit on strategy code entries to evaluate.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in smoke tests and exit.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.self_test:
        run_self_test()
        return

    batch_path = normalize_batch_path(args.batch)
    output_dir = Path(args.output_dir).expanduser()
    if not output_dir.is_absolute():
        output_dir = (Path.cwd() / output_dir).resolve()
    if args.output_folder:
        output_dir = output_dir / str(args.output_folder).strip()

    pair_rows = evaluate_batch(
        batch_path=batch_path,
        early_day=args.early_day,
        late_day=args.late_day,
        timeout_seconds=args.timeout_seconds,
        max_files=args.max_files,
        max_strategies=args.max_strategies,
    )
    summary_rows = summarize_pairs(pair_rows)
    console_rows = summarize_for_console(pair_rows)

    write_outputs(
        output_dir=output_dir,
        pair_rows=pair_rows,
        summary_rows=summary_rows,
        console_rows=console_rows,
    )

    print(f"Wrote {len(pair_rows)} pair rows to {output_dir}")
    print_console_summary(console_rows)


if __name__ == "__main__":
    main()
