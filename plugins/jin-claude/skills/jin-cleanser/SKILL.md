---
name: jin-cleanser
description: AI 가 생성한 코드의 슬롭(디버그 코드 잔재, 주석 처리된 코드, 자명한 주석, 과잉 에러 처리, 미사용 임포트, 불필요한 추상화)을 정적 스캔과 시맨틱 리뷰로 찾아 리포트한다. 코드는 수정하지 않는다. "jin cleanser", "jin deslop", "deslop", "slop", "슬롭 검사", "AI 코드 정리", "디버그 코드 남았는지", 커밋 전 diff 의 AI 흔적 점검을 요청할 때 사용한다.
argument-hint: "[파일/디렉토리 경로 | 생략 시 git diff]"
---

# jin-cleanser

AI 생성 코드의 슬롭을 찾아 리포트만 한다. **삭제/수정은 하지 않는다** — 판단과 수정은 사용자 몫.

전제: `python3`, `git`. `ruff` 는 선택 — 없으면 unused-import(F401) 검사를 건너뛰고 리포트에 그 사실을 적는다.

## 카테고리

| Category | Severity | 탐지 |
|----------|----------|------|
| leftover-debug | critical | 스크립트: `print(`, `pdb`, `breakpoint(` (Python) / `console.log(`, `debugger` (JS/TS) |
| dead-code | warning | 스크립트: `# def/class/if/for/while/return/import` 로 시작하는 주석 (Python). 그 외 언어·미사용 함수는 시맨틱 |
| unused-import | warning | 스크립트: ruff F401 (Python, ruff 설치 시) |
| unnecessary-comment | warning | 스크립트: TODO/FIXME/HACK/XXX/TEMP 주석. 자명한 주석(`# 리스트를 반복한다`)은 시맨틱 |
| excessive-error-handling | warning | 시맨틱: 발생 불가능한 예외 처리, 빈 except |
| boilerplate-docstring | info | 시맨틱: `"""This function does X."""` 류 |
| over-abstraction | info | 시맨틱: 한 곳에서만 쓰는 단순 래퍼 |
| redundant-type-annotation | info | 시맨틱: `x: int = 1` 처럼 리터럴로 자명한 타입 |

## 워크플로우

### Step 1: 대상 식별

1. 인자가 경로 → 그 경로 (diff 범위 제한 없음).
2. 인자 없음 → 미커밋 변경 + untracked 파일:
   ```bash
   git diff HEAD --name-only --diff-filter=ACMR
   git ls-files --others --exclude-standard
   ```
3. 둘 다 비면 → 최근 커밋: `git diff HEAD~1 --name-only --diff-filter=ACMR`

### Step 2: 정적 스캔 (스크립트 실행)

정적 검사는 이 스크립트 하나로만 한다. 읽지 말고 **실행**한다:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/slop_patterns.py" <파일|디렉토리> [...]
```

- 출력(stdout): 마크다운 리포트 — `### 요약`(심각도별 건수) + `### 이슈 목록` 테이블. ruff 가 없으면 끝에 `> ruff 미설치 — unused-import(F401) 검사 생략.` 한 줄.
- 디렉토리는 `.py .js .jsx .ts .tsx .mjs .cjs` 를 재귀 스캔 (`.git`, `node_modules`, `.venv`, `venv`, `__pycache__`, `dist`, `build` 제외). 파일 인자는 확장자와 무관하게 스캔.
- 종료 코드: `0` 정상, `2` 인자 없음, `3` 없는 경로 (stderr 에 경로 출력, 스캔 안 함).
- 라인 정규식이라 오탐 가능 (예: CLI 의 의도된 `print`). 리포트 전에 해당 라인을 확인해 걸러낸다.

### Step 3: 시맨틱 리뷰

카테고리 표의 "시맨틱" 항목을 파일별로 읽고 판단한다. 파일이 여러 개면 파일 단위로 병렬 실행.

diff 모드(Step 1 의 2·3)에서는 변경 라인만 본다:
```bash
git diff -U0 HEAD -- <file>   # 최근 커밋 모드는 HEAD~1
```
hunk 헤더 `@@ -a,b +c,d @@` → 라인 `c` ~ `c+d-1` (d 생략 = 1, d=0 = 삭제만이라 제외). 정적 결과도 이 범위 밖이면 제외한다. untracked 파일은 전체가 대상.

### Step 4: 리포트

스크립트 출력을 기반으로 시맨틱 결과를 같은 `이슈 목록` 테이블에 합친다 (심각도 내림차순 재번호, `요약` 건수 재집계). 끝에 카테고리별 상세를 붙인다:

```markdown
### 카테고리별 상세

#### leftover-debug (critical)
- `path/to/file.py:42` — `print(result)` 디버그 출력 잔존

#### unnecessary-comment (warning)
- `path/to/file.py:15` — `# 결과를 반환한다` (return 위의 자명한 주석)
```
