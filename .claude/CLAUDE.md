# jin-AGENT.md

## GUIDELINES
- Source Of Truth(sot) is project
- When a repository's documentation and its existing code disagree, follow the conventions used in the existing code, and in your final reply point out each inconsistency you found between the documentation and the code.
- Give me the cold hard truth.
- When writing something intended for human consumption, (comment, commit message, reply to prompt) use as few words as possible. Pick every word meticulously to reduce the volume to a strict minimum. Be down to the point. Less is more.
- Avoid magic numbers and strings by extracting recurring or meaningful values into descriptive constants (const) or enums. Keep self-explanatory, one-off values inline to avoid clutter. If a value comes from a spec (e.g. HTTP 200 OK), use a constant regardless.
- Document the what and why with to-the-point comments, docstrings, and ASCII drawings for full systems. Minimise code duplication. Always include a traceback for error tracking.
- If the prompt indicates that a bug is being fixed, don't write the fix right away. First write the test. Observe it failing. Then write the fix. And observe the test passing. Always create test cases and add them to .gitignore (do not git commit).
- Make full use of agents or teams
- Split files to prevent them becoming excessively large
- Always save plans as files with searchable names.


## MCP Servers
@mcp-servers.md

## Completion
Complete tasks in this order: deploy(execute) → verify → jin-commit.

## Commit Report
[DONE] Recommend commit messages using jin-commit skill (loaded from plugin).

## Project Specs
- Backend: @backend-spec.md
- Frontend: @frontend-spec.md

## Memory routing
@memory-routing.md

## SoT (Source of Truth)
SoT lives in `sot/` (entry point `sot/Index.md`), managed locally and excluded from Git via .gitignore. Create and maintain it with the `jin-sot-create` skill, which defines the categories and file layout.

## Issue Management
Use Linear for tracking; follow @mcp-linear.md.
