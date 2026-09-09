# {{COMPETITION}} — CTF workspace spec

This file is the workspace's agent instruction file, written once by `setup-ctf-skills`.
Every session opened in this workspace follows the conventions below. It is safe to edit;
re-running setup never overwrites it.

- **Competition**: {{COMPETITION}}
- **Workspace root**: `{{WORKSPACE}}`
- **Flag format**: {{FLAG_FORMAT}}
- **Tools inventory**: `{{TOOLS_PATH}}`

## Layout

```
Challenges/<Category>/<challenge>/   one folder per challenge
  notes.md                           the working record (see Notes)
  attachments/                       challenge files, copied in on intake
  solve/                             working scripts and scratch
  session/                           optional session transcripts (*.md, *.txt)
  writeup.md                         the durable write-up
WP/                                  published write-up archive
writeups.md                          merged competition write-up
templates/notes.md                   notes template
```

Categories, in canonical order: {{CATEGORIES}}.

Challenge folders are created by `solve-ctf` intake. A name collision inside one category
gets a numeric suffix so folders never merge.

## Notes

`notes.md` is the per-challenge working record. Required fields, in a table:

| Field | Value |
|---|---|
| Challenge | |
| Category | |
| Target | host:port, or — |
| Flag format | |
| Status | unsolved \| solved |
| Flag | — |

Required sections: `Statement`, `Attachments`, `Hints`, `Observations`, `Dead ends`,
`Tools & versions`, `Script`, `Conclusion`.

Rules:

- The **Statement** is recorded verbatim.
- **Attachments** are referenced by original path and copied into `attachments/`.
- The notes are updated **while** solving — observations, dead ends, tool versions, the
  working script — then the flag and `Status: solved`.
- The write-up is generated from the notes and the challenge folder's artifacts, **never**
  from the raw conversation.
- Working material is disposable once the write-up exists.

## Write-ups

- Per challenge: `Challenges/<Category>/<challenge>/writeup.md`, and it stays there.
- The challenge title is **H2** (`## <challenge>`); `Summary`, `Solution` and `Flag` are
  **H3** (`### Summary`, `### Solution`, `### Flag`).
- Reuse `ctf-writeup`'s output rules for the prose; keep this heading contract so
  write-ups concatenate cleanly.
- All write-ups are merged into `writeups.md` at the workspace root: one H2 per solved
  challenge, in category then challenge order.
- `organize-ctf-writeups` also copies the merged file and one file per challenge into
  `WP/` for publishing individually.

## Wrap-up

`organize-ctf-writeups` finds solved challenges that lack a write-up, generates them, and
merges everything.

- A note marked `solved` is **authoritative** — its `session/` transcripts are never read.
- A note still marked `unsolved` is checked against that challenge's `session/`
  transcripts; a flag found there means the challenge was solved just before the session
  closed, and it is treated as solved.

## Hard rules

- Never log into the platform, never fetch challenges, never submit flags. The human
  submits on the platform; the agent only finds and surfaces the flag.
- Do not load a category skill during a solve; `solve-ctf` carries the whole flow.
- Keep flags out of any repository; this workspace lives outside the skill repository and
  is disposable once every challenge is written up.
