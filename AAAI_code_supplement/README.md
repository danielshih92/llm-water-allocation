# AAAI Code Supplement

This anonymous package contains the experiment runner, analysis programs, and
minimal intermediate records used for the paper. It supports three workflows:

1. a deterministic test with no API calls;
2. an offline rebuild of the paper statistics, tables, and figures;
3. a complete OF/OPF experiment rerun with the five configured LLM APIs.

The package intentionally excludes full generation logs, prompts, API
responses, model reasoning, human annotations, repository history, and
machine-specific paths.

## Installation

Python 3.11 is recommended.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Pinned versions record the tested analysis environment. External providers can
change model availability independently of this package.

## Deterministic smoke test

No API key or network access is used:

```bash
bash scripts/run_smoke.sh
```

The suite checks OF/OPF information isolation, mock generation through replay
and aggregation, split-manifest merging, judge and failure-analysis units,
analysis self-tests, packaged design counts, and anonymity rules.

## Experimental conditions

The public interface uses `--condition OF|OPF`.

- OF reveals the focal agent's own previous policy and all agents' previous
  survival outcomes. It does not reveal opponents' policy code.
- OPF reveals the same information and additionally reveals opponents'
  previous policy code.

`configs/paper.json` maps these labels to the legacy internal modes used in the
original runs. The information boundary is covered by
`tests/test_condition_isolation.py`.

The fixed paper design has five models, temperature 0.1, medium scarcity,
20-day episodes, three meta-rounds, seed 42, repair-assisted validation, and at
most one JSON repair plus one code repair. The replay seeds are 10, 42, 98,
197, and 666. Analysis and bootstrap seeds are also recorded in the same
configuration.

## Complete API rerun

Set only the keys required by the configured providers:

```bash
export OPENAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."
export GEMINI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
bash scripts/run_paper_experiments.sh /path/to/output
```

There are 120 model-to-role permutations per condition. API execution can be
costly and provider outputs are not guaranteed to remain bitwise stable.
Slices can be run separately; their experiment entries are merged rather than
overwritten:

```bash
python3 -m wacbench.run_batch \
  --config configs/paper.json \
  --condition OF \
  --output-dir /path/to/output \
  --batch-name paper_OF \
  --slice-start 1 \
  --slice-end 30 \
  --no-plots
```

Repeat with non-overlapping slices and the same batch name. Do not mix
conditions or experiment settings in one batch directory.

## Offline paper rebuild

The packaged data contain exact policy code, simulation traces, environment
state, metrics, and model assignments needed by the deterministic analyses.
They contain no generation reasoning or raw responses.

```bash
bash scripts/run_offline_analysis.sh
```

Outputs are written to `outputs/`. The full structural and behavioral
convergence, delayed-scarcity, counterfactual-planning, and risk-response
analyses take longer than the smoke suite.

The packaged design counts are:

- 18,000 multi-seed replay records;
- 18,000 non-LLM reference replacements;
- 6,000 frozen-opponent pairs;
- 120 experiments × 3 meta-rounds for each of OF and OPF.

## Paper-result mapping

| Paper result | Program | Main rebuilt output |
| --- | --- | --- |
| WACScore and mortality | `analysis/replay_main_table.py` | `outputs/main_table/main_table.csv` |
| Adaptation trajectories | `analysis/adaptation_dynamics.py` | `outputs/adaptation_dynamics/` |
| Objective intervals | `analysis/objective_outcomes.py` | `outputs/objective_outcomes/` |
| Behavioral and structural convergence | `analysis/policy_convergence.py` | `outputs/policy_convergence/` |
| Non-LLM reference | `analysis/non_llm_reference.py`, `analysis/summarize_reference_replacements.py` | `outputs/non_llm_reference/` |
| Frozen-Opponent Survival Gain | `analysis/frozen_opponents.py`, `analysis/summarize_fosg.py` | `outputs/opponent_modeling/` |
| Delayed scarcity and counterfactual planning | `analysis/delayed_scarcity.py`, `analysis/counterfactual_planning.py` | `outputs/delayed_scarcity/`, `outputs/counterfactual_planning/` |
| Risk response | `analysis/risk_sensitivity.py` | `outputs/risk_response/` |
| Failure-analysis judges and figures | `failure_analysis/`, `judge_support/` | `outputs/failure_analysis/` |
| Homogeneous-population appendix | `analysis/homogeneous_populations.py`, `analysis/plot_homogeneous_summary.py` | `outputs/homogeneous_populations/` |

`reference_outputs/` contains compact numeric outputs from the paper run for
comparison. `data/paper_intermediates/` contains the minimum deterministic
records used by the offline rebuild.

## Failure-analysis judges

The packaged paired judgments rebuild the reported figures without API calls.
To conduct a new two-judge run, use:

```bash
python3 failure_analysis/failure_analysis_judge.py \
  --judge-backends openai deepseek \
  --judge-models gpt-5.4 deepseek-v4-flash
```

New judge calls require the corresponding API keys.

## Package integrity and anonymity

Run the scanner directly with:

```bash
python3 scripts/check_anonymity.py --root .
```

`PACKAGE_MANIFEST.json` lists only package-relative paths, purposes, and
SHA-256 digests. `ANONYMITY_REPORT.md` records the completed checks without
repeating any prohibited strings.

No license file is included. The repository owner will add the intended
license separately when publishing the final repository.
