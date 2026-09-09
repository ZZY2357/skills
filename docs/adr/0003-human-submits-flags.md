# Flags are submitted by the human, not the agent

The agent finds a flag and surfaces it; the **human submits it on the platform** and reports back; only then does the operator mark the challenge `submitted`. The family never auto-submits.

Why: submission is the one irreversible, platform-visible action. A wrong flag burns attempts, and the platform's confirmation is the only truth that a challenge is done. The old `ctf-ai-workflow` auto-submitted via in-browser fetch or API, which was fragile (session expiry, cookie replay outside the browser) and silently wrong on a malformed flag. Keeping submission manual puts the human exactly where their judgement is cheap and the cost of error is real, while the agent's work — finding and presenting the flag — stays automated. Consequence: `solved` is the state whose next action belongs to the human, and a rejected flag sends the challenge back to `in-progress`, not to `solved`.

Considered options: auto-submit any found flag (rejected — wrong-flag cost, fragile auth); format-gated auto-submit (rejected — flag formats lie often enough that the gate still needs a human); agent submits via the platform API (rejected — same fragility; most platforms' submission auth is browser-bound).
