# jin-claude

> Team-standard skills & hooks for Claude Code — **9 skills · 1 hook**
> Version: **5.1.1** · License: MIT · Marketplace: `jin-claudecode-mp`

팀 공통 Claude Code 환경을 표준화하는 플러그인. 커밋/인터뷰/초기화 자동화, 코드 리뷰 스킬을 한 곳에서 제공합니다. 멀티 에이전트 실행은 Claude Code 내장 Agent/Workflow 도구를 사용합니다.

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
├── skills/<skill-name>/SKILL.md    # 스킬
├── hooks/                          # hooks.json + hook 스크립트
├── scripts/                        # statusline + 사용량 타이머
├── launchd/ · systemd/             # 타이머 정의 (macOS · Linux)
└── settings.json                   # 플러그인 설정
```

---

## Skills (9)

### Analysis (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-codex-side` | `jin codex` | Codex CLI 로 독립 second opinion (review / challenge / consult) |

### Spec & Commit (2)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-interview` | — | In-depth interview to create a detailed spec |
| `mole-linear` | `linear`, `이슈 등록`, `MOLE-` | STEALTHMOLE Linear issue/comment work with team format rules |
| `jin-commit` | `jin commit`, `commit` | Gitmoji 기반 커밋 메시지 자동 추천 및 생성 |

### Code Quality (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-cleanser` | `jin cleanser`, `jin deslop` | AI 생성 코드 슬롭 리뷰어 — 불필요 코멘트/과잉 에러 처리/미사용 임포트 탐지 |

### Knowledge & Discovery (3)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-deepinit` | `jin deepinit`, `프로젝트 분석` | 프로젝트 구조 분석 → 스킬 안내 `AGENTS.md` 생성 |
| `jin-sot-create` | `jin sot` | SoT 문서셋 생성 — 세부항목별 파일, fact ID, `sot_index.py` 색인 생성, `sot_validate.py` drift 검증 |

### Environment Init (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `jin-claude-init` | `jin init`, `초기화`, `환경 세팅` | 팀원 Claude Code 환경 초기화 — plugin 설치/settings/MCP/hooks/skills 동기화 |

### Behavioral Guidelines (1)

| Slug | Trigger | Description |
|------|---------|-------------|

### Meta (1)

| Slug | Trigger | Description |
|------|---------|-------------|
| `manage-skills` | — | 세션 변경사항 분석 → 검증 스킬 누락 탐지 → 스킬 생성/업데이트 + CLAUDE.md 관리 |

---

## Hooks (1)

`hooks/hooks.json` 에 등록 — Claude Code 는 플러그인 루트의 이 파일만 로드한다.

| File | Event | Role |
|------|-------|------|
| `hooks/session_init.py` | `SessionStart` | 구버전 `~/.claude/skills` 사본 백업 이동 + 사용량 타이머 유실 시 재등록 + marketplace 저장소 자동 업데이트 |

> `hooks/keyword_detector.py` 는 미등록 상태(출력 형식이 hook 규격과 다름). 키워드 테이블은 상단 `KEYWORDS` dict.

---

## Project Conventions (요약)

- **Backend**: Python 3.12 · uv · Ruff · ty (type checker) · loguru
- **Frontend**: React + TypeScript + Vite · fluentui-system-icons · npm
- **Docs**: docstring + traceback 필수, 주석은 WHY만
- **Git**: `jin commit` 으로 gitmoji 기반 메시지 생성
- **Tool 우선순위**: Serena(심볼) → context-mode(대용량 출력) → Read(편집 대상만)

자세한 팀 가이드는 repo root의 `CLAUDE.md` 참조.
