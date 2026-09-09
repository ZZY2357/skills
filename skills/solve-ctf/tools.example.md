# Tools inventory (example)

This is the tracked **example** template. The real inventory is generated once by
`setup-ctf-skills` and written to `skills/solve-ctf/tools.md`, which is **gitignored**
(ADR-0007). Copy this file to `tools.md` if you want to seed it by hand.

Schema: `tool | purpose | invocation (command or MCP name) | notes (version, limits)`.

| Tool | Purpose | Invocation | Notes |
|---|---|---|---|
| sqlmap | SQL injection testing | `sqlmap` | 1.7+, `--batch` for non-interactive |
| dirsearch | Web content discovery | `dirsearch -u <url>` | 0.4.3 |
| upx | Unpack packed binaries | `upx -d <file>` | 4.x |
| IDA MCP | Disassembly / decompilation | MCP `ida` | configured in harness |
| jadx MCP | Android decompilation | MCP `jadx` | configured in harness |
