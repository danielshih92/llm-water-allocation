flowchart TD
  A[run_all_permutations.py builds permutations] --> B[Generate per-agent backend overrides]
  B --> C[run.py run_experiment]
  C --> D[Parse args and config.py]
  D --> E[Create LLM backend<br/>agent_interface.py]
  E --> F[PromptBuilder builds prompt<br/>prompt_builder.py]
  F --> G[AgentRunner generates reasoning + code<br/>agent_interface.py]
  G --> H[WACProgrammaticEnv simulates rounds<br/>wac_programmatic.py]
  H --> I[execute_strategy sandbox execution<br/>sandbox_executor.py]
  I --> H
  H --> J[Write meta-round log]
  J --> K[Write agent_averages.json + plots]
  J --> L[build_inference_for_experiment]
  J --> M[visualize_log.py / visualize_agent_performance.py]