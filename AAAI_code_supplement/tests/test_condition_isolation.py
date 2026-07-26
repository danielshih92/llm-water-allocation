import json
import unittest
from pathlib import Path

from wacbench.prompt_builder import PromptBuilder


ROOT = Path(__file__).resolve().parents[1]


class ConditionIsolationTests(unittest.TestCase):
    def setUp(self):
        self.builder = PromptBuilder()
        self.profile = {
            "agent_id": "Alex",
            "water_requirement": 7,
            "daily_salary": 100,
        }
        self.game_state = {
            "scenario": "medium",
            "supply_range": [15, 25],
            "episode_days": 20,
            "meta_round_id": 2,
            "players": [
                {"agent_id": name, "water_requirement": 7, "daily_salary": 100}
                for name in ("Alex", "Bob", "Cindy", "David", "Eric")
            ],
        }
        self.history = {
            "last_meta_round": 1,
            "agent_summaries": {
                name: {"valid": True, "survival_days": index + 10}
                for index, name in enumerate(("Alex", "Bob", "Cindy", "David", "Eric"))
            },
        }
        self.self_code = "SELF_POLICY_MARKER = 101"
        self.opponents = {
            "Bob": "BOB_POLICY_MARKER = 202",
            "Cindy": "CINDY_POLICY_MARKER = 303",
        }

    def build(self, legacy_mode):
        return self.builder.build_combined_prompt(
            agent_profile=self.profile,
            game_state=self.game_state,
            opponent_code=self.opponents,
            self_previous_code=self.self_code,
            history=self.history,
            opponent_info_mode=legacy_mode,
            show_opponent_code=True,
        )

    def test_of_exposes_self_policy_and_all_survival_outcomes_only(self):
        prompt = self.build("no_opponent_info")
        self.assertIn(self.self_code, prompt)
        for name in self.history["agent_summaries"]:
            self.assertIn(f'"{name}"', prompt)
        self.assertIn('"survival_days"', prompt)
        self.assertNotIn("BOB_POLICY_MARKER", prompt)
        self.assertNotIn("CINDY_POLICY_MARKER", prompt)
        self.assertNotIn("OPPONENT STRATEGY CODE", prompt)

    def test_opf_adds_opponent_previous_policies(self):
        prompt = self.build("full_code_access")
        self.assertIn(self.self_code, prompt)
        self.assertIn("BOB_POLICY_MARKER", prompt)
        self.assertIn("CINDY_POLICY_MARKER", prompt)
        self.assertIn("OPPONENT STRATEGY CODE", prompt)

    def test_public_conditions_map_to_expected_legacy_modes(self):
        config = json.loads((ROOT / "configs" / "paper.json").read_text())
        self.assertEqual(config["conditions"]["OF"], "no_opponent_info")
        self.assertEqual(config["conditions"]["OPF"], "full_code_access")


if __name__ == "__main__":
    unittest.main()

