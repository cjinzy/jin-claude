# jin-claude

Claude Code 팀 표준 환경 플러그인. 9개 스킬, 1개 hook, statusline 유틸리티를 단일 플러그인으로 제공합니다. 멀티 에이전트 실행은 Claude Code 내장 Agent/Workflow 도구를 사용합니다.

> **현재 버전**: `5.1.1` · 마켓플레이스 슬러그: `jin-claudecode-mp`

## 빠른 시작

### 마켓플레이스 설치

```bash
# 1. Marketplace 등록
claude plugin marketplace add cjinzy/jin-claude

# 2. Plugin 설치
claude plugin install jin-claude@jin-claudecode-mp
```

### 팀원 환경 초기화 (jin-claude-init)

Claude Code 내에서 `/jin-claude-init`을 실행하면 마켓플레이스, 플러그인, 설정, MCP, hooks, 동기화, 통계 타이머를 자동으로 구성합니다. 덮어쓰는 기존 설정 파일은 `<name>_backup_<YYYYMMDD>.<ext>` 로 백업하고, 완료 후 init 전/후 변경 요약을 출력합니다. 실측 결과는 `plugins/jin-claude/skills/jin-claude-init/SKILL.md`을 참조하세요.

#### Step 0 — Pre-flight Check

`scripts/preflight.py`가 marketplace, 플러그인, statusline, settings, venv, 타이머, MCP 서버, hooks 의 현재 설치 상태를 확인해 필요한 단계만 진행합니다.

#### Step 1·2 — Plugin 선택·설치 (`scripts/install_plugins.py`)

필수 3개는 항상, 선택 9개는 init 때 고른 것만 설치합니다. 선택은 `~/.claude/.jin-claude-plugins.json` 에 저장돼 재실행·preflight 가 따르고, 선택 해제한 플러그인은 제거하지 않고 알리기만 합니다. 필요한 marketplace 만 추가하며, `claude plugin` CLI 가 settings.json 을 다시 쓰며 지우는 키(hook group 의 `_gstack_source`, marketplace `autoUpdate`)는 실행 후 되살립니다. 목록 단일 출처: `preflight.py` 의 `CORE_PLUGINS`·`OPTIONAL_PLUGINS`·`EXPECTED_MARKETPLACES`.

| Plugin | Marketplace | 구분 | 용도 |
|--------|-------------|------|------|
| `context-mode` | `context-mode` | 필수 | 큰 출력을 sandbox·인덱스로 보냄 (컨텍스트 보호) |
| `serena` | `claude-plugins-official` | 필수 | 시맨틱 코드 검색·편집 MCP |
| `i-have-adhd` | `i-have-adhd` | 필수 | ADHD 친화 출력 (다음 행동 먼저, 번호 단계) — 팀 출력 형식 표준 |
| `context7` | `claude-plugins-official` | 선택 | 라이브러리 최신 문서 조회 MCP (claude.ai Context7 커넥터가 있으면 불필요) |
| `pyright-lsp` | `claude-plugins-official` | 선택 | Python 타입 검사 LSP |
| `code-simplifier` | `claude-plugins-official` | 선택 | 코드 단순화 agent |
| `ponytail` | `ponytail` | 선택 | 최소 코드 모드 — 매 세션 규칙 주입 |
| `superlite` | `superlite-dev` | 선택 | 빌드 라이프사이클 (승인 1회 → 병렬 → 짧은 보고) — 매 세션 주입 |
| `ui-ux-pro-max` | `ui-ux-pro-max-skill` | 선택 | UI/UX 디자인 DB (스타일·팔레트·폰트) |
| `browser-use` | `claude-plugins-official` | 선택 | 실제 Chrome 제어 (자동화·스크린샷) |
| `html-plan` | `claude-community` | 선택 | 구현 계획을 인터랙티브 HTML 한 장으로 |
| `typesafe` | `typesafe-ai` | 선택 | TypeSafe System One API 스킬 |

| Marketplace ID | 출처 |
|----------------|------|
| `context-mode` | `mksglu/claude-context-mode` |
| `claude-plugins-official` | `anthropics/claude-plugins-official` |
| `ponytail` | `DietrichGebert/ponytail` |
| `superlite-dev` | `iha2/superlite` |
| `ui-ux-pro-max-skill` | `nextlevelbuilder/ui-ux-pro-max-skill` |
| `claude-community` | `anthropics/claude-plugins-community` |
| `i-have-adhd` | `ayghri/i-have-adhd` |
| `typesafe-ai` | `typesafe-ai/skills` |

#### Step 3 — Repo 동기화 (`scripts/sync_repo.py`)

`https://github.com/cjinzy/jin-claude.git`에서 다음을 사용자 홈으로 복사·갱신합니다.

| 대상 | 위치 |
|------|------|
| statusline 렌더러 | `~/.claude/statusline-command.sh`, `statusline-config.txt` |
| 사용량 CLI venv | `~/.claude/.venv/` (uv 기반) |
| 통계 타이머 | macOS: launchd plist · Linux: systemd timer |

