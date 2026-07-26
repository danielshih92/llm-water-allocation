# Adaptation dynamics

Build OF/OPF meta-round trajectories and paired policy-revision effects from
the same strategies replayed under five fixed water-supply sequences.

## 1. Complete the multi-seed replay

From the `Alympics` project root:

```bash
MPLCONFIGDIR=/tmp/wacbench-matplotlib \
../venv/bin/python temp/main_combine.py \
  --resume \
  --meta-rounds 1 2 3 \
  --table-meta-rounds 2 3 \
  --trusted-fast-replay
```

`--resume` keeps all complete episode blocks and replays only missing or
partial blocks. The main table remains defined over MR2 and MR3, while
`replay_details.csv` contains MR1--MR3 for adaptation analysis.
`--trusted-fast-replay` is intended only for strategy code already admitted
and executed in the source logs. It keeps static checks and restricted
builtins, but avoids starting a new subprocess for every bid.

Expected complete design:

```text
2 conditions x 120 experiments x 3 meta-rounds x 5 seeds x 5 agents
= 18,000 agent-seed-round observations
```

## 2. Generate the adaptation analysis

```bash
MPLCONFIGDIR=/tmp/wacbench-matplotlib \
../venv/bin/python src/adaptation_dynamics/plot_adaptation_dynamics.py
```

Defaults:

- Replay input: `compare_result/main_table/replay_details.csv`
- OF: `log/batch_032_no_opp_info_c_med_20days`
- OPF: `log/batch_031_full_code_access_c_med_20days`
- Supply seeds: inferred from the replay input (expected: 10, 42, 98, 197, 666)
- Output: `compare_result/adaptation_dynamics`
- Bootstrap: 5,000 matched experiment-cluster samples

The five fixed-seed outcomes are first averaged within each experiment. The
bootstrap then resamples the 120 matched experiment/permutation clusters while
keeping conditions, meta-rounds, roles, and agents coupled. Consequently, the
confidence intervals are conditional on these five selected supply seeds; the
9,000 observations per condition must not be described as 9,000 independent
samples.

WACScore and mortality are macro-averaged over model-by-role strata. Outputs
include overall trajectories, adjacent and MR1-to-MR3 changes, OPF-minus-OF
revision contrasts, model-level trajectories, a baseline-adjusted model-effect
forest plot, and descriptive cross-model performance dispersion. The raw
dispersion curves are not a substitute for the matched difference in changes;
the latter is written to `opf_minus_of_performance_dispersion_change.csv`.
`adaptation_trajectories.png` is rendered as two compact side-by-side panels
within one AAAI column; the wider diagnostic figures remain intended for
supplementary two-column placement.

For comparison with the original single-seed analysis:

```bash
../venv/bin/python src/adaptation_dynamics/plot_adaptation_dynamics.py \
  --input-mode logs \
  --output-dir compare_result/adaptation_dynamics_seed42
```
