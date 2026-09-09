---
name: organize-ctf-writeups
description: Wrap up a CTF competition — find solved challenges that lack a write-up, generate the missing ones from their notes, and merge every write-up into one competition deliverable. Use at the end of an event, or any time after a batch of solves. Do not use it to solve challenges, log in to a platform, or submit flags.
---

# organize-ctf-writeups

The wrap-up. Runs per competition, after solving or at the end of the event. It finds every
**solved** challenge that lacks a write-up, fills the gaps from the notes, and merges
everything into one file.

## 1. Find the gaps

From inside the competition workspace:

```bash
python <skill-dir>/scripts/wrapup.py --detect
```

It reports, as JSON:

- `solved` — challenges treated as solved, with `source` (`note` or `transcript:<file>`),
  the flag, and whether a write-up already exists;
- `skipped` — challenges still unsolved.

**How "solved" is decided** (do not deviate):

- A note whose `Status` says `solved` is **authoritative** — its `session/` transcripts are
  never read. Trust it; do not waste time re-reading sessions.
- A note still marked `unsolved` is checked against that challenge's `session/`
  transcripts. If a flag is found there, the session was closed after the flag was found
  and before the note was updated, so the challenge **is** solved. Record the recovered
  flag and `Status: solved` in its `notes.md` before writing it up.

## 2. Fill the missing write-ups

For each solved challenge without `Challenges/<Category>/<challenge>/writeup.md`, generate
one by invoking the **`ctf-writeup`** skill. Source it from the challenge's `notes.md` and
the artifacts in its folder — **not** from the raw conversation, which may be gone.

Keep the family's heading contract so write-ups concatenate cleanly:

```markdown
## <challenge>

### Summary

<1–2 sentences: what it was and the core technique>

### Solution

<the key observations and one complete working script>

### Flag

```
<flag>
```
```

The challenge title is **H2**; `Summary`, `Solution` and `Flag` are **H3**. The
per-challenge write-up file stays in the challenge folder.

If you want a deterministic baseline instead of authoring by hand, run
`wrapup.py` without `--no-render`: it renders a write-up from the notes (observations,
script, conclusion, flag) using the same heading contract.

## 3. Merge

```bash
python <skill-dir>/scripts/wrapup.py --no-render
```

This merges every per-challenge write-up into `writeups.md` at the workspace root — one H2
per solved challenge, in category then challenge order — and copies the merged file plus
one file per challenge into the `WP/` archive for publishing individually.

Omit `--no-render` to also render any write-up still missing.

## 4. Report

Tell the player: how many challenges were solved, how many write-ups were generated, the
path to `writeups.md`, and the `WP/` archive contents. Remind them that the workspace's
scripts, attachments and scratch are disposable once the write-ups exist, but
`writeups.md` and `WP/` are the deliverable.

## Rules

- **A solved note is never re-checked** against transcripts.
- **An unsolved note is checked** against transcripts — this is the one case where a flag
  may be recovered after the fact.
- Write-ups come from notes and artifacts, never from the raw conversation.
- **Never log in to a platform or submit flags.** The human submits.
- Do not modify `ctf-writeup`; reuse its output rules as-is.

## Install note

This skill is a self-contained folder. It reads only the competition workspace; keep it
alongside `setup-ctf-skills` and `solve-ctf` in the harness's skill directory.
