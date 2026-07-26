# Human validation packet

This directory contains a blinded 50-case validation subset for the
failure-analysis labels.

## Files to send to annotators

- `human_annotation_cases.json`: the 50 cases. Each `llm_judge_prompt` is the
  exact blinded prompt constructed for the LLM judges, including the original
  taxonomy, boundary rules, policy, and reconstructed trajectory evidence.
- Give annotator 1 a copy of `annotator_1_response.json`.
- Give annotator 2 a copy of `annotator_2_response.json`.

Do **not** send `PRIVATE_case_mapping_do_not_share.json`. It contains model
identities, experiment metadata, and the existing LLM-judge labels.

## Annotation procedure

1. Annotators work independently and must not inspect the other annotator's
   answers or use another LLM.
2. Read the complete `llm_judge_prompt` for each case. The final response
   schema inside that prompt is preserved to make the evidence identical to
   the LLM study, but humans only need to fill the simplified response file.
3. Select one `attribution_status` from:
   - `dominant_policy_failure`
   - `mixed_policy_and_context`
   - `no_clear_policy_failure`
   - `insufficient_evidence`
4. In `failure_modes`, enter an unordered list of zero to three labels from:
   - `fatal_undercommitment`
   - `winners_curse_overpayment`
   - `emergency_response_failure`
   - `competitive_threshold_miscalibration`
   - `allocation_context_misreasoning`
5. Use an empty `failure_modes` list for `no_clear_policy_failure` or
   `insufficient_evidence`. Role disadvantage is contextual evidence, not a
   failure mode.
6. `confidence` is an integer from 1 (low) to 5 (high). `notes` is optional.

Example:

```json
{
  "case_id": "case_001",
  "attribution_status": "mixed_policy_and_context",
  "failure_modes": [
    "fatal_undercommitment",
    "competitive_threshold_miscalibration"
  ],
  "confidence": 4,
  "notes": ""
}
```

Preserve both independent response files before any discussion. Disagreements
may be adjudicated later, but pre-adjudication agreement must be calculated
from the original files.

## Sampling

The subset contains five cases from every model × feedback-condition stratum:
10 cases per model and 25 cases each from OF and OPF. Selection did not use
the existing LLM labels. `sampling_manifest.json` records the reproducible
seed and balance checks.

Regenerate the packet from the project root with:

```bash
python3 src_failure_analysis_judge/prepare_human_annotation.py
```
