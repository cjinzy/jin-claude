---
name: jin-ralph
description: 태스크 완료까지 자기참조 반복 루프. verifier가 승인할 때까지 실행→검증→수정을 반복합니다. "jin ralph" 시 사용.
triggers:
  - jin ralph
argument-hint: "[반복 실행할 작업 설명]"
---

# Jin Ralph - 자기참조 반복 루프

## 목적

태스크를 실행하고 독립 검증을 수행한 뒤, 검증 실패 시 피드백을 반영하여 재실행하는 자기참조 반복 루프입니다. verifier가 PASS를 줄 때까지 최대 5회 반복합니다:

| 단계 | 에이전트 | 역할 |
|------|----------|------|
| 실행 | `swe-agent` (sonnet) | 태스크 구현 (표준) |
| 실행 (복잡) | `swe-agent-high` (opus) | 태스크 구현 (복잡) |
| 검증 | `swe-verifier` (sonnet) | 독립 검증 + 피드백 생성 |

## 핵심 원칙

1. **반복 수렴**: 각 반복에서 verifier 피드백을 반영하여 점진적으로 품질 수렴
2. **독립 검증**: swe-verifier는 매 반복마다 원본 요청 + 최신 diff만으로 판단 (편향 방지)
3. **피드백 루프**: verifier의 FAIL 사유가 다음 반복의 수정 가이드
4. **반복 제한**: 최대 5회 반복 후 수동 수정 권장
5. **복잡도 에스컬레이션**: 2회 실패 후 swe-agent → swe-agent-high로 자동 에스컬레이션

## 워크플로우

### Step 1: 실행 (Execute)

작업 복잡도에 따라 적절한 에이전트에게 위임합니다.

**초기 실행 (반복 1)**: 코드베이스 분석 후 복잡도를 판단합니다.

| 조건 | 에이전트 | 이유 |
|------|----------|------|
| 1-2 파일, LOW/MEDIUM | `swe-agent` (sonnet) | 표준 워크플로우로 충분 |
| 3+ 파일, HIGH, 교차 모듈 | `swe-agent-high` (opus) | 깊은 추론 필요 |

**재실행 (반복 2+)**: verifier 피드백을 포함하여 위임합니다.

**위임 프롬프트 템플릿 (초기)**:
```
다음 작업을 수행하세요:

## 작업 요청
[사용자 요청 전문]

## 프로젝트 컨텍스트
[현재 작업 디렉토리, 프레임워크, 언어 정보]

6단계 워크플로우를 따르세요.
SWE Fix Result 형식으로 출력하세요.
```

**위임 프롬프트 템플릿 (재실행)**:
```
다음 작업을 수행하세요. 이전 시도에서 검증 실패한 피드백을 반영하세요:

## 작업 요청
[사용자 요청 전문]

## 이전 시도의 검증 피드백
[swe-verifier의 FAIL 보고서]

## 실패 원인
[구체적 실패 지점]

## 권장 수정 방향
[verifier가 제안한 수정 방향]

피드백을 반영하여 수정하세요.
SWE Fix Result 형식으로 출력하세요.
```

`TaskCreate`로 각 반복을 태스크로 등록합니다.

```markdown
### 실행 완료 (반복 N/5)

- **에이전트**: swe-agent / swe-agent-high
- **수정 파일**: N개
- **자체 검증**: PASS / FAIL
```

### Step 2: 검증 (Verify)

`swe-verifier`에게 독립 검증을 위임합니다.

**편향 방지**: 실행 에이전트의 추론은 전달하지 않습니다.

**위임 프롬프트 템플릿**:
```
다음 작업의 구현 결과를 독립적으로 검증하세요:

## 원본 작업 요청
[사용자 요청 전문]

## 변경 사항
[git diff 출력]

원본 요청과 diff만으로 독립적으로 판단하세요.
SWE Verification Report 형식으로 출력하세요.
```

검증 결과를 확인합니다:
- **PASS** → 완료 보고서 생성
- **FAIL** → Step 3 (루프)로 진행

```markdown
### 검증 결과 (반복 N/5)

- **판정**: PASS / FAIL
- **재현 검증**: PASS / FAIL
- **엣지케이스**: N개 PASS / M개 FAIL
- **회귀**: clean / N개 이슈
- **FAIL 사유**: [있으면 기록]
```

