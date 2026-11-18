# Linear MCP setup

Ask before each removal or install. Team doc: [Linear MCP Setup](https://linear.app/stealthmole/document/linear-mcp-setup-38a6483987e1).

1. Clean old setups:
   * MCP: in `claude mcp list`, Linear servers = name contains `linear` or URL `mcp.linear.app` (old `mcp-remote`, `/sse`, or `linear-server` in local/project scope — local overrides user). Never touch the claude.ai connector entry. Connector connected (`mcp__claude_ai_Linear__*` tools exist) → remove every Linear server; otherwise keep only user-scope `linear-server` with URL exactly `https://mcp.linear.app/mcp`. Scope from `claude mcp get <name>`, then `claude mcp remove <name> -s <scope>` (`project` = shared `.mcp.json`, ask before committing).
   * Old rules duplicate the skill: remove `@linear.md` / `@mcp-linear.md` lines in `~/.claude/CLAUDE.md` and project `CLAUDE.md` / `AGENTS.md`, then delete `~/.claude/linear.md`, `~/.claude/mcp-linear.md`, `<project>/linear.md`.
2. Install only if there is no connector and no `linear-server` — user scope, once per machine: `claude mcp add -s user --transport http linear-server https://mcp.linear.app/mcp`
3. If no connector and `claude mcp get linear-server` is not `✔ Connected`: user runs `/mcp` → `linear-server` → Authenticate (OAuth), then ask again. A server added mid-session needs a new session before `/mcp` shows it. Stop here.
4. Apply SKILL.md Rule 1 (project line in `CLAUDE.md`), then verify with `list_issues(project=<name>, assignee="me")`.
