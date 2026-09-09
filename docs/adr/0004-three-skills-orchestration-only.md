# Three skills: ctf-open, ctf-drive, ctf-triage

**Status**: superseded — rejected in the re-grill. The family is not an orchestrator; only setup and knowledge capture (spec + writeup) are in scope. See ADR-0005.

The family is exactly three skills, `ctf-` prefixed:

- **`ctf-open`** — per-competition kickoff: scaffold the workspace, log in, cache the platform profile, fetch the challenge list into the state record.
- **`ctf-drive`** — state-driven operator: read `state.md`, report, write the session brief for the chosen unit, collect the human's report, advance statuses, run the end-of-competition wrap-up.
- **`ctf-triage`** — rank the frontier and choose the next unit(s).

The family **orchestrates but never spawns sessions**: the operator writes a brief, the human opens the session, the human reports back. Decomposition of a multi-stage challenge is an action performed inside the session working that challenge — not a fourth skill.

Why three: triage (choosing what to work) and driving (advancing state) are different cognitive tasks with different cadence; decomposition needs the full context of the session that is inside the challenge, so extracting it into a skill would mean handing that context off. Why no spawning: flag submission is already human (ADR-0003), so the human is in the loop regardless; keeping session launch human makes the family harness-neutral (ADR-0002) and removes cross-harness process control from its job.

Considered options: one monolithic skill (rejected — grows a single context window, cannot express per-unit freshness); the old phase-split of separate init/fetch/solve/submit/status skills (rejected — five entry points for one job); operator-spawned sessions (rejected — harness-bound, and unnecessary once the human is already in the loop).
