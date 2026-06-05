flowchart TD
  A[run_all_permutations.py<br/>build permutations + slice] --> B[Generate per-agent backend overrides]
  B --> C[run.py run_experiment]
  C --> D[Parse args + config.py]
  D --> E[Create AgentRunner + backends<br/>agent_interface.py]
  E --> F[PromptBuilder builds prompt<br/>prompt_builder.py]
  F --> G[LLM generates JSON response]
  G --> H{JSON parse ok?}
  H -- yes --> I[Extract reasoning + code]
  H -- no --> J[Regex extract / fallback default code]
  I --> K[WACProgrammaticEnv simulates meta-round<br/>wac_programmatic.py]
  J --> K
  K --> L[execute_strategy sandbox execution<br/>sandbox_executor.py]
  L --> K
  K --> M[Record parse/default-code flags]
  K --> N[Write meta-round log]
  N --> O[Write agent_averages.json]
  O --> P[aggregate_batch_results<br/>global_batch_report.json]
  N --> Q[Plots + visualization]
  N --> R[build_inference_for_experiment]