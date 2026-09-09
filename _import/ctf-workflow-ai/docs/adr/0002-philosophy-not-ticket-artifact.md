# Carry the philosophy, not the ticket artifact

The CTF skill family borrows the **invariants** behind the mattpocock engineering skills — state in files not in the conversation; one fresh context window per unit of work; edges declared only where they are real; a single writer per state file; decisions to the human, facts to the agent; actively maintained domain vocabulary; the five phase-boundary options — but **not** the `to-tickets` artifact (a pre-planned set of tickets with blocking edges published to a tracker).

Live CTF breaks the artifact's assumptions: challenges are opaque until opened, so ticket sizing is guesswork; the competition level is almost a flat graph, so "marking concurrency" conveys nothing; and a timed event makes ticket publishing pure overhead. What survives is the unit of work (one challenge) and edges only where they genuinely exist — a multi-stage challenge's internal step chain, or a meta-challenge that consumes another challenge's flag.

Considered options: publishing tickets to GitHub as `to-tickets` does (rejected — fake planning, overhead mid-event); building a CTF-native ticket system (rejected — same, with no dependency structure to encode).
