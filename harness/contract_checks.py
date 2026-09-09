#!/usr/bin/env python3
"""Deterministic contract checks for the CTF skill family.

Fails fast when a skill drifts from the family's hard rules, so the
no-orchestration / no-category-skill decisions (ADR-0005, ADR-0006) cannot be
undone by accident.

Exit codes:
  0  every check passed
  1  at least one violation (readable messages on stderr/stdout)
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

REQUIRED_NOTES_FIELDS = ["Challenge", "Category", "Target", "Flag format", "Status", "Flag"]
REQUIRED_NOTES_SECTIONS = [
    "Statement",
    "Attachments",
    "Hints",
    "Observations",
    "Dead ends",
    "Tools & versions",
    "Script",
    "Conclusion",
]
REQUIRED_CATEGORIES = [
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

# `ctf-writeup` is the one reused external skill; `ctf-workflow-ai` is this repo.
FORBIDDEN_REFERENCE = re.compile(
    r"\bsolve-challenge\b|\bctf-(?:web|pwn|crypto|reverse|forensics|osint|malware|misc|ai-ml)\b",
    re.IGNORECASE,
)

TOOLS_FILE = SKILLS_DIR / "solve-ctf" / "tools.md"
TOOLS_EXAMPLE = SKILLS_DIR / "solve-ctf" / "tools.example.md"
NOTES_TEMPLATES = [
    SKILLS_DIR / "setup-ctf-skills" / "templates" / "notes.md",
    SKILLS_DIR / "solve-ctf" / "templates" / "notes.md",
]

# Decision records and the harness legitimately name the rejected skills, so the
# shipped-artifact scan skips them and checks everything else in the repo.
SCAN_EXCLUDED_PREFIXES = ("docs/adr/", "harness/")
SCAN_EXCLUDED_PARTS = {".git", ".pi", ".pi-glla", "__pycache__"}
SCAN_SUFFIXES = {".md", ".py", ".json", ".txt", ".yml", ".yaml"}


class Report:
    def __init__(self) -> None:
        self.violations: list[str] = []
        self.passes: list[str] = []

    def check(self, name: str, problems: list[str]) -> None:
        if problems:
            self.violations.extend(f"{name}: {problem}" for problem in problems)
        else:
            self.passes.append(name)


def _frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT)
        if any(part in SCAN_EXCLUDED_PARTS for part in rel.parts):
            continue
        if rel.as_posix().startswith(SCAN_EXCLUDED_PREFIXES):
            continue
        if path.suffix.lower() in SCAN_SUFFIXES:
            files.append(path)
    return files


def _load_categories(script: Path) -> list[str] | None:
    spec = importlib.util.spec_from_file_location(f"_contract_{script.stem}", script)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    categories = getattr(module, "CATEGORIES", None)
    return list(categories) if isinstance(categories, (list, tuple)) else None


def check_frontmatter(report: Report) -> None:
    problems: list[str] = []
    skills = sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()) if SKILLS_DIR.is_dir() else []
    if not skills:
        problems.append("no skill folders found under skills/")
    for skill in skills:
        skill_md = skill / "SKILL.md"
        if not skill_md.is_file():
            problems.append(f"{skill.name}: missing SKILL.md")
            continue
        data = _frontmatter(skill_md.read_text(encoding="utf-8"))
        if data is None:
            problems.append(f"{skill.name}: SKILL.md has no YAML frontmatter")
            continue
        for field in ("name", "description"):
            if not data.get(field):
                problems.append(f"{skill.name}: frontmatter missing non-empty `{field}`")
        if data.get("name") and data["name"] != skill.name:
            problems.append(f"{skill.name}: frontmatter name {data['name']!r} != folder name")
    report.check("frontmatter", problems)


def check_forbidden_references(report: Report) -> None:
    problems: list[str] = []
    for path in _iter_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            match = FORBIDDEN_REFERENCE.search(line)
            if match:
                rel = path.relative_to(REPO_ROOT).as_posix()
                problems.append(f"{rel}:{lineno}: references {match.group(0)!r}")
    report.check("no-category-skill-references", problems)


def check_tools_inventory(report: Report) -> None:
    problems: list[str] = []
    if not TOOLS_EXAMPLE.is_file():
        problems.append(f"{TOOLS_EXAMPLE.relative_to(REPO_ROOT).as_posix()}: missing example template")
    if TOOLS_EXAMPLE.is_file():
        tracked = _git("ls-files", "--error-unmatch", TOOLS_EXAMPLE.relative_to(REPO_ROOT).as_posix())
        if tracked.returncode != 0:
            problems.append(
                f"{TOOLS_EXAMPLE.relative_to(REPO_ROOT).as_posix()}: example template is not tracked by git"
            )
        ignored_example = _git("check-ignore", "-q", TOOLS_EXAMPLE.relative_to(REPO_ROOT).as_posix())
        if ignored_example.returncode == 0:
            problems.append(
                f"{TOOLS_EXAMPLE.relative_to(REPO_ROOT).as_posix()}: example template must not be gitignored"
            )
    if TOOLS_FILE.exists():
        tracked = _git("ls-files", "--error-unmatch", TOOLS_FILE.relative_to(REPO_ROOT).as_posix())
        if tracked.returncode == 0:
            problems.append(f"{TOOLS_FILE.relative_to(REPO_ROOT).as_posix()}: real inventory must not be tracked")
    ignored = _git("check-ignore", "-q", TOOLS_FILE.relative_to(REPO_ROOT).as_posix())
    if ignored.returncode != 0:
        problems.append(f"{TOOLS_FILE.relative_to(REPO_ROOT).as_posix()}: real inventory is not gitignored")
    report.check("tools-inventory-gitignore", problems)


def check_notes_templates(report: Report) -> None:
    problems: list[str] = []
    contents: list[tuple[Path, str]] = []
    for template in NOTES_TEMPLATES:
        if not template.is_file():
            problems.append(f"{template.relative_to(REPO_ROOT).as_posix()}: missing notes template")
            continue
        text = template.read_text(encoding="utf-8")
        contents.append((template, text))
        for field in REQUIRED_NOTES_FIELDS:
            if not re.search(rf"^\|\s*{re.escape(field)}\s*\|", text, re.MULTILINE):
                problems.append(
                    f"{template.relative_to(REPO_ROOT).as_posix()}: missing required field {field!r}"
                )
        for section in REQUIRED_NOTES_SECTIONS:
            if not re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE):
                problems.append(
                    f"{template.relative_to(REPO_ROOT).as_posix()}: missing required section {section!r}"
                )
    if len(contents) == 2 and contents[0][1] != contents[1][1]:
        problems.append("notes templates differ: " + " vs ".join(p.relative_to(REPO_ROOT).as_posix() for p, _ in contents))
    report.check("notes-template", problems)


def check_category_lists(report: Report) -> None:
    problems: list[str] = []
    scripts = {
        "setup.py": SKILLS_DIR / "setup-ctf-skills" / "scripts" / "setup.py",
        "intake.py": SKILLS_DIR / "solve-ctf" / "scripts" / "intake.py",
        "wrapup.py": SKILLS_DIR / "organize-ctf-writeups" / "scripts" / "wrapup.py",
    }
    for name, script in scripts.items():
        if not script.is_file():
            problems.append(f"{name}: missing")
            continue
        try:
            categories = _load_categories(script)
        except Exception as error:  # noqa: BLE001 - report any import failure
            problems.append(f"{name}: could not load CATEGORIES ({error})")
            continue
        if categories != REQUIRED_CATEGORIES:
            problems.append(f"{name}: CATEGORIES {categories!r} != canonical list")
    spec_template = SKILLS_DIR / "setup-ctf-skills" / "templates" / "workspace-spec.md"
    if spec_template.is_file():
        text = spec_template.read_text(encoding="utf-8")
        if "{{CATEGORIES}}" not in text:
            for category in REQUIRED_CATEGORIES:
                if category not in text:
                    problems.append(f"workspace-spec.md: category {category!r} not listed")
    report.check("category-lists", problems)


def main() -> int:
    report = Report()
    check_frontmatter(report)
    check_forbidden_references(report)
    check_tools_inventory(report)
    check_notes_templates(report)
    check_category_lists(report)

    for name in report.passes:
        print(f"PASS {name}")
    if report.violations:
        print("", file=sys.stderr)
        for violation in report.violations:
            print(f"FAIL {violation}", file=sys.stderr)
        print(f"\n{len(report.violations)} contract violation(s)", file=sys.stderr)
        return 1
    print(f"\nall {len(report.passes)} contract checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
