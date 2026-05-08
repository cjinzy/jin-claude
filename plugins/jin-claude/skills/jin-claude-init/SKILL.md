---
name: jin-claude-init
description: 팀원 Claude Code 환경 초기화. plugin 설치, settings 구성, MCP/hooks 설정, agents/skills 동기화를 자동화. "jin init", "jin 초기화", "Claude Code 초기 설정", "환경 세팅" 등의 요청 시 사용.
---

# Jin Claude Init

팀원이 새 머신에서 Claude Code를 설치한 뒤, 동일한 플러그인·설정·에이전트·스킬 환경을 한 번에 구성하는 자동화 스킬.

## Step 0 — Pre-flight Check

설치 상태를 사전 점검하여 이미 완료된 단계를 자동 스킵한다.

```bash
python3 "SKILL_DIR/scripts/preflight.py"
```

이 스크립트는 JSON으로 각 항목(marketplace, plugins, statusline, settings, venv, timer, MCP, hooks)의 설치 여부를 출력한다.

- `recommendation: "full"` → 전체 초기화 필요 (모든 Step 실행)
- `recommendation: "partial"` → 미설치 항목만 선택적 실행
- `recommendation: "none"` → 모든 항목 설치 완료, 사용자에게 확인 후 종료 가능

**자동 스킵 정책**: `recommendation`이 `"partial"`이면, `missing` 항목에 해당하는 Step만 실행한다.

## Step 1 — Plugin Marketplace 추가

아래 명령어를 **순서대로** Bash로 실행한다:

```bash
claude plugin marketplace add kepano/obsidian-skills
claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin marketplace add mksglu/claude-context-mode
claude plugin marketplace add SuperClaude-Org/SuperClaude_Plugin
claude plugin marketplace add revfactory/harness
claude plugin marketplace add uditgoenka/autoresearch
```

각 명령어 실행 결과를 확인하고, 이미 추가된 marketplace는 건너뛴다.

## Step 2 — Plugin 설치

아래 명령어를 **순서대로** Bash로 실행한다:

```bash
claude plugin install obsidian@obsidian-skills
claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill
claude plugin install superpowers@claude-plugins-official
claude plugin install context7@claude-plugins-official
claude plugin install code-simplifier@claude-plugins-official
claude plugin install claude-md-management@claude-plugins-official
claude plugin install serena@claude-plugins-official
claude plugin install pyright-lsp@claude-plugins-official
claude plugin install agent-sdk-dev@claude-plugins-official
claude plugin install context-mode@context-mode
claude plugin install sc@superclaude
claude plugin install harness@harness-marketplace
claude plugin install autoresearch@autoresearch
```

이미 설치된 플러그인은 건너뛴다.

> **SuperClaude:** Step 2의 `claude plugin install sc@superclaude`으로 설치된다.
> **anthropics/claude-plugins-official:** superpowers, context7, code-simplifier, claude-md-management, serena, pyright-lsp, agent-sdk-dev 7개 플러그인을 공식 마켓플레이스에서 일괄 설치한다.

## Step 3 — Git Repo에서 Statusline·설정 동기화 + 캐시 정리

jin-claude 저장소에서 statusline, 설정 파일, venv를 동기화한다. 동기화 직후 구버전 플러그인 캐시를 자동으로 정리한다.

> **참고:** Agents와 Skills는 Step 2의 `claude plugin install`이 자동으로 설치하므로, 이 단계에서는 동기화하지 않는다.

**먼저 사용자에게 사용량 수집 주기를 물어본다:**

> "사용량 수집 주기를 선택해 주세요: 1분 / 3분 / **5분(권장)** / 10분"

사용자가 선택한 값을 `INTERVAL` 변수로 사용한다 (기본값: 5).

```bash
python3 "SKILL_DIR/scripts/sync_repo.py" $INTERVAL
```

