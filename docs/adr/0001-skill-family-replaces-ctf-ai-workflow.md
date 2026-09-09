# Skill family replaces ctf-ai-workflow

**Status**: partially superseded — the family no longer fetches challenges or submits flags (ADR-0005); its source home is now the consolidated `ZZY2357/skills` catalog instead of a dedicated repo; the migration of platform knowledge stands.

We are building the CTF automation as a **family of small verb-named skills** (mirroring the mattpocock engineering skills: a setup skill, a state-driven operator, a task decomposer) instead of continuing the single monolithic `ctf-ai-workflow` skill. This repo (`ctf-workflow-ai`) is the canonical source home; the old skill and its `progress.json` format are migrated into the family, then retired from install locations.

Why: live-competition solving shares the engineering-flow shape mattpocock's skills already solve — one operator session owning shared state, per-unit-of-work sessions that must be fresh and isolated, explicit serial/concurrent edges between units. A monolith grows one context window and cannot express "this challenge's solve may run in parallel with that one". Migrating, not forking, keeps platform knowledge (in-browser fetch auth, submission caching, challenge-folder conventions, edge cases) instead of maintaining two overlapping state models that drift.
