<!-- Developer guide for agent prompt templates. Catalog of agents is in ../README.md -->

# Agent Prompt Authoring Guide

> 이 문서는 `plugins/jin-claude/agents/` 하위 에이전트 프롬프트 템플릿을 작성/유지하기 위한 **개발자 가이드**입니다. 에이전트 카탈로그(각 에이전트의 이름·역할)는 `../README.md` 를 참조하세요.

---

## Prompt Template Format

각 `<agent-name>.md` 파일은 아래 구조를 따릅니다.

```markdown
---
name: agent-name
description: Brief description of what this agent does
# model: 생략 — 호출자 세션의 모델을 상속합니다 (v3.0.4+ 정책).
#        명시가 필요하면 `model: opus | sonnet | haiku` 로 고정 가능.
tools: [Read, Glob, Grep, ...]
---

<Role>
에이전트의 정체성과 전문 영역.
</Role>

<Critical_Constraints>
금지된 행동 (차단 시 실패를 반환해야 함).
</Critical_Constraints>

## Instructions
구체적인 동작 지침.

## Output Format
결과 반환 형식.
```

### frontmatter 필드

| 필드 | 필수 | 비고 |
|------|------|------|
| `name` | ✅ | 에이전트 식별자. `Agent({subagent_type: "<name>"})` 호출 시 매칭됩니다. |
| `description` | ✅ | 라우터가 에이전트 선택 시 참고. |
| `tools` | 선택 | 허용 툴 whitelist. 생략 시 기본 툴셋. |
| `disallowedTools` | 선택 | 차단 툴 blacklist (읽기 전용 에이전트에서 자주 사용). |
| `model` | **생략 권장** | 생략 시 **호출자 세션 모델 상속** — 경제적 설계. 고정이 필요한 경우만 명시. |

---

## Creating a New Agent

1. `agents/<new-agent>.md` 파일 생성, 위 포맷에 맞춰 frontmatter 작성
2. Role / Critical_Constraints / Instructions / Output Format 섹션 구성
3. `../README.md` 의 해당 카테고리 표에 한 줄 추가
4. 필요 시 `skills/<relevant-skill>/SKILL.md` 에서 `Agent` 호출 예제에 포함

## Tool Assignment Patterns

| 에이전트 유형 | 권장 `tools` |
|---------------|-------------|
| Read-only 분석 | `[Read, Glob, Grep]` |
| Research / Web | `[Read, Glob, Grep, WebSearch, WebFetch]` |
| Execution (편집) | `[Read, Glob, Grep, Edit, Write, Bash, TodoWrite]` |
| Data/Compute | `[Read, Glob, Grep, Bash, python_repl]` |
| Orchestrator | `[Read, Glob, Grep, Agent, TaskCreate, TaskUpdate, TaskGet, TaskList, AskUserQuestion]` |

---

## Agent Categories (Common Tool Profiles)

| Category | Agents | Common Tools |
|----------|--------|--------------|
| Orchestration | `orchestrator-agent`, `task-planner-agent` | Read, Glob, Grep, Agent, TaskCreate, TaskUpdate |
| Interview | `jin-interview-agent`, `mole-interview-agent` | AskUserQuestion, Read, Glob, Grep, Write |
| CTI (MOLE) | `mole-research-agent`, `mole-review-agent`, `mole-report-presenter-agent`, `mole-intel-organizer-agent`, `mole-graph-generator-agent`, `mole-user-identifier-agent` | Read, Glob, Grep, WebSearch, WebFetch, Bash |
| SWE | `swe-agent`, `swe-agent-high` | Read, Glob, Grep, Edit, Write, Bash, lsp_* |
| SWE Analysis | `swe-analyst` | Read, Glob, Grep, Bash, lsp_* |
| SWE Verification | `swe-verifier` | Read, Glob, Grep, Bash, lsp_diagnostics |
| Language Expert | `python-expert` | Read, Glob, Grep, Edit, Write, Bash |

---

## Dependencies

- **Internal**: `skills/` 하위 스킬 워크플로우가 `Agent({subagent_type: ...})` 로 참조합니다.
- **External**: 없음 — 순수 Markdown 파일.

## Testing

에이전트 프롬프트는 실제 호출 통합 테스트로 검증합니다. 키워드 라우팅(훅) 테스트는 `../tests/` 에 격리되어 있습니다.
