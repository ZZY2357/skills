#!/usr/bin/env python3
"""Update a challenge's notes while solving.

Convenience wrapper so a session can record observations, dead ends, tool versions and
the working script without hand-editing Markdown. It only touches the named section or
field; everything else is left alone.

Examples:
  python scripts/note.py --challenge-dir <dir> --section Observations --text "small e, no padding"
  python scripts/note.py --challenge-dir <dir> --section Script --script-file solve/exploit.py
  python scripts/note.py --challenge-dir <dir> --field Status=solved --field Flag=flag{...}

Exit codes:
  0  notes updated
  2  usage error
  6  notes.md not found or a section/field is unknown
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SECTIONS = (
    "Statement",
    "Attachments",
    "Hints",
    "Observations",
    "Dead ends",
    "Tools & versions",
    "Script",
    "Conclusion",
)
FIELDS = ("Challenge", "Category", "Target", "Flag format", "Status", "Flag")
PLACEHOLDERS = {"", "-", "—", "_none_", "_none yet_", "_(none yet)_"}

SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
FIELD_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")


def _is_placeholder(text: str) -> bool:
    return text.strip().lower() in PLACEHOLDERS


def set_section(text: str, name: str, body: str, append: bool) -> tuple[str, bool]:
    matches = list(SECTION_HEADING.finditer(text))
    for index, heading in enumerate(matches):
        if heading.group(1).strip() != name:
            continue
        start = heading.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        current = text[start:end].strip()
        if _is_placeholder(current):
            new_body = body
        elif append:
            new_body = current.rstrip() + "\n\n" + body
        else:
            new_body = body
        replacement = "\n\n" + new_body.strip() + "\n\n"
        return text[:start] + replacement + text[end:], True
    return text, False


def set_field(text: str, name: str, value: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^\|\s*{re.escape(name)}\s*\|.*\|\s*$", re.MULTILINE)

    def repl(match: re.Match[str]) -> str:
        return f"| {name} | {value} |"

    new_text, count = pattern.subn(repl, text, count=1)
    return new_text, count == 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solve-ctf note",
        description="Update a challenge's notes while solving.",
    )
    parser.add_argument("--challenge-dir", required=True, help="the challenge folder holding notes.md")
    parser.add_argument("--section", action="append", default=[], help="section to write (repeatable)")
    parser.add_argument("--text", action="append", default=[], help="text for the matching --section")
    parser.add_argument("--script-file", help="file to read and record in the Script section")
    parser.add_argument("--append", action="store_true", help="append instead of replacing a non-empty section")
    parser.add_argument("--field", action="append", default=[], metavar="NAME=VALUE", help="table field to set")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    challenge_dir = Path(args.challenge_dir).expanduser().resolve()
    notes_path = challenge_dir / "notes.md"
    if not notes_path.is_file():
        print(f"notes.md not found in {challenge_dir}", file=sys.stderr)
        return 6
    text = notes_path.read_text(encoding="utf-8")

    if len(args.text) > len(args.section):
        parser.error("more --text values than --section values")

    updates: list[str] = []
    for index, section in enumerate(args.section):
        if section not in SECTIONS:
            print(f"unknown section: {section!r}; expected one of {', '.join(SECTIONS)}", file=sys.stderr)
            return 6
        if index < len(args.text):
            body = args.text[index]
        elif args.script_file and section == "Script":
            body = Path(args.script_file).read_text(encoding="utf-8").rstrip()
        else:
            print(f"no text provided for section {section!r}", file=sys.stderr)
            return 2
        text, found = set_section(text, section, body, args.append)
        if not found:
            print(f"section not found in notes.md: {section!r}", file=sys.stderr)
            return 6
        updates.append(section)

    if args.script_file and "Script" not in args.section:
        text, found = set_section(
            text,
            "Script",
            Path(args.script_file).read_text(encoding="utf-8").rstrip(),
            args.append,
        )
        if not found:
            print("section not found in notes.md: 'Script'", file=sys.stderr)
            return 6
        updates.append("Script")

    for pair in args.field:
        if "=" not in pair:
            parser.error(f"expected NAME=VALUE, got {pair!r}")
        name, value = pair.split("=", 1)
        name = name.strip()
        if name not in FIELDS:
            print(f"unknown field: {name!r}; expected one of {', '.join(FIELDS)}", file=sys.stderr)
            return 6
        text, found = set_field(text, name, value.strip())
        if not found:
            print(f"field not found in notes.md: {name!r}", file=sys.stderr)
            return 6
        updates.append(name)

    notes_path.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {"notes": notes_path.as_posix(), "updated": updates},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
