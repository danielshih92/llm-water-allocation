flowchart TD
  A[run.py 解析參數] --> B[選擇 backend<br/>agent_interface.py]
  B --> C[PromptBuilder 組提示詞<br/>prompt_builder.py]
  C --> D[AgentRunner 產生 reasoning + strategy code<br/>agent_interface.py]
  D --> E[WACProgrammaticEnv 回合模擬<br/>wac_programmatic.py]
  E --> F[execute_strategy 安全執行策略碼<br/>sandbox_executor.py]
  F --> E
  E --> G[輸出 meta-round log]
  G --> H[export_inference.py 萃取 CoT/Code]
  G --> I[visualize_log.py 視覺化]