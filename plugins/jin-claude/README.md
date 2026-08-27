# jin-claude

> Multi-agent orchestration for Claude Code — **15 agents · 17 skills · 4 hooks**
> Version: **3.0.10** · License: MIT · Marketplace: `jin-claudecode-mp`

팀 공통 Claude Code 환경을 표준화하는 플러그인. 오케스트레이션, 병렬 실행, SWE 워크플로우, CTI 파이프라인, 자동 키워드 라우팅, 커밋/인터뷰/초기화 자동화를 한 곳에서 제공합니다.

---

## Install

```sh
claude plugin install "jin-claude@jin-claudecode-mp"
```

업데이트 시에도 `update`가 아닌 `install` 재호출을 권장합니다 (marketplace 캐시/버전 불일치 회피).

---

## Directory Layout

```
plugins/jin-claude/
├── .claude-plugin/plugin.json     # 플러그인 메타데이터
├── agents/                         # 15 agent prompt templates (.md)
├── skills/<skill-name>/SKILL.md    # 16 skills
├── hooks/                          # 4 runtime hooks (Pre/Post/Session/Prompt)
├── commands/                       # (현재 비어 있음 — 커맨드 없음)
├── docs/                           # 가이드/템플릿 (로더 대상 아님)
└── tests/                          # 훅/스킬 검증 테스트 (로더 대상 아님)
```

---

## Agents (15)

### Interview & Planning (3)

| Name | Description |
|------|-------------|
| `jin-interview-agent` | Structured requirements interview. 모호한 작업 설명을 구체적 spec 문서로 변환 |
| `orchestrator-agent` | 멀티 에이전트 파이프라인 관리 · 태스크 분배 · 상태 전이 제어 |
| `task-planner-agent` | 사용자 요청을 원자적 태스크로 분해하고 의존성 그래프 생성 |

### SWE Engineering (4)

| Name | Description |
|------|-------------|
| `swe-agent` | Live-SWE-agent 워크플로우 기반 이슈 해결 실행자. 분석→재현→수정→검증→엣지케이스 6단계 |
| `swe-agent-high` | 복잡한 교차 모듈 버그 · 레이스 컨디션 · 아키텍처 결함 대응 (고급 tier) |
| `swe-analyst` | 읽기 전용 근본 원인 진단 및 수정 계획 생성 |
| `swe-verifier` | 수정 후 독립 검증 — 버그 재현 + 엣지케이스 커버 |

### MOLE / CTI (7)

Korean Cyber Threat Intelligence 파이프라인 전용 에이전트.

| Name | Description |
|------|-------------|
| `mole-review-agent` | CTI 프로파일링 파이프라인 오케스트레이터 |
| `mole-interview-agent` | CTI 조사 전 인터뷰로 조사 방향 확정 |
| `mole-research-agent` | StealthMole MCP 기반 위협 인텔리전스 수집 |
| `mole-intel-organizer-agent` | 위협 인텔리전스 분류 · 평가 · 구조화 |
| `mole-user-identifier-agent` | 사용자 신원 상관관계 분석 |
| `mole-graph-generator-agent` | 조사 결과를 Mermaid 그래프로 통합 시각화 |
| `mole-report-presenter-agent` | 위협 인텔리전스 발표자료(문서/슬라이드) 생성 |

### Language Expert (1)

| Name | Description |
|------|-------------|
| `python-expert` | Production-ready · secure · high-performance Python (SOLID + modern best practices) |

> All agents now **inherit the caller's model** (no hard-coded `model:` frontmatter — v3.0.4+ 기준). 호출 시 필요하면 `Agent({model: ...})` 로 명시 오버라이드 가능.

---

## Skills (17)

