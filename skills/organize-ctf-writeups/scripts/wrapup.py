#!/usr/bin/env python3
"""Wrap up a competition: fill in missing write-ups and merge them.

For every challenge:

- a note marked ``solved`` is authoritative — its ``session/`` transcripts are never read;
- a note still marked ``unsolved`` is checked against that challenge's transcripts, because
  the session may have been closed after the flag was found and before the note was updated.

Each solved challenge without a ``writeup.md`` gets one rendered from its notes and
artifacts, then every write-up is merged into ``writeups.md`` at the workspace root and
copied into the ``WP/`` archive.

Exit codes:
  0  wrap-up complete
  2  usage error
  5  no competition workspace found
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

CATEGORIES = [
    "Misc",
    "Web",
    "Pwn",
    "Crypto",
    "Reverse",
    "Forensics",
    "OSINT",
    "Malware",
    "AI-ML",
]

PLACEHOLDERS = {
    "",
    "-",
    "—",
    "none",
    "_none_",
    "_none yet_",
    "_(none yet)_",
    "n/a",
    "tbd",
}

TRANSCRIPT_SUFFIXES = {".md", ".txt", ".log", ".jsonl", ".json"}
FIELD_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.*?)\s*\|\s*$")
SECTION_HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
GENERIC_FLAG_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,24}\{[^}\s]{1,200}\}")
SPEC_COMPETITION = re.compile(r"^-\s*\*\*Competition\*\*:\s*(.+?)\s*$", re.MULTILINE)


def _meaningful(text: str | None) -> bool:
    return bool(text) and text.strip().lower() not in PLACEHOLDERS


def _flag_pattern(flag_format: str) -> re.Pattern[str]:
    flag_format = (flag_format or "").strip()
    if "{" in flag_format:
        prefix = flag_format.split("{", 1)[0]
        return re.compile(re.escape(prefix) + r"\{[^}\s]{1,200}\}")
    return GENERIC_FLAG_RE


def parse_notes(text: str) -> dict[str, object]:
    """Parse a notes.md into fields and sections."""
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = FIELD_ROW.match(line)
        if not match:
            continue
        key, value = match.group(1).strip(), match.group(2).strip()
        if not key or key.lower() == "field" or set(key) <= {"-", ":"}:
            continue
        fields[key] = value

    sections: dict[str, str] = {}
    matches = list(SECTION_HEADING.finditer(text))
    for index, heading in enumerate(matches):
        name = heading.group(1).strip()
        start = heading.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return {"fields": fields, "sections": sections}


def _field(fields: dict[str, str], *names: str) -> str:
    for name in names:
        if name in fields:
            return fields[name]
    return ""


def _section(sections: dict[str, str], *names: str) -> str:
    for name in names:
        if name in sections:
            return sections[name]
    return ""


def _first_meaningful(*values: str | None) -> str:
    for value in values:
        if _meaningful(value):
            return value.strip()
    return ""


def _first_paragraph(text: str) -> str:
    for block in re.split(r"\n\s*\n", text.strip()):
        block = block.strip()
        if block and not block.startswith("#"):
            return block
    return ""


def find_flag(text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text)
    if match:
        return match.group(0)
    match = re.search(r"(?im)^\s*(?:flag|答案)\s*[:：]\s*(\S{4,200})", text)
    return match.group(1) if match else None


def scan_transcripts(challenge_dir: Path, pattern: re.Pattern[str]) -> tuple[str | None, str | None]:
    session_dir = challenge_dir / "session"
    if not session_dir.is_dir():
        return None, None
    for path in sorted(session_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TRANSCRIPT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        flag = find_flag(text, pattern)
        if flag:
            return flag, path.name
    return None, None


def _read_spec(workspace: Path) -> str:
    for name in ("AGENTS.md", "CLAUDE.md"):
        spec = workspace / name
        if spec.is_file():
            return spec.read_text(encoding="utf-8", errors="ignore")
    return ""


def competition_name(workspace: Path) -> str:
    spec = _read_spec(workspace)
    match = SPEC_COMPETITION.search(spec)
    if match:
        return match.group(1).strip()
    for line in spec.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return workspace.name


def _resolve_script(challenge_dir: Path, body: str) -> str:
    stripped = body.strip()
    if not _meaningful(stripped):
        return ""
    if stripped.startswith("```"):
        return stripped
    first_line = stripped.splitlines()[0].strip().strip("`").strip()
    if first_line and "\n" not in first_line:
        for candidate in (challenge_dir / first_line, challenge_dir / "solve" / first_line):
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8", errors="ignore").rstrip()
    return stripped


def render_writeup(notes: dict[str, object], challenge_dir: Path, flag: str | None = None) -> str:
    fields = notes["fields"]  # type: ignore[assignment]
    sections = notes["sections"]  # type: ignore[assignment]
    challenge = _first_meaningful(_field(fields, "Challenge"), challenge_dir.name)
    statement = _section(sections, "Statement")
    conclusion = _section(sections, "Conclusion")
    observations = _section(sections, "Observations")
    script = _resolve_script(challenge_dir, _section(sections, "Script"))
    resolved_flag = _first_meaningful(flag, _field(fields, "Flag"), _section(sections, "Flag"))

    summary = _first_paragraph(conclusion) if _meaningful(conclusion) else ""
    if not summary:
        summary = _first_paragraph(statement) if _meaningful(statement) else ""
    if not summary:
        summary = f"Solved during the competition ({challenge_dir.parent.name})."

    solution_parts: list[str] = []
    if _meaningful(observations):
        solution_parts.append(observations)
    if script:
        if script.startswith("```"):
            solution_parts.append(script)
        else:
            solution_parts.append("```\n" + script + "\n```")
    if not solution_parts:
        solution_parts.append(_first_paragraph(statement) if _meaningful(statement) else "_See notes._")

    flag_text = resolved_flag.strip() if _meaningful(resolved_flag) else "—"
    return (
        f"## {challenge}\n\n"
        f"### Summary\n\n{summary}\n\n"
        f"### Solution\n\n" + "\n\n".join(solution_parts) + "\n\n"
        f"### Flag\n\n```\n{flag_text}\n```\n"
    )


def discover_challenges(workspace: Path) -> list[dict[str, object]]:
    root = workspace / "Challenges"
    if not root.is_dir():
        return []
    found: list[dict[str, object]] = []
    for category_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for challenge_dir in sorted(p for p in category_dir.iterdir() if p.is_dir()):
            notes_path = challenge_dir / "notes.md"
            if not notes_path.is_file():
                continue
            notes = parse_notes(notes_path.read_text(encoding="utf-8", errors="ignore"))
            fields = notes["fields"]  # type: ignore[assignment]
            flag_format = _field(fields, "Flag format")
            pattern = _flag_pattern(flag_format)
            status = _field(fields, "Status").strip().lower()
            note_flag = _field(fields, "Flag")
            if status.startswith("solved"):
                solved, flag, source = True, note_flag, "note"
            else:
                flag, transcript = scan_transcripts(challenge_dir, pattern)
                solved = flag is not None
                source = f"transcript:{transcript}" if transcript else None
            found.append(
                {
                    "category": category_dir.name,
                    "challenge": _first_meaningful(_field(fields, "Challenge"), challenge_dir.name),
                    "challenge_dir": challenge_dir,
                    "notes_path": notes_path,
                    "notes": notes,
                    "solved": solved,
                    "flag": flag,
                    "source": source,
                    "writeup": challenge_dir / "writeup.md",
                }
            )

    def order(item: dict[str, object]) -> tuple[int, str, str]:
        category = str(item["category"])
        rank = CATEGORIES.index(category) if category in CATEGORIES else len(CATEGORIES)
        return rank, category, str(item["challenge"])

    return sorted(found, key=order)


def _persist_recovered_flag(notes_path: Path, flag: str | None) -> None:
    """Record a flag recovered from a transcript in the note, so it becomes authoritative."""
    text = notes_path.read_text(encoding="utf-8")
    text = re.sub(r"^\|\s*Status\s*\|.*\|\s*$", "| Status | solved |", text, count=1, flags=re.MULTILINE)
    if _meaningful(flag):
        text = re.sub(
            r"^\|\s*Flag\s*\|.*\|\s*$",
            f"| Flag | {flag} |",
            text,
            count=1,
            flags=re.MULTILINE,
        )
    notes_path.write_text(text, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="organize-ctf-writeups",
        description="Fill in missing write-ups and merge them for a competition.",
    )
    parser.add_argument("--workspace", help="competition workspace (default: discovered from cwd)")
    parser.add_argument("--detect", action="store_true", help="report gaps as JSON and exit without writing")
    parser.add_argument("--no-render", dest="render", action="store_false", help="do not render missing write-ups")
    parser.add_argument("--no-merge", dest="merge", action="store_false", help="do not merge write-ups")
    parser.set_defaults(render=True, merge=True)
    return parser


def find_workspace(start: Path) -> Path | None:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "Challenges").is_dir():
            return candidate
        for spec_name in ("AGENTS.md", "CLAUDE.md"):
            spec = candidate / spec_name
            if spec.is_file():
                try:
                    if "CTF workspace spec" in spec.read_text(encoding="utf-8", errors="ignore"):
                        return candidate
                except OSError:
                    pass
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else find_workspace(Path.cwd())
    if workspace is None or not workspace.is_dir():
        print(
            "no competition workspace found; run setup-ctf-skills first or pass --workspace",
            file=sys.stderr,
        )
        return 5

    challenges = discover_challenges(workspace)
    solved = [c for c in challenges if c["solved"]]
    skipped = [c for c in challenges if not c["solved"]]

    if args.detect:
        print(
            json.dumps(
                {
                    "competition": competition_name(workspace),
                    "solved": [
                        {
                            "challenge": c["challenge"],
                            "category": c["category"],
                            "source": c["source"],
                            "flag": c["flag"],
                            "has_writeup": Path(c["writeup"]).is_file(),  # type: ignore[arg-type]
                        }
                        for c in solved
                    ],
                    "skipped": [{"challenge": c["challenge"], "category": c["category"]} for c in skipped],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    rendered: list[str] = []
    for item in solved:
        if str(item["source"]).startswith("transcript"):
            _persist_recovered_flag(item["notes_path"], item["flag"])  # type: ignore[arg-type]
        writeup_path: Path = item["writeup"]  # type: ignore[assignment]
        if args.render and not writeup_path.is_file():
            writeup_path.write_text(
                render_writeup(
                    item["notes"],  # type: ignore[arg-type]
                    item["challenge_dir"],  # type: ignore[arg-type]
                    flag=str(item["flag"]) if item["flag"] else None,
                ),
                encoding="utf-8",
            )
            rendered.append(writeup_path.as_posix())

    merged_path = workspace / "writeups.md"
    wp_dir = workspace / "WP"
    wp_written: list[str] = []
    if args.merge:
        sections: list[str] = []
        for item in solved:
            writeup_path = item["writeup"]  # type: ignore[assignment]
            if writeup_path.is_file():
                sections.append(writeup_path.read_text(encoding="utf-8").strip())
        body = "\n\n".join(sections).strip()
        merged = f"# {competition_name(workspace)} — Write-ups\n\n{body}\n"
        merged_path.write_text(merged, encoding="utf-8")

        wp_dir.mkdir(parents=True, exist_ok=True)
        (wp_dir / "writeups.md").write_text(merged, encoding="utf-8")
        wp_written.append((wp_dir / "writeups.md").as_posix())
        for item in solved:
            writeup_path = item["writeup"]  # type: ignore[assignment]
            if not writeup_path.is_file():
                continue
            destination = wp_dir / f"{item['category']}-{item['challenge']}.md"
            shutil.copy2(writeup_path, destination)
            wp_written.append(destination.as_posix())

    summary = {
        "competition": competition_name(workspace),
        "solved": [
            {
                "challenge": c["challenge"],
                "category": c["category"],
                "source": c["source"],
                "flag": c["flag"],
                "writeup": Path(c["writeup"]).as_posix(),  # type: ignore[arg-type]
            }
            for c in solved
        ],
        "skipped": [{"challenge": c["challenge"], "category": c["category"]} for c in skipped],
        "rendered": rendered,
        "writeups_md": merged_path.as_posix() if args.merge else None,
        "wp": wp_written,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
