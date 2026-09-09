# Skill Catalog

A public repository of skills authored in-house, installed with the `skills` CLI (`npx skills add ZZY2357/skills`). It carries only skills written here — third-party skills are never vendored into it — together with the language and decisions behind them.

## Language

### Repository

**Skill**:
A folder containing `SKILL.md` with `name` and `description` frontmatter, loaded by a coding harness. The unit the CLI installs.
_Avoid_: Plugin, extension, prompt, command

**Skill family**:
A set of skills designed to be installed together and that depend on each other at runtime; installing a subset leaves the family incomplete.
_Avoid_: Bundle, suite, package (when referring to a family)

**Skill catalog**:
This repository — the single install source for every skill authored here.
_Avoid_: Skills repo, collection, marketplace (a marketplace is third-party)

### CTF family

The CTF family is the trio `setup-ctf-skills`, `solve-ctf`, `organize-ctf-writeups`: scaffold the working area, record each challenge's solving information while it is being solved, then organise the result into writeups. It does **not** fetch challenges from the platform and does **not** submit flags — the human does both.

**Competition (比赛)**:
A single live CTF event, hosted on a remote platform, with its own deadline and challenge set. One working area per competition.
_Avoid_: Event, contest, game (except when quoting a platform's own term)

**Challenge (题目)**:
One solvable problem inside a competition, belonging to a category, holding one or more flags. The human decides which challenge to work; nothing is enumerated ahead of time.
_Avoid_: Problem, question, task, exercise

**Category (分类)**:
The canonical challenge taxonomy used for folder layout and writeup metadata: Misc, Web, Pwn, Crypto, Reverse, Forensics, OSINT, Malware, AI-ML.
_Avoid_: Domain, type (when referring to the taxonomy)

**Flag**:
The secret string that proves a challenge solved. Found while solving; submitted to the platform by the human.
_Avoid_: Token, key, answer

**Platform (平台)**:
The remote CTF site the human uses — challenge statements, instance provisioning, submission. The family never logs in to it.
_Avoid_: Site, server (when the user means the competition host)

**Solve (解题)**:
Working a challenge to find its flag. The session doing the solving is the unit of context; the family supports it, it does not schedule it.

**Competition workspace (比赛工作区, 简称工作区)**:
The per-event folder holding one competition's work: challenge folders, the WP archive, and the spec. Lives outside the skill repository at a configurable root (e.g. `D:\ctf\<event-slug>\`); disposable once every challenge is solved and written up.
_Avoid_: Working directory, project folder

**Spec**:
The agent instruction file at the root of a working area — `AGENTS.md`, or `CLAUDE.md` when that is the file already in use. Carries the conventions every session in that area must follow: folder layout, notes fields, writeup heading and merge rules, flag format. Written once by `setup-ctf-skills`; the durable source of conventions.
_Avoid_: `spec.md`, notes, README

**Intake (开题)**:
The moment the human hands a challenge to the family — running `/solve-ctf` with the statement, attachments and target. Intake remembers the challenge, creates its folder and basic files, then solving continues in the same session.
_Avoid_: Fetch, import, ingest, pull

**Notes (笔记)**:
The per-challenge working record of key solving information — challenge metadata, artifacts, remote instance, hints, observations, dead ends, the working script, the flag. Lives at `Challenges/<Category>/<challenge>/notes.md` while solving; disposable once the writeup exists.
_Avoid_: Spec, writeup draft, scratch

**Tools inventory (工具清单)**:
The file listing the tooling actually available on the machine — CLI tools (sqlmap, dirsearch, upx, …) and configured MCP servers (IDA MCP, jadx MCP, …) — with how to invoke each. Generated once from what the human says; stored inside the skill folder (gitignored) so a session knows what it may reach for.
_Avoid_: Tool list, toolbox, dependencies

**Wrap-up (收尾)**:
The end-of-competition pass: fill in missing writeups and merge all writeups into one file. It trusts `notes.md` when it says a challenge is **solved** (that line is written after the fact), but for challenges still marked **unsolved** it also reads that challenge's session transcripts — the session may have been closed after finding the flag, before the note was updated. A solved note is never re-checked against transcripts.
_Avoid_: Cleanup, archive, export

**Writeup (WP)**:
The durable per-challenge write-up, produced by `ctf-writeup`. Challenges are merged into one competition writeup file — `writeups.md` at the workspace root — each challenge an H2 section containing H3 `Summary` / `Solution` / `Flag`; the per-challenge file stays in the challenge folder.
_Avoid_: Notes, report

**Submit (提交)**:
Sending a found flag to the platform — a human action, out of the family's scope.

### Bridge

`bridge` lets a weak local harness borrow a strong web chat by copy-paste handoff. The human carries text between the two; the harness only participates at the first question and the final answer.

**Bridge package (首问包)**:
The sentinel-delimited block the harness emits for the human to paste into the web chat — task, context, and instructions in one piece.
_Avoid_: Prompt, request

**Answer package (终答包)**:
The sentinel-delimited block the web chat returns, which the harness parses back into the session.
_Avoid_: Reply, response

**Sentinel**:
An uppercase `===NAME===` marker on its own line, delimiting the package sections so a human and the harness read the same text.
_Avoid_: Tag, delimiter (when meaning the marker)

**Task type**:
The routing label — `debug`, `design`, `review`, `improve`, `code`, `general` — that selects the bridge package's template.
_Avoid_: Category (reserved for the CTF taxonomy)
