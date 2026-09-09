# Machine tooling state lives inside the skill, gitignored

`tools.md` — the list of CLI tools and MCP servers the machine actually has — is generated **once** by `setup-ctf-skills` from what the human says they have, and stored **inside the family's skill folder** (`solve-ctf/tools.md`), not at an invented global path. The repo tracks only `tools.example.md`; `tools.md` is gitignored. Setup regenerates it only when it is missing, so re-running setup per competition does not re-interrogate the human.

Why: a global state directory (e.g. `~/.ctf/tools.md`) was rejected as an awkward home for something that belongs to the skill consuming it; a per-competition copy was rejected because tooling is a property of the machine, not of an event. Keeping it in the skill means it travels with the skill into every harness that copies it, and the public repo never carries one machine's inventory. Cost: updating the skill from the repo can clobber the file, and multiple harness copies can drift — the repo working copy is the master, harness copies are deployed snapshots.

Considered options: global `~/.ctf/tools.md` (rejected — new hidden state location); per-competition `tools.md` in the workspace (rejected — machine property); committing it (rejected — one machine's inventory in a public repo).
