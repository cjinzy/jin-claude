# MCP Servers

Use a server only when its tools are in your tool list; otherwise fall back to built-in tools (Grep, Glob, Read, WebSearch).
Tool names below are the tool part only. The full name depends on how the server is installed: `mcp__<server>__<tool>`, `mcp__plugin_<plugin>_<server>__<tool>`, or `mcp__claude_ai_<connector>__<tool>`.

| Task | Server | Tools | Installed by |
|---|---|---|---|
| Code structure, symbol lookup, refactoring | Serena | call its instructions tool first; use what it exposes | init (plugin `serena`) |
| Library / API docs before using an unfamiliar API | Context7 | `resolve-library-id` → `query-docs` | init (plugin `context7`) |
| Output over 20 lines, logs, big JSON, fetching URLs | context-mode | `ctx_execute`, `ctx_batch_execute`, `ctx_fetch_and_index`, `ctx_search` | init (plugin `context-mode`) |
| Issue tracking | Linear | rules: @mcp-linear.md | claude.ai connector (per account) |
| Code search by meaning | Semble | `search`, `find_related` | personal |
| Long-term memory | Hindsight | `retain`, `recall` — rules: @memory-routing.md | personal |
| Browser automation, UI testing | Playwright | `browser_navigate`, `browser_snapshot`, `browser_click`, … | personal |
| Web search with citations | Tavily | search / extract (needs API key) | personal |
| Knowledge graph / RAG | GBrain | what it exposes | personal |
| Context compression | Headroom | `headroom_compress`, `headroom_retrieve` | personal |
| Explicit multi-step reasoning | Sequential-thinking | `sequentialthinking` | personal |

## Order of use
- Code: Semble to locate by meaning → Serena for exact symbols and edits.
- Use `Read` only for files you will edit; explore structure with Serena first when it is available.
- Libraries: query Context7 before implementing an unfamiliar API.
