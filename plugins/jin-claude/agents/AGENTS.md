<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-01-28 | Updated: 2026-03-09 -->

# agents (Prompt Templates)

Markdown prompt templates for all 13 agents in jinzy.

## Purpose

This directory contains the prompt templates that define agent behavior. Each file is a markdown document with YAML frontmatter for metadata.

## Key Files

### Interview Agents

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `jin-interview-agent.md` | jin-interview-agent | sonnet | Structured requirements interview and spec generation |

### Python Expert

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `python-expert.md` | python-expert | sonnet | Production-ready Python development |

### MOLE Agents (Korean CTI Specialists)

Specialized agents for MOLE (Malware/threat intelligence Organizer and Lifecycle Engine), focused on Korean-language Cyber Threat Intelligence.

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `mole-research-agent.md` | mole-research-agent | sonnet | Threat data collection and web research |
| `mole-review-agent.md` | mole-review-agent | opus | CTI profiling pipeline orchestrator |
| `mole-report-presenter-agent.md` | mole-report-presenter-agent | sonnet | PPTX/Markdown report generation |
| `mole-intel-organizer-agent.md` | mole-intel-organizer-agent | sonnet | Threat data classification and organization |
| `mole-graph-generator-agent.md` | mole-graph-generator-agent | sonnet | Threat relationship graph generation |
| `mole-interview-agent.md` | mole-interview-agent | sonnet | Pre-investigation interview for CTI scope |
| `mole-user-identifier-agent.md` | mole-user-identifier-agent | sonnet | Target user and audience identification |

## SWE Agents (Live-SWE-agent Integration)

Specialized agents for systematic software issue resolution, adapted from the Live-SWE-agent workflow (SWE-bench Verified #1, 79.2%).

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `swe-agent.md` | swe-agent | sonnet | 6단계 워크플로우 이슈 해결 실행자 |
| `swe-agent-high.md` | swe-agent-high | opus | 복잡한 교차 모듈 이슈 해결 |
| `swe-analyst.md` | swe-analyst | sonnet | 읽기 전용 근본원인 진단 |
| `swe-verifier.md` | swe-verifier | sonnet | 수정 후 독립 검증 |

## For AI Agents

### Working In This Directory

#### Prompt Template Format

Each file follows this structure:
```markdown
---
name: agent-name
description: Brief description of what this agent does
model: opus | sonnet | haiku
tools: [Read, Glob, Grep, ...]
---

# Agent Name

## Role
What this agent is and its expertise.

## Instructions
Detailed instructions for how the agent should behave.

## Constraints
What the agent should NOT do.

## Output Format
How results should be formatted.
```

#### Creating a New Agent Prompt

1. Create `new-agent.md` with YAML frontmatter
2. Define clear role, instructions, and constraints

### Common Patterns

**Tool assignment by agent type:**
- Read-only: `[Read, Glob, Grep]`
- Analysis: `[Read, Glob, Grep, WebSearch, WebFetch]`
- Execution: `[Read, Glob, Grep, Edit, Write, Bash, TodoWrite]`
- Data: `[Read, Glob, Grep, Bash, python_repl]`

### Testing Requirements

Agent prompts are tested via integration tests that spawn agents and verify behavior.

## Dependencies

### Internal
- Referenced by skill definitions in `skills/`

### External
None - pure markdown files.

## Agent Categories

| Category | Agents | Common Tools |
|----------|--------|--------------|
| Specialized | python-expert | Read, Glob, Grep, Edit, Write, Bash |
| Interview | jin-interview-agent | AskUserQuestion, Read, Glob, Grep, Write |
| CTI (MOLE) | mole-research-agent, mole-review-agent, mole-report-presenter-agent, mole-intel-organizer-agent, mole-graph-generator-agent, mole-interview-agent, mole-user-identifier-agent | Read, Glob, Grep, WebSearch, WebFetch, Bash |
| SWE | swe-agent, swe-agent-high | Read, Glob, Grep, Edit, Write, Bash, lsp_diagnostics, lsp_diagnostics_directory, lsp_goto_definition, lsp_find_references, python_repl |
| SWE Analysis | swe-analyst | Read, Glob, Grep, Bash, lsp_diagnostics, lsp_goto_definition, lsp_find_references, lsp_hover, python_repl |
| SWE Verification | swe-verifier | Read, Glob, Grep, Bash, lsp_diagnostics, lsp_diagnostics_directory, python_repl |

<!-- MANUAL: -->
