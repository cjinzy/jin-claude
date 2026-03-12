---
name: jin-swe-fix
description: Live-SWE-agent 워크플로우로 소프트웨어 이슈를 체계적으로 해결합니다. "swe fix", "fix issue", "fix bug" 시 사용.
triggers:
  - swe fix
  - fix issue
  - fix bug
  - solve issue
  - swe-agent
argument-hint: "[이슈 설명 또는 GitHub issue URL]"
---

# SWE Fix - Live-SWE-agent 통합 파이프라인

## 목적

Live-SWE-agent(SWE-bench Verified 1위, 79.2%)의 6단계 워크플로우를 4-에이전트 파이프라인으로 오케스트레이션합니다:

| 단계 | 에이전트 | 역할 |
|------|----------|------|
| 분석 | `swe-analyst` (sonnet) | 읽기 전용 근본원인 진단 |
| 수정 | `swe-agent` (sonnet) | 6단계 워크플로우 실행 |
| 수정 (복잡) | `swe-agent-high` (opus) | 교차 모듈/복잡 이슈 |
| 검증 | `swe-verifier` (sonnet) | 독립 검증 (편향 방지) |

## 핵심 원칙

1. **분석과 실행 분리**: swe-analyst(읽기 전용) → swe-agent(쓰기)
2. **실행과 검증 분리**: swe-agent(수정) → swe-verifier(독립 검증)
3. **편향 방지**: swe-verifier는 원본 이슈 + diff만 받음 (분석자의 추론은 전달하지 않음)
4. **THOUGHT 기반 추론**: 모든 에이전트가 행동 전 명시적 추론 기록

## 워크플로우

### Step 1: 이슈 접수

이슈 입력을 파싱합니다:

- **GitHub URL**: `gh issue view <number>` 또는 `gh issue view <url>`로 상세 내용을 가져옵니다
- **텍스트 설명**: 이슈 설명으로 직접 사용합니다
- **모호한 경우**: `AskUserQuestion`으로 추가 정보를 요청합니다 (또는 `jin-interview` 스킬 추천)

```markdown
## SWE Fix 시작

**이슈**: [이슈 제목/설명 요약]
**소스**: GitHub Issue #N / 사용자 설명

파이프라인을 시작합니다...
```

### Step 2: 분석 단계

`swe-analyst` 에이전트에게 위임합니다.

**위임 프롬프트 템플릿**:
```
다음 이슈를 분석하세요:

## 이슈
[Step 1에서 파싱한 이슈 전문]

## 프로젝트 컨텍스트
[현재 작업 디렉토리, 프레임워크, 언어 정보]

SWE Analysis Report 형식으로 출력하세요.
```

분석 결과에서 다음을 추출합니다:
- 근본 원인
- 영향 파일 목록
- 수정 계획
- 복잡도 평가 (LOW/MEDIUM/HIGH)
- 모델 라우팅 권장

```markdown
### 분석 완료

- **근본 원인**: [요약]
- **영향 파일**: N개
- **복잡도**: LOW / MEDIUM / HIGH
```

**사소한 이슈 바이패스**: 이슈가 명백히 단순한 경우 (오타 수정, 단일 줄 변경 등) 이 단계를 건너뛰고 Step 4로 바로 진행할 수 있습니다.

### Step 3: 복잡도 판단 및 에이전트 선택

분석 결과의 복잡도와 영향 파일 수를 기반으로 실행 에이전트를 선택합니다:

| 조건 | 에이전트 | 이유 |
|------|----------|------|
| 1-2 파일, 단순 패턴, LOW/MEDIUM | `swe-agent` (sonnet) | 표준 워크플로우로 충분 |
| 3+ 파일, 교차 모듈, HIGH | `swe-agent-high` (opus) | 깊은 추론 필요 |
| 레이스 컨디션, 동시성 이슈 | `swe-agent-high` (opus) | 복잡한 메커니즘 추적 |
| 아키텍처 결함 | `swe-agent-high` (opus) | 구조적 수정 필요 |

```markdown
### 에이전트 선택

- **선택**: swe-agent / swe-agent-high
- **이유**: [선택 근거]
```

### Step 4: 수정 실행

선택된 에이전트(`swe-agent` 또는 `swe-agent-high`)에게 위임합니다.

