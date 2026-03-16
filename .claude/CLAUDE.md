# GENERAL

## work method
Make full use of agent or Claude Code team members
Split files to prevent them becoming excessively large.
Before beginning the task, I utilise jin-interview skills.

## MCP
Actively use MCP servers for efficient work:
- **Serena**: Use symbolic tools (find_symbol, get_symbols_overview) for code exploration instead of reading entire files
- **Context7**: Query library docs before implementing unfamiliar APIs
- **context-mode**: Route large outputs (>20 lines) through ctx_execute to protect context window

## write plan
Always save plans as files named Header1.

## completion report
```
[DONE] Recommend commit messages using jin-commit skills
```

## test case
alway create teset case (do not git commit)

## Backend
python 3.12

### Management
uv

### type checker
ty

### linter & formatter
ruff

### logging
loguru

### etc
Always write `doc strings`
Always include a traceback for error tracking.
Minimise code duplication.

## Frontend
React + TypeScript + vite

### icon bundle
https://github.com/microsoft/fluentui-system-icons

### management
npm

