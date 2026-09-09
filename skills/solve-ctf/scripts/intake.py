#!/usr/bin/env python3
"""Take a challenge into a competition workspace.

Parses one free-form intake command (Chinese or English labels), infers the
category, creates `Challenges/<Category>/<challenge>/` with `notes.md`,
`attachments/`, `solve/` and `session/`, and copies any attachments in.

Exit codes:
  0  challenge recorded
  2  usage error
  3  the category could not be inferred confidently — ask the player, then re-run
     with --category
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

SKILL_DIR = Path(__file__).resolve().parent.parent
BUNDLED_NOTES_TEMPLATE = SKILL_DIR / "templates" / "notes.md"

COMMAND_PREFIX = re.compile(r"^\s*/?\s*(?:solve[-_ ]ctf)\b[\s:：,，]*", re.IGNORECASE)
NAME_TOKEN = re.compile(r"^([^\s,，:：]+)")

TARGET_LABELS = ("靶机", "目标机", "目标", "target")
ATTACH_LABELS = ("附件", "文件", "attachments", "attachment", "files", "file")
FLAG_LABELS = ("flag格式", "flag format", "flag 格式", "flag")
HINT_LABELS = ("提示", "hints", "hint")
CATEGORY_LABELS = ("分类", "类别", "category")

_LABEL_PATTERN = re.compile(
    r"(?P<label>"
    + "|".join(
        re.escape(x)
        for x in sorted(
            TARGET_LABELS + ATTACH_LABELS + FLAG_LABELS + HINT_LABELS + CATEGORY_LABELS,
            key=len,
            reverse=True,
        )
    )
    + r")\s*[:：]",
    re.IGNORECASE,
)

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Web": (
        "web", "http", "https", "url", "sql", "sqli", "xss", "ssrf", "csrf", "cookie",
        "session", "php", "flask", "django", "node", "nginx", "apache", "jwt", "upload",
        "rce", "lfi", "rfi", "注入", "网站", "网页", "接口", "后台", "登录",
    ),
    "Pwn": (
        "pwn", "binary", "elf", "buffer overflow", "overflow", "rop", "shellcode", "libc",
        "heap", "stack", "format string", "溢出", "二进制", "栈", "堆", "canary", "gets",
    ),
    "Crypto": (
        "crypto", "rsa", "aes", "des", "cipher", "encrypt", "decrypt", "密文", "加密",
        "解密", "密码", "prime", "modulus", "ecc", "ecdsa", "xor", "base64", "哈希",
        "hash", "nonce", "signature", "签名",
    ),
    "Reverse": (
        "reverse", "reversing", "apk", "dex", "decompile", "反编译", "逆向", "wasm",
        "firmware", "固件", "jadx", "ida", "ghidra", "unpack", "upx", "bytecode", "反汇编",
    ),
    "Forensics": (
        "forensic", "forensics", "取证", "pcap", "流量", "wireshark", "memory dump",
        "内存", "disk", "镜像", "volatility", "registry", "注册表", "steg", "隐写",
        "steganography", "exif", "carving",
    ),
    "OSINT": (
        "osint", "情报", "社工", "social", "geolocation", "地理", "username", "用户名",
        "wayback", "whois", "dork", "邮箱", "email",
    ),
    "Malware": (
        "malware", "恶意", "病毒", "木马", "c2", "c&c", "yara", "obfuscat", "混淆",
        "packer", "加壳", "persistence", "rootkit",
    ),
    "AI-ML": (
        "machine learning", "机器学习", "neural", "神经网络", "llm", "prompt injection",
        "adversarial", "jailbreak", "lora", "embedding", "classifier", "模型", "ai",
    ),
    "Misc": (
        "misc", "杂项", "pyjail", "jail", "sandbox", "esoteric", "esolang", "qr", "二维码",
        "audio", "音频", "编码", "encode", "decode", "puzzle", "brainfuck",
    ),
}

GENERIC_FLAG_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{1,24}\{[^}\s]{1,120}\}")


def _canonical_category(value: str) -> str | None:
    wanted = value.strip().lower().replace("_", "-")
    for category in CATEGORIES:
        if category.lower() == wanted:
            return category
    return None


def _slugify(name: str) -> str:
    slug = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", name.strip())
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-.")
    return slug or "challenge"


def _clean_value(value: str) -> str:
    return value.strip().strip("，,。;；\n\t ")


def parse_command(raw: str, base_dir: Path | None = None) -> dict[str, object]:
    """Parse a free-form intake command into structured fields."""
    base_dir = base_dir or Path.cwd()
    text = COMMAND_PREFIX.sub("", raw.strip(), count=1)
    match = NAME_TOKEN.match(text)
    if not match:
        raise ValueError("no challenge name found in the intake command")
    name = match.group(1)
    rest = text[match.end():].lstrip(" \t，,：:")

    fields: dict[str, list[str]] = {
        "target": [],
        "attachments": [],
        "flag_format": [],
        "hints": [],
        "category": [],
    }
    matches = list(_LABEL_PATTERN.finditer(rest))
    for index, label_match in enumerate(matches):
        label = label_match.group("label").lower()
        start = label_match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(rest)
        value = _clean_value(rest[start:end])
        if label in TARGET_LABELS:
            fields["target"].append(value)
        elif label in ATTACH_LABELS:
            fields["attachments"].append(value)
        elif label in FLAG_LABELS:
            fields["flag_format"].append(value)
        elif label in HINT_LABELS:
            fields["hints"].append(value)
        elif label in CATEGORY_LABELS:
            fields["category"].append(value)

    target = _clean_value(fields["target"][0].splitlines()[0]) if fields["target"] else ""
    flag_format = fields["flag_format"][0] if fields["flag_format"] else ""
    if not flag_format:
        found = GENERIC_FLAG_RE.search(rest)
        flag_format = found.group(0) if found else ""
    hints = " ".join(fields["hints"]).strip()
    category_hint = fields["category"][0] if fields["category"] else ""

    attachments: list[str] = []
    for blob in fields["attachments"]:
        for piece in re.split(r"[,，;；\n]+", blob):
            piece = _clean_value(piece)
            if not piece:
                continue
            if " " in piece and not (base_dir / piece).expanduser().exists():
                attachments.extend(token for token in piece.split() if token)
            else:
                attachments.append(piece)

    return {
        "name": name,
        "statement": rest,
        "target": target,
        "attachments": attachments,
        "flag_format": flag_format,
        "hints": hints,
        "category_hint": category_hint,
    }


def infer_category(statement: str) -> tuple[str | None, dict[str, int]]:
    """Score categories against the statement. Returns (best, scores)."""
    lowered = statement.lower()
    scores: dict[str, int] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in lowered:
                score += 2 if " " in keyword else 1
        if score:
            scores[category] = score
    if not scores:
        return None, scores
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best, best_score = ranked[0]
    tied = [name for name, score in ranked if score == best_score]
    if len(tied) > 1:
        return None, scores
    return best, scores


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


def _render_notes(
    template: str,
    *,
    name: str,
    category: str,
    target: str,
    flag_format: str,
    statement: str,
    attachments: list[tuple[str, str]],
    hints: str,
) -> str:
    if attachments:
        attachment_lines = "\n".join(
            f"- `{source}` → `attachments/{copied}`" for source, copied in attachments
        )
    else:
        attachment_lines = "_none_"
    values = {
        "CHALLENGE": name,
        "CATEGORY": category,
        "TARGET": target or "—",
        "FLAG_FORMAT": flag_format or "—",
        "STATEMENT": statement or "_(not provided)_",
        "ATTACHMENTS": attachment_lines,
        "HINTS": hints or "_none_",
    }
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", value)
    return out


def _unique_challenge_dir(category_dir: Path, slug: str) -> tuple[Path, bool]:
    candidate = category_dir / slug
    if not candidate.exists():
        return candidate, False
    index = 2
    while (category_dir / f"{slug}-{index}").exists():
        index += 1
    return category_dir / f"{slug}-{index}", True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solve-ctf intake",
        description="Take a challenge into a competition workspace.",
    )
    parser.add_argument("command", help="the free-form intake command")
    parser.add_argument("--workspace", help="competition workspace (default: discovered from cwd)")
    parser.add_argument("--category", help="override the inferred category")
    parser.add_argument("--base-dir", help="base directory for relative attachment paths (default: cwd)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        parsed = parse_command(
            args.command,
            Path(args.base_dir).expanduser().resolve() if args.base_dir else Path.cwd(),
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else find_workspace(Path.cwd())
    if workspace is None or not workspace.is_dir():
        print(
            "no competition workspace found; run setup-ctf-skills first or pass --workspace",
            file=sys.stderr,
        )
        return 5

    if args.category:
        category = _canonical_category(args.category)
        if category is None:
            print(f"unknown category: {args.category!r}", file=sys.stderr)
            return 2
        scores: dict[str, int] = {}
    elif parsed["category_hint"]:
        category = _canonical_category(str(parsed["category_hint"]))
        scores = {}
        if category is None:
            print(
                f"unknown category label: {parsed['category_hint']!r}",
                file=sys.stderr,
            )
            return 2
    else:
        category, scores = infer_category(str(parsed["statement"]))
        if category is None:
            print(
                "category could not be inferred confidently; ask the player and re-run with "
                "--category <Misc|Web|Pwn|Crypto|Reverse|Forensics|OSINT|Malware|AI-ML>",
                file=sys.stderr,
            )
            print(json.dumps({"status": "needs-category", "scores": scores}, ensure_ascii=False))
            return 3

    base_dir = Path(args.base_dir).expanduser().resolve() if args.base_dir else Path.cwd()
    category_dir = workspace / "Challenges" / category
    category_dir.mkdir(parents=True, exist_ok=True)
    challenge_dir, collided = _unique_challenge_dir(category_dir, _slugify(str(parsed["name"])))
    challenge_dir.mkdir(parents=True)
    (challenge_dir / "attachments").mkdir()
    (challenge_dir / "solve").mkdir()
    (challenge_dir / "session").mkdir()

    copied: list[tuple[str, str]] = []
    attachment_report: list[dict[str, object]] = []
    for source_text in parsed["attachments"]:  # type: ignore[union-attr]
        source = Path(source_text).expanduser()
        if not source.is_absolute():
            source = base_dir / source
        copied_name = source.name
        destination = challenge_dir / "attachments" / copied_name
        exists = source.is_file()
        if exists:
            shutil.copy2(source, destination)
        copied.append((source_text, copied_name))
        attachment_report.append(
            {
                "source": source_text,
                "resolved": source.as_posix(),
                "copied": f"attachments/{copied_name}" if exists else None,
                "exists": exists,
            }
        )

    workspace_template = workspace / "templates" / "notes.md"
    template_path = workspace_template if workspace_template.is_file() else BUNDLED_NOTES_TEMPLATE
    notes = _render_notes(
        template_path.read_text(encoding="utf-8"),
        name=str(parsed["name"]),
        category=category,
        target=str(parsed["target"]),
        flag_format=str(parsed["flag_format"]),
        statement=str(parsed["statement"]),
        attachments=copied,
        hints=str(parsed["hints"]),
    )
    notes_path = challenge_dir / "notes.md"
    notes_path.write_text(notes, encoding="utf-8")

    summary = {
        "status": "ok",
        "challenge": parsed["name"],
        "category": category,
        "challenge_dir": challenge_dir.as_posix(),
        "notes": notes_path.as_posix(),
        "target": parsed["target"] or None,
        "flag_format": parsed["flag_format"] or None,
        "attachments": attachment_report,
        "collision": collided,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
