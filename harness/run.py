#!/usr/bin/env python3
"""Fixture harness for the CTF skill family.

Creates scratch competition workspaces, runs the skills' scripts against them,
asserts the files the skills produce, and exits non-zero on any mismatch.

Usage:
  python harness/run.py                 # every case
  python harness/run.py --case setup    # one case
  python harness/run.py --keep          # keep scratch directories
  python harness/run.py --list          # list cases
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "skills"
SETUP = SKILLS / "setup-ctf-skills" / "scripts" / "setup.py"
INTAKE = SKILLS / "solve-ctf" / "scripts" / "intake.py"
WRAPUP = SKILLS / "organize-ctf-writeups" / "scripts" / "wrapup.py"
NOTE = SKILLS / "solve-ctf" / "scripts" / "note.py"
CONTRACT = REPO_ROOT / "harness" / "contract_checks.py"

CATEGORIES = ["Misc", "Web", "Pwn", "Crypto", "Reverse", "Forensics", "OSINT", "Malware", "AI-ML"]
NOTES_FIELDS = ["Challenge", "Category", "Target", "Flag format", "Status", "Flag"]
NOTES_SECTIONS = [
    "Statement",
    "Attachments",
    "Hints",
    "Observations",
    "Dead ends",
    "Tools & versions",
    "Script",
    "Conclusion",
]


class CaseFailure(Exception):
    pass


class Check:
    """Collects assertion failures for one case."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.failures: list[str] = []
        self.notes: list[str] = []

    def ok(self, condition: object, message: str) -> None:
        if not condition:
            self.failures.append(message)

    def equal(self, actual: object, expected: object, message: str) -> None:
        if actual != expected:
            self.failures.append(f"{message}: expected {expected!r}, got {actual!r}")

    def contains(self, needle: str, haystack: str, message: str) -> None:
        if needle not in haystack:
            self.failures.append(f"{message}: {needle!r} not found")

    def not_contains(self, needle: str, haystack: str, message: str) -> None:
        if needle in haystack:
            self.failures.append(f"{message}: {needle!r} unexpectedly present")


