# jin-claude-init

Claude Code statusline utilities. Claude Code의 상태 표시줄(statusline)에 세션 정보, 컨텍스트, API 사용량 등을 실시간으로 표시합니다.

## Statusline 출력 예시

```
claude │ ⎇ master │ Opus │ v1.0 │ 5h: 8% →02:00 │ 7d: 11% →03/06(Fri)
ctx: 50% │ cache: 1.0K
```

### Line 1 구성 요소

| 요소 | 색상 | 설명 |
|------|------|------|
| 디렉토리 | Blue | 현재 작업 디렉토리명 |
| 브랜치 | Green | 현재 git 브랜치 (`⎇ branch`) |
| 모델 | Cyan | 사용 중인 Claude 모델명 |
| 버전 | Magenta | Claude Code 버전 |
| 5h 사용량 | Amber + gradient | 5시간 세션 사용량 (%), 24시간제 리셋 시간 |
| 7d 사용량 | Violet + gradient | 7일 주간 사용량 (%), MM/DD(요일) 리셋 날짜 |

### Line 2 구성 요소

| 요소 | 색상 | 설명 |
|------|------|------|
| ctx | gradient | 컨텍스트 윈도우 사용률 (%) |
| cache | Light Blue | 캐시 읽기 토큰 수 |

### 사용량 색상 (10단계 gradient)

사용률에 따라 dark green → deep red로 자동 변경됩니다.

| 사용률 | 색상 |
|--------|------|
| 0-10% | Dark Green |
| 11-30% | Green 계열 |
| 31-50% | Yellow-Green |
| 51-70% | Yellow-Orange |
| 71-90% | Orange-Red |
| 91-100% | Deep Red |

## 설치

### 요구사항

- macOS (Keychain 접근용)
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Claude Pro/Max/Team/Enterprise 구독 (사용량 API 접근용)
- `jq` (statusline JSON 파싱용)

### 설정

```bash
# 1. 의존성 설치
uv sync

# 2. settings.json에 statusline 설정 추가
```

`~/.claude/settings.json` 또는 프로젝트의 `settings.json`에 추가:

```json
{
  "statusLine": {
    "type": "command",
    "command": "bash {$HOME}/.claude/script/statusline-command.sh"
  }
}
```

### 설정 옵션

`~/.claude/statusline-config.txt`에서 표시 항목을 제어합니다:

```
SHOW_DIRECTORY=1
SHOW_BRANCH=1
SHOW_MODEL=1
SHOW_VERSION=1
SHOW_CONTEXT=1
SHOW_USAGE=1
```

`0`으로 설정하면 해당 항목이 숨겨집니다.

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
- **캐시**: `~/.claude/.usage-cache.json` (30초 TTL, 빈번한 statusline 호출 최적화)
- **외부 의존성**: 없음 (Python stdlib만 사용)
- **API**: Anthropic 비공개 OAuth 엔드포인트 (beta)

### statusline 렌더링 (`statusline-command.sh`)

Claude Code가 stdin으로 전달하는 JSON을 파싱하여 2줄의 ANSI 컬러 텍스트를 출력합니다. `fetch-claude-usage` CLI를 호출하여 사용량 데이터를 가져옵니다.

## 개발

```bash
# 린트
uv run ruff check src/ tests/

# 테스트
uv run pytest tests/ -v

# CLI 직접 실행
uv run fetch-claude-usage
```

## 프로젝트 구조

```
./
├── src/jin_claude/
│   ├── __init__.py
│   └── fetch_claude_usage.py       # OAuth usage API 클라이언트
├── tests/
│   ├── __init__.py
│   ├── test_fetch_claude_usage.py  # Python 유닛 테스트 (38개)
│   └── test_statusline.sh          # Shell 통합 테스트
├── .claude/
│   ├── agents/                     # Claude Code 커스텀 에이전트
│   ├── skills/                     # Claude Code 커스텀 스킬
│   ├── script/
│   │   ├── statusline-command.sh   # statusline 렌더러 (bash)
│   │   └── statusline-config.txt   # 표시 설정
│   ├── settings.json               # 공유 프로젝트 설정
│   └── CLAUDE.md                   # 프로젝트 지침
└── pyproject.toml                  # uv 프로젝트 설정
```
