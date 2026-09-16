# MCP Servers

Choose by task type. Detailed usage: @mcp-*.md files.

## Code Tasks
- Semble: Natural language search and code discovery — @mcp-semble.md
- Serena: Symbolic code manipulation, refactoring, and structure exploration — @mcp-serena.md  
  (use `get_symbols_overview` → `find_symbol` for code navigation, `search_for_pattern` for symbol search)
- Context7: Library documentation lookup before implementing unfamiliar APIs — @mcp-context7.md

## Project Management
- Linear: Issue tracking and workflow management — @mcp-linear.md

## Memory
- Hindsight: Persistent memory storage and retrieval — @mcp-hindsight.md

## External Content
- Tavily: Web search and content extraction (requires authentication) — @mcp-tavily.md
- Playwright: Browser automation and UI testing — @mcp-playwright.md
- GBrain: Knowledge graph and RAG queries — @mcp-gbrain.md

## Output Handling
- context-mode: Large output processing (>20 lines) and batch operations — @mcp-context-mode.md  
  (use `ctx_execute`, `ctx_batch_execute`, `ctx_fetch_and_index` for external URLs, build outputs, data analysis)
- Headroom: Automatic context window optimization — @mcp-headroom.md

## Reasoning
- Sequential-Thinking: Complex multi-step reasoning tasks — @mcp-sequential-thinking.md

## File Reading
Use `Read` only for files that will actually be edited. For code structure exploration, always use Serena's symbolic tools first.
