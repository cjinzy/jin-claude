---
name: jin-orchestrator
description: 멀티 에이전트 오케스트레이션 파이프라인. 태스크 분해, 병렬 실행, 검증, 자동 수정을 관리합니다. "jin orchestrate", "오케스트레이션" 시 사용.
triggers:
  - jin orchestrate
  - 오케스트레이션
argument-hint: "[작업 설명]"
---

# Jin Orchestrator - 멀티 에이전트 오케스트레이션 파이프라인

## 목적

복잡한 작업을 원자적 태스크로 분해하고, 적절한 에이전트에게 병렬/순차 위임하여 실행한 뒤, 독립 검증과 자동 수정 루프를 통해 품질을 보장하는 4단계 파이프라인입니다:

| 단계 | 에이전트 | 역할 |
|------|----------|------|
| 계획 | `task-planner-agent` (opus) | 태스크 분해 + 의존성 그래프 생성 |
| 오케스트레이션 | `orchestrator-agent` (opus) | 파이프라인 관리 + 에이전트 디스패치 |
| 실행 | `swe-agent` / `python-expert` (sonnet) | 태스크 구현 |
| 실행 (복잡) | `swe-agent-high` (opus) | 교차 모듈 복잡 태스크 |
| 검증 | `swe-verifier` (sonnet) | 독립 검증 (편향 방지) |

## 핵심 원칙

1. **계획과 실행 분리**: task-planner-agent(읽기 전용) → swe-agent/python-expert(쓰기)
2. **실행과 검증 분리**: 실행 에이전트(수정) → swe-verifier(독립 검증)
3. **의존성 기반 실행**: 의존성 그래프에 따라 순차/병렬 실행 자동 결정
4. **워크트리 격리**: 파일 충돌 위험이 있는 태스크는 `isolation="worktree"`로 격리
5. **자동 수정 루프**: 검증 실패 시 최대 3회 자동 재시도

## 워크플로우

### Step 1: 계획 (Planning)

`task-planner-agent`에게 위임하여 작업을 원자적 태스크로 분해합니다.

**위임 프롬프트 템플릿**:
```
다음 작업을 원자적 태스크로 분해하세요:

## 작업 요청
[사용자 요청 전문]

## 프로젝트 컨텍스트
[현재 작업 디렉토리, 프레임워크, 언어 정보]

태스크 분해 보고서 형식으로 출력하세요.
```

분해된 태스크를 `TaskCreate`로 등록하고, `TaskUpdate(addBlockedBy)`로 의존성을 설정합니다.

```markdown
## 계획 완료

### 태스크 목록
| ID | 태스크 | 대상 파일 | 에이전트 | 복잡도 | 의존성 |
|----|--------|-----------|----------|--------|--------|
| T1 | [설명] | [파일] | swe-agent | LOW | - |
| T2 | [설명] | [파일] | python-expert | MEDIUM | T1 |
| T3 | [설명] | [파일] | swe-agent-high | HIGH | T1 |

- **총 태스크**: N개
- **병렬 가능**: M개
- **예상 실행 순서**: T1 → (T2, T3 병렬)
```

### Step 2: 실행 (Execution)

의존성 순서를 존중하면서 각 태스크를 적절한 에이전트에게 위임합니다.

**실행 규칙**:
1. 의존성이 없거나 의존 태스크가 완료된 태스크부터 실행
2. 독립적인 태스크는 `Agent(run_in_background=true)`로 병렬 실행
3. 파일 충돌 위험이 있는 태스크는 `Agent(isolation="worktree")`로 격리
4. `TaskUpdate(status="in_progress")`로 시작, `TaskUpdate(status="completed")`로 완료 추적

**에이전트 선택 기준**:

| 조건 | 에이전트 | 이유 |
|------|----------|------|
| 1-2 파일, 단순 변경, LOW/MEDIUM | `swe-agent` (sonnet) | 표준 워크플로우로 충분 |
| Python 전문 작업, 아키텍처 설계 | `python-expert` (sonnet) | 도메인 전문성 필요 |
| 3+ 파일, 교차 모듈, HIGH | `swe-agent-high` (opus) | 깊은 추론 필요 |

**위임 프롬프트 템플릿**:
```
다음 태스크를 수행하세요:

## 태스크
[태스크 설명]

## 대상 파일
[수정 대상 파일 목록]

## 컨텍스트
[관련 태스크 결과 또는 의존성 정보]

수정 완료 후 변경 내용을 보고하세요.
```

