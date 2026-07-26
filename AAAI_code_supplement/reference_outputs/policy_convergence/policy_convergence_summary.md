# Policy convergence summary

Behavioral distance is the experiment-level mean pairwise RMSE between the five
policies' normalized bids over the same 144 controlled states. Lower is more similar.
Structural similarity is a normalized-AST 3-gram Jaccard robustness diagnostic.
All intervals use matched experiment-cluster bootstrap samples.

| Condition | MR | Behavioral distance (95% CI) | Structural similarity (95% CI) |
| --- | ---: | ---: | ---: |
| OF | 1 | 0.2949 [0.2856, 0.3046] | 0.3058 [0.3009, 0.3110] |
| OF | 2 | 0.3154 [0.3064, 0.3244] | 0.3143 [0.3078, 0.3205] |
| OF | 3 | 0.3315 [0.3225, 0.3404] | 0.3228 [0.3182, 0.3273] |
| OPF | 1 | 0.2835 [0.2757, 0.2916] | 0.3112 [0.3064, 0.3159] |
| OPF | 2 | 0.2733 [0.2634, 0.2833] | 0.3995 [0.3931, 0.4057] |
| OPF | 3 | 0.2734 [0.2636, 0.2832] | 0.4209 [0.4133, 0.4281] |

## Baseline-adjusted OPF-minus-OF changes

| Transition | Metric | Difference in change (95% CI) |
| --- | --- | ---: |
| MR2-MR1 | Behavioral distance | -0.0307 [-0.0450, -0.0161] |
| MR2-MR1 | Structural similarity | +0.0799 [+0.0714, +0.0883] |
| MR3-MR2 | Behavioral distance | -0.0159 [-0.0278, -0.0040] |
| MR3-MR2 | Structural similarity | +0.0129 [+0.0031, +0.0228] |
| MR3-MR1 | Behavioral distance | -0.0467 [-0.0613, -0.0325] |
| MR3-MR1 | Structural similarity | +0.0928 [+0.0826, +0.1029] |
