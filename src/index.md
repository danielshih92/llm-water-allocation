survival_days：Agent 活了幾天。
final_hp：最後剩下多少 HP。
total_bid：整場總共花多少 bid。
average_bid：平均每天出價多少。
bid_variance：出價變化程度，高代表策略不固定。
bid_entropy：出價多樣性，高代表行為更隨機或多變。
adaptation_score：bid 是否會跟 supply 變化一起調整。
panic_score：低 HP 時是否突然暴力加價。
static_policy：是否幾乎固定同一個 bid。
opponent_awareness_score：COT 中是否有考慮對手策略。
recovery_score：低血量後是否成功恢復生存。
supply_bid_correlation：supply 與 bid 的相關性。
compile_success：生成的 code 是否成功 compile。
runtime_success：code 執行時是否沒有 runtime error。
hallucinated_api_count：是否使用不存在的 API 或 environment 欄位。
strategy_complexity：AST node 數量，代表程式整體複雜度。
branch_count：用了多少 if 分支。
loop_count：用了多少 loop。
function_call_count：用了多少 function call。
utility_score：綜合 survival、HP、bid 成本後的效益分數。
survival_efficiency：每單位 bid 換到多少生存天數。
failure_types：自動分類 agent 的失敗原因。