# jin-AGENT.md

## GUIDELINES
- Source Of Truth(sot) is project
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
SoT is managed locally and excluded from Git via .gitignore.

Structure:
- Root: sot/ directory
- Index: sot/Index.md (links to all entries)
- Content: Split by category into subdirectories with individual .md files.

Categories:
1. Project Overview — What this project is, purpose, goals
2. Tech Stack — Backend (@backend-spec.md), Frontend (@frontend-spec.md), Database, Infrastructure
3. Database Schema — Table definitions, column specs, ER diagrams
4. Architecture — Components, layers, data flow, API contracts
5. Workflow — How components interact, business logic flow, user journey, system behavior
6. Rules — Coding standards, naming conventions, commit rules (see jin-commit skill)

Create subdirectories under sot/ for each category (e.g., sot/architecture/). Store details in separate .md files. List all files in sot/Index.md.

## Issue Management
- Use Linear for tracking.
- Check for existing issues. Create one if none exists.
- When creating, fill in project, priority, assign, and label.
- When planning, set status to plan and write the plan.
- When working, set status to in progress.
- When done, write a summary, set status to done, and set a due date.
- If no project exists, ask the user whether to create one or which project to use.
