---
name: jin-maxwork
description: 병렬 에이전트 실행 엔진. 독립적인 태스크를 동시에 실행하여 처리 속도를 극대화합니다. "jin maxwork", "병렬" 시 사용.
triggers:
  - jin maxwork
  - 병렬
argument-hint: "[병렬 처리할 작업 설명]"
---

# Jin Maxwork - 병렬 에이전트 실행 엔진

## 목적

독립적인 태스크를 최대한 병렬로 실행하여 처리 속도를 극대화하는 실행 엔진입니다. 워크트리 격리로 파일 충돌을 방지하고, 병렬 완료 후 통합 검증을 수행합니다:

| 단계 | 에이전트 | 역할 |
|------|----------|------|
| 분석 | `task-planner-agent` (opus) | 태스크 분해 + 병렬 그룹 식별 |
| 실행 | `swe-agent` / `swe-agent-high` (sonnet/opus) | 병렬 태스크 구현 |
| 검증 | `swe-verifier` (sonnet) | 통합 변경 독립 검증 |

## 핵심 원칙

1. **속도 극대화**: 독립 태스크는 모두 `run_in_background=true`로 병렬 실행
2. **워크트리 격리**: 각 병렬 태스크는 `isolation="worktree"`로 파일 소유권 격리
3. **의존성 존중**: 의존성이 있는 태스크는 선행 태스크 완료 후 실행
4. **통합 검증**: 개별 검증이 아닌, 모든 변경을 통합한 후 한 번에 검증

## 워크플로우

### Step 1: 태스크 분석 (Task Analysis)

`task-planner-agent`에게 위임하여 작업을 분해하고 병렬 가능 태스크를 식별합니다.

**위임 프롬프트 템플릿**:
```
다음 작업을 원자적 태스크로 분해하세요.
특히 병렬 실행 가능한 독립 태스크를 식별하는 데 집중하세요:

## 작업 요청
[사용자 요청 전문]

## 프로젝트 컨텍스트
[현재 작업 디렉토리, 프레임워크, 언어 정보]

## 분석 초점
- 파일 소유권이 겹치지 않는 독립 태스크 식별
- 병렬 실행 그룹 생성
- 각 태스크의 파일 소유권 명시

태스크 분해 보고서 형식으로 출력하세요.
```

`TaskCreate`로 각 태스크를 등록합니다.

```markdown
## 태스크 분석 완료

### 병렬 실행 그룹
| 그룹 | 태스크 | 파일 소유권 |
|------|--------|-------------|
| G1 (병렬) | T1, T2, T3 | 각각 독립 파일 |
| G2 (순차) | T4 | T1, T2 결과 의존 |

- **총 태스크**: N개
- **병렬 가능**: M개 (그룹 G1)
- **순차 필요**: K개 (의존성)
```

### Step 2: 병렬 디스패치 (Parallel Dispatch)

각 병렬 그룹의 태스크를 동시에 실행합니다.

**실행 규칙**:
1. 같은 그룹의 독립 태스크는 모두 `Agent(run_in_background=true, isolation="worktree")`
2. `TaskUpdate(status="in_progress")`로 시작 추적
3. 모든 병렬 태스크 완료 대기
4. 다음 그룹이 있으면 순차적으로 다음 그룹 실행

**에이전트 선택**:

| 복잡도 | 에이전트 | 실행 방식 |
|--------|----------|-----------|
| LOW/MEDIUM | `swe-agent` | `run_in_background=true, isolation="worktree"` |
| HIGH | `swe-agent-high` | `run_in_background=true, isolation="worktree"` |

**위임 프롬프트 템플릿**:
```
다음 태스크를 수행하세요:

## 태스크
[태스크 설명]

## 대상 파일 (파일 소유권)
[이 태스크가 수정할 파일 목록 — 이 파일만 수정하세요]

## 컨텍스트
[관련 정보]

수정 완료 후 변경 내용을 보고하세요.
```

```markdown
### 병렬 실행 현황

**그룹 G1** (병렬 실행 중):
| ID | 태스크 | 에이전트 | 상태 | 격리 |
|----|--------|----------|------|------|
| T1 | [설명] | swe-agent | in_progress | worktree |
| T2 | [설명] | swe-agent | in_progress | worktree |
| T3 | [설명] | swe-agent-high | in_progress | worktree |

- **실행 중**: N개
- **완료**: M개
```

### Step 3: 수집 + 검증 (Collect + Verify)

모든 태스크 완료 후 변경을 수집하고 통합 검증합니다.

**수집 절차**:
1. 각 워크트리의 변경 사항을 메인 브랜치로 통합
2. 충돌이 있으면 수동 해결 또는 재실행
3. `TaskUpdate(status="completed")`로 완료 처리

**검증**: `swe-verifier`에게 통합된 전체 변경에 대해 독립 검증을 위임합니다.

**위임 프롬프트 템플릿**:
```
다음 작업의 구현 결과를 독립적으로 검증하세요:

## 원본 작업 요청
[사용자 요청 전문]

## 변경 사항
[git diff 출력 — 모든 병렬 태스크의 통합 diff]

원본 요청과 diff만으로 독립적으로 판단하세요.
SWE Verification Report 형식으로 출력하세요.
```

```markdown
## Maxwork Report

### 작업 요약
- **요청**: [사용자 요청 요약]
- **총 태스크**: N개
- **병렬 실행**: M개 (동시)
- **순차 실행**: K개

### 실행 결과
| ID | 태스크 | 에이전트 | 실행 방식 | 상태 |
|----|--------|----------|-----------|------|
| T1 | [설명] | swe-agent | 병렬 (G1) | completed |
| T2 | [설명] | swe-agent | 병렬 (G1) | completed |
| T3 | [설명] | swe-agent-high | 병렬 (G1) | completed |
| T4 | [설명] | swe-agent | 순차 (G2) | completed |

### 검증 결과
- **독립 검증**: PASS / FAIL
- **재현 테스트**: PASS / FAIL
- **엣지케이스**: N개 PASS / M개 FAIL
- **회귀**: clean / N개 이슈

### 성능
- **병렬 효율**: M개 태스크 동시 실행
- **예상 순차 시간 대비**: ~N배 단축

### 변경 파일 목록
- `path/to/file1.py`
- `path/to/file2.py`
```

**FAIL 시**: 실패한 태스크를 식별하고 개별 재실행 (최대 2회 재시도)

## 예외사항

다음은 **문제가 아닙니다**:

1. **단일 태스크**: 병렬화할 태스크가 1개뿐인 경우 직접 실행
2. **모든 태스크가 의존**: 병렬 가능 태스크가 없으면 순차 실행 (jin-orchestrator 스킬 추천)
3. **워크트리 미지원**: isolation 없이 순차 실행으로 폴백
4. **테스트가 없는 프로젝트**: 회귀 검증에서 "테스트 없음"은 SKIP

## Related Files

| File | Purpose |
|------|---------|
| `agents/task-planner-agent.md` | 태스크 분해 및 병렬 그룹 식별 플래너 |
| `agents/orchestrator-agent.md` | 파이프라인 관리 오케스트레이터 |
| `agents/swe-agent.md` | 태스크 실행 에이전트 (sonnet) |
| `agents/swe-agent-high.md` | 복잡 태스크 실행 에이전트 (opus) |
| `agents/swe-verifier.md` | 독립 검증 에이전트 |
| `skills/jin-orchestrator/SKILL.md` | 전체 오케스트레이션 파이프라인 |
