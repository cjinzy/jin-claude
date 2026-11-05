---
name: jin-claude-init
description: 팀원 Claude Code 환경을 한 번에 초기화한다 — marketplace·plugin 설치, jin-claude 저장소(https) 동기화, ~/.claude/settings.json 병합, 사용량 타이머 설치. 덮어쓰는 기존 파일은 "<이름>_backup_<YYYYMMDD>.<확장자>"로 백업하고, 끝나면 이전 설정 대비 변경점을 안내한다. "jin init", "jin 초기화", "jin-claude-init", "Claude Code 초기 설정", "환경 세팅", "새 머신 세팅", "팀 환경 재설정" 요청이나, 새 머신에 Claude Code를 설치한 직후 또는 팀 공통 설정·플러그인을 최신으로 맞추고 싶을 때 사용한다.
---

# Jin Claude Init

새 머신(또는 재설정)에서 팀 공통 플러그인·설정·statusline 을 구성한다.

**전제 조건**: `git`, `python3`, `claude` CLI, `uv`(없으면 `pip` fallback).

**스크립트 규칙**: `${CLAUDE_SKILL_DIR}/scripts/*.py` 는 **실행**한다 (읽지 않는다). 각 Step 에 출력이 적혀 있다.

## Step 0 — Pre-flight

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/preflight.py"
```

출력: 항목별(marketplaces, plugins, statusline, settings, venv, timer, hooks) 설치 상태 JSON + `recommendation`.

- `"full"` → 모든 Step 실행
- `"partial"` → `missing` 항목에 해당하는 Step 만 실행
- `"none"` → 사용자에게 재실행 여부를 묻고, 원하지 않으면 종료

## Step 1 — 사용자 확인 (필수)

Step 2–4 는 사용자 파일을 덮어쓴다. 실행 전 아래를 알리고 **명시적 동의**를 받는다. 동의하지 않으면 Step 2–4 를 건너뛴다.

- 덮어쓰는 파일: `~/.claude/CLAUDE.md`, 그것이 @include 하는 `~/.claude/*.md` 보조 문서, `~/.claude/statusline-command.sh`, `~/.claude/settings.json`
- `settings.json`: Step 2(plugin 설치)가 `enabledPlugins`·`extraKnownMarketplaces` 를 쓰고, Step 4 가 팀 필수 키를 **덮어쓰고** 개인 선호 키는 없을 때만 넣는다. 전역 `hooks` 는 구버전 `jin-hooks/` 항목만 제거한다.
- 내용이 바뀌는 파일만 같은 폴더에 `<이름>_backup_<YYYYMMDD>.<확장자>` 로 백업한다 (예: `settings_backup_20260101.json`). 그날 백업이 이미 있으면 유지하고(첫 init 전 원본), 같은 날 재실행이 덮어쓰는 내용은 `<이름>_backup_<YYYYMMDD>_<HHMMSS>.<확장자>` 에 추가 백업한다.

동의하면 첫 쓰기 전에 실행한다:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/report_changes.py" --snapshot ~/.claude/settings.json
```

출력: `[report_changes] 기준 저장: ...`. 이전 변경 기록을 비우고 Step 2 이전 `settings.json` 을 백업·기준으로 저장한다 (Step 7 diff 기준).

같은 질문에서 사용량 수집 주기도 받는다: 1분 / 3분 / **5분(권장)** / 10분 → `INTERVAL` (기본 5).

## Step 2 — Marketplace·Plugin 설치

순서대로 실행한다. 이미 추가/설치된 항목은 건너뛴다.

```bash
claude plugin marketplace add kepano/obsidian-skills
claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin marketplace add mksglu/claude-context-mode
claude plugin marketplace add SuperClaude-Org/SuperClaude_Plugin
claude plugin marketplace add revfactory/harness
claude plugin marketplace add uditgoenka/autoresearch
claude plugin marketplace add iha2/superlite
```

```bash
claude plugin install obsidian@obsidian-skills
claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill
claude plugin install superlite@superlite-dev
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

skills·agents·hooks·context-mode MCP 는 plugin 설치가 제공한다. `enabledPlugins` 도 이 단계가 기록한다.

## Step 3 — 저장소 동기화

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/sync_repo.py" "$INTERVAL"
```

동작:
- `https://github.com/cjinzy/jin-claude.git` 을 `~/.claude/.jin-claude-repo/` 에 clone, 있으면 origin 을 https 로 바꾼 뒤 `pull --ff-only`
- pull 실패 시 기존 clone 을 `.jin-claude-repo_backup_<YYYYMMDD>` 로 옮기고(경고 출력) 다시 clone
- 구버전 플러그인 캐시(`~/.claude/plugins/cache/jin-claudecode-mp/jin-claude/`) 정리
- statusline, `CLAUDE.md`, 보조 문서를 `~/.claude/` 에 복사 (변경 시 백업)
- `~/.claude/.venv/` 생성 후 저장소 패키지 설치 (statusline 용 `fetch-claude-usage`)
- 사용량 타이머 설치 (macOS launchd / Linux systemd)

출력: 단계별 `[sync_repo]` 로그. 실패 시 traceback 과 exit 1.

## Step 4 — Settings 병합

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/merge_settings.py"
```

`~/.claude/settings.json` 에 병합한다 (중첩 dict 는 해당 하위 키만). 표에 없는 키는 보존. 이미 같으면 파일을 쓰지 않는다.
- 전역 `hooks`: 구버전 `~/.claude/jin-hooks/` 항목만 제거 (현재는 plugin `hooks/hooks.json` 이 관리). 개인 hooks 는 보존.

| 키 | 값 | 적용 |
|----|----|------|
| `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | `"1"` | 덮어씀 |
| `enableAllProjectMcpServers` | `true` | 덮어씀 |
| `statusLine` | `bash ~/.claude/statusline-command.sh` | 덮어씀 |
| `skipDangerousModePermissionPrompt` | `true` | 덮어씀 |
| `permissions.defaultMode` | `"plan"` | 없을 때만 |
| `outputStyle` | `"Explanatory"` | 없을 때만 |
| `language` | `"korean"` | 없을 때만 |
| `effortLevel` | `"high"` | 없을 때만 |
| `model` | `"opus"` | 없을 때만 |
| `advisorModel` | `"fable"` | 없을 때만 |

## Step 5 — MCP

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/setup_mcp_and_teams.py"
```

standalone 자동 설치 대상 MCP 는 현재 없다 (`MCP_SERVERS = []`). 추가 MCP 는 `claude mcp add` 또는 plugin 으로.

## Step 6 — 검증

1. `preflight.py` 를 다시 실행한다. `hooks.missing` 이 비어 있어야 한다 (SessionStart: 구버전 `~/.claude/skills` 사본 백업 이동 + 타이머 재등록 + marketplace 자동 업데이트). 남은 `missing` 항목은 사용자에게 알린다.
2. `claude plugin list`, `claude mcp list` 로 설치 상태 확인.

## Step 7 — 변경 안내 (필수)

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/report_changes.py"
```

출력: 파일별 신규/변경/동일 개수, 변경 파일의 백업 경로, 텍스트 파일 줄 diff (`줄 +N / -M` + 앞쪽 변경 줄), `settings.json` 키 diff (Step 2 포함, `+` 추가, `~` 이전→이후, `-` 삭제), 롤백 방법. 실행 후 기록은 비워진다.

출력을 **그대로** 사용자에게 전달하고 롤백 방법을 덧붙인다:
- 변경 파일: 출력의 `백업:` 경로로 `cp <백업> <원본>` (전체 변경은 `diff -u <백업> <원본>`)
- 신규 파일: 삭제

마지막으로 `${CLAUDE_SKILL_DIR}/welcome.md` 를 읽어 사용법을 안내한다.

```
[DONE] jin-claude-init
- Marketplace: N개 추가 / Plugins: N개 설치
- 파일: 신규 N · 변경 N · 동일 N (report_changes 출력 기준)
- Settings: 필수 키 반영, 개인 선호·hooks 보존
- Hooks: SessionStart 확인
```
