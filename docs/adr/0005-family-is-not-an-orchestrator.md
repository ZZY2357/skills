# The family is not an orchestrator

The three-skill orchestration architecture (ADR-0004: `ctf-open` / `ctf-drive` / `ctf-triage`, session briefs, frontier, edges, spawning rules) is **rejected**. The family's jobs are **setup + the per-challenge solve flow + writeup organisation**: scaffold the competition workspace, take a challenge in when the human hands it over, record its key solving information as notes while solving it, and organise the result into writeups. Scheduling, prioritisation, ticketing and session launching are out of scope.

Why: during the grilling the orchestration layer kept growing (briefs, edges, status machine, verbs, single-writer rules) while the only jobs with durable value were the ones the user named — setup, writeup organisation, and persisting key solve information. Live-competition scheduling is done by the human, cheaply, in their head; a skill that models it adds ceremony without removing work.

Status: the new skill set and the spec's shape are still under re-grill; this ADR records the reversal, not the replacement.