### Orchestration & Workflow (5)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-orchestrator` | `jin orchestrate`, `오케스트레이션` | 멀티 에이전트 오케스트레이션 — 태스크 분해 · 병렬 실행 · 검증 · 자동 수정 |
| `jin-maxwork` | `jin maxwork`, `병렬` | 병렬 에이전트 실행 엔진 |
| `jin-fsd` | `jin fsd`, `자율실행` | Full Self-Driving 모드. 단계별 사용자 승인 파이프라인 |
| `jin-ralph` | `jin ralph` | 자기참조 반복 루프 — verifier 승인까지 실행→검증→수정 |
| `jin-gcc` | `jin gcc`, `다관점` | 다중 관점 분석 (codex/gemini CLI 우선, 없으면 Claude agent 폴백) |

### SWE Workflow (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-swe-fix` | `swe fix`, `fix bug` | Live-SWE-agent 워크플로우로 소프트웨어 이슈 체계적 해결 |

### Spec & Commit (2)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-interview` | — | In-depth interview to create a detailed spec |
| `jin-commit` | `jin commit`, `commit` | Gitmoji 기반 커밋 메시지 자동 추천 및 생성 |

### Code Quality (2)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-cleanser` | `jin cleanser`, `jin deslop` | AI 생성 코드 슬롭 리뷰어 — 불필요 코멘트/과잉 에러 처리/미사용 임포트 탐지 |
| `verify-implementation` | — | 프로젝트의 모든 `verify-*` 스킬을 순차 실행 → 통합 검증 보고서 |

### Knowledge & Discovery (3)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-chub` | `jin chub`, `chub`, `API 문서 검색` | 커뮤니티 큐레이션 API 문서를 `chub` CLI로 검색/조회/어노테이션 |
| `jin-suggest` | `jin suggest`, `추천`, `뭐 써야` | 사용자 요청에 가장 적합한 jin-claude 스킬/에이전트 추천 |
| `jin-deepinit` | `jin deepinit`, `프로젝트 분석` | 프로젝트 구조 분석 → 적합 에이전트 추천 `AGENTS.md` 생성 |

### Environment Init (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-claude-init` | `jin init`, `초기화`, `환경 세팅` | 팀원 Claude Code 환경 초기화 — plugin 설치/settings/MCP/hooks/agents·skills 동기화 |

### Behavioral Guidelines (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `guidelines` | 코드 작성/리뷰/리팩토링 시 | LLM 코딩 행동 가이드 — Think Before · Simplicity · Surgical · Goal-Driven (Karpathy 기반) |

### Meta (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `manage-skills` | — | 세션 변경사항 분석 → 검증 스킬 누락 탐지 → 스킬 생성/업데이트 + CLAUDE.md 관리 |

---

## Hooks (4)

| File | Event | Role |
|------|-------|------|
| `hooks/pre_tool_enforcer.sh` | `PreToolUse` | 도구 사용 전 규칙 강제 (현재 pass-through) |
| `hooks/post_tool_verifier.sh` | `PostToolUse` | 도구 실행 후 결과 검증 (현재 pass-through) |
| `hooks/session_init.py` | `SessionStart` | 세션 시작 시 marketplace 저장소 자동 업데이트 |
| `hooks/keyword_detector.py` | `UserPromptSubmit` | 프롬프트 매직 키워드 감지 → 스킬 자동 라우팅 |

> 키워드 라우팅 테이블은 `hooks/keyword_detector.py` 상단의 `KEYWORDS` dict 참조.
> 키워드 등록 검증 테스트는 `tests/test_keyword_detector_chub.py` 에 격리되어 있어 훅 로더가 로드하지 않습니다.

---

## Project Conventions (요약)

- **Backend**: Python 3.12 · uv · Ruff · ty (type checker) · loguru
- **Frontend**: React + TypeScript + Vite · fluentui-system-icons · npm
- **Docs**: docstring + traceback 필수, 주석은 WHY만
- **Git**: `jin commit` 으로 gitmoji 기반 메시지 생성
- **Tool 우선순위**: Serena(심볼) → context-mode(대용량 출력) → Read(편집 대상만)

자세한 팀 가이드는 repo root의 `CLAUDE.md` 참조.
