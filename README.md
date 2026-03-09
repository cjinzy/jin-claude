# jin-claude

Claude Code용 멀티 에이전트 오케스트레이션 시스템. 9개 에이전트, 6개 스킬, statusline 유틸리티, CTI 파이프라인을 단일 플러그인으로 제공합니다.

## 빠른 시작

### 마켓플레이스 설치

```bash
# 1. Marketplace 등록
claude plugin marketplace add cjinzy/jin-claude

# 2. Plugin 설치
claude plugin install jin-claude@jin-claudecode-mp
```

### 팀원 환경 초기화 (jin-claude-init)

Claude Code 내에서 `/jin-claude-init`을 실행하면 플러그인, 설정, 에이전트, 스킬을 자동으로 구성합니다.

---

## 에이전트 (9개)

### Opus (고비용, 고품질)

| 에이전트 | 설명 |
|----------|------|
| `mole-review-agent` | CTI 프로파일링 오케스트레이터 |

### Sonnet (기본, 균형)

| 에이전트 | 설명 |
|----------|------|
| `python-expert` | Python 프로덕션 코드 |
| `jin-interview-agent` | 구조적 요구사항 인터뷰 |
| `mole-research-agent` | 위협 인텔리전스 수집 |
| `mole-intel-organizer-agent` | 인텔리전스 분류 및 구조화 |
| `mole-interview-agent` | CTI 조사 전 인터뷰 |
| `mole-user-identifier-agent` | 사용자 신원 상관관계 분석 |
| `mole-graph-generator-agent` | Mermaid 그래프 시각화 |
| `mole-report-presenter-agent` | 발표자료 생성 |

---

## 스킬 (6개)

| 스킬 | 설명 |
|------|------|
| `jin-claude-init` | 팀원 환경 초기화 자동화 |
| `jin-commit` | gitmoji 기반 커밋 메시지 추천 |
| `jin-interview` | 구현 전 심층 인터뷰 → 스펙 문서 |
| `manage-skills` | 스킬 관리 (추가/제거/목록) |
| `py-standard` | Python 프로젝트 컨벤션 가이드 |
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

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- `jq` (statusline JSON 파싱용)
- Claude Pro/Max/Team/Enterprise 구독

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
│       ├── agents/                      # 9 에이전트
│       │   └── templates/               # 에이전트 템플릿
│       ├── skills/                      # 6 스킬
│       │   ├── jin-claude-init/
│       │   ├── jin-commit/
│       │   ├── jin-interview/
│       │   ├── manage-skills/
│       │   ├── py-standard/
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
