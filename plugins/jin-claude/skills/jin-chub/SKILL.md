---
name: jin-chub
description: 커뮤니티 큐레이션 API 문서를 chub CLI로 검색/조회/어노테이션합니다. "jin chub", "chub", "context-hub", "API 문서 검색" 요청 시 사용.
triggers:
  - jin chub
  - chub
  - context-hub
  - API 문서
argument-hint: "[search query | get <id> | annotate <id> <note>]"
---

# jin-chub: 커뮤니티 큐레이션 API 문서 도구

## 개요

[context-hub](https://github.com/andrewyng/context-hub) (`chub` CLI)는 AI 코딩 에이전트를 위한 **커뮤니티 큐레이션 API 문서** 도구다.

| 항목 | Context7 MCP | chub CLI |
|------|-------------|----------|
| 소스 | 공식 라이브러리 문서 | 커뮤니티 큐레이션 문서 |
| 최적화 | 범용 | 에이전트 최적화 (토큰 효율) |
| 어노테이션 | 불가 | 로컬 어노테이션 영속화 |
| 피드백 루프 | 없음 | up/down 피드백으로 품질 개선 |
| 접근 방식 | MCP 서버 (자동 연동) | CLI (명시적 호출) |

**사용 시점**: Context7에 없는 문서, 커뮤니티 팁이 필요한 경우, 문서에 갭이 있어 어노테이션을 남기고 싶은 경우.

---

## 사전 조건

- **Node.js >= 18** 필수
- 설치 스크립트: `bash plugins/jin-claude/skills/jin-chub/scripts/install_chub.sh`

---

## 워크플로우

### Step 0: CLI 존재 확인

```bash
which chub
```

chub가 없으면 사용자에게 설치를 안내한다:

```
chub CLI가 설치되어 있지 않습니다.
설치하시겠습니까? → bash plugins/jin-claude/skills/jin-chub/scripts/install_chub.sh
```

설치 후 다시 `which chub`로 확인한다.

### Step 1: 검색

```bash
chub search [query]
```

- 사용자가 인자를 제공하면 해당 쿼리로 검색
- 인자가 없으면 `AskUserQuestion`으로 검색어를 요청

검색 결과에서 `id`, `title`, `description`을 테이블로 정리하여 사용자에게 보여준다.

### Step 2: 문서 조회

```bash
chub get <id> [--lang py|js|ts|go|rust]
```

- 프로젝트 언어를 자동 감지하여 `--lang` 옵션을 설정한다:
  - `pyproject.toml` 또는 `*.py` 존재 → `--lang py`
  - `package.json` 존재 → `--lang js` 또는 `--lang ts` (tsconfig.json 존재 시)
  - `go.mod` 존재 → `--lang go`
  - `Cargo.toml` 존재 → `--lang rust`
- 조회한 문서 내용을 바탕으로 사용자 질문에 답변한다

### Step 3: 어노테이션 (갭 발견 시)

문서에 누락되거나 부정확한 내용을 발견하면:

```bash
chub annotate <id> "<note>"
```

- 어노테이션은 로컬에 영속화된다
- 팀원이 같은 문서를 조회할 때 어노테이션이 함께 표시된다

### Step 4: 피드백

문서 품질에 대한 피드백을 남긴다:

```bash
chub feedback <id> up    # 유용한 문서
chub feedback <id> down  # 개선 필요
```

---

## Context7 vs chub 선택 기준

| 상황 | 선택 | 이유 |
|------|------|------|
| 공식 API 레퍼런스 필요 | Context7 | 공식 문서 자동 연동 |
| Context7에 해당 라이브러리 없음 | chub | 커뮤니티 커버리지가 넓음 |
| 에이전트 최적화된 짧은 문서 필요 | chub | 토큰 효율 최적화 |
| 문서에 팀 내부 메모 남기기 | chub | 어노테이션 기능 |
| 최신 공식 API 변경 확인 | Context7 | 공식 소스 직접 참조 |
| 두 도구 모두 결과 없음 | WebSearch | 웹 검색 폴백 |

**일반 규칙**: Context7 먼저 시도 → 결과 불충분 시 chub → 둘 다 없으면 WebSearch

---

## 어노테이션 관리

```bash
chub annotate --list              # 모든 로컬 어노테이션 조회
chub annotate --list <id>         # 특정 문서의 어노테이션 조회
chub annotate --clear <id>        # 특정 문서의 어노테이션 삭제
```

---

## 주의사항

1. chub는 커뮤니티 소스이므로 공식 문서와 차이가 있을 수 있다. 중요한 API 사용 시 Context7과 교차 검증을 권장한다.
2. 어노테이션은 로컬 저장이므로 팀 간 공유가 필요하면 별도 동기화가 필요하다.
3. `--lang` 자동 감지가 잘못된 경우 사용자에게 확인 후 수동 지정한다.
