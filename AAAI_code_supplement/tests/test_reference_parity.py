import csv
import unittest
from pathlib import Path

from replay_main_table import summarize


ROOT = Path(__file__).resolve().parents[1]


class ReferenceParityTests(unittest.TestCase):
    def test_packaged_replays_rebuild_paper_main_table(self):
        with (
            ROOT
            / "data"
            / "paper_intermediates"
            / "main_table"
            / "replay_details.csv"
        ).open(newline="", encoding="utf-8") as handle:
            replay_rows = [
                row for row in csv.DictReader(handle) if int(row["meta_round"]) in (2, 3)
            ]
        rebuilt = summarize(replay_rows)
        with (
            ROOT / "reference_outputs" / "main_table" / "main_table.csv"
        ).open(newline="", encoding="utf-8") as handle:
            expected = list(csv.DictReader(handle))

        numeric_fields = [
            "OF WACScore",
            "OF Mortality (%)",
            "OPF WACScore",
            "OPF Mortality (%)",
            "Δ Survival",
            "Δ Mortality (pp)",
        ]
        expected_by_model = {row["Model"]: row for row in expected}
        self.assertEqual({row["Model"] for row in rebuilt}, set(expected_by_model))
        for row in rebuilt:
            expected_row = expected_by_model[row["Model"]]
            for field in numeric_fields:
                self.assertAlmostEqual(
                    float(row[field]), float(expected_row[field]), places=2
                )


if __name__ == "__main__":
    unittest.main()
