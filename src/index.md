# Global Batch Report Metric Revision Plan

這份文件記錄下一版 `global_batch_report.json` 的指標調整計劃。目標是在重跑實驗前，先把適合 AAAI paper 比較與分析的欄位定義清楚，讓後續 `run_all_permutations.py` 的實作可以直接依照這份規格更新。

## 一、設計目標

目前 batch report 已經能比較模型的整體 performance 與 generation reliability，但有幾個問題：

- 現有的 `grand_avg_opponent_awareness_score` 是從 reasoning text 的關鍵字計算，不代表模型生成的 code 真的使用 `opponents_status`。
- 現有 report 大多是 grand average，較難觀察不同 meta-round 之間的策略演化。
- 部分舊指標和 paper 的主要研究問題關聯較弱，可能會讓比較表過於雜訊化。

下一版指標會優先觀察：

- 模型是否真的在 code 中使用對手資訊。
- opponent-aware code 是否會隨 meta-round 增加。
- 模型的 performance 是否也隨 meta-round 改善。
- 模型是否有在 meta-round 之間實質修改策略。
- 模型表現是否穩定，或是否高度依賴 agent role。

## 二、新增指標計劃

### 1. Opponent Code Awareness Raw Count

新增欄位：

- `meta_round_1_opp_code_aware_score`
- `meta_round_2_opp_code_aware_score`
- `meta_round_3_opp_code_aware_score`
- `grand_avg_opp_code_aware_score`

定義：

對每個 agent 在每個 meta-round 生成的 `strategy_code` 做靜態文字統計，計算 code body 中 opponent-related references 的 raw count。

計算時應排除 function signature：

```python
def get_bid(day_context, my_status, opponents_status):
```

原因是所有合法策略都會包含 `opponents_status` 參數，如果把 signature 算進去，每份 code 都會天然得到至少 1 分，區辨力會變差。

初步計入的關鍵字或 pattern：

- `opponents_status`
- `opponent`
- `opp`
- `other`
- `rival`
- `competitor`
- `last_bid`
- `last_status`
- `last_hp_after`
- `last_budget_after`
- `water_requirement`
- `daily_salary`
- `trace_history`

目的：

觀察模型生成的策略 code 是否真的參考對手資訊。這個指標可以用來檢查一個核心假設：隨著 meta-round 推進，模型是否變得更 opponent-aware；performance 較好的模型是否也更常在 code 中使用 opponent state。

彙整方式：

- `meta_round_n_opp_code_aware_score`：同一 model 在第 n 個 meta-round 的 raw count 平均。
- `grand_avg_opp_code_aware_score`：同一 model 跨所有 meta-round 的 raw count 平均。

### 2. Opponent Code Use Rate

新增欄位：

- `meta_round_1_opp_code_use_rate`
- `meta_round_2_opp_code_use_rate`
- `meta_round_3_opp_code_use_rate`
- `grand_avg_opp_code_use_rate`

定義：

每份 generated code 先判斷是否真正使用 opponent information：

```text
opp_code_used = 1 if code body 中有非 signature 的 opponent info usage else 0
opp_code_use_rate = sum(opp_code_used) / total_code_count
```

建議判斷為 used 的情況：

- `opponents_status.items()`
- `opponents_status.values()`
- `opponents_status.get(...)`
- `opponents_status[...]`
- `for ... in opponents_status`
- `for ... in opponents_status.items()`
- `if opponents_status`
- 讀取 opponent 狀態欄位，例如 `opp.get("hp")`, `opp["budget"]`, `opp.get("last_bid")`

不應判斷為 used 的情況：

- 只有 function signature 出現 `opponents_status`
- 只有註解提到 opponent
- 只有字串 literal 提到 `opponents_status`

目的：

和 raw count 互補。`opp_code_aware_score` 觀察使用強度，`opp_code_use_rate` 觀察「有多少比例的 code 真的使用 opponent info」。這可以避免少數超長 code 把平均 raw count 拉高。

彙整方式：

- `meta_round_n_opp_code_use_rate`：同一 model 在第 n 個 meta-round 中，真正使用 opponent info 的 code 比例。
- `grand_avg_opp_code_use_rate`：同一 model 跨所有 meta-round 的使用比例。

### 3. Reasoning Opponent Awareness

新增欄位：

- `meta_round_1_reasoning_opp_aware_score`
- `meta_round_2_reasoning_opp_aware_score`
- `meta_round_3_reasoning_opp_aware_score`
- `grand_avg_reasoning_opp_aware_score`

定義：

對每個 agent 的 `reasoning_cot` 或 `generation_stats.final_reasoning` 做 opponent-related keyword raw count。

可使用的關鍵詞包含：

- `opponent`
- `opponents`
- `competition`
- `competitor`
- `rival`
- `other agents`
- `their bid`
- `last bid`
- `aggressive`
- `conservative`

目的：

