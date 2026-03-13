---
name: jin-deepinit
description: 프로젝트 구조를 분석하고 적합한 jin-claude 에이전트를 추천하는 AGENTS.md를 생성합니다. "jin deepinit", "프로젝트 분석" 시 사용.
triggers:
  - jin deepinit
  - 프로젝트 분석
argument-hint: "[프로젝트 경로 (기본: 현재 디렉토리)]"
---

# jin-deepinit: 프로젝트 분석 및 AGENTS.md 생성

프로젝트 구조를 분석하여 사용 언어, 프레임워크, 디렉토리 구조를 감지하고,
프로젝트에 적합한 jin-claude 에이전트를 추천하는 AGENTS.md 파일을 생성한다.

## 워크플로우

### Step 1: 스캔

`project_analyzer.py`를 실행하여 프로젝트 기본 정보를 감지한다:

- **언어 감지**: 파일 확장자 기반 (`.py` → Python, `.ts` → TypeScript 등)
- **프레임워크 감지**: 설정 파일 파싱
  - `package.json` → React, Vue, Svelte, Next.js 등 (dependencies 확인)
  - `pyproject.toml` → FastAPI, Django, Flask 등 (dependencies 확인)
  - `Cargo.toml` → Rust
  - `go.mod` → Go
  - `build.gradle` / `pom.xml` → Java/Kotlin
- **구조 유형**: monorepo, standard, flat 판별
- **주요 디렉토리**: src, tests, docs, scripts 등 식별

```bash
python scripts/project_analyzer.py [프로젝트_경로]
```

### Step 2: 심층 분석

주요 파일을 읽어 프로젝트 아키텍처를 이해한다:

- `README.md` — 프로젝트 개요, 목적
- 설정 파일 (`pyproject.toml`, `package.json` 등) — 의존성, 빌드 설정
- 엔트리 포인트 (`main.py`, `app.py`, `index.ts` 등) — 애플리케이션 구조
- 개발 패턴, 코딩 컨벤션 파악

### Step 3: 에이전트 추천

프로젝트 특성을 jin-claude 에이전트에 매핑한다:

| 프로젝트 특성 | 추천 에이전트 | 이유 |
|--------------|-------------|------|
| Python 프로젝트 | `python-expert` | Python 전문 코딩 |
| Python 프로젝트 | `swe-agent` | 버그 수정, 이슈 해결 |
| 복수 모듈/서비스 | `jin-orchestrator` | 멀티 에이전트 오케스트레이션 |
| 복수 모듈/서비스 | `jin-maxwork` | 대규모 병렬 작업 |
| 보안 민감 프로젝트 | `jin-gcc` | 보안 관점 코드 리뷰 |
| 복잡한 버그 | `swe-agent-high` | 심층 디버깅 |
| CTI/위협 인텔리전스 | `mole-*` 에이전트 | 위협 정보 분석 |
| 신규 팀원 온보딩 | `jin-claude-init` | 프로젝트 초기 설정 |

### Step 4: AGENTS.md 생성

`AskUserQuestion`으로 생성 여부를 확인한 후, 프로젝트 루트에 AGENTS.md를 생성한다.

## 출력 형식

```markdown
# AGENTS.md

## 프로젝트 개요
- **언어**: Python 3.12
- **프레임워크**: FastAPI, SQLAlchemy
- **구조**: Standard (src/tests)

## 추천 에이전트

| 에이전트 | 모델 | 추천 이유 | 사용 예시 |
|----------|------|-----------|-----------|
| python-expert | sonnet | Python 프로젝트 | "이 함수를 리팩토링해줘" |
| swe-agent | sonnet | 버그 수정 | "jin swe [이슈 설명]" |

## 사용 가능한 스킬

| 스킬 | 트리거 | 설명 |
|------|--------|------|
| jin-orchestrator | "jin orchestrate" | 멀티 에이전트 오케스트레이션 |
| jin-maxwork | "jin maxwork" | 대규모 병렬 작업 처리 |
| jin-commit | "commit" | Gitmoji 기반 커밋 메시지 생성 |
| jin-deepinit | "jin deepinit" | 프로젝트 분석 및 AGENTS.md 생성 |
```

## 관련 파일

- `agents/` — jin-claude 에이전트 정의 파일
- `skills/` — jin-claude 스킬 정의 파일
- `scripts/project_analyzer.py` — 프로젝트 구조 분석 모듈

## 주의사항

- 숨김 디렉토리 (`.git`, `.venv`, `node_modules`, `__pycache__`)는 스캔에서 제외한다
- 기존 AGENTS.md가 있을 경우 덮어쓰기 전 확인을 요청한다
- 분석 결과는 JSON 형식으로도 출력 가능하다
