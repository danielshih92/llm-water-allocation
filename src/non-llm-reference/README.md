# Non-LLM reference policy

This analysis evaluates one fixed **risk-aware pacing heuristic**. For each
feedback condition, experiment, meta-round, role, and supply seed, it replaces
only the focal LLM policy and keeps the other four submitted policy programs
fixed. The heuristic never receives future supply or current-day opponent bids,
and the analysis makes no model API calls.

The policy has three risk levels. Its base bid is a fixed multiple of a
sustainable daily spending rate computed from current budget, known future
salary, and remaining days:

- safe: `0.5 × paced bid`;
- death within two consecutive losses: `1.0 × paced bid`;
- death on the current loss: `2.0 × paced bid`.

In the latter two states, the bid is at least one unit above the median positive
previous-day bid of living opponents. All constants are fixed before evaluation;
there is no hyperparameter search.

Run the validation and complete MR1--MR3 evaluation from the repository root:

```bash
../venv/bin/python src/non-llm-reference/evaluate_reference.py --self-test
../venv/bin/python src/non-llm-reference/evaluate_reference.py
../venv/bin/python src/non-llm-reference/plot_reference_results.py
```

Outputs are written to `compare_result/non-llm-reference`. Positive
`wac_difference` means that the original focal LLM policy outperforms the
heuristic; negative `mortality_difference` favors the LLM policy.
