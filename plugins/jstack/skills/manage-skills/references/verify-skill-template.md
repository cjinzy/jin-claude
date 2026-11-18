# verify-<name> 스킬 템플릿

위치: 프로젝트 `.claude/skills/verify-<name>/SKILL.md`.

## Frontmatter

```yaml
---
name: verify-<name>
description: <무엇을 검사한다>. <트리거 조건> 후 사용한다.
---
```

## 필수 섹션

| 섹션 | 내용 |
|------|------|
| Purpose | 번호 매긴 검증 카테고리 2-5개 |
| When to Run | 트리거 조건 3-5개 |
| Related Files | 실제 경로 표(`ls` 로 확인, placeholder 금지) |
| Workflow | 검사 단계. 각 단계에 도구(Grep/Glob/Read/Bash), 정확한 경로·패턴, PASS/FAIL 기준, 실패 시 수정법 |
| Output Format | 결과 마크다운 표 |
| Exceptions | 위반이 아닌 현실적 사례 2-3개 이상 |

## Workflow 단계 예

````markdown
### Step N: <검사 이름>

**파일:** `path/to/file.ts`
**검사:** <무엇을 확인하는지>

```bash
grep -n "pattern" path/to/file.ts
```

**PASS:** <조건> · **FAIL:** <조건> → <수정법>
````

## 품질 기준

- 경로는 실재, 탐지 명령은 현재 파일에 매칭(드라이런 확인).
- 각 검사에 명확한 PASS/FAIL.
- 기존 verify 스킬과 같은 형식(frontmatter, 섹션 헤더, 표 구조).
