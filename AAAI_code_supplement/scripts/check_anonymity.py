#!/usr/bin/env python3
"""Fail if the distributable tree contains identity, secret, or provenance leaks."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def joined(*parts: str) -> str:
    return "".join(parts)


FORBIDDEN_FILE_NAMES = {
    joined(".", "git"),
    joined(".", "env"),
    joined(".", "DS_Store"),
    joined("__py", "cache__"),
    joined("cot", ".json"),
    joined("PRIVATE", "_case_mapping_do_not_share.json"),
}
FORBIDDEN_FILE_PREFIXES = (
    joined("LICENSE"),
    joined("CODE", "_OF_CONDUCT"),
)

TEXT_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    (
        "email address",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    ),
    (
        "user-home absolute path",
        re.compile(
            re.escape(joined("/", "home", "/"))
            + "|"
            + re.escape(joined("/", "Users", "/"))
            + r"|[A-Za-z]:\\Users\\",
            re.I,
        ),
    ),
    (
        "repository-host URL",
        re.compile(
            r"https?://(?:www\.)?"
            + re.escape(joined("git", "hub.com"))
            + r"\b|git@"
            + re.escape(joined("git", "hub.com"))
            + r":",
            re.I,
        ),
    ),
    (
        "rights claim",
        re.compile(r"\b" + joined("copy", "right") + r"\b|" + chr(169), re.I),
    ),
    (
        "identity metadata field",
        re.compile(
            r"\b(?:"
            + joined("auth", "or")
            + "|"
            + joined("affili", "ation")
            + r"|contact)\s*[:=]",
            re.I,
        ),
    ),
    (
        "private-key material",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    ),
    (
        "provider secret token",
        re.compile(
            r"\b(?:sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|"
            r"AIza[0-9A-Za-z_-]{30,})\b"
        ),
    ),
    (
        "literal secret assignment",
        re.compile(
            r"\b(?:api[_-]?key|access[_-]?token|secret[_-]?key)\s*[:=]\s*"
            r"['\"][^'\"\s]{8,}['\"]",
            re.I,
        ),
    ),
]


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def scan_text(text: str) -> List[str]:
    return [label for label, pattern in TEXT_PATTERNS if pattern.search(text)]


def record(
    findings: List[Dict[str, str]], path: Path, category: str, detail: str = ""
) -> None:
    findings.append(
        {
            "path": path.as_posix(),
            "category": category,
            "detail": detail,
        }
    )


def scan_structured(path: Path, relative: Path, findings: List[Dict[str, str]]) -> None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            for value in iter_strings(payload):
                for label in scan_text(value):
                    record(findings, relative, f"structured {label}")
        elif suffix == ".jsonl":
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    payload = json.loads(line)
                    for value in iter_strings(payload):
                        for label in scan_text(value):
                            record(findings, relative, f"structured {label}")
        elif suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.reader(handle):
                    for value in row:
                        for label in scan_text(value):
                            record(findings, relative, f"structured {label}")
    except (UnicodeDecodeError, csv.Error, json.JSONDecodeError) as exc:
        record(findings, relative, "invalid structured data", type(exc).__name__)


def scan_tree(root: Path) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.is_symlink():
            record(findings, relative, "symbolic link")
            continue
        if any(part.startswith(".") for part in relative.parts):
            record(findings, relative, "hidden path")
        if path.name in FORBIDDEN_FILE_NAMES or any(
            path.name.upper().startswith(prefix) for prefix in FORBIDDEN_FILE_PREFIXES
        ):
            record(findings, relative, "forbidden file or directory")
        if path.is_dir():
            continue
        try:
            raw = path.read_bytes()
        except OSError as exc:
            record(findings, relative, "unreadable file", type(exc).__name__)
            continue
        text = raw.decode("utf-8", errors="ignore")
        for label in scan_text(text):
            record(findings, relative, label)
        scan_structured(path, relative, findings)

    unique = {}
    for item in findings:
        unique[(item["path"], item["category"], item["detail"])] = item
    return list(unique.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error("--root must be a directory")
    findings = scan_tree(root)
    result = {
        "files_checked": sum(1 for path in root.rglob("*") if path.is_file()),
        "findings": len(findings),
        "categories": sorted({item["category"] for item in findings}),
    }
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            f"Checked {result['files_checked']} files; "
            f"anonymity findings: {result['findings']}."
        )
        for item in findings:
            print(f"{item['path']}: {item['category']}")
    if findings:
        sys.exit(1)


if __name__ == "__main__":
    main()
