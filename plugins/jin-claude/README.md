# jin-claude

> Team-standard skills & hooks for Claude Code — **12 skills · 4 hooks**
> Version: **4.0.1** · License: MIT · Marketplace: `jin-claudecode-mp`

팀 공통 Claude Code 환경을 표준화하는 플러그인. 자동 키워드 라우팅, 커밋/인터뷰/초기화 자동화, 코드 리뷰·검증 스킬을 한 곳에서 제공합니다. 멀티 에이전트 실행은 Claude Code 내장 Agent/Workflow 도구를 사용합니다.

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
├── skills/<skill-name>/SKILL.md    # 12 skills
├── hooks/                          # 4 runtime hooks (Pre/Post/Session/Prompt)
├── commands/                       # (현재 비어 있음 — 커맨드 없음)
├── docs/                           # 가이드/템플릿 (로더 대상 아님)
└── tests/                          # 훅/스킬 검증 테스트 (로더 대상 아님)
```

---

## Skills (12)

### Analysis (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-gcc` | `jin gcc`, `다관점` | 다중 관점 분석 (codex/gemini CLI 우선, 없으면 Claude agent 폴백) |

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

### Knowledge & Discovery (4)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-chub` | `jin chub`, `chub`, `API 문서 검색` | 커뮤니티 큐레이션 API 문서를 `chub` CLI로 검색/조회/어노테이션 |
| `jin-suggest` | `jin suggest`, `추천`, `뭐 써야` | 사용자 요청에 가장 적합한 jin-claude 스킬 추천 |
| `jin-deepinit` | `jin deepinit`, `프로젝트 분석` | 프로젝트 구조 분석 → 스킬 안내 `AGENTS.md` 생성 |
| `jin-sot-create` | `jin sot` | SoT(Source of Truth) 디렉토리 구조 생성 — `sot/` 카테고리 + `Index.md` |

### Environment Init (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-claude-init` | `jin init`, `초기화`, `환경 세팅` | 팀원 Claude Code 환경 초기화 — plugin 설치/settings/MCP/hooks/skills 동기화 |

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