區分模型「在 reasoning 中意識到對手」和「在 code 中真的使用對手資訊」。這能分析 reasoning-code gap，也能支持 paper 中關於 LLM strategic reasoning faithfulness 的討論。

### 4. Opponent Awareness Gap

新增欄位：

- `grand_avg_opp_awareness_gap`

定義：

```text
grand_avg_opp_awareness_gap =
    grand_avg_reasoning_opp_aware_score - grand_avg_opp_code_aware_score
```

目的：

量化模型「說了但沒做」的程度。若 gap 很高，表示模型在 reasoning 中大量提到 opponent-aware strategy，但 code implementation 沒有相應落地。

### 5. Meta-Round Performance Breakdown

新增欄位：

- `meta_round_1_avg_survival_days`
- `meta_round_2_avg_survival_days`
- `meta_round_3_avg_survival_days`
- `meta_round_1_avg_utility_score`
- `meta_round_2_avg_utility_score`
- `meta_round_3_avg_utility_score`
- `meta_round_1_mortality_rate`
- `meta_round_2_mortality_rate`
- `meta_round_3_mortality_rate`

定義：

將現有的 survival days、utility score、mortality rate 依 meta-round 拆開統計，而不只保留 grand average。

目的：

觀察模型是否隨 meta-round 改善。這對本研究很重要，因為 meta-round 的意義就是讓模型根據前一輪經驗更新策略；若只看 grand average，會看不出策略演化軌跡。

### 6. Meta-Round Delta Metrics

新增欄位：

- `survival_delta_mr3_mr1`
- `utility_delta_mr3_mr1`
- `opp_code_aware_delta_mr3_mr1`

定義：

```text
survival_delta_mr3_mr1 =
    meta_round_3_avg_survival_days - meta_round_1_avg_survival_days

utility_delta_mr3_mr1 =
    meta_round_3_avg_utility_score - meta_round_1_avg_utility_score

opp_code_aware_delta_mr3_mr1 =
    meta_round_3_opp_code_aware_score - meta_round_1_opp_code_aware_score
```

目的：

把 learning/adaptation trend 壓縮成單一可比較欄位。這適合放在 paper 表格中，用來比較不同模型是否真的在 meta-round 之間變好，以及 opponent-aware code 是否同步增加。

### 7. Strategy Revision Score

新增欄位：

- `meta_round_2_strategy_revision_score`
- `meta_round_3_strategy_revision_score`
- `grand_avg_strategy_revision_score`

定義：

比較同一 experiment、同一 agent 在相鄰 meta-round 之間的 `strategy_code` 差異。

候選實作：

- token-level Jaccard distance
- normalized edit distance
- AST node sequence distance

初版建議使用 token-level Jaccard distance，因為實作穩定、成本低，且對格式差異較不敏感：

```text
strategy_revision_score =
    1 - |tokens_previous ∩ tokens_current| / |tokens_previous ∪ tokens_current|
```

目的：

觀察模型是否真的修改策略，而不是在 meta-round 之間重複貼上幾乎相同的 code。此指標可以和 performance delta、opponent awareness delta 一起分析：有修改不一定代表更好，但「修改幅度增加且 performance 提升」會支持模型有策略更新能力。

### 8. Role Sensitivity / Robustness

新增欄位：

- `role_sensitivity_score`
- `best_role_survival_days`
- `worst_role_survival_days`
- `best-worst_gap`
定義：

同一 model 在不同 agent role 中的表現差異。role 包含 Alex、Bob、Cindy、David、Eric，這些 role 的 water requirement 和 daily salary 不同。

role_sensitivity_score：

```text
role_sensitivity_score =
    standard_deviation(avg_survival_days across roles)
```
best-worst_gap:
```text
best_role_survival_days - worst_role_survival_days
```

目的：

避免只看 model grand average 而忽略 role effect。若某模型平均表現高，但只在特定 role 強，則 robustness 可能不足。這個指標可以觀察模型策略是否能適應不同 resource requirement 和 income condition。

## 三、預計刪除或不放入主報表的舊指標

以下欄位要從 `global_batch_report.json` 的主要比較欄位中刪除：

- `grand_avg_bid_entropy`
- `grand_avg_opponent_awareness_score`
- `grand_avg_survival_efficiency`
- `grand_avg_loop_count`


## 四、下一步實作順序

建議實作順序如下：

1. 在 `run_all_permutations.py` 中新增從 `meta_round_*.json` 直接掃描 `strategy_code` 和 `reasoning_cot` 的彙整流程。
2. 先實作 `opp_code_aware_score` 與 `opp_code_use_rate`。
3. 加入 meta-round-level performance breakdown。
4. 加入 delta metrics。
5. 加入 reasoning opponent awareness 與 awareness gap。
6. 加入 strategy revision score。
7. 最後加入 role sensitivity。
8. 從 global report 的主要欄位中移除指定舊指標。

這樣做的好處是，前兩步可以最快驗證核心假設：模型是否隨 meta-round 更常使用 opponent information，以及這件事是否和 performance 有關。
