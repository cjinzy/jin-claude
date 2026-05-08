# jin-claude

Claude Code용 멀티 에이전트 오케스트레이션 시스템. 15개 에이전트, 16개 스킬, statusline 유틸리티, CTI 파이프라인을 단일 플러그인으로 제공합니다.

> **현재 버전**: `3.0.9` · 마켓플레이스 슬러그: `jin-claudecode-mp`

## 빠른 시작

### 마켓플레이스 설치

```bash
# 1. Marketplace 등록
claude plugin marketplace add cjinzy/jin-claude

# 2. Plugin 설치
claude plugin install jin-claude@jin-claudecode-mp
```

### 팀원 환경 초기화 (jin-claude-init)

Claude Code 내에서 `/jin-claude-init`을 실행하면 마켓플레이스, 플러그인, 설정, 에이전트, 스킬, 통계 타이머를 자동으로 구성합니다.

**Step 1 — 마켓플레이스 7개 등록**

| Marketplace | 출처 |
|-------------|------|
| `obsidian-skills` | `kepano/obsidian-skills` |
| `ui-ux-pro-max-skill` | `nextlevelbuilder/ui-ux-pro-max-skill` |
| `claude-plugins-official` | `anthropics/claude-plugins-official` |
| `context-mode` | `mksglu/claude-context-mode` |
| `superclaude` | `SuperClaude-Org/SuperClaude_Plugin` |
| `harness` | `revfactory/harness` |
| `autoresearch` | `uditgoenka/autoresearch` |

**Step 2 — 플러그인 13개 일괄 설치**

`anthropics/claude-plugins-official`에서 `superpowers`, `context7`, `code-simplifier`, `claude-md-management`, `serena`, `pyright-lsp`, `agent-sdk-dev` 7개를 설치하고, 나머지 마켓플레이스에서 `obsidian`, `ui-ux-pro-max`, `context-mode`, `sc`, `harness`, `autoresearch`를 설치합니다.

**그 외 자동화 단계**

- `Step 3` — jin-claude 저장소에서 statusline · 설정 · venv 동기화 + 사용량 타이머 (macOS launchd / Linux systemd) 설치
- `Step 4` — `~/.claude/settings.json` deep merge (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS, statusLine, outputStyle, language 등)
- `Step 4.5` — standalone MCP 추가 설치 (현재는 비어 있음 — `serena`/`context7`은 plugin 형태로 이전됨)
- `Step 5` — `.claude-plugin/hooks/hooks.json` 4 hooks 적용 검증

---

## 에이전트 (15개)

> v3.0.4+ 부터 **모든 에이전트가 호출자 모델을 상속**합니다. 모델을 고정하지 않으므로 Opus 세션에서 호출하면 Opus로, Sonnet 세션에서 호출하면 Sonnet으로 실행됩니다. 필요 시 `Agent({model: ...})`로 명시 오버라이드 가능.

### Interview & Planning (3)

| 에이전트 | 설명 |
|----------|------|
| `jin-interview-agent` | 구조적 요구사항 인터뷰 → 구체적 spec 문서 생성 |
| `orchestrator-agent` | 멀티 에이전트 파이프라인 관리 · 태스크 분배 · 상태 전이 |
| `task-planner-agent` | 사용자 요청을 원자적 태스크로 분해 + 의존성 그래프 생성 |

### SWE Engineering (4)

| 에이전트 | 설명 |
|----------|------|
| `swe-agent` | Live-SWE-agent 6단계 워크플로우 이슈 해결 실행자 |
| `swe-agent-high` | 복잡한 교차 모듈 · 레이스 컨디션 · 아키텍처 결함 대응 |
| `swe-analyst` | 읽기 전용 근본 원인 진단 + 수정 계획 생성 |
| `swe-verifier` | 수정 후 독립 검증 (버그 재현 + 엣지케이스) |

### MOLE / CTI (7)

| 에이전트 | 설명 |
|----------|------|
| `mole-review-agent` | CTI 프로파일링 파이프라인 오케스트레이터 |
| `mole-interview-agent` | CTI 조사 전 인터뷰로 조사 방향 확정 |
| `mole-research-agent` | StealthMole MCP 기반 위협 인텔리전스 수집 |
| `mole-intel-organizer-agent` | 위협 인텔리전스 분류 · 평가 · 구조화 |
| `mole-user-identifier-agent` | 사용자 신원 상관관계 분석 |
| `mole-graph-generator-agent` | 조사 결과를 Mermaid 그래프로 통합 시각화 |
| `mole-report-presenter-agent` | 위협 인텔리전스 발표자료/보고서 생성 |

### Language Expert (1)

| 에이전트 | 설명 |
|----------|------|
| `python-expert` | Production-ready Python (SOLID + modern best practices) |

---

## 스킬 (16개)

### 핵심 워크플로우

| 스킬 | 설명 |
|------|------|
| `jin-claude-init` | 팀원 환경 초기화 자동화 |
| `jin-commit` | gitmoji 기반 커밋 메시지 추천 |
| `jin-interview` | 구현 전 심층 인터뷰 → 스펙 문서 |
| `jin-suggest` | 적합한 스킬/에이전트 추천 |
| `jin-swe-fix` | Live-SWE-agent 워크플로우 기반 이슈 수정 |

### 오케스트레이션 & 자동화

| 스킬 | 설명 |
|------|------|
| `jin-orchestrator` | 멀티 에이전트 오케스트레이션 파이프라인 |
| `jin-fsd` | Full Self-Driving 모드 (단계별 승인 기반 자율 실행) |
| `jin-maxwork` | 병렬 에이전트 실행 엔진 |
| `jin-ralph` | 자기참조 반복 루프 (검증 통과까지 반복) |

### 코드 품질 & 분석

