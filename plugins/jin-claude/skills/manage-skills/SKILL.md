---
name: manage-skills
description: 브랜치/세션 변경 파일을 프로젝트의 verify-* 검증 스킬(.claude/skills/verify-*/SKILL.md)과 대조해 커버리지 누락·깨진 참조·오래된 검사를 찾고, 사용자 승인 후 verify-* 스킬을 생성하거나 업데이트한다. 기능 구현 후, PR 전, verify 스킬이 이슈를 놓쳤을 때, verify 스킬을 만들거나 정리할 때 사용한다. "manage skills", "verify 스킬 생성", "검증 스킬 업데이트", "스킬 드리프트".
disable-model-invocation: true
argument-hint: "[verify 스킬 이름 또는 집중할 영역]"
---

# verify-* 스킬 유지보수

변경 파일 기준으로 프로젝트 로컬 verify-* 스킬의 드리프트를 찾아 고친다.

- 대상: 사용자 프로젝트의 `.claude/skills/verify-<name>/SKILL.md` 만 생성·수정한다.
- 플러그인 파일(이 SKILL.md 포함)은 읽기 전용 cache 다. 절대 수정하지 않는다. 등록 목록은 두지 않고 매 실행 시 탐색한다.
- 검증 실행 = 발견한 각 verify 스킬 호출(`/verify-<name>`). 이 스킬은 목록을 보여주고 실행을 제안만 한다.

## Step 1: 변경 파일 수집

```bash
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || echo main)
git diff HEAD --name-only            # 미커밋
git diff "$BASE"...HEAD --name-only  # 분기 이후 커밋
git ls-files --others --exclude-standard  # 새 파일
```

합쳐 중복 제거. 인수가 있으면 관련 파일만 남긴다. 상위 1-2 경로 세그먼트로 묶어 보여준다.

## Step 2: verify 스킬 탐색 · 매핑

1. Glob `.claude/skills/verify-*/SKILL.md` (프로젝트 루트 기준).
2. 0개 → 모든 변경 파일 UNCOVERED, Step 4 로.
3. 각 SKILL.md 의 **Related Files** 표와 **Workflow** 의 grep/glob/read 대상에서 경로·패턴을 추출한다.
4. 변경 파일이 패턴 일치 / 참조 디렉토리 내부 / 탐지 regex 일치이면 그 스킬에 매핑한다.

```markdown
| 스킬 | 변경 파일 | 액션 |
|------|-----------|------|
| verify-api | `router.ts` | CHECK |
| (없음) | `package.json` | UNCOVERED |
```

## Step 3: 영향받은 스킬 갭 분석

CHECK 스킬마다 SKILL.md 전체와 매핑된 변경 파일을 읽고 점검한다.

| 갭 유형 | 점검 |
|---------|------|
| 파일 누락 | 도메인 관련 변경 파일이 Related Files 에 없음 |
| 깨진 참조 | Related Files 경로가 더 이상 없음 |
| 오래된 명령 | grep/glob 를 실제 실행해 현재 구조와 맞는지 확인 |
| 새 패턴 | 새 타입·enum·export·등록·설정·명명 규칙을 검사하지 않음 |
| 변경된 값 | 검사 대상 식별자·설정 키·타입명이 바뀜 |

## Step 4: CREATE vs UPDATE 결정

```
UNCOVERED 파일 그룹마다:
  기존 스킬 도메인 → UPDATE
  아니고 3개+ 파일이 공통 규칙 공유 → CREATE (verify-<name>)
  그 외 → 면제 (아래 면제 목록)
```

제안(UPDATE 목록 + 갭, CREATE 후보 + 패턴, 면제 + 사유)을 보여주고 `AskUserQuestion` 으로 업데이트할 스킬, 생성할 스킬, 전체 건너뛰기를 확인한다. 승인 없이 파일을 쓰지 않는다.

## Step 5: UPDATE

승인된 스킬만 대상 편집한다.

- 추가/수정만. 아직 동작하는 검사는 지우지 않는다.
- 새 경로 → Related Files, 새 규칙 → Workflow 단계, 바뀐 값 갱신, 삭제 확인된 파일 참조만 제거.

## Step 6: CREATE

1. 관련 변경 파일을 읽어 패턴을 이해한다.
2. `AskUserQuestion` 으로 이름을 확인한다. `verify-` 접두사(없으면 붙이고 알림), kebab-case.
3. [references/verify-skill-template.md](references/verify-skill-template.md) 를 따라 `.claude/skills/verify-<name>/SKILL.md` 를 만든다.

## Step 7: CLAUDE.md `## Skills` (선택)

프로젝트 `CLAUDE.md` 에 verify 스킬 목록을 둘지 사용자에게 묻는다(`AskUserQuestion`). 승인 시에만:

- `CLAUDE.md` 없음 → 만들지 묻고 생성.
- `## Skills` 없음 → 파일 끝에 섹션 추가.
- 표 행 추가/갱신: `| verify-<name> | <한 줄 설명> |`. 다른 내용은 건드리지 않는다.

## Step 8: 확인

1. 수정한 SKILL.md 를 다시 읽어 frontmatter·코드 블록·표 형식 확인.
2. Related Files 경로 존재 확인: `ls <path> 2>/dev/null || echo "MISSING: <path>"`.
3. 스킬마다 탐지 명령 하나를 드라이런.

## Step 9: 보고

```markdown
## verify 스킬 유지보수 보고
- 변경 파일: N
- 업데이트: `verify-<name>` — <변경 요약>
- 생성: `verify-<name>` — <커버 패턴>
- CLAUDE.md: 갱신함 / 안 함
- 면제: `path` — <사유>
- 실행 제안: `/verify-a`, `/verify-b`
```

## 면제 (스킬 불필요)

- lock·생성 파일·빌드 출력·자동 생성 마이그레이션
- 버전 범프, 린터/포매터 소폭 설정 변경
- 문서(`README.md`, `CHANGELOG.md`, `LICENSE`, `CLAUDE.md`)
- 테스트 픽스처(`fixtures/`, `__fixtures__/`, `test-data/`)
- 벤더/서드파티(`vendor/`, `node_modules/`, 복사된 라이브러리)
- CI/CD·인프라(`.github/`, `.gitlab-ci.yml`, `Dockerfile`)
- `.claude/skills/` 자체