### Step 3: 루프 (Loop)

검증 FAIL 시 피드백을 반영하여 Step 1로 복귀합니다.

**루프 판단 로직**:

```
if 판정 == PASS:
    → 완료 보고서 생성
elif 반복 횟수 >= 5:
    → 최종 FAIL 보고서 생성 (수동 수정 권장)
elif 반복 횟수 >= 2 and 현재 에이전트 == swe-agent:
    → swe-agent-high로 에스컬레이션 후 Step 1
else:
    → verifier 피드백 반영하여 Step 1
```

**에스컬레이션 (반복 3회차)**:
```markdown
### 에스컬레이션

- **이유**: swe-agent로 2회 시도 실패
- **변경**: swe-agent → swe-agent-high (opus)
- **반복**: 3/5
```

`TaskUpdate`로 각 반복의 상태를 추적합니다.

```markdown
### 반복 이력
| 반복 | 에이전트 | 판정 | 실패 원인 |
|------|----------|------|-----------|
| 1 | swe-agent | FAIL | [사유] |
| 2 | swe-agent | FAIL | [사유] |
| 3 | swe-agent-high | PASS | - |
```

**PASS 완료 보고서**:

```markdown
## Ralph Report

### 작업 요약
- **요청**: [사용자 요청 요약]
- **총 반복**: N회
- **최종 에이전트**: swe-agent / swe-agent-high
- **판정**: PASS

### 반복 이력
| 반복 | 에이전트 | 판정 | 실패 원인 | 수정 내용 |
|------|----------|------|-----------|-----------|
| 1 | swe-agent | FAIL | [사유] | [초기 구현] |
| 2 | swe-agent | FAIL | [사유] | [피드백 반영 수정] |
| 3 | swe-agent-high | PASS | - | [에스컬레이션 수정] |

### 최종 검증 결과
- **독립 검증**: PASS
- **재현 테스트**: PASS
- **엣지케이스**: N개 PASS
- **회귀**: clean

### 변경 파일 목록
- `path/to/file1.py`
- `path/to/file2.py`
```

**최종 FAIL 보고서** (5회 초과):

```markdown
## Ralph Report - 수동 수정 필요

### 작업 요약
- **요청**: [사용자 요청 요약]
- **총 반복**: 5회
- **판정**: FAIL (최대 반복 초과)

### 반복 이력
| 반복 | 에이전트 | 판정 | 실패 원인 |
|------|----------|------|-----------|
| 1 | swe-agent | FAIL | [사유] |
| 2 | swe-agent | FAIL | [사유] |
| 3 | swe-agent-high | FAIL | [사유] |
| 4 | swe-agent-high | FAIL | [사유] |
| 5 | swe-agent-high | FAIL | [사유] |

### 패턴 분석
[반복 실패의 공통 패턴이나 근본 원인 추론]

### 권장 사항
[수동 수정을 위한 가이드]

### 수집된 분석 정보
[과정에서 확인된 유용한 정보]
```

## 예외사항

다음은 **문제가 아닙니다**:

1. **1회 PASS**: 첫 번째 시도에서 PASS하면 반복 없이 즉시 완료
2. **테스트가 없는 프로젝트**: 회귀 검증에서 "테스트 없음"은 FAIL이 아닌 SKIP
3. **lsp 서버 미설정**: lsp_diagnostics 실패 시 Bash 기반 검증으로 대체
4. **에스컬레이션 불필요**: 초기부터 swe-agent-high를 선택한 경우 에스컬레이션 없음

## Related Files

| File | Purpose |
|------|---------|
| `agents/swe-agent.md` | 6단계 워크플로우 이슈 해결 실행자 (sonnet) |
| `agents/swe-agent-high.md` | 복잡 이슈 해결 에이전트 (opus) |
| `agents/swe-verifier.md` | 독립 검증 에이전트 |
| `skills/jin-orchestrator/SKILL.md` | 멀티 에이전트 오케스트레이션 파이프라인 |
| `skills/jin-swe-fix/SKILL.md` | SWE Fix 파이프라인 (유사 구조) |
