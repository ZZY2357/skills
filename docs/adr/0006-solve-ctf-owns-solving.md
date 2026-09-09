# solve-ctf owns the solving flow; ctf-writeup is the only external skill reused

The family does **not** delegate to `solve-challenge` or to any `ctf-*` category skill (`ctf-web`, `ctf-pwn`, `ctf-crypto`, …). `solve-ctf` carries the whole per-challenge flow itself — intake, notes, solving, and the hand-off to the writeup — and `ctf-writeup` is the single external skill reused (for its submission-style output rules).

Why: the family is meant to be small and owned end-to-end. The category skills are large, overlapping, and pull a routing decision (and a lot of context) into every solve; the model already carries the techniques they document. Keeping exactly one external dependency makes the family's behaviour predictable and its maintenance surface tiny.

Considered options: delegate to `solve-challenge` + `ctf-*` (rejected — routing overhead, context bloat, behaviour varies with which category skill loads); use them optionally when they exist (rejected — the flow would differ per machine and per competition); fork their content into `solve-ctf` (rejected — that is the same encyclopedia, moved).
