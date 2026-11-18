---
name: sot-verify
description: 프로젝트 `sot/` 문서셋을 검증한다 — Index 최신 여부, frontmatter·ID 규칙, Index 링크, drift(문서 기준 커밋 이후 코드 변경). 오류는 고치고 경고는 보고한다. `/jstack:sot-verify` 로만 실행.
disable-model-invocation: true
---

# sot-verify

`sot/` 가 아직 코드와 맞는지 확인한다. 자동 실행 없음 — 사용자가 호출할 때만.
`sot/` 가 없으면 "SoT 없음 — `/jstack:sot-create`" 한 줄로 끝낸다.

## 1. 실행

```bash
python3 "${CLAUDE_SKILL_DIR}/../sot-create/scripts/sot_index.py" --root sot --check
python3 "${CLAUDE_SKILL_DIR}/../sot-create/scripts/sot_validate.py" --root sot
```

- `--check` exit 1 → `Index.md` 가 낡음. `--check` 없이 다시 실행해 재생성.
- validate: JSON stdout, exit 1 = error 있음. 코드표는 sot-create 스킬 Step 5.

| 검사 | 방법 |
|---|---|
| frontmatter | `id`·`category`·`title`·`status`·`updated` 필수 |
| ID | 카테고리 접두사, 전체 고유 |
| Index | 모든 문서 링크, 링크 대상 존재 |
| drift | `git diff --name-only <verified_commit>..HEAD -- <verified_paths>` 에 변경 있음 → `verified` 면 error |

## 2. 수정

- 구조 error (`MISSING_*`·`BAD_*`·`DUPLICATE_ID`·`NOT_INDEXED`·`DEAD_LINK`) → 해당 문서 frontmatter·ID 수정, Index 재생성.
- `DRIFT` → `git diff <verified_commit>..HEAD -- <verified_paths>` 를 읽고:
  - 사실 정정 + `updated`·`verified_commit` 갱신, `status: verified` 유지
  - 판단 불가 → `status: stale` + 무엇을 확인할지 `TODO(sot):`
- 기존 문서를 템플릿으로 덮어쓰거나 새로 쓰지 않는다 (편집만).
- 수정 후 1 을 다시 실행해 error 0 확인.

## 3. 보고

```
[DONE] sot-verify
- 문서 N · fact N · stale N
- error: 수정 N (남음 N) / warning: 코드별 개수 / TODO(sot): N
```
