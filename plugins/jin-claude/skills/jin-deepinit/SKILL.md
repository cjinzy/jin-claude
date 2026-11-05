---
name: jin-deepinit
description: 프로젝트의 언어·프레임워크·디렉토리 구조를 분석하고, 설치된 jin-claude 스킬 목록을 담은 AGENTS.md 를 프로젝트 루트에 생성한다. "jin deepinit", "프로젝트 분석", "AGENTS.md 생성", "AGENTS.md 만들어", "analyze project", "generate AGENTS.md" 요청이나 새 프로젝트에 에이전트용 안내 문서를 처음 만들 때 사용한다.
argument-hint: "[프로젝트 경로 (기본: 현재 디렉토리)]"
---

# jin-deepinit: 프로젝트 분석 및 AGENTS.md 생성

사전 조건: `python3` (표준 라이브러리만 사용).

## 워크플로우

### Step 1: 스캔

번들 스크립트를 **실행한다** (소스를 읽지 않는다). 경로 기본값은 현재 디렉토리.

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/project_analyzer.py" <path>              # JSON
python3 "${CLAUDE_SKILL_DIR}/scripts/project_analyzer.py" --markdown <path>   # AGENTS.md 초안
```

| 출력 | 내용 |
|------|------|
| JSON (기본) | `project_dir`, `project_name`, `languages`(빈도순), `frameworks`, `structure`(`monorepo`/`standard`/`flat`) |
| `--markdown` | AGENTS.md 초안: 프로젝트 개요, 디렉토리 구조, 사용 가능한 스킬 표 |

스킬 표는 실행 시점에 플러그인 `skills/*/SKILL.md` 의 `name`·`description` 에서 생성된다. 손으로 고치지 않는다.

### Step 2: 심층 분석

초안을 보강하기 위해 `README.md`, 설정 파일(`pyproject.toml`, `package.json` 등), 엔트리 포인트를 읽고 아키텍처·개발 패턴·코딩 컨벤션을 파악한다. 근거 없는 내용은 쓰지 않는다.

### Step 3: AGENTS.md 작성 (확인 게이트)

1. 프로젝트 루트에 `AGENTS.md` 가 있는지 확인한다.
2. **있으면**: 기존 내용과 새 초안의 차이를 보여주고 `AskUserQuestion` 으로 덮어쓰기 / 병합 / 취소 중 선택받는다. 답 없이 덮어쓰지 않는다.
3. **없으면**: 생성할 내용을 보여주고 `AskUserQuestion` 으로 생성 여부를 확인한다.
4. 승인된 내용만 쓴다.

## 관련 파일

- `${CLAUDE_SKILL_DIR}/scripts/project_analyzer.py` — 분석 스크립트 (실행 전용)
- `${CLAUDE_SKILL_DIR}/scripts/test_project_analyzer.py` — 테스트 (`cd "${CLAUDE_SKILL_DIR}/scripts" && python3 -m pytest -q`)

## 주의사항

- `.git`, `.venv`, `node_modules`, `__pycache__` 등 숨김·빌드 디렉토리는 스캔에서 제외된다.
