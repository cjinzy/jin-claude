<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-01-28 | Updated: 2026-02-28 -->

# agents (Prompt Templates)

Markdown prompt templates for all 56 agents in jinzy.

## Purpose

This directory contains the prompt templates that define agent behavior. Each file is a markdown document with YAML frontmatter for metadata.

## Key Files

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `architect.md` | architect | opus | Architecture, debugging, root cause analysis |
| `architect-medium.md` | architect-medium | sonnet | Moderate analysis tasks |
| `architect-low.md` | architect-low | haiku | Quick code questions |
| `executor.md` | executor | sonnet | Focused task implementation |
| `executor-high.md` | executor-high | opus | Complex multi-file changes |
| `executor-low.md` | executor-low | haiku | Simple single-file tasks |
| `explore.md` | explore | haiku | Fast codebase search |
| `explore-medium.md` | explore-medium | sonnet | Thorough search with reasoning |
| `explore-high.md` | explore-high | opus | Architectural discovery |
| `designer.md` | designer | sonnet | UI/UX, component design |
| `designer-high.md` | designer-high | opus | Complex UI architecture |
| `designer-low.md` | designer-low | haiku | Simple styling tweaks |
| `researcher.md` | researcher | sonnet | Documentation research |
| `researcher-low.md` | researcher-low | haiku | Quick doc lookups |
| `writer.md` | writer | haiku | Technical documentation |
| `vision.md` | vision | sonnet | Image/screenshot analysis |
| `critic.md` | critic | opus | Critical plan review |
| `analyst.md` | analyst | opus | Pre-planning requirements |
| `planner.md` | planner | opus | Strategic planning |
| `qa-tester.md` | qa-tester | sonnet | Interactive CLI testing |
| `qa-tester-high.md` | qa-tester-high | opus | Production-ready QA |
| `scientist.md` | scientist | sonnet | Data analysis |
| `scientist-high.md` | scientist-high | opus | Complex ML/research |
| `scientist-low.md` | scientist-low | haiku | Quick data inspection |
| `security-reviewer.md` | security-reviewer | opus | Security audits |
| `security-reviewer-low.md` | security-reviewer-low | haiku | Quick security scans |
| `build-fixer.md` | build-fixer | sonnet | Build error resolution |
| `build-fixer-low.md` | build-fixer-low | haiku | Simple type errors |
| `tdd-guide.md` | tdd-guide | sonnet | TDD workflow |
| `tdd-guide-low.md` | tdd-guide-low | haiku | Test suggestions |
| `code-reviewer.md` | code-reviewer | opus | Expert code review |
| `code-reviewer-low.md` | code-reviewer-low | haiku | Quick code checks |
| `backend-architect.md` | backend-architect | sonnet | Backend system design and reliability |
| `devops-architect.md` | devops-architect | sonnet | Infrastructure automation and deployment |
| `frontend-architect.md` | frontend-architect | sonnet | UI/UX architecture and accessibility |
| `system-architect.md` | system-architect | sonnet | Scalable system design |
| `performance-engineer.md` | performance-engineer | sonnet | Performance optimization |
| `security-engineer.md` | security-engineer | sonnet | Security vulnerability detection and compliance |
| `quality-engineer.md` | quality-engineer | sonnet | Testing strategies and quality assurance |
| `refactoring-expert.md` | refactoring-expert | sonnet | Code quality improvement |
| `python-expert.md` | python-expert | sonnet | Production-ready Python development |
| `requirements-analyst.md` | requirements-analyst | sonnet | Requirements discovery and specification |
| `root-cause-analyst.md` | root-cause-analyst | sonnet | Root cause investigation |
| `deep-research-agent.md` | deep-research-agent | sonnet | Comprehensive adaptive research |
| `learning-guide.md` | learning-guide | sonnet | Programming education and explanation |
| `socratic-mentor.md` | socratic-mentor | sonnet | Socratic learning guide |
| `technical-writer.md` | technical-writer | sonnet | Technical documentation |
| `pm-agent.md` | pm-agent | sonnet | Self-improvement workflow executor |
| `business-panel-experts.md` | business-panel-experts | sonnet | Multi-expert business strategy panel |

## Interview Agents

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `jin-interview-agent.md` | jin-interview-agent | sonnet | Structured requirements interview and spec generation |

## MOLE Agents (Korean CTI Specialists)

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

#### Tiered Variants

For model routing, create variants with complexity-appropriate instructions:

| Tier | File Suffix | Instructions Focus |
|------|-------------|-------------------|
| LOW (Haiku) | `-low.md` | Quick, simple tasks, minimal reasoning |
| MEDIUM (Sonnet) | Base file or `-medium.md` | Standard complexity |
| HIGH (Opus) | `-high.md` | Complex reasoning, deep analysis |

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
| Analysis | architect, architect-medium, architect-low | Read, Glob, Grep, lsp_diagnostics |
| Execution | executor, executor-low, executor-high | Read, Glob, Grep, Edit, Write, Bash, lsp_diagnostics |
| Search | explore, explore-medium, explore-high | Read, Glob, Grep, ast_grep_search, lsp_document_symbols, lsp_workspace_symbols |
| Research | researcher, researcher-low | WebSearch, WebFetch |
| Frontend | designer, designer-low, designer-high | Edit, Write, Bash |
| Docs | writer | Edit, Write |
| Visual | vision | Read, Glob, Grep |
| Planning | planner, analyst, critic | Read, Glob, Grep |
| Testing | qa-tester, qa-tester-high | Bash, Read, Grep, Glob, TodoWrite, lsp_diagnostics |
| Security | security-reviewer, security-reviewer-low | Read, Grep, Bash |
| Build | build-fixer, build-fixer-low | Read, Glob, Grep, Edit, Write, Bash, lsp_diagnostics, lsp_diagnostics_directory |
| TDD | tdd-guide, tdd-guide-low | Read, Grep, Glob, Bash, lsp_diagnostics |
| Review | code-reviewer, code-reviewer-low | Read, Grep, Glob, Bash, lsp_diagnostics |
| Data | scientist, scientist-low, scientist-high | Read, Glob, Grep, Bash, python_repl |
| Engineering | backend-architect, devops-architect, frontend-architect, system-architect | Read, Glob, Grep, Edit, Write, Bash |
| Quality | performance-engineer, security-engineer, quality-engineer, refactoring-expert | Read, Glob, Grep, Bash, lsp_diagnostics |
| Specialized | python-expert | Read, Glob, Grep, Edit, Write, Bash |
| Investigation | requirements-analyst, root-cause-analyst, deep-research-agent | Read, Glob, Grep, WebSearch, WebFetch |
| Communication | learning-guide, socratic-mentor, technical-writer | Read, Glob, Grep |
| Meta | pm-agent | Read, Glob, Grep, Edit, Write, Bash |
| Business | business-panel-experts | Read, Glob, Grep, WebSearch |
| Interview | jin-interview-agent | AskUserQuestion, Read, Glob, Grep, Write |
| CTI (MOLE) | mole-research-agent, mole-review-agent, mole-report-presenter-agent, mole-intel-organizer-agent, mole-graph-generator-agent, mole-interview-agent, mole-user-identifier-agent | Read, Glob, Grep, WebSearch, WebFetch, Bash |

<!-- MANUAL: -->
