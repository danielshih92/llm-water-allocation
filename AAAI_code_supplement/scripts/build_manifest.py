#!/usr/bin/env python3
"""Build a relative-path SHA-256 package manifest."""

import argparse
import hashlib
import json
from pathlib import Path


def purpose(path: Path) -> str:
    labels = {
        "README.md": "usage and reproducibility guide",
        "requirements.txt": "pinned Python dependencies",
        "ANONYMITY_REPORT.md": "anonymous-package verification summary",
        "configs": "fixed experiment and smoke configurations",
        "wacbench": "experiment runner and simulator",
        "analysis": "paper analysis programs",
        "failure_analysis": "failure-analysis pipeline",
        "judge_support": "judge evidence and evaluation support",
        "data": "sanitized deterministic intermediate data",
        "reference_outputs": "compact paper-run reference outputs",
        "scripts": "reproduction and package-verification entry points",
        "tests": "deterministic unit and integration tests",
    }
    return labels.get(path.parts[0], "supplement file")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = root / "PACKAGE_MANIFEST.json"
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path == manifest_path:
            continue
        relative = path.relative_to(root)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append(
            {
                "path": relative.as_posix(),
                "purpose": purpose(relative),
                "sha256": digest,
            }
        )
    payload = {"schema_version": 1, "files": files}
    manifest_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(files)} entries to {manifest_path.name}")


if __name__ == "__main__":
    main()