```markdown
### 실행 진행 현황

| ID | 태스크 | 상태 | 에이전트 | 비고 |
|----|--------|------|----------|------|
| T1 | [설명] | completed | swe-agent | - |
| T2 | [설명] | in_progress | python-expert | 병렬 실행 중 |
| T3 | [설명] | in_progress | swe-agent-high | 병렬 실행 중 |

- **완료**: N / M 태스크
- **진행 중**: K개
```

### Step 3: 검증 (Verification)

모든 태스크 완료 후 `swe-verifier`에게 독립 검증을 위임합니다.

**편향 방지**: 실행 에이전트의 추론이나 분석 보고서는 전달하지 않습니다.

**위임 프롬프트 템플릿**:
```
다음 작업의 구현 결과를 독립적으로 검증하세요:

## 원본 작업 요청
[사용자 요청 전문]

## 변경 사항
[git diff 출력 — `git diff` 또는 `git diff HEAD~1`로 생성]

원본 요청과 diff만으로 독립적으로 판단하세요.
SWE Verification Report 형식으로 출력하세요.
```

검증 결과를 확인합니다:
- PASS → Step 4 (완료)로 진행
- FAIL → Step 4 (수정 루프)로 진행

```markdown
### 검증 결과

- **판정**: PASS / FAIL
- **재현 검증**: PASS / FAIL
- **엣지케이스**: N개 PASS / M개 FAIL
- **회귀**: clean / N개 이슈
```

### Step 4: 수정 루프 / 완료 (Fix Loop / Completion)

**PASS 경로**:

```markdown
## Orchestration Report

### 작업 요약
- **요청**: [사용자 요청 요약]
- **태스크**: N개 (병렬 M개, 순차 K개)
- **검증**: PASS

### 실행 결과
| ID | 태스크 | 에이전트 | 상태 | 변경 파일 |
|----|--------|----------|------|-----------|
| T1 | [설명] | swe-agent | completed | `path/to/file.py` |
| T2 | [설명] | python-expert | completed | `path/to/file2.py` |

### 검증 결과
- **독립 검증**: PASS
- **재현 테스트**: PASS
- **엣지케이스**: N개 PASS
- **회귀**: clean

### 변경 파일 목록
- `path/to/file1.py`
- `path/to/file2.py`
```

**FAIL 경로** (수정 루프):

FAIL 사유를 기반으로 수정 태스크를 생성하여 재실행합니다.

```markdown
### 수정 루프 (N/3)

- **실패 원인**: [verifier 보고서에서 추출]
- **수정 태스크**: [새로 생성된 태스크 목록]

Step 2로 돌아갑니다...
```

- 최대 3회 반복
- 3회 반복 후에도 FAIL → 사용자에게 보고 후 수동 수정 권장

**최종 FAIL** (3회 반복 초과):

```markdown
## Orchestration Report - 수동 수정 필요

### 작업 요약
[작업 요약]

### 시도한 수정
| 반복 | 접근 방식 | 실패 원인 |
|------|-----------|-----------|
| 1차 | [접근법] | [실패 원인] |
| 2차 | [접근법] | [실패 원인] |
| 3차 | [접근법] | [실패 원인] |

### 권장 사항
[수동 수정을 위한 가이드]

### 수집된 분석 정보
[과정에서 확인된 유용한 정보]
```

## 예외사항

다음은 **문제가 아닙니다**:

1. **단순 작업**: 태스크가 1개인 경우 오케스트레이션 없이 직접 에이전트 위임
2. **테스트가 없는 프로젝트**: 회귀 검증에서 "테스트 없음"은 FAIL이 아닌 SKIP
3. **lsp 서버 미설정**: lsp_diagnostics 실패 시 Bash 기반 검증으로 대체
4. **워크트리 미지원 환경**: isolation 없이 순차 실행으로 폴백

## Related Files

| File | Purpose |
|------|---------|
| `agents/orchestrator-agent.md` | 파이프라인 관리 및 에이전트 디스패치 오케스트레이터 |
| `agents/task-planner-agent.md` | 태스크 분해 및 의존성 그래프 생성 플래너 |
| `agents/swe-agent.md` | 6단계 워크플로우 이슈 해결 실행자 (sonnet) |
| `agents/swe-agent-high.md` | 복잡 이슈 해결 에이전트 (opus) |
| `agents/swe-verifier.md` | 독립 검증 에이전트 |
| `agents/python-expert.md` | Python 전문 개발 에이전트 |
| `skills/jin-maxwork/SKILL.md` | 병렬 에이전트 실행 엔진 |
| `skills/jin-fsd/SKILL.md` | Full Self-Driving 모드 (사용자 승인 게이트) |
| `skills/jin-ralph/SKILL.md` | 자기참조 반복 루프 |
