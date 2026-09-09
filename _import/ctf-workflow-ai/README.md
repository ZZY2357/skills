# ctf-workflow-ai

A small, self-contained **skill family** for solving live CTF challenges and writing
them up. Three skills and two files:

| Skill | Job |
|---|---|
| `setup-ctf-skills` | One run per competition: scaffold the competition workspace, write its spec, generate the tools inventory once. |
| `solve-ctf` | One session per challenge: take the challenge in, create its folder and notes, then solve it while keeping the notes current. |
| `organize-ctf-writeups` | The wrap-up: find solved challenges with no writeup, fill the gaps, merge every writeup into one file. |

The family **never logs into the platform, never fetches challenges, and never submits
flags** — the human does both (ADR-0003). The only external skill reused is `ctf-writeup`;
no category skill is loaded during a solve (ADR-0006).

Design decisions live in [`docs/adr/`](docs/adr/) and the vocabulary in
[`CONTEXT.md`](CONTEXT.md). Read those before changing behaviour.

## Install convention

Each skill is a **self-contained, copy-installable folder** under `skills/`:

```
skills/
  setup-ctf-skills/      SKILL.md, scripts/setup.py, templates/
  solve-ctf/             SKILL.md, scripts/intake.py, tools.example.md, tools.md
  organize-ctf-writeups/ SKILL.md, scripts/wrapup.py
```

To install, copy the skill folder(s) into your harness's skill directory, for example:

```bash
cp -r skills/setup-ctf-skills     ~/.pi/agent/skills/
cp -r skills/solve-ctf            ~/.pi/agent/skills/
cp -r skills/organize-ctf-writeups ~/.pi/agent/skills/
```

Copy **all three** folders next to each other. `setup-ctf-skills` resolves the tools
inventory path relative to its own location (`../solve-ctf/tools.md`), so the folders must
remain siblings.

**The repo working copy is the master for the tools inventory; harness copies are
deployed snapshots** (ADR-0007). A deployed `setup-ctf-skills` writes `tools.md` into the
deployed `solve-ctf` folder. To persist it, copy that file back to
`skills/solve-ctf/tools.md` in this repo. The real `tools.md` is gitignored; only
`tools.example.md` is tracked.

Scripts need **Python 3** (standard library only) and nothing else.

## Using the family

```bash
# 1. Once per competition — choose a workspace outside this repo (never commit flags)
/setup-ctf-skills D:\ctf\my-event

# 2. Once per challenge, from inside the workspace
/solve-ctf ez-sql，小明说他的网站非常安全… 靶机：1.2.3.4:1337 附件：./handout.zip

# 3. At the end of the event (or any time)
/organize-ctf-writeups
```

Workspace layout produced by setup:

```
<workspace>/
  AGENTS.md | CLAUDE.md     spec: folder conventions, notes fields, writeup rules, flag format
  Challenges/<Category>/<challenge>/
    notes.md                the per-challenge working record
    attachments/            copied-in challenge files
    solve/                  working scripts
    session/                optional session transcripts (used by wrap-up only when the note is unsolved)
    writeup.md              the durable write-up
  WP/                       published writeup archive
  writeups.md               merged competition write-up
  templates/notes.md        notes template
```

The workspace is **disposable** once every challenge is written up.

## Development

Deterministic checks, no third-party dependencies:

```bash
python harness/contract_checks.py   # family hard rules (frontmatter, no category skills, gitignore, notes fields)
python harness/run.py               # fixture harness: setup, intake, wrap-up, full flow
python harness/run.py --case setup  # one case
```

`harness/run.py` creates scratch workspaces under a temp directory, runs the skills'
scripts, asserts the files they produce, and exits non-zero on any mismatch.

`contract_checks.py` scans shipped artifacts (skills, README, `CONTEXT.md`, `docs/agents/`).
`docs/adr/` is exempt because decision records must be free to name the skills the family
rejected, and `harness/` is exempt because it contains the check itself.
