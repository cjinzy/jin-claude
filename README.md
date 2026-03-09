# jin-claude

Claude Code용 멀티 에이전트 오케스트레이션 시스템. 58개 에이전트, 6개 스킬, statusline 유틸리티, CTI 파이프라인을 단일 플러그인으로 제공합니다.

## 빠른 시작

### 마켓플레이스 설치

```bash
# 1. Marketplace 등록
claude plugin marketplace add cjinzy/jin-claude

# 2. Plugin 설치
claude plugin install jin-claude@jin-mp-claudecode
```

### 팀원 환경 초기화 (jin-claude-init)

Claude Code 내에서 `/jin-claude-init`을 실행하면 플러그인, 설정, 에이전트, 스킬을 자동으로 구성합니다.

---

## 에이전트 (58개, 3-tier)

역할과 비용 효율에 따라 Opus / Sonnet / Haiku 모델을 자동 배정합니다.

### Opus (고비용, 고품질)

전략적 판단, 심층 분석, 복합 실행에 사용됩니다.

| 에이전트 | 설명 |
|----------|------|
| `architect` | 아키텍처 설계 및 디버깅 어드바이저 (READ-ONLY) |
| `analyst` | 요구사항 분석 사전 컨설턴트 |
| `critic` | 작업 계획 리뷰 및 비평 |
| `planner` | 전략적 계획 수립 (인터뷰 워크플로우) |
| `code-reviewer` | 코드 리뷰 전문가 (심층) |
| `security-reviewer` | 보안 취약점 탐지 (OWASP Top 10) |
| `designer-high` | UI 아키텍처 및 디자인 시스템 |
| `executor-high` | 복합 멀티파일 태스크 실행 |
| `explore-high` | 심층 아키텍처 탐색 |
| `scientist-high` | 복합 연구, 가설 검증, ML |
| `qa-tester-high` | 프로덕션 레벨 QA 테스트 |

### Sonnet (기본, 균형)

일반적인 코드 작성, 리뷰, 리서치에 사용됩니다.

| 에이전트 | 설명 |
|----------|------|
| `executor` | 구현 작업 실행 |
| `designer` | UI/UX 디자이너-개발자 |
| `scientist` | 데이터 분석 및 연구 |
| `researcher` | 외부 문서 및 레퍼런스 조사 |
| `qa-tester` | 대화형 CLI 테스트 (tmux) |
| `backend-architect` | 백엔드 시스템 설계 |
| `frontend-architect` | 프론트엔드 인터페이스 설계 |
| `system-architect` | 확장 가능한 시스템 아키텍처 |
| `architect-medium` | 중간 복잡도 아키텍처 |
| `explore-medium` | 코드베이스 탐색 (추론 포함) |
| `build-fixer` | 빌드/컴파일 에러 해결 |
| `technical-writer` | 기술 문서 작성 |
| `deep-research-agent` | 적응형 심층 리서치 |
| `python-expert` | Python 프로덕션 코드 |
| `tdd-guide` | TDD 방법론 가이드 |
| `refactoring-expert` | 리팩토링 및 클린 코드 |
| `requirements-analyst` | 요구사항 발견 및 분석 |
| `performance-engineer` | 성능 최적화 |
| `quality-engineer` | 소프트웨어 품질 보증 |
| `security-engineer` | 보안 엔지니어링 |
| `devops-architect` | 인프라 및 배포 자동화 |
| `learning-guide` | 프로그래밍 교육 가이드 |
| `socratic-mentor` | 소크라테스식 교육 멘토 |
| `root-cause-analyst` | 근본 원인 분석 |
| `pm-agent` | 자기 개선 워크플로우 실행 |
| `business-panel-experts` | 멀티 전문가 비즈니스 전략 패널 |
| `jin-interview-agent` | 구조적 요구사항 인터뷰 |

### Haiku (저비용, 고속)

빠른 조회, 간단한 수정, 가벼운 작업에 사용됩니다.

| 에이전트 | 설명 |
|----------|------|
| `explore` | 빠른 코드베이스 검색 |
| `writer` | 문서 작성 (README, API docs) |
| `executor-low` | 단일 파일 간단 작업 |
| `build-fixer-low` | 단순 빌드 에러 수정 |
| `architect-low` | 간단한 코드 질문 |
| `code-reviewer-low` | 빠른 코드 품질 확인 |
| `security-reviewer-low` | 빠른 보안 스캔 |
| `scientist-low` | 데이터 조회 및 간단 통계 |
| `researcher-low` | 문서 빠른 조회 |
| `designer-low` | 간단한 스타일링 |
| `tdd-guide-low` | 간단한 테스트 제안 |

### CTI 파이프라인 (Mole 에이전트)

StealthMole MCP 기반 위협 인텔리전스 수집 및 분석 에이전트입니다.

| 에이전트 | 설명 |
|----------|------|
| `mole-research-agent` | 위협 인텔리전스 수집 |
| `mole-intel-organizer-agent` | 인텔리전스 분류 및 구조화 |
| `mole-interview-agent` | CTI 조사 전 인터뷰 |
| `mole-user-identifier-agent` | 사용자 신원 상관관계 분석 |
| `mole-graph-generator-agent` | Mermaid 그래프 시각화 |
| `mole-report-presenter-agent` | 발표자료 생성 |
| `mole-review-agent` | CTI 프로파일링 오케스트레이터 |

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
│       ├── agents/                      # 58 에이전트 (3-tier)
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
