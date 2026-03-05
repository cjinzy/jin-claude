---
name: jin-claude-init
description: 팀원 Claude Code 환경 초기화. plugin 설치, settings 구성, agents/skills 동기화를 자동화. "jin init", "jin 초기화", "Claude Code 초기 설정", "환경 세팅" 등의 요청 시 사용.
---

# Jin Claude Init

팀원이 새 머신에서 Claude Code를 설치한 뒤, 동일한 플러그인·설정·에이전트·스킬 환경을 한 번에 구성하는 자동화 스킬.

## Step 1 — Plugin Marketplace 추가

아래 명령어를 **순서대로** Bash로 실행한다:

```bash
claude plugin marketplace add kepano/obsidian-skills
claude plugin marketplace add nextlevelbuilder/ui-ux-pro-max-skill
claude plugin marketplace add obra/superpowers-marketplace
claude plugin marketplace add mksglu/claude-context-mode
```

각 명령어 실행 결과를 확인하고, 이미 추가된 marketplace는 건너뛴다.

## Step 2 — Plugin 설치

아래 명령어를 **순서대로** Bash로 실행한다:

```bash
claude plugin install obsidian@obsidian-skills
claude plugin install ui-ux-pro-max@ui-ux-pro-max-skill
claude plugin install superpowers@superpowers-marketplace
claude plugin install context-mode@claude-context-mode
```

이미 설치된 플러그인은 건너뛴다.

> **SuperClaude:** marketplace/plugin 절차를 거치지 않고, Step 3의 `sync_repo.py` 내 `install_superclaude()` 함수가 `pipx install superclaude && superclaude install`을 직접 실행한다. fallback 순서: `pipx` → `pip install --user` → `uv tool install`.

## Step 3 — Git Repo에서 Agents & Skills 동기화

jin-claude 저장소에서 에이전트 정의와 스킬을 동기화한다.

**먼저 사용자에게 사용량 수집 주기를 물어본다:**

> "사용량 수집 주기를 선택해 주세요: 1분 / 3분 / **5분(권장)** / 10분"

사용자가 선택한 값을 `INTERVAL` 변수로 사용한다 (기본값: 5).

```bash
python3 "SKILL_DIR/scripts/sync_repo.py" $INTERVAL
```

이 스크립트는:
- `https://github.com/cjinzy/jin-claude.git`을 `~/.claude/.jin-claude-repo/`에 clone (또는 pull)
- `.claude/agents/` → `~/.claude/agents/` 로 파일 복사
- `.claude/skills/` → `~/.claude/skills/` 로 파일 복사
- `.claude/script/statusline-command.sh`, `.claude/CLAUDE.md` 등 개별 파일도 동기화
- `~/.claude/.venv/`에 Python 가상환경 생성 및 패키지 설치 (`uv` 우선, `pip` fallback)
  - `pyproject.toml`이 존재할 때만 실행
  - statusline에서 사용하는 `fetch-claude-usage` 등의 CLI 도구가 이 venv에 설치됨
- systemd user timer 설치 (`scripts/install-timer.sh`)
  - 사용자가 선택한 주기(`$INTERVAL`)를 인자로 전달
  - systemd가 없는 환경(macOS 등)에서는 자동 건너뜀

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

`enabledPlugins`는 Step 2의 `claude plugin install`이 자동으로 추가하므로 병합 대상에서 제외한다.

## Step 5 — 검증 및 완료 보고

모든 단계 완료 후:

1. `claude plugin list`로 플러그인 설치 상태 확인
2. `~/.claude/settings.json` 내용 읽어서 설정 반영 확인
3. `~/.claude/agents/` 디렉토리에 에이전트 파일 존재 확인
4. 결과를 사용자에게 요약 보고

```
[DONE] jin-claude-init: 환경 초기화 완료
- Marketplace: N개 추가
- Plugins: N개 설치
- Agents: N개 동기화
- Skills: N개 동기화
- Settings: 병합 완료
```

## Step 6 — oh-my-claudecode 셋업

환경 초기화 완료 후, oh-my-claudecode 플러그인 셋업을 시작한다:

```
/oh-my-claudecode:omc-setup
```

HUD 설정은 제외한다. omc-setup 진행 중 HUD 관련 설정이 나오면 건너뛴다.
