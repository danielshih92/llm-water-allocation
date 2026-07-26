import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MockEndToEndTests(unittest.TestCase):
    def run_command(self, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT)
        env["MPLCONFIGDIR"] = str(self.temp_dir / "matplotlib")
        subprocess.run(
            [sys.executable, *map(str, args)],
            cwd=ROOT,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_generation_logs_replay_analysis_and_slice_merge(self):
        base = [
            "-m",
            "wacbench.run_batch",
            "--config",
            ROOT / "configs" / "smoke.json",
            "--output-dir",
            self.temp_dir,
            "--no-plots",
        ]
        self.run_command(
            *base,
            "--condition",
            "OF",
            "--batch-name",
            "smoke_of",
            "--slice-start",
            "1",
            "--slice-end",
            "1",
        )
        self.run_command(
            *base,
            "--condition",
            "OF",
            "--batch-name",
            "smoke_of",
            "--slice-start",
            "2",
            "--slice-end",
            "2",
        )
        self.run_command(
            *base,
            "--condition",
            "OPF",
            "--batch-name",
            "smoke_opf",
            "--slice-start",
            "1",
            "--slice-end",
            "1",
        )

        manifest = json.loads(
            (self.temp_dir / "smoke_of" / "batch_manifest.json").read_text()
        )
        self.assertEqual(manifest["completed_experiments"], 2)
        self.assertEqual(len(manifest["experiments"]), 2)

        output = self.temp_dir / "analysis"
        self.run_command(
            ROOT / "analysis" / "replay_main_table.py",
            "--of-dir",
            self.temp_dir / "smoke_of",
            "--opf-dir",
            self.temp_dir / "smoke_opf",
            "--output-dir",
            output,
            "--seeds",
            "42",
            "--meta-rounds",
            "1",
            "--table-meta-rounds",
            "1",
            "--trusted-fast-replay",
        )
        self.assertTrue((output / "replay_details.csv").is_file())
        self.assertTrue((output / "main_table.csv").is_file())
        with (output / "replay_details.csv").open(encoding="utf-8") as handle:
            replay_rows = sum(1 for _ in handle) - 1
        self.assertEqual(replay_rows, 15)


if __name__ == "__main__":
    unittest.main()
