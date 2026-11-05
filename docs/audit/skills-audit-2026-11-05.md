# 배포 스킬 감사 — 공식 Skill authoring 기준 (2026-11-05)

기준: [best-practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) · [Claude Code skills](https://code.claude.com/docs/en/skills) · [overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
대상: `plugins/jin-claude/skills/*` 12개. 전 스킬 SKILL.md < 500줄(통과), Windows 경로 없음(통과), eval 없음(전 스킬).

## 공통 (여러 스킬)

| # | 문제 | 대상 | 수정 |
|---|---|---|---|
| X1 | `triggers:` 는 Claude Code frontmatter 필드가 아님 → 무시됨. 여기만 있는 트리거 단어는 호출에 안 쓰임 | jin-chub, jin-cleanser, jin-commit, jin-deepinit, jin-gcc, jin-sot-create, jin-suggest | 단어를 description 으로 옮기고 필드 삭제 |
| X2 | 스크립트 경로가 저장소/작업 디렉토리 기준 → 플러그인 설치 환경에서 깨짐. `SKILL_DIR` 은 정의 안 된 placeholder | jin-chub, jin-cleanser, jin-deepinit, jin-sot-create, jin-claude-init | `${CLAUDE_SKILL_DIR}/scripts/...` (공식 치환 변수, cc-skills.md:489) + "실행, 읽지 말 것" 명시 |
| X3 | description 에 WHEN(언제 쓰는지) 없음 / 3인칭 아님 | jin-commit(28자), jin-interview, manage-skills, verify-implementation, jin-gcc, jin-cleanser | "무엇을 한다. ~할 때 사용." 형태로 재작성 |
| X4 | 스킬 목록 하드코딩 → 새 스킬 추가 시 drift | jin-suggest, welcome.md, project_analyzer.py | 누락 스킬 추가 또는 런타임 탐색 |

## High — 동작이 깨지거나 문서와 코드가 어긋남

| 스킬 | 위치 | 문제 |
|---|---|---|
| jin-chub | scripts/install_chub.sh:35,38 | `@anthropic-ai/context-hub` 는 npm 404. 실제 패키지 `@aisuite/chub`(0.1.4, andrewyng/context-hub) — **설치 항상 실패** |
| jin-gcc | SKILL.md:35,40 | `codex --quiet` 플래그 없음(비대화형은 `codex exec`). `"{user_prompt}"` 를 셸에 그대로 삽입 → 따옴표·`$`·백틱에서 깨짐 |
| verify-implementation | SKILL.md:30 | 실행 대상 표가 "(아직 등록된 검증 스킬이 없습니다)" 고정 → 항상 "없음" 출력 후 종료 |
| manage-skills | SKILL.md:256-262 | 자기 자신·verify-implementation SKILL.md 를 수정하라고 지시 → 플러그인 cache 라 업데이트 시 소실 |
| manage-skills / verify-implementation | 여러 줄 | `.claude/skills/manage-skills/...` 등 존재하지 않는 경로 참조 |
| jin-deepinit | SKILL.md:30, 44-62 | 상대 경로 + `python`(macOS 없음). SKILL 은 AGENTS.md 생성을 기대하지만 CLI 는 JSON 만 출력 |
| jin-claude-init | SKILL.md:85 vs sync_repo.py:13 | 문서는 https clone, 코드는 SSH(`git@github.com:`) → SSH 키 없는 팀원 실패 |
| jin-claude-init | SKILL.md:102 vs merge_settings.py:75 | 문서는 "기존 값 보존", 코드는 model 등 덮어쓰기 + 전역 `hooks` 키 삭제 |
| jin-claude-init | sync_repo.py | ~/.claude/ 의 include 문서 15개를 백업 없이 덮어씀 (CLAUDE.md 만 .bak) |

## Med

| 스킬 | 문제 |
|---|---|
| jin-commit | "프로젝트 사용빈도(89회…)" 열은 낡은 수치. 이모지 표 2개 + 자동 선택 규칙 중복. "50자·첫 글자 대문자" 규칙이 한국어 예시와 모순. "사소한 수정은 이모지 없이" vs 🩹 |
| jin-cleanser | SKILL 의 grep 패턴과 slop_patterns.py 정규식 중복 → 결과 불일치. 리포트 형식에 없는 "confidence" 언급. ruff 미설치 대비 없음 |
| jin-chub | :86 "로컬 영속화" vs :87 "팀원에게 함께 표시" 모순. Context7 도구명 미정규화 |
| jin-sot-create | 사용자 확인 없이 CLAUDE.md·.gitignore 수정. 타 스킬(`../jin-deepinit`) 스크립트 상대 호출 |
| jin-gcc | 사용자 프롬프트를 외부 CLI(codex/gemini)로 보내면서 고지 없음. CLI 1개일 때와 0개일 때 관점 구성 불일치 |
| jin-interview | 출력 파일 경로·형식 미지정. `AskUserQuestionTool` → 실제 이름 `AskUserQuestion` |
| jin-suggest | "추천" 단독 트리거 과도. `jin interview` 처럼 실제 없는 호출명 표기 |
| jin-claude-init | 완료 리포트 "Skills: N개 동기화" vs "skills 는 동기화 안 함". Step 5 인라인 코드가 빈 cache 에서 IndexError. pull 실패 시 경고 없이 `rmtree` |

## Low (요약)
- 스킬 디렉토리 안의 dev 전용 파일: `test_*.py`, `jin-claude-init 업데이트 계획.md`(83줄, 낡은 계획서)
- Claude 가 이미 아는 내용 반복(guidelines, verify-implementation Purpose/When 중복 등)
- 이름 `jin-claude-init` 에 예약어 `claude` — API 규칙 위반, Claude Code 는 정상 로드(이름 변경은 breaking 이라 보류 권장)
- eval 없음(전 스킬) — 공식 권장: 스킬당 3개 이상
