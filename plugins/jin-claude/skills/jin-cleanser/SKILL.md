---
name: jin-cleanser
description: AI 생성 코드 슬롭 리뷰어. git diff 또는 지정 파일에서 불필요한 코멘트, 과잉 에러 처리, 미사용 임포트 등을 탐지하여 리포트를 생성합니다. "jin cleanser", "jin deslop" 시 사용.
triggers:
  - jin cleanser
  - jin deslop
argument-hint: "[파일/디렉토리 경로 또는 공백=최근 git diff]"
---

# jin-cleanser: AI 생성 코드 슬롭 리뷰어

AI가 생성한 코드에서 흔히 발생하는 불필요한 패턴(슬롭)을 정적 분석 + 시맨틱 분석으로 탐지하여 리포트를 생성한다. **자동 삭제/수정은 하지 않는다.**

## 슬롭 카테고리

| Category | Severity | Detection | 설명 |
|----------|----------|-----------|------|
| unnecessary-comment | warning | Semantic (agent) | 코드가 자명한데 붙은 불필요한 주석 |
| excessive-error-handling | warning | Semantic (agent) | 발생 불가능한 예외를 잡는 과잉 에러 처리 |
| unused-import | warning | Static (ruff F401) | 사용하지 않는 임포트 |
| boilerplate-docstring | info | Semantic (agent) | 의미 없는 보일러플레이트 독스트링 |
| over-abstraction | info | Semantic (agent) | 한 번만 사용되는 불필요한 추상화 |
| redundant-type-annotation | info | Semantic (agent) | 타입 추론 가능한 곳의 중복 타입 명시 |
| leftover-debug | critical | Static (grep) | 남겨진 디버그 코드 (print, console.log, debugger 등) |
| dead-code | warning | Static (grep) | 주석 처리된 대량 코드 블록, 미사용 함수 |

## 워크플로우

### Step 1: Target Identification (대상 식별)

분석 대상을 결정한다:

1. **인자가 파일/디렉토리인 경우** → 해당 경로를 분석
2. **인자가 없는 경우** → `git diff HEAD`로 미커밋 변경사항 분석
3. **미커밋 변경이 없는 경우** → `git diff HEAD~1`로 최근 커밋 분석

```bash
# 변경된 파일 목록 추출
git diff HEAD --name-only --diff-filter=ACMR
# 변경 없으면 최근 커밋 대상
git diff HEAD~1 --name-only --diff-filter=ACMR
```

### Step 2: Static Scan (정적 스캔)

자동화 가능한 패턴을 정적 도구로 탐지한다.

#### unused-import (ruff F401)
```bash
ruff check --select F401 --output-format json {target_files}
```

#### leftover-debug (grep)
```bash
grep -rn 'console\.log\|print(\|debugger\|pdb\.set_trace\|breakpoint()' {target_files}
```

#### dead-code (grep)
```bash
# 연속 3줄 이상 주석 처리된 코드 블록 탐지
grep -rn -A2 '^[[:space:]]*#.*[=\(\)\[\]{};]' {target_files}
```

정적 스캔에는 `scripts/slop_patterns.py` 모듈을 활용할 수 있다.

### Step 3: Semantic Review (시맨틱 리뷰)

Claude 에이전트가 각 파일을 읽고 다음 항목을 분석한다:

- **unnecessary-comment**: 코드가 자명한데 붙은 주석 (`# 리스트를 반복한다` 등)
- **excessive-error-handling**: 발생 불가능한 예외를 잡는 try/except, 빈 except 블록
- **boilerplate-docstring**: `"""This function does X."""` 같은 의미 없는 독스트링
- **over-abstraction**: 한 곳에서만 호출되는 단순 래퍼 함수
- **redundant-type-annotation**: `x: int = 1` 같이 리터럴에서 타입이 자명한 경우

시맨틱 리뷰는 파일 단위로 병렬 실행한다.

### Step 4: Report (리포트 생성)

정적 스캔 + 시맨틱 리뷰 결과를 통합하여 마크다운 보고서를 생성한다.

#### 리포트 형식

```markdown
## AI Slop 분석 리포트

### 요약
| 심각도 | 건수 |
|--------|------|
| critical | N |
| warning | N |
| info | N |

### 이슈 목록
| # | 파일 | 라인 | 카테고리 | 심각도 | 제안 |
|---|------|------|----------|--------|------|
| 1 | path/to/file.py | 42 | leftover-debug | critical | `print()` 호출 제거 |
| 2 | path/to/file.py | 15 | unnecessary-comment | warning | 자명한 주석 제거 고려 |
| 3 | path/to/file.py | 8 | unused-import | warning | `import os` 미사용 |

### 카테고리별 상세

#### leftover-debug (critical)
- `path/to/file.py:42` — `print(result)` 디버그 출력 잔존

#### unnecessary-comment (warning)
- `path/to/file.py:15` — `# 결과를 반환한다` (return 문 위의 자명한 주석)

**주의: 이 도구는 리뷰만 수행합니다. 자동 삭제/수정은 하지 않습니다.**
```

## 관련 파일

- `skills/jin-cleanser/SKILL.md` — 본 스킬 정의
- `skills/jin-cleanser/scripts/slop_patterns.py` — 정적 슬롭 패턴 감지 모듈
- `skills/jin-cleanser/scripts/test_slop_patterns.py` — 패턴 감지 테스트

## 주의사항

- **리포트 전용**: 자동 삭제/수정은 절대 수행하지 않는다. 사용자가 직접 판단하여 수정한다.
- 시맨틱 리뷰의 판단은 확률적이므로 오탐(false positive)이 있을 수 있다. confidence 레벨을 함께 표시한다.
- 대규모 diff(파일 50개 이상)에서는 변경된 줄 근처만 분석하여 시간을 절약한다.
