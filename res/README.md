res/ outputs for post-processing and visualization.

Structure:
- res/{experiment_id}/plots/ holds plot images generated from meta-round logs.
- res/{experiment_id}/inference/{agent_id}/ contains:
  - cot.json: CoT history across all meta-rounds for the agent.
  - code.py: strategy code history across all meta-rounds for the agent.
