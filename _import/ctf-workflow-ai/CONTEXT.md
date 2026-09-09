# ctf-workflow-ai

Designs and develops an agent-skill family that supports **solving live CTF challenges and writing them up**: scaffold the working area, record each challenge's key solving information as notes *while* it is being solved, and organise the result into writeups. It does **not** fetch challenges from the platform and does **not** submit flags — the human does both. Once a challenge is solved and written up, its working material is disposable.

## Language

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
The secret string that proves a challenge solved. Found while solving; submitted to the platform by the human (ADR-0003).
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
The file listing the tooling actually available on the machine — CLI tools (sqlmap, dirsearch, upx, …) and configured MCP servers (IDA MCP, jadx MCP, …) — with how to invoke each. Generated once from what the human says; stored inside the skill folder (gitignored, ADR-0007) so a session knows what it may reach for.
_Avoid_: Tool list, toolbox, dependencies

**Wrap-up (收尾)**:
The end-of-competition pass: fill in missing writeups and merge all writeups into one file. It trusts `notes.md` when it says a challenge is **solved** (that line is written after the fact), but for challenges still marked **unsolved** it also reads that challenge's session transcripts — the session may have been closed after finding the flag, before the note was updated. A solved note is never re-checked against transcripts.
_Avoid_: Cleanup, archive, export

**Writeup (WP)**:
The durable per-challenge write-up, produced by `ctf-writeup`. Challenges are merged into one competition writeup file — `writeups.md` at the workspace root — each challenge an H2 section containing H3 `Summary` / `Solution` / `Flag`; the per-challenge file stays in the challenge folder.
_Avoid_: Notes, report

**Submit (提交)**:
Sending a found flag to the platform — a human action, out of the family's scope (ADR-0003).
