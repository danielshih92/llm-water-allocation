import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "paper_intermediates"


class PackagedDesignCountTests(unittest.TestCase):
    def test_manifest_design_counts(self):
        manifest = json.loads((DATA / "DATA_MANIFEST.json").read_text())
        counts = manifest["counts"]
        self.assertEqual(counts["replay_records"], 18000)
        self.assertEqual(counts["reference_replacements"], 18000)
        self.assertEqual(counts["frozen_opponent_pairs"], 6000)
        for condition in ("OF", "OPF"):
            self.assertEqual(counts[condition]["experiments"], 120)
            self.assertEqual(counts[condition]["meta_rounds"], 360)
            self.assertEqual(counts[condition]["agent_records"], 1800)

    def test_csv_counts_match_manifest(self):
        paths = {
            "replay_records": DATA / "main_table" / "replay_details.csv",
            "reference_replacements": DATA / "non_llm_reference" / "paired_replacements.csv",
            "frozen_opponent_pairs": DATA / "opponent_modeling" / "frozen_opponent_pairs.csv",
        }
        manifest = json.loads((DATA / "DATA_MANIFEST.json").read_text())
        for key, path in paths.items():
            with path.open(newline="", encoding="utf-8") as handle:
                count = sum(1 for _ in csv.DictReader(handle))
            self.assertEqual(count, manifest["counts"][key])

    def test_packaged_logs_have_no_reasoning_or_raw_responses(self):
        forbidden = {"reasoning_cot", "raw_response_preview", "_raw_response"}
        for condition in ("OF", "OPF"):
            for path in (DATA / "logs" / condition).glob("exp_*/meta_round_*.json"):
                payload = json.loads(path.read_text())[0]
                for agent in payload["agents"]:
                    self.assertTrue(forbidden.isdisjoint(agent))
                    self.assertTrue(
                        forbidden.isdisjoint((agent.get("generation_stats") or {}).keys())
                    )


if __name__ == "__main__":
    unittest.main()