def run(script: Path, *args: str, cwd: Path | None = None, expect: int | None = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    if expect is not None and result.returncode != expect:
        raise CaseFailure(
            f"{script.name} exited {result.returncode} (expected {expect})\n"
            f"args: {args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def snapshot(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def notes_path(workspace: Path, category: str, challenge: str) -> Path:
    return workspace / "Challenges" / category / challenge / "notes.md"


def set_note_field(path: Path, field: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    text = re.sub(rf"^\|\s*{re.escape(field)}\s*\|.*$", f"| {field} | {value} |", text, count=1, flags=re.MULTILINE)
    path.write_text(text, encoding="utf-8")


def set_note_section(path: Path, section: str, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"(^##\s+{re.escape(section)}\s*$\n)(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    text, count = pattern.subn(lambda m: m.group(1) + "\n" + body + "\n\n", text, count=1)
    if count != 1:
        raise CaseFailure(f"section {section!r} not found in {path}")
    path.write_text(text, encoding="utf-8")


def setup_workspace(root: Path, name: str = "Demo CTF", tools: bool = True) -> tuple[Path, Path]:
    workspace = root / "workspace"
    tools_path = root / "tools" / "tools.md"
    args = [
        str(workspace),
        "--competition",
        name,
        "--flag-format",
        "flag{...}",
        "--tools-path",
        str(tools_path),
    ]
    if tools:
        args += ["--cli-tool", "sqlmap|SQL injection|sqlmap|1.7"]
    run(SETUP, *args)
    return workspace, tools_path


def h2_sections(text: str) -> list[str]:
    return re.findall(r"^##\s+(.+?)\s*$", text, re.MULTILINE)


def h3_sections(text: str) -> list[str]:
    return re.findall(r"^###\s+(.+?)\s*$", text, re.MULTILINE)


def make_attachment(root: Path, name: str, content: str) -> Path:
    path = root / name
    path.write_text(content, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- cases


def case_contract(root: Path) -> Check:
    check = Check("contract")
    result = subprocess.run([sys.executable, str(CONTRACT)], capture_output=True, text=True, check=False)
    check.equal(result.returncode, 0, "contract checks should pass")
    if result.returncode != 0:
        check.notes.append(result.stdout + result.stderr)
    return check


def case_setup(root: Path) -> Check:
    check = Check("setup")
    workspace, tools_path = setup_workspace(root)

    for directory in ("Challenges", "WP", "templates"):
        check.ok((workspace / directory).is_dir(), f"missing directory {directory}/")
    for filename in ("AGENTS.md", "templates/notes.md"):
        check.ok((workspace / filename).is_file(), f"missing {filename}")
    check.ok(tools_path.is_file(), "tools inventory not created")
    check.ok(not (workspace / "CLAUDE.md").exists(), "AGENTS.md should be chosen when CLAUDE.md is absent")

    spec = (workspace / "AGENTS.md").read_text(encoding="utf-8")
    for needle in (
        "Challenges/<Category>/<challenge>/",
        "## Notes",
        "### Summary",
        "### Solution",
        "### Flag",
        "writeups.md",
        "WP/",
        "Flag format",
        "flag{...}",
        "Wrap-up",
        tools_path.as_posix(),
    ):
        check.contains(needle, spec, f"spec should state {needle!r}")
    for category in CATEGORIES:
        check.contains(category, spec, f"spec should list category {category!r}")

    tools = tools_path.read_text(encoding="utf-8")
    check.contains("sqlmap", tools, "tools inventory should record the CLI tool")
    check.contains("| Tool | Purpose | Invocation | Notes |", tools, "tools inventory schema header")

    before = snapshot(root)
    second = run(SETUP, str(workspace), "--competition", "Demo CTF", "--tools-path", str(tools_path))
    check.contains('"tools_inventory": "reused"', second.stdout, "second run should reuse the inventory")
    after = snapshot(root)
    check.equal(after, before, "second setup run must not add or change files")

    # CLAUDE.md is preferred when it already exists.
    claude_root = root / "claude-case"
    claude_workspace = claude_root / "workspace"
    claude_workspace.mkdir(parents=True)
    (claude_workspace / "CLAUDE.md").write_text("# pre-existing\n", encoding="utf-8")
    run(
        SETUP,
        str(claude_workspace),
        "--competition",
        "Claude CTF",
        "--tools-path",
        str(claude_root / "tools.md"),
        "--cli-tool",
        "x|y|z|w",
    )
    claude_spec = (claude_workspace / "CLAUDE.md").read_text(encoding="utf-8")
    check.contains("CTF workspace spec", claude_spec, "CLAUDE.md should receive the spec when it exists")
    check.ok(not (claude_workspace / "AGENTS.md").exists(), "AGENTS.md should not be created when CLAUDE.md exists")

    # The inventory is only written once; a missing inventory with no answers asks for them.
    bare_root = root / "bare"
    bare = run(
        SETUP,
        str(bare_root / "workspace"),
        "--tools-path",
        str(bare_root / "tools.md"),
        expect=4,
    )
    check.contains("tools inventory missing", bare.stderr, "missing inventory should ask for tooling answers")

    # Malformed tooling answers fail with the documented usage error, not a traceback.
    bad = run(
        SETUP,
        str(bare_root / "workspace"),
        "--tools-path",
        str(bare_root / "tools.md"),
        "--tools-file",
        str(bare_root / "does-not-exist.json"),
        expect=2,
    )
    check.contains("could not read tooling answers", bad.stderr, "bad tooling input should report a usage error")

    # ADR-0007: the default inventory path is the sibling solve-ctf skill folder.
    printed = run(SETUP, "--print-tools-path")
    check.equal(
        printed.stdout.strip(),
        (SKILLS / "solve-ctf" / "tools.md").as_posix(),
        "default tools path should live inside the solve-ctf skill folder",
    )
    return check


def case_intake(root: Path) -> Check:
    check = Check("intake")
    workspace, _ = setup_workspace(root)
    attachment = make_attachment(root, "handout.zip", "zip-bytes")

    chinese = (
        "solve-ctf ez-sql，小明说他的网站非常安全，让我来测测看 "
        f"靶机：1.2.3.4:1337 附件：{attachment.as_posix()}"
    )
    result = run(INTAKE, chinese, "--workspace", str(workspace))
    summary = json.loads(result.stdout)
    check.equal(summary["challenge"], "ez-sql", "challenge name")
    check.equal(summary["category"], "Web", "Chinese intake category")
    check.equal(summary["target"], "1.2.3.4:1337", "Chinese intake target")

    challenge_dir = workspace / "Challenges" / "Web" / "ez-sql"
    notes = (challenge_dir / "notes.md").read_text(encoding="utf-8")
    for field in NOTES_FIELDS:
        check.ok(re.search(rf"^\|\s*{re.escape(field)}\s*\|", notes, re.MULTILINE), f"notes missing field {field!r}")
    for section in NOTES_SECTIONS:
        check.ok(re.search(rf"^##\s+{re.escape(section)}\s*$", notes, re.MULTILINE), f"notes missing section {section!r}")
    check.contains("小明说他的网站非常安全", notes, "statement should be recorded verbatim")
    check.not_contains("靶机：", notes, "statement should not duplicate the target label")
    check.contains("1.2.3.4:1337", notes, "target should be recorded")
    check.contains("| Status | unsolved |", notes, "new notes should be unsolved")
    check.ok((challenge_dir / "attachments" / "handout.zip").is_file(), "attachment not copied into the challenge folder")
    check.contains("attachments/handout.zip", notes, "attachment should be referenced in notes")

    english = run(
        INTAKE,
        "solve-ctf baby-rsa RSA with a small e, flag format: flag{...} "
        f"target: nc 10.0.0.5 31337 attachments: {attachment.as_posix()} hints: check small exponents",
        "--workspace",
        str(workspace),
    )
    english_summary = json.loads(english.stdout)
    check.equal(english_summary["category"], "Crypto", "English intake category")
    check.equal(english_summary["flag_format"], "flag{...}", "English intake flag format")
    check.equal(len(english_summary["attachments"]), 1, "English attachments label should be parsed")
    english_notes = Path(english_summary["notes"]).read_text(encoding="utf-8")
    check.contains("check small exponents", english_notes, "English hints label should be recorded")

    collision = run(INTAKE, "solve-ctf baby-rsa another RSA task", "--workspace", str(workspace))
    collision_summary = json.loads(collision.stdout)
    check.ok(collision_summary["collision"], "same-name challenge should report a collision")
    check.ok(Path(collision_summary["challenge_dir"]).is_dir(), "collision folder should exist")
    check.ok(Path(collision_summary["challenge_dir"]).name == "baby-rsa-2", "collision folder should be suffixed")

    minimal = run(INTAKE, "solve-ctf forensics-1 a disk image to analyse", "--workspace", str(workspace))
    minimal_summary = json.loads(minimal.stdout)
    check.equal(minimal_summary["category"], "Forensics", "minimal intake category")
    check.equal(minimal_summary["target"], None, "minimal intake should have no target")
    check.equal(minimal_summary["attachments"], [], "minimal intake should have no attachments")
    minimal_notes = (Path(minimal_summary["notes"])).read_text(encoding="utf-8")
    check.contains("| Target | — |", minimal_notes, "minimal notes should record an empty target")

    # An attachment path containing a space stays a single attachment.
    spaced = make_attachment(root, "hand out.bin", "binary")
    spaced_result = run(
        INTAKE,
        f"solve-ctf spaced-attach a web challenge 附件：{spaced.as_posix()}",
        "--workspace",
        str(workspace),
    )
    spaced_summary = json.loads(spaced_result.stdout)
    check.equal(len(spaced_summary["attachments"]), 1, "a path with a space should stay one attachment")
    check.ok(spaced_summary["attachments"][0]["exists"], "the spaced attachment should be found")

    # A missing attachment is reported, not silently claimed as copied.
    missing = run(
        INTAKE,
        f"solve-ctf missing-attach a web challenge 附件：{root / 'not-here.zip'}",
        "--workspace",
        str(workspace),
    )
    missing_summary = json.loads(missing.stdout)
    check.ok(not missing_summary["attachments"][0]["exists"], "missing attachment should be reported")
    check.equal(missing_summary["attachments"][0]["copied"], None, "missing attachment should not be claimed as copied")
    missing_notes = Path(missing_summary["notes"]).read_text(encoding="utf-8")
    check.contains("missing at intake", missing_notes, "missing attachment should be marked in notes")

    # Keyword scoring must not fire on substrings (ai in explain, des in modes).
    puzzle = run(
        INTAKE,
        "solve-ctf puzzle-box please explain the modes of this puzzle",
        "--workspace",
        str(workspace),
    )
    check.equal(json.loads(puzzle.stdout)["category"], "Misc", "substring keywords should not mis-file the challenge")

    ambiguous = run(
        INTAKE,
        "solve-ctf mystery help me figure this thing out",
        "--workspace",
        str(workspace),
        expect=3,
    )
    check.contains("needs-category", ambiguous.stdout, "ambiguous intake should ask for a category")

    override = run(
        INTAKE,
        "solve-ctf mystery2 help me figure this thing out",
        "--workspace",
        str(workspace),
        "--category",
        "Misc",
    )
    check.equal(json.loads(override.stdout)["category"], "Misc", "--category should override inference")

    # Notes are updated while solving through the bundled helper.
    exploit = challenge_dir / "solve" / "exploit.py"
    exploit.write_text("print('flag{ez}')\n", encoding="utf-8")
    run(
        NOTE,
        "--challenge-dir",
        str(challenge_dir),
        "--section",
        "Observations",
        "--text",
        "the login form is injectable",
        "--section",
        "Dead ends",
        "--text",
        "a WAF blocked UNION payloads",
        "--section",
        "Tools & versions",
        "--text",
        "sqlmap 1.7, python 3.14",
        "--script-file",
        str(exploit),
        "--field",
        "Status=solved",
        "--field",
        "Flag=flag{ez_sql}",
    )
    updated = (challenge_dir / "notes.md").read_text(encoding="utf-8")
    check.contains("the login form is injectable", updated, "observations should be recorded")
    check.contains("a WAF blocked UNION payloads", updated, "dead ends should be recorded")
    check.contains("sqlmap 1.7, python 3.14", updated, "tool versions should be recorded")
    check.contains("print('flag{ez}')", updated, "the working script should be recorded")
    check.contains("| Status | solved |", updated, "status should be updated")
    check.contains("| Flag | flag{ez_sql} |", updated, "flag should be recorded")
    return check


def case_wrapup(root: Path) -> Check:
    check = Check("wrapup")
    workspace, _ = setup_workspace(root)

    run(INTAKE, "solve-ctf solved-one textbook RSA with a tiny exponent", "--workspace", str(workspace))
    run(INTAKE, "solve-ctf closed-early a web challenge with a login page", "--workspace", str(workspace))

    solved_notes = notes_path(workspace, "Crypto", "solved-one")
    set_note_field(solved_notes, "Status", "solved")
    set_note_field(solved_notes, "Flag", "flag{note_flag}")
    set_note_section(solved_notes, "Observations", "Small e with no padding; integer cube root of the ciphertext.")
    set_note_section(solved_notes, "Conclusion", "Textbook RSA with a tiny exponent.")
    # A decoy in the solved challenge's transcript must never be read.
    (workspace / "Challenges/Crypto/solved-one/session/transcript.md").write_text(
        "we guessed flag{decoy_should_not_win}\n", encoding="utf-8"
    )
    # The unsolved challenge was actually solved just before its session closed.
    (workspace / "Challenges/Web/closed-early/session/transcript.md").write_text(
        "finally: flag{transcript_flag}\n", encoding="utf-8"
    )

    run(WRAPUP, "--workspace", str(workspace))
    merged_path = workspace / "writeups.md"
    check.ok(merged_path.is_file(), "wrap-up should write writeups.md")
    merged = merged_path.read_text(encoding="utf-8")

    check.equal(sorted(h2_sections(merged)), ["closed-early", "solved-one"], "one H2 per solved challenge")
    h3 = h3_sections(merged)
    for section in ("Summary", "Solution", "Flag"):
        check.equal(h3.count(section), 2, f"each challenge should have one H3 {section}")
    check.contains("flag{note_flag}", merged, "note-solved flag should appear")
    check.not_contains("flag{decoy_should_not_win}", merged, "solved note is authoritative; its transcript is never read")
    check.contains("flag{transcript_flag}", merged, "unsolved-but-actually-solved flag should be recovered")

    for category, challenge in (("Crypto", "solved-one"), ("Web", "closed-early")):
        writeup = workspace / "Challenges" / category / challenge / "writeup.md"
        check.ok(writeup.is_file(), f"per-challenge write-up missing for {challenge}")
        body = writeup.read_text(encoding="utf-8")
        check.ok(body.startswith(f"## {challenge}\n"), f"{challenge} write-up should start with an H2 title")
    check.ok((workspace / "WP" / "writeups.md").is_file(), "WP/writeups.md should exist")
    check.ok((workspace / "WP" / "Crypto-solved-one.md").is_file(), "WP should hold per-challenge copies")

    # A flag recovered from a transcript is persisted, so the note becomes authoritative.
    closed_notes = notes_path(workspace, "Web", "closed-early").read_text(encoding="utf-8")
    check.contains("| Status | solved |", closed_notes, "transcript-solved note should be marked solved")
    check.contains("| Flag | flag{transcript_flag} |", closed_notes, "transcript flag should be persisted")
    return check


def case_integration(root: Path) -> Check:
    check = Check("integration")
    workspace, _ = setup_workspace(root, name="Integration CTF")

    run(INTAKE, "solve-ctf crypto-one an RSA challenge with a tiny exponent", "--workspace", str(workspace))
    run(INTAKE, "solve-ctf web-one a login page with a SQL injection", "--workspace", str(workspace))

    crypto_notes = notes_path(workspace, "Crypto", "crypto-one")
    set_note_field(crypto_notes, "Status", "solved")
    set_note_field(crypto_notes, "Flag", "flag{integration_note}")
    set_note_section(crypto_notes, "Conclusion", "Tiny exponent, integer cube root.")
    (workspace / "Challenges/Web/web-one/session/transcript.md").write_text(
        "flag{integration_transcript}\n", encoding="utf-8"
    )

    run(WRAPUP, "--workspace", str(workspace))
    merged = (workspace / "writeups.md").read_text(encoding="utf-8")
    check.equal(sorted(h2_sections(merged)), ["crypto-one", "web-one"], "integration should merge both solved challenges")
    check.contains("flag{integration_note}", merged, "note branch flag")
    check.contains("flag{integration_transcript}", merged, "transcript branch flag")
    for section in ("Summary", "Solution", "Flag"):
        check.equal(h3_sections(merged).count(section), 2, f"integration should have two H3 {section}")

    # The deliverable is self-contained: working material is disposable afterwards.
    for disposable in (
        workspace / "Challenges/Crypto/crypto-one/solve",
        workspace / "Challenges/Crypto/crypto-one/attachments",
        workspace / "Challenges/Crypto/crypto-one/session",
        workspace / "Challenges/Web/web-one/session",
    ):
        if disposable.exists():
            shutil.rmtree(disposable)
    check.ok((workspace / "writeups.md").is_file(), "writeups.md should survive disposing of working material")
    check.ok((workspace / "WP" / "writeups.md").is_file(), "WP archive should survive disposing of working material")
    check.contains("flag{integration_note}", (workspace / "writeups.md").read_text(encoding="utf-8"), "deliverable keeps the note flag")
    return check


CASES = {
    "contract": case_contract,
    "setup": case_setup,
    "intake": case_intake,
    "wrapup": case_wrapup,
    "integration": case_integration,
}


def main() -> int:
    parser = argparse.ArgumentParser(prog="fixture-harness")
    parser.add_argument("--case", action="append", choices=sorted(CASES), help="run only this case (repeatable)")
    parser.add_argument("--list", action="store_true", help="list cases and exit")
    parser.add_argument("--keep", action="store_true", help="keep scratch directories")
    args = parser.parse_args()

    if args.list:
        for name in sorted(CASES):
            print(name)
        return 0

    selected = args.case or sorted(CASES)
    scratch = Path(tempfile.mkdtemp(prefix="ctf-fixture-"))
    failures: list[str] = []
    try:
        for name in selected:
            case_root = scratch / name
            case_root.mkdir(parents=True, exist_ok=True)
            try:
                check = CASES[name](case_root)
            except CaseFailure as error:
                failures.append(f"{name}: {error}")
                print(f"FAIL {name}")
                continue
            if check.failures:
                failures.extend(f"{name}: {failure}" for failure in check.failures)
                print(f"FAIL {name}")
                for failure in check.failures:
                    print(f"  - {failure}")
                for note in check.notes:
                    print(note)
            else:
                print(f"PASS {name}")
    finally:
        if args.keep:
            print(f"\nscratch kept at {scratch}")
        else:
            shutil.rmtree(scratch, ignore_errors=True)

    if failures:
        print(f"\n{len(failures)} fixture failure(s)", file=sys.stderr)
        return 1
    print(f"\nall {len(selected)} fixture cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