| 스킬 | 설명 |
|------|------|
| `jin-cleanser` | AI 생성 코드 슬롭 리뷰어 (deslop) |
| `jin-gcc` | 다중 관점 분석 (codex/gemini CLI 우선) |
| `jin-deepinit` | 프로젝트 구조 분석 → AGENTS.md 생성 |
| `jin-chub` | Context-Hub CLI 기반 커뮤니티 API 문서 검색 |

### 유틸리티

| 스킬 | 설명 |
|------|------|
| `manage-skills` | 스킬 관리 (추가/제거/목록) |
| `guidelines` | LLM 코딩 행동 가이드 (Karpathy 기반) |
| `verify-implementation` | 구현 검증 체크리스트 |

---

## Statusline

Claude Code 상태 표시줄에 세션 정보, 컨텍스트, API 사용량을 실시간 표시합니다.

```
claude │ ⎇ master │ Opus │ v1.0 │ 5h: 8% →02:00 │ 7d: 11% →03/06(Fri)
ctx: 50% │ cache: 1.0K
```

### 구성 요소

| 요소 | 설명 |
|------|------|
| 디렉토리 | 현재 작업 디렉토리명 |
| 브랜치 | 현재 git 브랜치 |
| 모델 | 사용 중인 Claude 모델 |
| 버전 | Claude Code 버전 |
| 5h 사용량 | 5시간 세션 사용률 (%) + 리셋 시간 |
| 7d 사용량 | 7일 주간 사용률 (%) + 리셋 날짜 |
| ctx | 컨텍스트 윈도우 사용률 (%) |
| cache | 캐시 읽기 토큰 수 |

사용률에 따라 dark green(0%) → deep red(100%)로 10단계 gradient 색상이 자동 적용됩니다.

### 설정

`~/.claude/settings.json`에 추가:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash {$HOME}/.claude/statusline-command.sh"
  }
}
```

표시 항목은 `~/.claude/statusline-config.txt`에서 제어합니다 (`0`으로 숨김):

```
SHOW_DIRECTORY=1
SHOW_BRANCH=1
SHOW_MODEL=1
SHOW_VERSION=1
SHOW_CONTEXT=1
SHOW_USAGE=1
```

---

## 아키텍처

### 사용량 가져오기 (`fetch-claude-usage`)

```
macOS Keychain / ~/.claude/.credentials.json
    │
    ▼
OAuth Bearer Token 추출
    │
    ▼
GET https://api.anthropic.com/api/oauth/usage
    Header: anthropic-beta: oauth-2025-04-20
    │
    ▼
~/.claude/.usage-cache.json (30초 TTL 캐시)
    │
    ▼
stdout: "5h_util|5h_resets|7d_util|7d_resets"
```

- **토큰 소스**: `~/.claude/.credentials.json` → macOS Keychain (fallback)
- **캐시**: `~/.claude/.usage-cache.json` (30초 TTL)
- **외부 의존성**: 없음 (Python stdlib만 사용)

### statusline 렌더링 (`statusline-command.sh`)

Claude Code가 stdin으로 전달하는 JSON을 파싱하여 2줄의 ANSI 컬러 텍스트를 출력합니다.

---

## 요구사항

| 구분 | 도구 | 버전 |
|------|------|------|
| Language | Python | 3.13 |
| Package manager | [uv](https://docs.astral.sh/uv/) | latest |
| Type checker | ty | latest |
| Linter / formatter | ruff | latest |
| Logging | loguru | latest |
| Shell util | `jq` (statusline JSON 파싱용) | — |
| 구독 | Claude Pro/Max/Team/Enterprise | — |

---

## 개발

```bash
# 의존성 설치
uv sync

# 린트
uv run ruff check src/ tests/

# 테스트
uv run pytest tests/ -v

# CLI 직접 실행
uv run fetch-claude-usage
```

---

## 프로젝트 구조

```
jin-claude/
├── .claude-plugin/
│   └── marketplace.json                 # 마켓플레이스 카탈로그
├── plugins/
│   └── jin-claude/                      # 단일 플러그인
│       ├── .claude-plugin/
│       │   └── plugin.json              # 플러그인 매니페스트
│       ├── agents/                      # 15 에이전트
│       │   └── templates/               # 에이전트 템플릿
│       ├── skills/                      # 16 스킬
│       │   ├── guidelines/
│       │   ├── jin-chub/
│       │   ├── jin-claude-init/
│       │   ├── jin-cleanser/
│       │   ├── jin-commit/
│       │   ├── jin-deepinit/
│       │   ├── jin-fsd/
│       │   ├── jin-gcc/
│       │   ├── jin-interview/
│       │   ├── jin-maxwork/
│       │   ├── jin-orchestrator/
│       │   ├── jin-ralph/
│       │   ├── jin-suggest/
│       │   ├── jin-swe-fix/
│       │   ├── manage-skills/
│       │   └── verify-implementation/
│       ├── scripts/                     # statusline + timer
│       │   ├── statusline-command.sh    # statusline 렌더러
│       │   ├── statusline-config.txt    # 표시 설정
│       │   ├── tmux-usage.sh            # tmux 연동
│       │   └── install-timer.sh         # 타이머 설치 (Linux/macOS/Windows)
│       ├── settings.json                # 플러그인 설정
│       ├── systemd/                     # Linux systemd timer
│       └── launchd/                     # macOS launchd plist
├── src/jin_claude/
│   ├── __init__.py
│   └── fetch_claude_usage.py            # OAuth usage API 클라이언트
├── .claude/
│   ├── CLAUDE.md                        # 프로젝트 지침
│   └── settings.json                    # 개발용 설정
└── pyproject.toml                       # uv 프로젝트 설정
```

---

## 라이선스

MIT
