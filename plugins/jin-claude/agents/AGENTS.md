<!-- Parent: ../AGENTS.md -->
<!-- Generated: 2026-01-28 | Updated: 2026-03-09 -->

# agents (Prompt Templates)

Markdown prompt templates for all 15 agents in jinzy.

## Purpose

This directory contains the prompt templates that define agent behavior. Each file is a markdown document with YAML frontmatter for metadata.

## Key Files

### Interview Agents

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `jin-interview-agent.md` | jin-interview-agent | sonnet | Structured requirements interview and spec generation |

### Orchestration Agents

| File | Agent | Model | Purpose |
|------|-------|-------|---------|
| `orchestrator-agent.md` | orchestrator-agent | opus | 멀티 에이전트 파이프라인 관리 및 태스크 디스패치 |
| `task-planner-agent.md` | task-planner-agent | opus | 요청 분해, 의존성 그래프 생성, 에이전트 라우팅 |

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

## Skills (Workflow Definitions)

에이전트가 참여하는 스킬 워크플로우 목록. 각 스킬은 `skills/<name>/SKILL.md`에 정의된다.

### Orchestration Skills

| Skill | 트리거 | 설명 |
|-------|--------|------|
| `jin-orchestrator` | "jin orchestrate", "오케스트레이션" | 풀 오케스트레이션 파이프라인 (Planning→Executing→Verifying→Fixing) |
| `jin-maxwork` | "jin maxwork", "병렬" | 병렬 실행 엔진 — 독립 태스크를 worktree 격리 병렬 실행 |
| `jin-fsd` | "jin fsd", "자율실행" | 단계별 승인 자율실행 (오케스트레이터 + AskUserQuestion 게이트) |
| `jin-ralph` | "jin ralph" | 자기참조 반복 루프 (최대 5회, verifier PASS까지) |

### Analysis Skills

| Skill | 트리거 | 설명 |
|-------|--------|------|
| `jin-gcc` | "jin gcc", "다관점" | 멀티 관점 분석 (codex/gemini CLI 또는 Claude 5관점 fallback) |
| `jin-cleanser` | "jin cleanser", "jin deslop" | AI 슬롭 리뷰어 — 8카테고리 정적+시맨틱 스캔 (리포트 전용) |
| `jin-deepinit` | "jin deepinit", "프로젝트 분석" | 프로젝트 구조 분석 + 에이전트 추천 + AGENTS.md 생성 |

### Existing Skills

| Skill | 트리거 | 설명 |
|-------|--------|------|
| `jin-claude-init` | "jin init", "jin 초기화" | 팀원 Claude Code 환경 초기화 |
| `jin-commit` | "jin commit" | gitmoji 기반 커밋 메시지 자동 추천 |
| `jin-interview` | "jin interview" | 구조화된 요구사항 인터뷰 → 스펙 문서 생성 |
| `jin-swe-fix` | "jin swe" | SWE-agent 워크플로우 기반 이슈 해결 |
| `py-standard` | - | Python 프로젝트 표준 컨벤션 가이드 |

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
| Orchestration | orchestrator-agent, task-planner-agent | Read, Glob, Grep, Agent, TaskCreate, TaskUpdate |
| Specialized | python-expert | Read, Glob, Grep, Edit, Write, Bash |
| Interview | jin-interview-agent | AskUserQuestion, Read, Glob, Grep, Write |
| CTI (MOLE) | mole-research-agent, mole-review-agent, mole-report-presenter-agent, mole-intel-organizer-agent, mole-graph-generator-agent, mole-interview-agent, mole-user-identifier-agent | Read, Glob, Grep, WebSearch, WebFetch, Bash |
| SWE | swe-agent, swe-agent-high | Read, Glob, Grep, Edit, Write, Bash, lsp_diagnostics, lsp_diagnostics_directory, lsp_goto_definition, lsp_find_references, python_repl |
| SWE Analysis | swe-analyst | Read, Glob, Grep, Bash, lsp_diagnostics, lsp_goto_definition, lsp_find_references, lsp_hover, python_repl |
| SWE Verification | swe-verifier | Read, Glob, Grep, Bash, lsp_diagnostics, lsp_diagnostics_directory, python_repl |

<!-- MANUAL: -->
