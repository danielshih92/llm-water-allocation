# Alympics 統計欄位說明

這份文件說明目前實驗輸出中常見的統計欄位，以及它們代表的意義。

## 一、欄位層級

### 1. `agent_averages.json`
每個 experiment 會為每個 agent 統整一份平均表現。

### 2. `global_batch_report.json`
batch 結束後，會再把所有 experiment 的 `agent_averages.json` 彙總成模型層級與角色層級的總報表。

---

## 二、主要統計欄位

### 生存與經濟

- `avg_survival_days` / `grand_avg_survival_days`
  - 平均存活天數。
  - 越高代表越能撐過更多回合。

- `avg_final_budget` / `grand_avg_final_budget`
  - 平均最終剩餘預算。
  - 越高代表資源使用越保守。

- `avg_daily_bid` / `grand_avg_daily_bid`
  - 平均每日出價。
  - 代表策略整體出價水準。

- `avg_total_bid` / `grand_avg_total_bid`
  - 所有回合出價總和。

- `avg_utility_score` / `grand_avg_utility_score`
  - 綜合效用分數。
  - 目前主要由存活天數、最終 HP、總出價等因素組成。

- `avg_survival_efficiency` / `grand_avg_survival_efficiency`
  - 存活效率，概念上可理解為「每單位出價換到多少存活天數」。
  - 越高表示越省錢。

### 風險與穩定性

- `mortality_rate` / `global_mortality_rate`
  - 死亡率。
  - 例如 `50.0%` 代表一半的實驗中該 agent 曾經死亡。

- `avg_compile_success` / `grand_avg_compile_success`
  - 程式碼成功被 `exec()` 編譯的比例。
  - 1.0 代表每次都可編譯，0.0 代表每次都編譯失敗。

- `avg_runtime_success` / `grand_avg_runtime_success`
  - 程式碼成功執行且沒有 runtime error 的比例。

- `avg_hallucinated_api_count` / `grand_avg_hallucinated_api_count`
  - 偵測到模型使用了不允許 API 的次數。

### LLM 輸出格式穩定性

- `json_parse_fail_rate` / `grand_avg_json_parse_fail_rate`
  - LLM 原始回應無法直接 `json.loads()` 的比例。
  - 例如 0.25 代表 25% 的生成回應不是合法 JSON。

- `default_code_usage_rate` / `grand_avg_default_code_usage_rate`
  - 最終需要退回預設 `default code` 的比例。
  - 這比 `json_parse_fail_rate` 更嚴格，因為有些 parse 失敗仍可能從回應中救出有效程式碼。

### 策略風格

- `avg_bid_variance` / `grand_avg_bid_variance`
  - 出價變異數。
  - 越高代表策略波動越大。

- `avg_bid_entropy` / `grand_avg_bid_entropy`
  - 出價分布的熵。
  - 越高代表出價更不固定。

- `avg_adaptation_score` / `grand_avg_adaptation_score`
  - 策略對供應變化的反應程度。

- `avg_panic_score` / `grand_avg_panic_score`
  - 低 HP 時突然大幅拉高出價的傾向。

- `avg_opponent_awareness_score` / `grand_avg_opponent_awareness_score`
  - 說明文字中對對手、競爭、策略等詞彙的出現程度。

- `avg_recovery_score` / `grand_avg_recovery_score`
  - 低 HP 後是否成功回升的次數。

- `avg_supply_bid_correlation` / `grand_avg_supply_bid_correlation`
  - 供給與出價的相關性。
  - 正值代表供給高時可能跟著調整出價，負值則相反。

### 程式複雜度

- `avg_strategy_complexity` / `grand_avg_strategy_complexity`
  - 以 AST 節點數粗略衡量程式複雜度。

- `avg_branch_count` / `grand_avg_branch_count`
  - `if` 分支數量。

- `avg_loop_count` / `grand_avg_loop_count`
  - `for` / `while` 迴圈數量。

- `avg_function_call_count` / `grand_avg_function_call_count`
  - 函式呼叫次數。

---

## 三、這些機率欄位怎麼看

- 這裡的機率欄位都是介於 `0` 到 `1` 之間。
- `0.0` 代表完全沒有發生。
- `1.0` 代表每次都發生。
- 例如：
  - `json_parse_fail_rate = 0.30` 表示 30% 的 LLM 回應不是直接可解析 JSON。
  - `default_code_usage_rate = 0.10` 表示 10% 的策略生成最後退回預設 code。

---

## 四、補充

- `json_parse_fail_rate` 不等於 `runtime_error`。
  - 前者是「LLM 回應格式問題」。
  - 後者是「程式碼進 sandbox 後執行失敗」。

- `default_code_usage_rate` 也不等於 `runtime_error`。
  - default code 代表「生成階段無法可靠取得策略碼」；
  - runtime error 則是「已取得策略碼，但執行時出錯」。

- `global_batch_report.json` 是 batch 層級的加權平均彙總。
  - 如果你想比較模型表現，優先看 `performance_by_model`。
  - 如果你想比較某個角色在不同模型下的表現，優先看 `performance_by_agent`。
