# GENERAL

## Tool Priority (Serena vs context-mode)
- 코드 탐색/심볼 검색/리팩터링: Serena 심볼릭 도구 우선 사용 (find_symbol, get_symbols_overview, find_referencing_symbols, replace_symbol_body)
- 외부 URL 수집, 대용량 명령 출력(빌드/테스트), 데이터 분석: context-mode 도구 사용 (ctx_execute, ctx_batch_execute, ctx_fetch_and_index)
- Read: 편집할 파일을 읽을 때만 사용. 코드 구조 파악은 Serena의 get_symbols_overview → find_symbol(include_body=True) 순서로 진행
- Grep/search_for_pattern: 심볼 이름을 모를 때는 Serena의 search_for_pattern 우선, 비코드 파일 검색은 Grep 사용

## work method
Make full use of agent or Claude Code team members
Split files to prevent them becoming excessively large.
Before beginning the task, I utilise jin-interview skills.

## MCP
Actively use MCP servers for efficient work:
- **Serena**: Use symbolic tools (find_symbol, get_symbols_overview) for code exploration instead of reading entire files
- **Context7**: Query library docs before implementing unfamiliar APIs
- **context-mode**: Route large outputs (>20 lines) through ctx_execute to protect context window
- **Context-Hub (chub)**: Use `chub search/get` for community-curated agent-optimized docs when Context7 lacks coverage

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

