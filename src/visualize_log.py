import argparse
import json
import os
import re
import sys
import webbrowser
from typing import Any, Dict, List, Optional, Tuple

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.27.0.min.js"
DEFAULT_START_HP = 8


def load_log(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    raise ValueError("Log file must contain a list of meta-round records")


def load_logs_from_dir(log_dir: str) -> List[Dict[str, Any]]:
  records: List[Dict[str, Any]] = []
  if not os.path.isdir(log_dir):
    raise ValueError(f"Log directory not found: {log_dir}")
  for name in sorted(os.listdir(log_dir)):
    if not name.endswith(".json"):
      continue
    path = os.path.join(log_dir, name)
    records.extend(load_log(path))
  records.sort(key=lambda item: item.get("meta_round_id", 0))
  return records


def select_meta_round(records: List[Dict[str, Any]], meta_round_id: Optional[int]) -> Dict[str, Any]:
    if meta_round_id is None:
        return records[0]
    for record in records:
        if record.get("meta_round_id") == meta_round_id:
            return record
    raise ValueError(f"meta_round_id {meta_round_id} not found")


def infer_win_flags(traces: List[Dict[str, Any]]) -> List[int]:
    wins: List[int] = []
    prev_hp = DEFAULT_START_HP
    for trace in traces:
        status = trace.get("status")
        hp_after = trace.get("hp_after", prev_hp)
        if status == "dead":
            wins.append(0)
            prev_hp = hp_after
            continue
        wins.append(1 if hp_after >= prev_hp else 0)
        prev_hp = hp_after
    return wins


def extract_series(record: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    agents = record.get("agents", [])
    if not agents:
        raise ValueError("No agents found in record")

    days = [trace.get("day") for trace in agents[0].get("daily_trace", [])]
    if not days:
        raise ValueError("No daily_trace data found")

    agent_ids = [agent.get("agent_id", "unknown") for agent in agents]

    hp_series = []
    budget_series = []
    bid_series = []
    win_matrix = []

    supply = [trace.get("supply") for trace in agents[0].get("daily_trace", [])]

    for agent in agents:
        traces = agent.get("daily_trace", [])
        hp_series.append([trace.get("hp_after") for trace in traces])
        budget_series.append([trace.get("budget_after") for trace in traces])
        bid_series.append([trace.get("bid") for trace in traces])
        win_matrix.append(infer_win_flags(traces))

    summary_rows = []
    for idx, agent in enumerate(agents):
        final_trace = agent.get("daily_trace", [])[-1]
        metrics = agent.get("metrics", {})

        summary_rows.append(
            {
                "agent_id": agent_ids[idx],

                "hp": final_trace.get("hp_after"),

                "budget": final_trace.get("budget_after"),

                "status": final_trace.get("status"),

                # ====================================================
                # Survival
                # ====================================================

                "survival_days":
                metrics.get("survival_days"),

                "final_hp":
                metrics.get("final_hp"),

                # ====================================================
                # Bidding
                # ====================================================

                "avg_bid":
                round(
                    metrics.get("average_bid", 0),
                    2
                ),

                "bid_variance":
                round(
                    metrics.get("bid_variance", 0),
                    2
                ),

                "bid_entropy":
                round(
                    metrics.get("bid_entropy", 0),
                    2
                ),

                # ====================================================
                # Strategy
                # ====================================================

                "bid_supply_sensitivity":
                round(
                  metrics.get("bid_supply_sensitivity", 0),
                    2
                ),

                "opponent_awareness":
                metrics.get(
                    "opponent_awareness_score"
                ),

                "recovery_score":
                metrics.get(
                    "recovery_score"
                ),

                "supply_bid_corr":
                round(
                    metrics.get(
                        "supply_bid_correlation",
                        0
                    ),
                    2
                ),

                # ====================================================
                # Reliability
                # ====================================================

                "compile_success":
                metrics.get(
                    "compile_success"
                ),

                "runtime_success":
                metrics.get(
                    "runtime_success"
                ),

                "hallucinated_api":
                metrics.get(
                    "hallucinated_api_count"
                ),

                # ====================================================
                # Complexity
                # ====================================================

                "strategy_complexity":
                metrics.get(
                    "strategy_complexity"
                ),

                "branch_count":
                metrics.get(
                    "branch_count"
                ),

                # ====================================================
                # Economics
                # ====================================================

                "utility_score":
                round(
                    metrics.get(
                        "utility_score",
                        0
                    ),
                    2
                ),

                "survival_efficiency":
                round(
                    metrics.get(
                        "survival_efficiency",
                        0
                    ),
                    4
                ),

                # ====================================================
                # Failure
                # ====================================================

                "failure_types":
                ", ".join(
                    metrics.get(
                        "failure_types",
                        []
                    )
                ),
            }
        )

    data_bundle = {
        "days": days,
        "agent_ids": agent_ids,
        "hp_series": hp_series,
        "budget_series": budget_series,
        "bid_series": bid_series,
        "supply": supply,
        "win_matrix": win_matrix,
        "summary": summary_rows,
    }
    return data_bundle, agents


def build_html(record: Dict[str, Any]) -> str:
    data_bundle, _ = extract_series(record)
    data_json = json.dumps(data_bundle)
    return """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>WAC Meta-Round Visualization</title>
  <script src=\"{plotly_cdn}\"></script>
  <style>
    body {{
      font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      margin: 24px;
      color: #1f2933;
    }}
    h1 {{ margin-bottom: 8px; }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
    }}
    .chart {{
      border: 1px solid #e0e6ed;
      padding: 16px;
      border-radius: 12px;
      background: #f8fafc;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      background: white;
    }}
    th, td {{
      border: 1px solid #e0e6ed;
      padding: 8px 12px;
      text-align: left;
    }}
    th {{ background: #f1f5f9; }}
  </style>
</head>
<body>
  <h1>WAC Meta-Round Visualization</h1>
  <p>Shows HP, budget, bids vs supply, and inferred wins for a single meta-round.</p>

  <div class=\"grid\">
    <div class=\"chart\" id=\"hp-chart\"></div>
    <div class=\"chart\" id=\"budget-chart\"></div>
    <div class=\"chart\" id=\"bid-chart\"></div>
    <div class=\"chart\" id=\"win-chart\"></div>
    <div class=\"chart\">
      <h3>Final Summary</h3>
      <table id=\"summary-table\"></table>
    </div>
  </div>

  <script>
    const data = {data_json};

    const hpTraces = data.agent_ids.map((agent, idx) => ({{
      x: data.days,
      y: data.hp_series[idx],
      name: agent,
      type: 'scatter',
      mode: 'lines+markers'
    }}));
    Plotly.newPlot('hp-chart', hpTraces, {{
      title: 'HP Over Days',
      xaxis: {{ title: 'Day' }},
      yaxis: {{ title: 'HP' }}
    }});

    const budgetTraces = data.agent_ids.map((agent, idx) => ({{
      x: data.days,
      y: data.budget_series[idx],
      name: agent,
      type: 'scatter',
      mode: 'lines+markers'
    }}));
    Plotly.newPlot('budget-chart', budgetTraces, {{
      title: 'Budget Over Days',
      xaxis: {{ title: 'Day' }},
      yaxis: {{ title: 'Budget' }}
    }});

    const bidTraces = data.agent_ids.map((agent, idx) => ({{
      x: data.days,
      y: data.bid_series[idx],
      name: agent,
      type: 'scatter',
      mode: 'lines+markers'
    }}));
    bidTraces.push({{
      x: data.days,
      y: data.supply,
      name: 'Supply',
      type: 'scatter',
      mode: 'lines',
      line: {{ dash: 'dash', color: '#111827' }}
    }});
    Plotly.newPlot('bid-chart', bidTraces, {{
      title: 'Bids vs Supply',
      xaxis: {{ title: 'Day' }},
      yaxis: {{ title: 'Units / Bid' }}
    }});

    const winHeat = [{{
      z: data.win_matrix,
      x: data.days,
      y: data.agent_ids,
      type: 'heatmap',
      colorscale: [[0, '#fee2e2'], [1, '#bbf7d0']],
      showscale: false
    }}];
    Plotly.newPlot('win-chart', winHeat, {{
      title: 'Inferred Win (Green) / Loss (Red)',
      xaxis: {{ title: 'Day' }},
      yaxis: {{ title: 'Agent' }}
    }});

    const table = document.getElementById('summary-table');
    const header = document.createElement('tr');
    [
      'Agent',
      'HP',
      'Budget',
      'Status',

      'Survival Days',
      'Final HP',

      'Avg Bid',
      'Bid Var',
      'Entropy',

      'Bid-Supply Sensitivity',
      'Opponent Aware',
      'Recovery',
      'Supply-Bid Corr',

      'Compile OK',
      'Runtime OK',
      'Hallucinated API',

      'Complexity',
      'Branches',

      'Utility',
      'Efficiency',

      'Failure Types',
    ].forEach(text => {{
      const th = document.createElement('th');
      th.textContent = text;
      header.appendChild(th);
    }});
    table.appendChild(header);

    data.summary.forEach(row => {
      const tr = document.createElement('tr');

      [
        'agent_id',
        'hp',
        'budget',
        'status',
        'survival_days',
        'avg_bid',
        'bid_supply_sensitivity',
        'compile_success',
        'runtime_success',
      ].forEach(key => {

        const td = document.createElement('td');

        td.textContent = row[key];

        tr.appendChild(td);
      });

      table.appendChild(tr);
    });
  </script>
</body>
</html>
""".format(plotly_cdn=PLOTLY_CDN, data_json=data_json)


def _safe_import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "matplotlib is required for static plotting. Install with: pip install matplotlib"
        ) from exc
    return plt


def build_static_plots(record: Dict[str, Any], output_dir: str, prefix: str) -> List[str]:
  data_bundle, _ = extract_series(record)
  plt = _safe_import_matplotlib()

  os.makedirs(output_dir, exist_ok=True)
  days = data_bundle["days"]
  agent_ids = data_bundle["agent_ids"]
  output_files: List[str] = []

  def _jitter_offsets(series_list: List[List[Any]]) -> List[float]:
    all_values = [value for series in series_list for value in series if value is not None]
    if not all_values:
      return [0.0 for _ in series_list]
    value_range = max(all_values) - min(all_values)
    jitter_step = value_range * 0.003
    if jitter_step == 0:
      jitter_step = 0.02
    center = (len(series_list) - 1) / 2.0
    return [(idx - center) * jitter_step for idx in range(len(series_list))]

  hp_offsets = _jitter_offsets(data_bundle["hp_series"])
  budget_offsets = _jitter_offsets(data_bundle["budget_series"])
  bid_offsets = _jitter_offsets(data_bundle["bid_series"])

  # HP plot
  plt.figure(figsize=(8, 4.5))
  for idx, agent in enumerate(agent_ids):
    series = [value + hp_offsets[idx] for value in data_bundle["hp_series"][idx]]
    plt.plot(days, series, marker="o", label=agent)
  plt.title("HP Over Days")
  plt.xlabel("Day")
  plt.ylabel("HP")
  plt.legend(loc="best")
  hp_path = os.path.join(output_dir, f"{prefix}_hp.png")
  plt.tight_layout()
  plt.savefig(hp_path, dpi=150)
  plt.close()
  output_files.append(hp_path)

  # Budget plot
  plt.figure(figsize=(8, 4.5))
  for idx, agent in enumerate(agent_ids):
    series = [value + budget_offsets[idx] for value in data_bundle["budget_series"][idx]]
    plt.plot(days, series, marker="o", label=agent)
  plt.title("Budget Over Days")
  plt.xlabel("Day")
  plt.ylabel("Budget")
  plt.legend(loc="best")
  budget_path = os.path.join(output_dir, f"{prefix}_budget.png")
  plt.tight_layout()
  plt.savefig(budget_path, dpi=150)
  plt.close()
  output_files.append(budget_path)

  # Bid vs supply plot
  plt.figure(figsize=(8, 4.5))
  for idx, agent in enumerate(agent_ids):
    series = [value + bid_offsets[idx] for value in data_bundle["bid_series"][idx]]
    plt.plot(days, series, marker="o", label=agent)
  plt.plot(days, data_bundle["supply"], linestyle="--", color="#111827", label="Supply")
  plt.title("Bids vs Supply")
  plt.xlabel("Day")
  plt.ylabel("Units / Bid")
  plt.legend(loc="best")
  bid_path = os.path.join(output_dir, f"{prefix}_bids.png")
  plt.tight_layout()
  plt.savefig(bid_path, dpi=150)
  plt.close()
  output_files.append(bid_path)

  # Win heatmap
  plt.figure(figsize=(8, 3.5))
  plt.imshow(data_bundle["win_matrix"], aspect="auto", cmap="RdYlGn")
  plt.title("Inferred Win (Green) / Loss (Red)")
  plt.xlabel("Day")
  plt.ylabel("Agent")
  plt.xticks(range(len(days)), days)
  plt.yticks(range(len(agent_ids)), agent_ids)
  win_path = os.path.join(output_dir, f"{prefix}_wins.png")
  plt.tight_layout()
  plt.savefig(win_path, dpi=150)
  plt.close()
  output_files.append(win_path)

  return output_files


def build_survival_plots(records: List[Dict[str, Any]], output_dir: str) -> List[str]:
  plt = _safe_import_matplotlib()
  os.makedirs(output_dir, exist_ok=True)

  if not records:
    return []

  first_agents = records[0].get("agents", [])
  if not first_agents:
    return []

  agent_ids = [agent.get("agent_id", "unknown") for agent in first_agents]
  days = [trace.get("day") for trace in first_agents[0].get("daily_trace", [])]

  survival_by_agent: Dict[str, List[List[int]]] = {agent_id: [] for agent_id in agent_ids}
  alive_counts_by_meta_round: List[List[int]] = []
  meta_round_labels: List[str] = []

  for record in records:
    meta_round_id = record.get("meta_round_id", "unknown")
    meta_round_labels.append(f"MR {meta_round_id}")
    day_alive_counts = [0 for _ in days]

    agents = record.get("agents", [])
    agent_map = {agent.get("agent_id", "unknown"): agent for agent in agents}

    for agent_id in agent_ids:
      agent = agent_map.get(agent_id, {})
      traces = agent.get("daily_trace", [])
      alive_flags: List[int] = []
      for trace in traces:
        status = trace.get("status")
        alive_flags.append(0 if status == "dead" else 1)
      survival_by_agent[agent_id].append(alive_flags)
      for idx, flag in enumerate(alive_flags):
        if idx < len(day_alive_counts):
          day_alive_counts[idx] += flag

    alive_counts_by_meta_round.append(day_alive_counts)

  output_files: List[str] = []

  # Plot 1: Agent Survival Heatmap
  cols = 2 if len(agent_ids) > 1 else 1
  rows = (len(agent_ids) + cols - 1) // cols
  fig, axes = plt.subplots(rows, cols, figsize=(10, 3.5 * rows), squeeze=False)
  colors = plt.cm.get_cmap("RdYlGn", 2)

  for idx, agent_id in enumerate(agent_ids):
    row = idx // cols
    col = idx % cols
    ax = axes[row][col]
    matrix = survival_by_agent.get(agent_id, [])
    ax.imshow(matrix, aspect="auto", cmap=colors, vmin=0, vmax=1)
    ax.set_title(agent_id)
    ax.set_xlabel("Day")
    ax.set_ylabel("Meta-Round")
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_yticks(range(len(meta_round_labels)))
    ax.set_yticklabels(meta_round_labels)

  for idx in range(len(agent_ids), rows * cols):
    row = idx // cols
    col = idx % cols
    axes[row][col].axis("off")

  fig.suptitle("Agent Survival Status Across Meta-Rounds")
  heatmap_path = os.path.join(output_dir, "survival_heatmap_agents.png")
  fig.tight_layout(rect=[0, 0, 1, 0.95])
  fig.savefig(heatmap_path, dpi=150)
  plt.close(fig)
  output_files.append(heatmap_path)

  # Plot 2: Alive-Agent Count Over Days
  plt.figure(figsize=(8, 4.5))
  for idx, counts in enumerate(alive_counts_by_meta_round):
    label = meta_round_labels[idx] if idx < len(meta_round_labels) else f"MR {idx + 1}"
    plt.plot(days, counts, marker="o", label=label)
  plt.title("Alive Agent Count Across Days by Meta-Round")
  plt.xlabel("Day")
  plt.ylabel("Alive Agents")
  plt.legend(loc="best")
  summary_path = os.path.join(output_dir, "survival_summary.png")
  plt.tight_layout()
  plt.savefig(summary_path, dpi=150)
  plt.close()
  output_files.append(summary_path)

  return output_files


def infer_experiment_id(log_path: str, fallback: str) -> str:
  basename = os.path.basename(log_path)
  match = re.search(r"_exp([A-Za-z0-9]+)", basename)
  if match:
    return f"exp{match.group(1)}"
  if os.path.isdir(log_path):
    if re.fullmatch(r"exp\w+", basename):
      return basename
  parent = os.path.basename(os.path.dirname(log_path))
  if re.fullmatch(r"exp\w+", parent):
    return parent
  return fallback


def write_inference_outputs(
  records: List[Dict[str, Any]],
  experiment_id: str,
  res_root: str,
  source_log: str,
) -> None:
  inference_root = os.path.join(res_root, experiment_id, "inference")
  os.makedirs(inference_root, exist_ok=True)

  cot_history: Dict[str, List[Dict[str, Any]]] = {}
  code_history: Dict[str, List[Tuple[int, str]]] = {}

  for record in records:
    meta_round_id = record.get("meta_round_id")
    for agent in record.get("agents", []):
      agent_id = agent.get("agent_id", "unknown")
      cot_history.setdefault(agent_id, []).append(
        {
          "meta_round_id": meta_round_id,
          "reasoning_cot": agent.get("reasoning_cot", ""),
        }
      )
      code_history.setdefault(agent_id, []).append(
        (meta_round_id, agent.get("strategy_code", ""))
      )

  for agent_id, history in cot_history.items():
    agent_dir = os.path.join(inference_root, agent_id)
    os.makedirs(agent_dir, exist_ok=True)

    cot_payload = {
      "experiment_id": experiment_id,
      "agent_id": agent_id,
      "source_log": source_log,
      "cot_history": history,
    }
    cot_path = os.path.join(agent_dir, "cot.json")
    with open(cot_path, "w", encoding="utf-8") as handle:
      json.dump(cot_payload, handle, indent=2)

    code_path = os.path.join(agent_dir, "code.py")
    with open(code_path, "w", encoding="utf-8") as handle:
      handle.write("# ============================================================\n")
      handle.write(f"# Experiment: {experiment_id}\n")
      handle.write(f"# Agent: {agent_id}\n")
      handle.write(f"# Source: {source_log}\n")
      handle.write("# ============================================================\n\n")

      for meta_round_id, code in code_history.get(agent_id, []):
        handle.write("# ============================================================\n")
        handle.write(f"# Meta Round {meta_round_id}\n")
        handle.write("# ============================================================\n\n")
        handle.write(f"META_ROUND_{meta_round_id}_CODE = r'''\n")
        handle.write(code)
        handle.write("\n'''\n\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize WAC meta-round logs")
    parser.add_argument("--log", type=str, default=None, help="Path to meta-round log JSON")
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help="Directory containing meta-round log JSONs",
    )
    parser.add_argument(
        "--meta-round", type=int, default=None, help="Select a meta_round_id from the log"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output HTML file path (defaults to log path with .html)",
    )
    parser.add_argument("--open", action="store_true", help="Open the HTML in a browser")
    parser.add_argument(
      "--mode",
      type=str,
      default="static",
      choices=["static", "html", "res"],
      help="Visualization mode: static PNGs, HTML dashboard, or res export",
    )
    parser.add_argument(
      "--output-dir",
      type=str,
      default=None,
      help="Output directory for static PNGs (defaults to log/)",
    )
    parser.add_argument(
      "--experiment-id",
      type=str,
      default=None,
      help="Experiment ID for res/ output (defaults to expXX from log name)",
    )
    args = parser.parse_args()

    if not args.log and not args.log_dir:
      raise SystemExit("Provide --log or --log-dir")

    if args.log_dir:
      records = load_logs_from_dir(args.log_dir)
    else:
      records = load_log(args.log)
    record = select_meta_round(records, args.meta_round)

    if args.mode == "html":
      html = build_html(record)
      output_path = args.output
      if output_path is None:
        if args.log:
          output_path = os.path.splitext(args.log)[0] + ".html"
        else:
          meta_round_id = record.get("meta_round_id", "unknown")
          output_path = os.path.join(args.log_dir, f"meta_round_{meta_round_id}.html")

      with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(html)

      print(f"Wrote visualization: {output_path}")
      if args.open:
        webbrowser.open(f"file://{os.path.abspath(output_path)}")
      return

    if args.mode == "static":
      output_dir = args.output_dir or os.path.dirname(args.log) or "."
      prefix = os.path.splitext(os.path.basename(args.log))[0]
      output_files = build_static_plots(record, output_dir, prefix)
      output_files.extend(build_survival_plots(records, output_dir))
      print("Wrote static plots:")
      for path in output_files:
        print(f"- {path}")
      return

    # res export
    res_root = args.output_dir or "res"
    log_source = args.log if args.log else args.log_dir
    experiment_id = args.experiment_id or infer_experiment_id(log_source, "exp1")
    source_log = os.path.basename(log_source)
    write_inference_outputs(records, experiment_id, res_root, source_log)

    plots_dir = os.path.join(res_root, experiment_id, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    for meta_record in records:
      meta_round_id = meta_record.get("meta_round_id", "unknown")
      prefix = f"meta_round_{meta_round_id}"
      build_static_plots(meta_record, plots_dir, prefix)

    build_survival_plots(records, plots_dir)

    print(f"Wrote res/ outputs to: {os.path.join(res_root, experiment_id)}")


if __name__ == "__main__":
    main()
