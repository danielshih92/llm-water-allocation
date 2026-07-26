# Failure Analysis Judge

This pipeline uses two independent LLM judges only for evidence-grounded
failure attribution. It does not assign strategy-quality scores.

## Taxonomy

The five primary modes are:

1. `fatal_undercommitment`
2. `winners_curse_overpayment`
3. `emergency_response_failure`
4. `competitive_threshold_miscalibration`
5. `allocation_context_misreasoning`

`insufficient_evidence` is a non-failure sentinel that prevents forced
attribution. In version 3 it is an attribution status, not a failure mode.
Reasoning--policy and policy--trajectory mismatches are separate binary outputs.

Before selecting a failure mode, each judge assigns one attribution status:

1. `dominant_policy_failure`
2. `mixed_policy_and_context`
3. `no_clear_policy_failure`
4. `insufficient_evidence`

Only the first two statuses may contain a primary policy failure. They may also
contain up to two contributing failure modes. Context is recorded separately as
`resource_disadvantaged_role`, `unaffordable_competitive_pressure`,
`severe_supply_scarcity`, or `opponent_bid_outlier`. This prevents every death
from being forced into a policy-failure category.

`no_clear_policy_failure` may retain a contextual trajectory chain explaining
how role or competition constrained survival, but it must have a null primary,
no contributing policy modes, an empty code mechanism, and all boundary checks
set to false. `insufficient_evidence` cannot assert a causal chain.

The winner's-curse label follows the Alympics observation that early bidding
success may reduce long-term survival when a winner overpays. The judge must
use actual winner payments, never losing bids, and must connect those payments
to reduced later flexibility. Version 2 derives a conservative bridge test:
the accumulated ex-post premium on prior wins must be large enough to cover a
later critical unaffordable threshold gap. This is necessary but not sufficient;
the judge must still identify the policy-code mechanism that produced it.

The other boundaries are similarly explicit. Emergency failure requires a
defective risk-to-bid mapping; competitive miscalibration requires a dominant
opponent-price mechanism plus repeated or lethal affordable misses; fatal
undercommitment requires a code-linked budget cap or reserve mechanism. A lethal
miss includes a critical affordable miss immediately followed by an unbroken
loss and death on the next active day. Winner's curse may coexist as a
contributing mode when undercommitment more directly explains the death.
A non-dominant boundary may remain true without being forced into the two-slot
contributing list. Primary modes still require their own boundary evidence, and
responses that contradict reconstructed trajectory evidence are retried and
never enter aggregation.

For `dominant_policy_failure`, undercommitment and competitive miscalibration
still require repeated or lethal critical affordable misses. For
`mixed_policy_and_context`, one critical affordable miss can establish the
policy contribution only when a separate contextual chain is materially needed
to explain the eventual death. This weaker mixed threshold never applies to a
non-critical affordable miss.

## Pilot command

The default input includes both OPF (`batch_031`) and OF (`batch_032`). Replace
the example models with two judge models available through the configured
backends.

```bash
python3 src_failure_analysis_judge/failure_analysis_judge.py \
  --judge-backends openai deepseek \
  --judge-models gpt-5.4 deepseek-v4-flash \
  --exp-start 1 --exp-end 2 \
  --output-dir judge_result/failure_analysis_pilot_gpt_deepseek_v3
```

By default, only admitted, outcome-valid death cases are sent to the judges.
Every successful item is checkpointed immediately. Re-running the command
skips successful records and retries previously failed items.

Non-retryable quota exhaustion is fail-fast: the first `insufficient_quota`
response checkpoints the current error and stops the run instead of retrying
every remaining item. Replenish the same provider account and resume with the
same output directory.

To execute the cheaper second judge before judge 1 while preserving their
configured identities and existing checkpoints, add:

```bash
--judge-run-order 2 1
```

Do not swap `--judge-backends` or `--judge-models` when resuming an existing
output directory; changing their order is a different run configuration.

## Full run

```bash
python3 src_failure_analysis_judge/failure_analysis_judge.py \
  --judge-backends openai deepseek \
  --judge-models gpt-5.4 deepseek-v4-flash \
  --exp-start 1 --exp-end 120 \
  --output-dir judge_result/failure_analysis_full_gpt_deepseek_v3
```

## Outputs

- `judge_1_records.jsonl`, `judge_2_records.jsonl`: independent raw judgments.
- `judge_1_errors.jsonl`, `judge_2_errors.jsonl`: permanent API/parse failures.
- `paired_judge_records.jsonl`: paired labels and 0.5/0.5 item-level votes.
- `failure_summary_*.json`: averaged distributions and mismatch rates.
- `failure_mode_distribution.csv`: long-form table for heatmaps and paper plots.
- `attribution_status_distribution.csv`: dominant, mixed, no-clear, and
  insufficient-evidence coverage.
- `contextual_contributor_distribution.csv`: contextual pressure prevalence.
- `judge_agreement.json`: exact agreement and Cohen's kappa.
- `failure_run_config.json`, `failure_run_report.json`: reproducibility metadata.

For paper figures, first report `policy_attribution_coverage_rate` and the full
attribution-status distribution. Failure-mode heatmaps should use
`averaged_primary_rates_attributable`, conditioned on policy-attributed votes.
The `any_mode` columns include both primary and contributing mechanisms and may
sum above 100%. Do not convert judge disagreement into an arbitrary consensus
label: a disagreement contributes 0.5 to each selected category.
