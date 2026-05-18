import json
import re
from pathlib import Path

# Update this to the log batch you want to process.
SOURCE_LOG = "log/batch_20260517_140047"

META_ROUND_PATTERN = re.compile(r"^meta_round_(\d+)\.json$")


def load_meta_rounds(exp_dir: Path):
    meta_rounds = []

    for entry in exp_dir.iterdir():
        if not entry.is_file():
            continue

        match = META_ROUND_PATTERN.match(entry.name)
        if not match:
            continue

        try:
            with entry.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            continue

        if not isinstance(data, list) or not data:
            continue

        payload = data[0]
        meta_round_id = payload.get("meta_round_id")
        if not isinstance(meta_round_id, int):
            try:
                meta_round_id = int(match.group(1))
            except Exception:
                continue

        meta_rounds.append((meta_round_id, payload))

    meta_rounds.sort(key=lambda item: item[0])
    return meta_rounds


def build_cot_json(exp_id: str, source_log: str, agent_id: str, cot_history: list):
    return {
        "experiment_id": exp_id,
        "agent_id": agent_id,
        "source_log": source_log,
        "cot_history": cot_history,
    }


def wrap_code_block(code_text: str):
    if code_text is None:
        code_text = ""

    if "\"\"\"" in code_text:
        code_text = code_text.replace("\"\"\"", "\\\"\\\"\\\"")

    return f"\"\"\"\n{code_text}\n\"\"\""


def build_code_py(exp_id: str, source_log: str, agent_id: str, meta_rounds: list):
    lines = []
    lines.append("# ============================================================")
    lines.append(f"# Experiment: {exp_id}")
    lines.append(f"# Agent: {agent_id}")
    lines.append(f"# Source: {source_log}")
    lines.append("# ============================================================")
    lines.append("")

    for meta_round_id, payload in meta_rounds:
        lines.append("# ============================================================")
        lines.append(f"# Meta Round {meta_round_id}")
        lines.append("# ============================================================")
        lines.append("")

        strategy_code = ""
        for agent_entry in payload.get("agents", []):
            if agent_entry.get("agent_id") == agent_id:
                strategy_code = agent_entry.get("strategy_code") or ""
                break

        block = wrap_code_block(strategy_code)
        lines.append(f"META_ROUND_{meta_round_id}_CODE = {block}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def process_experiment(exp_dir: Path, source_path: Path):
    exp_id = exp_dir.name
    meta_rounds = load_meta_rounds(exp_dir)
    if not meta_rounds:
        return

    inference_dir = exp_dir / "inference"
    inference_dir.mkdir(parents=True, exist_ok=True)

    # Collect agents from the first meta round payload.
    first_payload = meta_rounds[0][1]
    agent_ids = [agent.get("agent_id") for agent in first_payload.get("agents", [])]
    agent_ids = [agent_id for agent_id in agent_ids if agent_id]

    for agent_id in agent_ids:
        cot_history = []

        for meta_round_id, payload in meta_rounds:
            reasoning_cot = ""
            for agent_entry in payload.get("agents", []):
                if agent_entry.get("agent_id") == agent_id:
                    reasoning_cot = agent_entry.get("reasoning_cot") or ""
                    break

            cot_history.append({
                "meta_round_id": meta_round_id,
                "reasoning_cot": reasoning_cot,
            })

        agent_dir = inference_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)

        cot_path = agent_dir / "cot.json"
        with cot_path.open("w", encoding="utf-8") as handle:
            json.dump(
                build_cot_json(exp_id, exp_dir.relative_to(source_path).as_posix(), agent_id, cot_history),
                handle,
                indent=2,
                ensure_ascii=False,
            )
            handle.write("\n")

        code_path = agent_dir / "code.py"
        code_text = build_code_py(
            exp_id,
            exp_dir.relative_to(source_path).as_posix(),
            agent_id,
            meta_rounds,
        )
        code_path.write_text(code_text, encoding="utf-8")


def main():
    base_dir = Path(__file__).resolve().parents[1]
    source_path = base_dir / SOURCE_LOG
    if not source_path.exists():
        raise SystemExit(f"SOURCE_LOG not found: {SOURCE_LOG}")

    for exp_dir in sorted(source_path.iterdir()):
        if not exp_dir.is_dir():
            continue
        if not exp_dir.name.startswith("exp_"):
            continue

        process_experiment(exp_dir, source_path)

    print("Inference export complete.")


if __name__ == "__main__":
    main()
