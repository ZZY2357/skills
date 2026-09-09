---
name: setup-ctf-skills
description: Scaffold a CTF competition workspace and write down its conventions. Use once per competition, before solving, to create the Challenges/ and WP/ folders, the notes template, the workspace spec (AGENTS.md or CLAUDE.md), and the machine's tools inventory. Use again at the start of a second competition with a different workspace directory. Do not use it to log in to a platform, fetch challenges, or submit flags.
license: MIT
---

# setup-ctf-skills

One run per competition. Creates the competition workspace, writes the spec every session
in that workspace must follow, and records the machine's tools inventory once.

The workspace lives **outside this skill repository** — a public repo must never contain
flags. Pick a root such as `D:\ctf\<event-slug>\`.

## Workflow

### 1. Confirm the workspace directory

Ask the player which directory to use if it is not already given, a name for the
competition (defaults to the directory name), and the competition's flag format if it is
uniform across challenges (e.g. `flag{...}`). Then run:

```bash
python <skill-dir>/scripts/setup.py "<workspace-dir>" --competition "<competition name>" \
  --flag-format "flag{...}"
```

This creates:

```
<workspace>/
  Challenges/            challenge root
  WP/                    write-up archive
  templates/notes.md     notes template
  AGENTS.md | CLAUDE.md  the workspace spec
```

The spec filename is `CLAUDE.md` when that file already exists in the workspace, otherwise
`AGENTS.md`. The spec carries the folder conventions, the required notes fields, the
write-up heading and merge rules, the flag format, the category list, and where the tools
inventory lives. It is written once: if the chosen file already exists it is appended to
(never overwritten), and a re-run that already contains the spec leaves it untouched, so
re-running setup is safe.

### 2. Record the tools inventory (only when missing)

The inventory lists the CLI tools and MCP servers the machine actually has, so later
solves stop reaching for tools that are not installed. It lives in the sibling
`solve-ctf` skill folder as `tools.md` (gitignored, ADR-0007).

If the inventory already exists, **do not ask again** — the script reuses it and reports
`"tools_inventory": "reused"`.

If it is missing, the script exits `4`. Then:

1. Ask the player once: which CLI tools (e.g. `sqlmap`, `dirsearch`, `upx`) and which
   configured MCP servers (e.g. IDA MCP, jadx MCP) are available, and how to invoke each.
2. Re-run setup with the answers:

```bash
python <skill-dir>/scripts/setup.py "<workspace-dir>" \
  --cli-tool "sqlmap|SQL injection testing|sqlmap|1.7+" \
  --cli-tool "dirsearch|Web content discovery|dirsearch -u <url>|0.4.3" \
  --mcp "IDA MCP|Disassembly / decompilation|MCP ida|configured"
```

Or write the answers to a JSON file and pass `--tools-file answers.json`:

```json
{
  "cli": [{"name": "sqlmap", "purpose": "SQL injection", "invocation": "sqlmap", "notes": "1.7+"}],
  "mcp": [{"name": "IDA MCP", "purpose": "Disassembly", "invocation": "MCP ida", "notes": "configured"}]
}
```

To see where the inventory will be written without writing anything:

```bash
python <skill-dir>/scripts/setup.py --print-tools-path
```

### 3. Report

Summarise for the player: the workspace root, the spec filename, and whether the tools
inventory was created or reused. Then they open a session in the workspace and start
handing challenges over with `/solve-ctf`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | workspace ready |
| 2 | usage error |
| 4 | tools inventory missing and no answers supplied — ask the player, then re-run |

## Rules

- **Idempotent.** Re-running never destroys notes or write-ups; existing files are kept.
- **Never log in, never fetch challenges, never submit flags.** Those are out of scope
  (ADR-0003).
- **Ask for tooling once**, not once per competition. Reuse `tools.md` when it exists.
- This skill only scaffolds. Taking a challenge in is `/solve-ctf`; organising write-ups
  is `/organize-ctf-writeups`.

## Install note

This skill resolves the inventory path relative to its own location
(`../solve-ctf/tools.md`), so `setup-ctf-skills` and `solve-ctf` must stay sibling folders
in the harness's skill directory. The repo working copy is the master for `tools.md`;
harness copies are deployed snapshots (ADR-0007).