이 스크립트는:
- `https://github.com/cjinzy/jin-claude.git`을 `~/.claude/.jin-claude-repo/`에 clone (또는 pull)
- 구버전 플러그인 캐시 자동 정리 (`~/.claude/plugins/cache/jin-claudecode-mp/jin-claude/`)
- `plugins/jin-claude/scripts/statusline-command.sh`, `.claude/CLAUDE.md` 등 개별 파일 동기화
- `~/.claude/.venv/`에 Python 가상환경 생성 및 패키지 설치 (`uv` 우선, `pip` fallback)
  - `pyproject.toml`이 존재할 때만 실행
  - statusline에서 사용하는 `fetch-claude-usage` 등의 CLI 도구가 이 venv에 설치됨
- OS별 타이머 설치 (`scripts/install-timer.sh` — macOS launchd / Linux systemd 자동 감지)
  - 사용자가 선택한 주기(`$INTERVAL`)를 인자로 전달

## Step 4 — Settings 병합

설정 파일에 필수 값을 deep merge한다:

```bash
python3 "SKILL_DIR/scripts/merge_settings.py"
```

이 스크립트는 `~/.claude/settings.json`에 아래 설정을 병합한다 (기존 값 보존):
- `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`: `"1"`
- `permissions.defaultMode`: `"plan"`
- `enableAllProjectMcpServers`: `true`
- `statusLine`: statusline-command.sh 실행
- `outputStyle`: `"Explanatory"`
- `language`: `"korean"`
- `skipDangerousModePermissionPrompt`: `true`
- `effortLevel`: `"high"`

`enabledPlugins`는 Step 2의 `claude plugin install`이 자동으로 추가하므로 병합 대상에서 제외한다.

## Step 4.5 — MCP + Teams 설정

플러그인이 자동 제공하지 않는 standalone MCP 서버를 설치한다. 이미 설치된 서버는 자동 스킵한다.

```bash
python3 "SKILL_DIR/scripts/setup_mcp_and_teams.py"
```

현재는 standalone 으로 자동 설치하는 MCP 서버가 없다 (`MCP_SERVERS = []`). 필요한 MCP는 사용자가 직접 `claude mcp add` 또는 플러그인을 통해 추가한다.

> **참고:** context-mode MCP는 Step 2의 `context-mode@context-mode` 플러그인이 자동 제공한다.

> **팀 설정**: `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 환경변수가 Step 4에서 설정되므로, 별도 팀 제한 설정은 불필요하다.

## Step 5 — Hooks 확인

jin-claude 플러그인의 `.claude-plugin/hooks/hooks.json`에 4개 hooks가 정의되어 있다:

| Hook | 파일 | 역할 |
|------|------|------|
| UserPromptSubmit | `hooks/keyword_detector.py` | magic keyword 감지 → 스킬 자동 호출 |
| PreToolUse | `hooks/pre_tool_enforcer.sh` | 도구 사용 규칙 강제 |
| PostToolUse | `hooks/post_tool_verifier.sh` | 도구 실행 결과 검증 |
| SessionStart | `hooks/session_init.py` | 세션 시작 시 자동 업데이트 |

플러그인 설치(Step 2) 시 `${CLAUDE_PLUGIN_ROOT}` 치환과 함께 자동으로 적용되므로, 여기서는 설치 확인만 수행한다:

```bash
python3 -c "
import json; from pathlib import Path
cache = Path.home() / '.claude/plugins/cache/jin-claudecode-mp/jin-claude'
ver = sorted([d for d in cache.iterdir() if d.name[0].isdigit()])[-1]
d = json.loads((ver / '.claude-plugin/hooks/hooks.json').read_text())
print('Hooks:', list(d['hooks'].keys()))
"
```

## Step 6 — 검증 및 완료 보고

모든 단계 완료 후:

1. `claude plugin list`로 플러그인 설치 상태 확인
2. `~/.claude/settings.json` 내용 읽어서 설정 반영 확인
3. `~/.claude/agents/` 디렉토리에 에이전트 파일 존재 확인
4. `claude mcp list`로 MCP 서버 설치 확인
5. `SKILL_DIR/welcome.md`를 읽어 사용자에게 사용법 안내를 표시한다.

```
[DONE] jin-claude-init: 환경 초기화 완료
- Marketplace: N개 추가
- Plugins: N개 설치
- Agents: N개 동기화
- Skills: N개 동기화
- Settings: 병합 완료 (effortLevel: high)
- MCP: N개 서버 설치
- Hooks: 4개 설치
```
