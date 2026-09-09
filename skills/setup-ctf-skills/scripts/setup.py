#!/usr/bin/env python3
"""Scaffold a CTF competition workspace and its conventions.

Creates the workspace tree, the notes template, the workspace spec (the agent
instruction file), and — once — the machine's tools inventory.

The script is deterministic and non-destructive: it only creates what is missing,
so re-running it never destroys notes or write-ups.

Exit codes:
  0  workspace ready (created or already present)
  2  usage error
  4  the tools inventory is missing and no tooling answers were supplied
"""

from __future__ import annotations

import argparse
import json
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

DEFAULT_FLAG_FORMAT = "not recorded — read it from each challenge statement"

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = SKILL_DIR.parent
DEFAULT_TOOLS_PATH = SKILLS_DIR / "solve-ctf" / "tools.md"
TEMPLATES_DIR = SKILL_DIR / "templates"


def _read_template(name: str) -> str:
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _render(template: str, values: dict[str, str]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def _parse_entry(raw: str, kind: str) -> dict[str, str]:
    """Parse `name|purpose|invocation|notes` into a tool row."""
    parts = [p.strip() for p in raw.split("|")]
    parts += [""] * (4 - len(parts))
    name, purpose, invocation, notes = parts[:4]
    if not name:
        raise argparse.ArgumentTypeError(f"empty tool name in --{kind}: {raw!r}")
    return {
        "name": name,
        "purpose": purpose,
        "invocation": invocation or name,
        "notes": notes,
    }


def _load_entries(args: argparse.Namespace) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    if args.tools_file:
        data = json.loads(Path(args.tools_file).expanduser().read_text(encoding="utf-8"))
        if isinstance(data, list):
            data = {"cli": data}
        for kind in ("cli", "mcp"):
            for item in data.get(kind, []) or []:
                if isinstance(item, str):
                    entries.append(_parse_entry(item, kind))
                else:
                    entries.append(
                        {
                            "name": str(item.get("name", "")).strip(),
                            "purpose": str(item.get("purpose", "")).strip(),
                            "invocation": str(item.get("invocation", "")).strip()
                            or str(item.get("name", "")).strip(),
                            "notes": str(item.get("notes", "")).strip(),
                        }
                    )
    for raw in args.cli_tool:
        entries.append(_parse_entry(raw, "cli-tool"))
    for raw in args.mcp:
        entries.append(_parse_entry(raw, "mcp"))
    return [e for e in entries if e["name"]]


def _render_tools(entries: list[dict[str, str]]) -> str:
    lines = [
        "# Tools inventory",
        "",
        "Generated once by `setup-ctf-skills`; reused on later runs. Machine-specific and",
        "gitignored (ADR-0007) — only `tools.example.md` is tracked.",
        "",
        "Schema: `tool | purpose | invocation (command or MCP name) | notes (version, limits)`.",
        "",
        "| Tool | Purpose | Invocation | Notes |",
        "|---|---|---|---|",
    ]
    for e in entries:
        lines.append(
            "| {name} | {purpose} | {invocation} | {notes} |".format(
                name=e["name"] or "—",
                purpose=e["purpose"] or "—",
                invocation=e["invocation"] or "—",
                notes=e["notes"] or "—",
            )
        )
    lines.append("")
    return "\n".join(lines)


def _render_spec(workspace: Path, competition: str, flag_format: str, tools_path: Path) -> str:
    return _render(
        _read_template("workspace-spec.md"),
        {
            "COMPETITION": competition,
            "WORKSPACE": workspace.as_posix(),
            "FLAG_FORMAT": flag_format,
            "TOOLS_PATH": tools_path.as_posix(),
            "CATEGORIES": ", ".join(CATEGORIES),
        },
    )


def _write_if_missing(path: Path, content: str) -> bool:
    """Write `content` unless `path` exists. Returns True when it wrote."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def _write_spec(path: Path, spec: str) -> str:
    """Write the spec to `path`, preserving any pre-existing content.

    Returns one of ``created``, ``appended`` or ``reused``.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(spec, encoding="utf-8")
        return "created"
    existing = path.read_text(encoding="utf-8", errors="ignore")
    if "CTF workspace spec" in existing:
        return "reused"
    path.write_text(existing.rstrip() + "\n\n" + spec, encoding="utf-8")
    return "appended"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="setup-ctf-skills",
        description="Scaffold a CTF competition workspace.",
    )
    parser.add_argument(
        "workspace",
        nargs="?",
        help="directory to create/use as the competition workspace",
    )
    parser.add_argument("--competition", help="competition name (default: the workspace directory name)")
    parser.add_argument(
        "--flag-format",
        default=DEFAULT_FLAG_FORMAT,
        help="flag format recorded in the spec (default: %(default)r)",
    )
    parser.add_argument(
        "--agent-file",
        choices=["AGENTS.md", "CLAUDE.md"],
        help="spec filename; default: CLAUDE.md when it already exists, otherwise AGENTS.md",
    )
    parser.add_argument(
        "--tools-path",
        help="where the tools inventory lives (default: the sibling solve-ctf skill folder)",
    )
    parser.add_argument("--tools-file", help="JSON file with {'cli': [...], 'mcp': [...]} answers")
    parser.add_argument(
        "--cli-tool",
        action="append",
        default=[],
        metavar="NAME|PURPOSE|INVOCATION|NOTES",
        help="a CLI tool; repeatable",
    )
    parser.add_argument(
        "--mcp",
        action="append",
        default=[],
        metavar="NAME|PURPOSE|INVOCATION|NOTES",
        help="an MCP server; repeatable",
    )
    parser.add_argument(
        "--print-tools-path",
        action="store_true",
        help="print the resolved tools inventory path and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    tools_path = Path(args.tools_path).expanduser().resolve() if args.tools_path else DEFAULT_TOOLS_PATH
    if args.print_tools_path:
        print(tools_path.as_posix())
        return 0

    if not args.workspace:
        parser.error("the workspace argument is required")

    workspace = Path(args.workspace).expanduser().resolve()
    competition = args.competition or workspace.name

    if args.agent_file:
        agent_file = args.agent_file
    elif (workspace / "CLAUDE.md").exists():
        agent_file = "CLAUDE.md"
    else:
        agent_file = "AGENTS.md"

    created: list[str] = []
    reused: list[str] = []

    workspace.mkdir(parents=True, exist_ok=True)
    for rel in ("Challenges", "WP", "templates"):
        directory = workspace / rel
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(rel + "/")

    notes_template = _read_template("notes.md")
    if _write_if_missing(workspace / "templates" / "notes.md", notes_template):
        created.append("templates/notes.md")
    else:
        reused.append("templates/notes.md")

    spec = _render_spec(workspace, competition, args.flag_format, tools_path)
    spec_action = _write_spec(workspace / agent_file, spec)
    if spec_action == "reused":
        reused.append(agent_file)
    else:
        created.append(agent_file)

    tools_existed = tools_path.exists()
    if tools_existed:
        reused.append(tools_path.as_posix())
    else:
        entries = _load_entries(args)
        if not entries:
            print(
                "tools inventory missing at {path}; re-run with --cli-tool/--mcp/--tools-file "
                "after asking the player what the machine has".format(path=tools_path.as_posix()),
                file=sys.stderr,
            )
            return 4
        _write_if_missing(tools_path, _render_tools(entries))
        created.append(tools_path.as_posix())

    summary = {
        "workspace": workspace.as_posix(),
        "competition": competition,
        "agent_file": agent_file,
        "agent_file_action": spec_action,
        "tools_path": tools_path.as_posix(),
        "tools_inventory": "reused" if tools_existed else "created",
        "created": created,
        "reused": reused,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
