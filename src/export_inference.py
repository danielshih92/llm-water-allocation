import argparse
import json
import os
import re
from typing import Any, Dict, List, Optional


def load_log(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    raise ValueError("Log file must contain a list of meta-round records")


def infer_experiment_id(log_path: str, fallback: str = "exp-1") -> str:
    # Example filename: meta_round_20260424_0630_exp97.json -> exp-97
    match = re.search(r"_(exp\d+)\.json$", os.path.basename(log_path))
    if match:
        return match.group(1).replace("exp", "exp-")
    parent = os.path.basename(os.path.dirname(log_path))
    if re.fullmatch(r"exp\w+", parent):
        return parent.replace("exp", "exp-")
    return fallback


def export_inference_from_log(
    log_path: str,
    inference_root: str = "inference",
    experiment_id: Optional[str] = None,
) -> None:
    records = load_log(log_path)
    exp_id = experiment_id or infer_experiment_id(log_path)

    for record in records:
        meta_round_id = record.get("meta_round_id", 1)
        meta_dir = os.path.join(inference_root, exp_id, f"meta-round-{meta_round_id}")
        os.makedirs(meta_dir, exist_ok=True)

        agents = record.get("agents", [])
        for agent in agents:
            agent_id = agent.get("agent_id", "unknown")

            cot = agent.get(
                "reasoning_cot",
                ""
            )

            code = agent.get(
                "strategy_code",
                ""
            )

            metrics = agent.get(
                "metrics",
                {}
            )

            cot_path = os.path.join(
                meta_dir,
                f"{agent_id}_COT.txt"
            )

            code_path = os.path.join(
                meta_dir,
                f"{agent_id}_code.py"
            )

            metrics_path = os.path.join(
                meta_dir,
                f"{agent_id}_metrics.json"
            )

            with open(
                cot_path,
                "w",
                encoding="utf-8"
            ) as handle:

                handle.write(
                    cot.strip() + "\n"
                )

            with open(
                code_path,
                "w",
                encoding="utf-8"
            ) as handle:

                handle.write(
                    code.strip() + "\n"
                )

            with open(
                metrics_path,
                "w",
                encoding="utf-8"
            ) as handle:

                json.dump(
                    metrics,
                    handle,
                    indent=2
                )


def export_inference_from_dir(
    log_dir: str = "log",
    inference_root: str = "inference",
) -> None:
    for name in sorted(os.listdir(log_dir)):
        if name.endswith(".json"):
            export_inference_from_log(
                os.path.join(log_dir, name),
                inference_root=inference_root,
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export COT and code from meta-round logs into inference folder"
    )
    parser.add_argument("--log", type=str, help="Path to a meta-round log JSON")
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory containing log JSON files",
    )
    parser.add_argument(
        "--inference-root",
        type=str,
        default="inference",
        help="Output root directory for inference",
    )
    parser.add_argument(
        "--experiment-id",
        type=str,
        default=None,
        help="Optional experiment id (e.g., exp-1). If not set, inferred from filename.",
    )
    args = parser.parse_args()

    if args.log:
        export_inference_from_log(
            args.log,
            inference_root=args.inference_root,
            experiment_id=args.experiment_id,
        )
        return

    if args.log_dir:
        export_inference_from_dir(
            log_dir=args.log_dir,
            inference_root=args.inference_root,
        )
        return

    raise SystemExit("Provide --log or --log-dir")


if __name__ == "__main__":
    main()