**위임 프롬프트 템플릿**:
```
다음 이슈를 해결하세요:

## 이슈
[Step 1에서 파싱한 이슈 전문]

## 분석 결과
[Step 2의 분석 보고서 - 근본 원인, 영향 파일, 수정 계획]

6단계 워크플로우(분석→재현→수정→검증→엣지케이스→완료)를 따르세요.
SWE Fix Result 형식으로 출력하세요.
```

수정 완료 후 결과를 확인합니다:
- 수정된 파일 목록
- 검증 결과 (PASS/FAIL)

```markdown
### 수정 완료

- **수정 파일**: N개
- **자체 검증**: PASS / FAIL
```

### Step 5: 독립 검증

`swe-verifier` 에이전트에게 위임합니다.

**편향 방지**: 분석 보고서나 수정자의 추론은 전달하지 않습니다.

**위임 프롬프트 템플릿**:
```
다음 이슈 수정을 독립적으로 검증하세요:

## 원본 이슈
[Step 1에서 파싱한 이슈 전문]

## 변경 사항
[git diff 출력 — `git diff` 또는 `git diff HEAD~1`로 생성]

원본 이슈와 diff만으로 독립적으로 판단하세요.
SWE Verification Report 형식으로 출력하세요.
```

검증 결과를 확인합니다:
- PASS → Step 6으로 진행
- FAIL → Step 4로 재시도 (FAIL 사유 포함)

```markdown
### 검증 결과

- **판정**: PASS / FAIL
- **재현 검증**: PASS / FAIL
- **엣지케이스**: N개 PASS / M개 FAIL
- **회귀**: clean / N개 이슈
```

### Step 6: 완료

최종 보고서를 생성합니다.

**PASS 경로**:

```markdown
## SWE Fix Report

### 이슈
- **설명**: [이슈 요약]
- **소스**: [GitHub Issue #N / 사용자 설명]

### 근본 원인
[분석 결과 요약]

### 수정 내용
| 파일 | 변경 | 이유 |
|------|------|------|
| `path:line` | [변경 설명] | [이유] |

### 검증 결과
- **독립 검증**: PASS
- **재현 테스트**: PASS
- **엣지케이스**: N개 PASS
- **회귀**: clean

### 수정 파일 목록
- `path/to/file1.py`
- `path/to/file2.py`
```

**FAIL 경로** (재시도):

- FAIL 사유를 포함하여 Step 4로 재시도
- 최대 2회 재시도
- 2회 재시도 후에도 FAIL → 사용자에게 보고 후 수동 수정 권장

```markdown
### 재시도 (N/2)

- **실패 원인**: [verifier 보고서에서 추출]
- **수정 방향**: [추가 수정 계획]

Step 4로 돌아갑니다...
```

**최종 FAIL** (2회 재시도 초과):

```markdown
## SWE Fix Report - 수동 수정 필요

### 이슈
[이슈 요약]

### 시도한 수정
| 시도 | 접근 방식 | 실패 원인 |
|------|-----------|-----------|
| 1차 | [접근법] | [실패 원인] |
| 2차 | [접근법] | [실패 원인] |

### 권장 사항
[수동 수정을 위한 가이드]

### 수집된 분석 정보
[분석 과정에서 확인된 유용한 정보]
```

## 예외사항

다음은 **문제가 아닙니다**:

1. **사소한 이슈**: 오타, 단일 줄 변경 등은 분석 단계(Step 2)를 건너뛰고 바로 `swe-agent`에게 위임
2. **테스트가 없는 프로젝트**: 회귀 검증에서 "테스트 없음"은 FAIL이 아닌 SKIP
3. **lsp 서버 미설정**: lsp_diagnostics 실패 시 Bash 기반 검증으로 대체
4. **GitHub URL이 아닌 이슈**: 텍스트 설명도 동등하게 처리

## Related Files

| File | Purpose |
|------|---------|
| `agents/swe-analyst.md` | 읽기 전용 근본원인 분석 에이전트 |
| `agents/swe-agent.md` | 6단계 워크플로우 이슈 해결 실행자 (sonnet) |
| `agents/swe-agent-high.md` | 복잡 이슈 해결 에이전트 (opus) |
| `agents/swe-verifier.md` | 독립 검증 에이전트 |