#### Step 4 — Settings 병합 (`scripts/merge_settings.py`)

`~/.claude/settings.json`을 deep merge로 갱신합니다. 팀 필수 키(`env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`, `enableAllProjectMcpServers`, `statusLine`, `skipDangerousModePermissionPrompt`)는 덮어쓰고, 개인 선호 키(`permissions.defaultMode`, `outputStyle`, `language`, `effortLevel`, `model`, `advisorModel`)는 없을 때만 넣습니다. 전역 `hooks` 는 구버전 `jin-hooks/` 항목만 제거합니다.

#### Step 4.5 — Standalone MCP 설치 (`scripts/setup_mcp_and_teams.py`)

현재 `MCP_SERVERS = []` — **추가 standalone MCP 서버는 0개**입니다. 과거 standalone으로 설치하던 `serena`(필수)·`context7`(선택)은 Step 2의 `claude-plugins-official` 플러그인이, `context-mode`는 동명 플러그인이 MCP 기능을 자동 제공합니다. 향후 플러그인이 커버하지 않는 MCP가 필요하면 `MCP_SERVERS`에 항목을 추가하는 방식으로 확장합니다.

#### Step 5 — Hook 검증

`plugins/jin-claude/hooks/hooks.json`(플러그인 루트 — Claude Code 로드 위치)에 SessionStart hook 1개가 등록됩니다. 플러그인 캐시에서 직접 실행되므로 플러그인 업데이트만으로 배포됩니다.

| Hook Event | 실행 명령 | 역할 |
|------------|-----------|------|
| `SessionStart` | `python3 "${CLAUDE_PLUGIN_ROOT}/hooks/session_init.py"` | 구버전 `~/.claude/skills` 사본 백업 이동 + 사용량 타이머 유실 시 재등록 + marketplace 자동 업데이트 |

#### Step 6 — 검증 및 완료 보고

`claude plugin list`, `claude mcp list`, `cat ~/.claude/settings.json`을 통해 등록 상태를 확인하고 결과를 사용자에게 출력합니다.

---

## 스킬 (9개)

### 핵심 워크플로우

| 스킬 | 설명 |
|------|------|
| `jin-claude-init` | 팀원 환경 초기화 자동화 |
| `jin-commit` | gitmoji 기반 커밋 메시지 추천 |
| `jin-interview` | 구현 전 심층 인터뷰 → 스펙 문서 |
| `mole-linear` | STEALTHMOLE 팀 Linear 이슈·댓글 작업 (As-is/To-be 양식, Plan/Done/BLOCKED 댓글) |
| `jin-sot-create` | SoT 문서셋 생성 — 세부항목별 파일 + fact ID 인용 + Index 생성기 + drift 검증 |

### 코드 품질 & 분석

| 스킬 | 설명 |
|------|------|
| `jin-cleanser` | AI 생성 코드 슬롭 리뷰어 (deslop) |
| `jin-codex-side` | Codex CLI 로 독립 second opinion (review / challenge / consult) |
| `jin-deepinit` | 프로젝트 구조 분석 → AGENTS.md 생성 |

### 유틸리티

| 스킬 | 설명 |
|------|------|
| `manage-skills` | 프로젝트 verify-* 검증 스킬 생성·업데이트 (변경 파일 대비 누락 탐지) |

---

## Statusline

Claude Code 상태 표시줄에 세션 정보, 컨텍스트, API 사용량을 실시간 표시합니다.

```
claude │ ⎇ master │ Opus │ high │ v1.0
ctx: 50% │ cache: 1.0K │ 7D: 36% →1D/18H CHILL │ Fable: 20% →1D/18H
```

### 구성 요소

| 줄 | 요소 | 설명 |
|----|------|------|
| 1 | 디렉토리 | 현재 작업 디렉토리명 |
| 1 | 브랜치 | 현재 git 브랜치 |
| 1 | 모델 | 사용 중인 Claude 모델 |
| 1 | effort | reasoning effort 레벨 (low~max) |
| 1 | 버전 | Claude Code 버전 |
| 2 | ctx | 컨텍스트 윈도우 사용률 (%) |
| 2 | cache | 캐시 읽기 토큰 수 |
| 2 | 7D 사용량 | 7일 주간 사용률 (%) + 리셋 시간 + pacing |
| 2 | 모델 사용량 | 모델별 주간 한도 (예: Fable) 사용률 (%) + 리셋 시간 |

사용률에 따라 dark green(0%) → deep red(100%)로 10단계 gradient 색상이 자동 적용됩니다.

### 설정

`~/.claude/settings.json`에 추가:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash ~/.claude/statusline-command.sh"
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
stdout: "7d_util|7d_resets|model_label|model_util|model_resets"
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
│       ├── skills/                      # 스킬
│       │   ├── jin-claude-init/
│       │   ├── jin-cleanser/
│       │   ├── jin-codex-side/
│       │   ├── jin-commit/
│       │   ├── jin-deepinit/
│       │   ├── jin-interview/
│       │   ├── mole-linear/
│       │   ├── jin-sot-create/
│       │   └── manage-skills/
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
