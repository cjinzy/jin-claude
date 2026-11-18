# 스킬별 동작

한국어 · [English](skills.en.md) · [README](../README.md)

jstack 스킬 13개가 각각 어떻게 동작하는지 설명합니다. 호출은 `/jstack:<스킬>` 이고, "(질문)" 은 진행 중 사용자에게 묻는 지점입니다.

| 분류 | 스킬 |
|---|---|
| 시작 | [`claude-init`](#claude-init) · [`onboard`](#onboard) |
| 계획 | [`interview`](#interview) · [`ambition`](#ambition) · [`maestro`](#maestro) |
| 문서화 | [`deepinit`](#deepinit) · [`sot-create`](#sot-create) · [`sot-verify`](#sot-verify) |
| 리뷰 | [`cleanser`](#cleanser) · [`codex-side`](#codex-side) |
| 마무리 | [`commit`](#commit) · [`mole-linear`](#mole-linear) |
| 메타 | [`manage-skills`](#manage-skills) |

---

# 시작

<a name="claude-init"></a>

## `claude-init` — 작성자의 Claude Code 환경(플러그인·설정·statusline)을 한 번에 설치·갱신

- **호출**: `/jstack:claude-init` — 인자 없음. 자동 실행: "jin init", "환경 세팅", "새 머신 세팅" 같은 요청이면 Claude 가 고른다
- **언제**: 새 머신에 Claude Code 를 설치한 직후, 또는 팀 플러그인·설정을 최신으로 맞출 때

**동작**
1. `preflight.py` 로 설치 상태를 점검하고 빠진 항목의 단계만 실행한다. 빠진 게 없으면 재실행·선택만 변경·충돌 audit 만·종료 중 고른다 (질문)
2. 덮어쓸 파일을 알리고 동의와 사용량 수집 주기(1/3/5/10분, 권장 5분)를 받는다. 동의하지 않으면 플러그인 설치·저장소 동기화·설정 병합을 건너뛴다 (질문)
3. 선택 플러그인을 고른다. 필수 플러그인(`context-mode`, `serena`, `i-have-adhd`)과 고른 것 중 빠진 것만 설치한다 (질문)
4. `jstack` 저장소를 `~/.claude/.jin-claude-repo/` 에 clone·pull 하고 statusline·`CLAUDE.md`·보조 문서를 `~/.claude/` 에 복사한다. venv 와 사용량 타이머도 설치한다
5. `~/.claude/settings.json` 에 팀 필수 키는 덮어쓰고, 개인 선호 키(`model`, `language` 등)는 없을 때만 넣는다
6. 다시 점검하고 MCP 연결을 확인한 뒤 충돌 audit 을 돌린다. 적용할 해결안을 고른다 (질문)
7. 이전 대비 변경점·백업 경로·되돌리는 법을 보여주고 `onboard` 를 실행한다

**결과물**: `~/.claude/CLAUDE.md`·보조 문서·`statusline-command.sh`·`settings.json` 갱신(바뀐 파일은 `<이름>_backup_<YYYYMMDD>.<확장자>` 로 백업), `~/.claude/.jin-claude-repo/`·`~/.claude/.venv/`·사용량 타이머(launchd/systemd)·`~/.claude/.jin-claude-plugins.json` 생성, 플러그인 설치
**주의**: `statusLine`·`skipDangerousModePermissionPrompt` 같은 팀 필수 키는 기존 값을 덮어쓴다. 선택 해제한 플러그인은 제거하지 않는다. 타이머가 사라지면 세션 시작 hook 이 init 때 고른 주기(`~/.claude/.jin-claude-usage-interval`, 없으면 5분)로 다시 등록한다.

<a name="onboard"></a>

## `onboard` — 상황별 jstack 사용 흐름 안내

- **호출**: `/jstack:onboard [상황]` — `새 프로젝트`·`기능`·`버그`·`큰 작업`·`리뷰`·`이슈`·`환경` 중 하나, 없으면 전체 안내. 자동 실행: `claude-init` 이 끝날 때, 또는 "온보딩", "사용법", "뭐부터 해야" 같은 요청
- **언제**: jstack 을 처음 쓰거나 지금 할 일에 어떤 스킬을 쓸지 모를 때

**동작**
1. 인자가 상황 이름이면 그 상황의 흐름만 보여준다
2. 인자가 없으면 기본 흐름(plan 모드로 계획 → 승인 → 실행 → 검증 → `commit`, push 는 직접)과 상황 목록을 보여준다
3. 지금 하려는 일을 고르게 한다 (질문)
4. 고른 상황에서 어떤 스킬을 어떤 순서로 부르는지 자세히 안내한다

**결과물**: 없음
**주의**: 키워드로 부르면 Claude 가 스킬을 고르지만 확정은 아니다. 확실히 실행하려면 `/jstack:<스킬>` 로 부른다.

---

# 계획

<a name="interview"></a>

## `interview` — 구현 전에 질문으로 결정을 확정하고 스펙 파일을 쓴다

- **호출**: `/jstack:interview [지시]` — 인터뷰할 기능이나 주제. 자동 실행: "jin interview", "인터뷰", "스펙 작성", "요구사항 정리", "spec" 같은 요청이나, 모호한 기능을 구현하기 전에 결정을 확정하려는 요청을 Claude 가 알아보면 실행
- **언제**: 요구가 모호해서 구현 전에 기술·UI/UX·트레이드오프를 정해야 할 때.

**동작**
1. 관련 코드를 먼저 읽어 질문에 근거를 둔다.
2. 뻔한 건 건너뛰고 구현 방식·UI/UX·우려·트레이드오프를 묻는다 (질문).
3. 질문은 `D1`, `D2` … 번호가 붙은 결정 브리프다: 쉬운 설명, 추천안과 이유, 선택지별 장단점, 한 줄 요약.
4. 추천안은 항상 첫 번째 선택지이고 `(recommended)` 가 붙는다. 선택지마다 다루는 범위가 다르면 `Completeness` 점수(10점 만점)를 붙인다.
5. 모든 결정이 정해질 때까지 계속 묻는다.
6. 스펙을 `docs/specs/<topic>-spec.md` 에 쓴다. `<topic>` 은 지시에서 뽑은 kebab-case 다. 파일이 이미 있으면 덮어쓸지 묻는다 (질문).

**결과물**: `docs/specs/<topic>-spec.md` — `Goal`, `Scope`, `Decisions`, `Accepted shortcuts`, `Open questions`, `Success criteria` 섹션.
**주의**: `Completeness` 7 이하인 선택지를 고르면 그 한계와 업그레이드 조건이 `## Accepted shortcuts` 에 기록된다. `sot-create` 는 시작할 때 이 스킬을 먼저 부른다.

<a name="ambition"></a>

## `ambition` — 계획을 더 크게가 아니라 더 높게·깊게·넓게 키운다

- **호출**: `/jstack:ambition [altitude|depth|range]` — 축 하나만 적용. 생략하면 세 축 모두. 자동 실행: 프롬프트에 `ambition`·`앰비션` 이 있으면 hook 이 묻지 않고 로드한다. 이 단어 없이 plan 모드면 대화당 한 번 ambition 모드로 계획할지 묻는다. "altitude", "depth", "range", "깊게", "다른 분야" 같은 요청도 Claude 가 알아보면 실행
- **언제**: 눈앞의 작업 너머의 결과, 전문가 수준의 깊이, 다른 분야의 기법까지 계획에 담고 싶을 때.

**동작**
1. plan 모드가 아니면 plan 모드 진입 승인을 받는다. 거절하면 현재 모드로 계속한다. (질문)
2. Altitude: 목표 너머의 목표를 2–3단 사다리로 쓴다 (예: 크래시 하나 수정 → 이번 릴리스 크래시 0 → 항상 크래시 없음).
3. 어느 단으로 계획할지 고르게 한다. 원래 작업도 선택지에 있다. (질문)
4. 고른 단을 사람 없이 유지할 전제조건(데이터 접근, 결과↔원인 매핑, 재현·검증 환경)을 점검한다. 부족한 것이 계획의 첫 단계가 된다.
5. Depth: 최고 전문가가 요청받지 않아도 하는 일, 출발할 원자료, 쓸 도구, 결과를 판정할 외부 기준을 한 줄씩 답한다. 핵심 가정 하나를 원자료로 반증해 보는 단계를 넣는다.
6. Range: 산출물을 '하는 일'(동사)로 다시 쓰고, 분야 2–4개와 red team 1개를 꾸린다. 분야마다 실제 기법·도구를 한 줄로 적는다.
7. 채택할 기법을 고르게 한다 (복수 선택). (질문)
8. 계획에 `## Ambition` 섹션을 넣는다. 적용한 축마다 한 항목, 해당 없으면 `N/A — 이유`.

**결과물**: 계획 안의 `## Ambition` 섹션.
**주의**: hook 은 `ambition`·`앰비션` 을 대소문자 구분 없이 부분 문자열로 찾는다. 그 단어를 언급만 해도 스킬이 로드된다. 결과 확인은 테스트·벤치마크·지표 같은 외부 판정으로만 하고, 판정자가 없으면 목표를 높이지 않는다.

<a name="maestro"></a>

## `maestro` — 이 세션을 지휘만 하는 오케스트레이터로 바꾼다

- **호출**: `/jstack:maestro` — 인자 없음. 자동 실행: 없음 (`disable-model-invocation`)
- **언제**: 여러 갈래 작업을 하위 세션에 나눠 맡기고, 이 세션은 계획·분배·보고만 하게 하고 싶을 때.

**동작**
1. 이 세션은 계획·원장 관리·보고 종합·사용자 질문만 한다. 코드 수정·빌드·테스트·조사는 하위 세션 몫이다.
2. plan 모드면 분배 계획(세션 이름·영역·mode·브리프)만 쓴다. 승인 후에 원장을 만들고 위임을 시작한다. (질문)
3. 원장 `.maestro/ledger.md` 를 현재 디렉터리에 만든다. git 저장소면 `.maestro/` 를 `info/exclude` 에 넣는다.
4. 같은 영역의 active·idle 세션이 있으면 그 세션에 이어 맡긴다. 새 일은 새 하위 세션 `m-<영역>-<번호>` 가 받는다. herdr 안에서 실행 중이고 ultracode·오래 걸리는 일이면 herdr pane 에 독립 Claude 세션을 띄우고(Workflow 사용 가능), 그 외엔 named subagent 를 쓴다. 후속 없는 넓은 1회성 일은 Workflow 로 직접 돌린다.
5. 같은 저장소 파일을 동시에 고칠 세션이 둘 이상이면 세션마다 worktree 를 따로 준다. 병합도 하위 세션에 맡긴다.
6. 맡길 때마다 mode 를 정한다: audit·마이그레이션·리뷰·고위험 변경은 `ultracode`, 소규모 수정은 `normal`.
7. 하위 세션이 질문·결정·승인을 요청하면 오케스트레이터가 답하지 않고 사용자에게 그대로 묻는다. 받은 답을 그 세션에 전달한다. (질문)
8. 하위 세션 보고(`STATUS: DONE|BLOCKED`, 변경 파일, 검증 증거, 질문, 후속)를 받아 원장을 고치고 사용자에게 요약한다.
9. 후속도 맥락 유지 가치도 없는 세션은 보관한다. "maestro 종료" 라고 하면 전부 보관하고 최종 요약을 낸다.

**결과물**: `.maestro/ledger.md`, pane 세션 보고 `.maestro/reports/<name>.md`, git `info/exclude` 의 `.maestro/` 한 줄, 하위 세션들, 필요하면 worktree.
**주의**: active 세션은 최대 5개, 그중 `ultracode` 는 동시에 2개까지다. 보관은 원장에 `archived` 로 적고 실행 중이면 멈추는 것이다 (pane 은 닫는다). 보관한 세션엔 다시 맡기지 않고, 같은 영역 새 일은 새 세션이 받는다.

---

# 문서화

<a name="deepinit"></a>

## `deepinit` — 프로젝트를 분석해 에이전트용 `AGENTS.md` 를 만든다

- **호출**: `/jstack:deepinit [프로젝트 경로]` — 생략하면 현재 디렉터리. 자동 실행: "jin deepinit", "프로젝트 분석", "AGENTS.md 생성", "analyze project", "generate AGENTS.md" 같은 요청이나, 새 프로젝트에 에이전트용 안내 문서를 처음 만들려는 요청을 Claude 가 알아보면 실행
- **언제**: 새 프로젝트에 에이전트가 읽을 `AGENTS.md` 가 없을 때.

**동작**
1. `project_analyzer.py` 가 언어(확장자 빈도순), 프레임워크, 구조(`monorepo`·`standard`·`flat`)를 감지한다. `.git`·`.venv`·`node_modules`·`dist`·`build` 등은 건너뛴다.
2. 같은 스크립트가 `AGENTS.md` 초안을 출력한다: 프로젝트 개요, 루트와 한 단계 아래 디렉터리 트리(폴더당 5개까지), 사용 가능한 스킬 표.
3. 스킬 표는 실행 시점의 플러그인 `skills/*/SKILL.md` 의 `name`·`description` 으로 채운다.
4. `README.md`, 설정 파일, 엔트리 포인트를 읽어 아키텍처·개발 패턴·코딩 컨벤션을 보강한다. 근거 없는 내용은 쓰지 않는다.
5. `AGENTS.md` 가 이미 있으면 차이를 보여 주고 덮어쓰기·병합·취소 중에서 고르게 한다 (질문).
6. 없으면 만들 내용을 보여 주고 생성 여부를 묻는다 (질문). 승인한 내용만 쓴다.

**결과물**: 프로젝트 루트 `AGENTS.md` (승인했을 때만).
**주의**: 프레임워크는 루트에 있는 설정 파일(`package.json`, `pyproject.toml`, `requirements.txt` 등)만 보고, 패키지 이름 문자열이 들어 있는지로 판단한다. 초안의 제목·항목명은 한국어다. `python3` 가 필요하다 (표준 라이브러리만).

<a name="sot-create"></a>

## `sot-create` — 에이전트가 인용·검증하는 SoT 문서셋을 `sot/` 에 만든다

- **호출**: `/jstack:sot-create [프로젝트 경로]` — 생략하면 현재 디렉터리. 자동 실행: "jin sot", "SoT 생성", "source of truth", "document this project" 같은 요청이나, 아키텍처·DB 스키마·워크플로·디자인 규칙을 문서로 정리하려는 요청을 Claude 가 알아보면 실행
- **언제**: 프로젝트 지식이 `AGENTS.md`·`CLAUDE.md` 에 담기엔 크거나, 문서 체계를 처음 세울 때.

**동작**
1. 먼저 `interview` 스킬로 인터뷰해 스펙을 확정한다 (질문).
2. 저장소를 읽기만 하며 조사한다: `deepinit` 분석기(언어·프레임워크·구조), 최신 커밋, 루트 `DESIGN.md` 유무.
3. `sot/` 아래 7개 카테고리 디렉터리(`overview`·`tech-stack`·`database-schema`·`architecture`·`workflow`·`design`·`rules`)와 `rules/sot-maintenance.md` 를 만든다. 이건 묻지 않는다.
4. `.gitignore` 에 `sot/`, `CLAUDE.md` 에 `## SoT` 블록을 붙일지 줄 단위로 보여 주고 묻는다 (질문). 승인한 것만 붙인다.
5. 하위 주제마다 파일 하나를 만든다. 사실마다 `## ARC-001 — <주장>` 같은 ID 와 `Evidence: path:line` 을 단다. 모르는 건 `TODO(sot):` 로 남긴다.
6. `sot_index.py` 가 각 문서 frontmatter 로 `Index.md` 를 생성한다.
7. `sot_validate.py` 로 검증하고 error 는 모두 고친다. `DRIFT` 는 diff 를 읽어 사실을 고치거나 `status: stale` 로 표시한다. warning·info 는 요약에 넣는다.

**결과물**: `sot/` 문서셋(`Index.md`, 카테고리별 문서, `rules/sot-maintenance.md`), 인터뷰 스펙 `docs/specs/<topic>-spec.md`. 승인 시 `.gitignore`·`CLAUDE.md` 에 몇 줄 추가.
**주의**: `sot/` 가 이미 있으면 기존 문서를 덮어쓰지 않고 빠진 것만 더한 뒤 재검증한다. `DESIGN.md` 는 만들거나 고치지 않고 인용만 한다. 대화할 수 없는 실행(서브에이전트·CI·`-p`)이면 모든 문서를 `draft` 로 두고 `sot/` 밖은 건드리지 않는다.

<a name="sot-verify"></a>

## `sot-verify` — `sot/` 가 아직 코드와 맞는지 검사하고 오류를 고친다

- **호출**: `/jstack:sot-verify` — 인자 없음. 자동 실행: 없음 (`disable-model-invocation`)
- **언제**: `sot/` 를 고쳤거나, 문서의 `verified_paths` 아래 코드가 바뀐 뒤.

**동작**
1. `sot/` 가 없으면 "SoT 없음 — `/jstack:sot-create`" 한 줄로 끝난다.
2. `sot-create` 의 `sot_index.py --check` 로 `Index.md` 가 최신인지 본다. 낡았으면 다시 생성한다.
3. `sot_validate.py` 로 frontmatter 필수 키, ID 접두사·고유성, `Index.md` 링크, drift 를 검사한다.
4. drift 는 `git diff <verified_commit>..HEAD -- <verified_paths>` 로 잡는다. `status: verified` 문서면 error, 아니면 warning 이다.
5. 구조 error 는 해당 문서의 frontmatter·ID 를 고치고 `Index.md` 를 다시 만든다.
6. `DRIFT` 는 diff 를 읽고 사실을 고친 뒤 `updated`·`verified_commit` 을 올린다. 판단이 안 서면 `status: stale` 과 확인할 내용을 `TODO(sot):` 로 단다.
7. error 가 0 이 될 때까지 다시 검사하고, 문서·fact 수, drift 의심 파일 수, 수정·남은 error, warning 개수를 보고한다.

**결과물**: `sot/` 문서 수정, `sot/Index.md` 재생성.
**주의**: 확인 없이 `sot/` 문서를 고친다 (편집만 하고 템플릿으로 덮어쓰지 않는다). 경로가 `sot` 로 고정이라 프로젝트 루트에서 실행해야 한다. drift 는 커밋된 변경만 본다 — 커밋 안 한 수정은 잡지 않는다.

---

# 리뷰

<a name="cleanser"></a>

## `cleanser` — AI 가 남긴 코드 슬롭을 찾아 리포트만 한다

- **호출**: `/jstack:cleanser [경로]` — 검사할 파일·디렉터리. 생략하면 git 변경분. 자동 실행: "deslop", "slop", "슬롭 검사", "AI 코드 정리", "디버그 코드 남았는지" 같은 요청을 Claude 가 알아보면 실행
- **언제**: 커밋 전에 diff 에 디버그 코드·주석 처리된 코드 같은 AI 흔적이 남았는지 볼 때.

**동작**
1. 경로를 주면 그 경로 전체를 본다.
2. 경로가 없으면 미커밋 변경과 untracked 파일을 본다. 둘 다 없으면 최근 커밋(`HEAD~1` 대비)을 본다.
3. `slop_patterns.py` 로 정적 스캔한다: 디버그 출력(`print(`·`console.log(`·`debugger`·`pdb`·`breakpoint(`), `#` 로 주석 처리된 코드, TODO·FIXME 류 주석. Python 패턴은 `.py` 에만, JS 패턴(`console.log`·`debugger`)은 JS/TS 파일에만 적용한다.
4. `ruff` 가 있으면 Python 미사용 임포트(F401)도 찾는다. 없으면 건너뛰고 리포트에 적는다.
5. Claude 가 파일을 읽고 정규식이 못 잡는 것을 찾는다: 자명한 주석, 과잉·빈 예외 처리, 상투적 docstring, 한 곳에서만 쓰는 래퍼, 뻔한 타입 표기.
6. diff 모드에선 변경된 라인만 남긴다. untracked 파일은 전체가 대상이다.
7. 오탐(의도된 `print` 등)을 걸러 하나의 리포트로 합친다: 심각도(critical·warning·info)별 요약, 이슈 표, 카테고리별 상세.

**결과물**: 없음. 마크다운 리포트만 출력하고 코드는 고치지 않는다.
**주의**: 디렉터리는 `.py .js .jsx .ts .tsx .mjs .cjs` 만 재귀로 훑는다 (`node_modules`·`.venv`·`dist`·`build` 등 제외). 정적 검사는 라인 정규식이라 오탐이 날 수 있다.

<a name="codex-side"></a>

## `codex-side` — OpenAI Codex CLI 로 독립된 2차 의견을 받는다

- **호출**: `/jstack:codex-side [review [focus] | challenge [focus] | <질문>]` — `review` 는 diff 코드 리뷰, `challenge` 는 깨뜨리기 위한 적대적 검증, 그 밖의 텍스트는 질문·계획 검토. `focus` 는 집중할 관점 (예: `challenge security`). 생략하면 고르게 한다. 자동 실행: "codex review", "2차 의견", "second opinion", "교차 검토" 같은 요청을 Claude 가 알아보면 실행
- **언제**: 머지 전에 다른 모델의 독립 리뷰를 받거나, 설계·계획을 다른 AI 로 검증하고 싶을 때.

**동작**
1. `codex` 설치·인증, base 브랜치, 앞선 커밋 수, 미커밋 변경 수를 점검한다. 설치나 인증이 없으면 멈춘다.
2. 인자가 없으면 모드를 정한다. 변경이 있으면 리뷰·적대적 검증·질문 중 고르게 하고, 없으면 질문을 받는다. (질문)
3. 직접 넘긴 base·sha·모델·effort 는 형식을 검사한다. 통과하지 못하면 다시 묻는다. (질문)
4. 모드·범위, OpenAI 전송, 유료 호출, 최대 약 9분 소요를 알리고 보낼지 묻는다. 취소하면 아무것도 보내지 않는다. (질문)
5. Codex 를 읽기 전용 샌드박스에서 실행한다. 540초가 넘으면 끊는다.
6. Codex 답을 원문 그대로 보여준다. `review` 는 게이트를 붙인다: `[P0]`·`[P1]` 이 있으면 FAIL, `P2`·`P3` 만 있으면 PASS, 태그가 없으면 UNVERIFIED.
7. Claude 가 동의·반대 지점을 짚고 `Recommendation:` 한 줄로 권고한다. 결정은 사용자가 한다.
8. consult 후속 질문이면 앞선 Codex 대화를 이어갈지 새로 시작할지 묻는다. (질문)

**결과물**: 저장소 파일은 바꾸지 않는다. 임시 디렉터리에 `last.md`·`transcript.log` 를 만들고 끝나면 지운다. 프롬프트와 저장소 내용이 OpenAI 로 간다.
**주의**: `codex` CLI(`npm install -g @openai/codex`)와 `codex login`(또는 `CODEX_API_KEY`·`OPENAI_API_KEY`)이 필요하다. 실행 실패·타임아웃·빈 출력은 리뷰 FAIL 로 본다. `xhigh` effort 는 타임아웃에 걸리기 쉬우니 `high` 로 다시 시도한다.

---

# 마무리

<a name="commit"></a>

## `commit` — 변경을 분석해 gitmoji + 한국어 메시지로 바로 커밋

- **호출**: `/jstack:commit [message]` — 메시지에 반영할 내용(선택). 자동 실행: "커밋", "commit", "jin commit" 요청이나 작업을 마치고 변경을 커밋할 때 Claude 가 고른다
- **언제**: 작업을 끝내고 변경을 커밋할 때

**동작**
1. `git status`·`git diff`(스테이징돼 있으면 `git diff --staged`)로 변경을 분석한다
2. 지정한 파일이나 이번 변경에 속한 파일만 대상으로 고른다. 무관한 변경·비밀 파일(`.env` 등)은 빼고 알린다. 대상이 모호할 때만 묻는다 (질문)
3. 변경 성격에 맞는 gitmoji 를 고르고 `<이모지> [<이슈 ID>] <한국어 제목> [— 스코프] [+ 추가사항]` 형식으로 메시지를 쓴다. 이슈 ID(예: `[MOLE-123]`)는 브랜치 이름이나 대화에서 알 수 있을 때만 넣는다. 인자가 있으면 반영한다
4. 확인 없이 `git add <파일>` → `git commit` 한다. 호출 자체가 커밋 승인이다
5. 커밋 해시·메시지·포함/제외 파일을 보고한다

**결과물**: 로컬 git 커밋 1개
**주의**: push 는 하지 않는다. `git add -A`·`git add .` 는 쓰지 않는다. `Co-Authored-By` 줄을 넣지 않는다.

<a name="mole-linear"></a>

## `mole-linear` — STEALTHMOLE 팀 규칙대로 Linear 이슈·댓글 작업

- **호출**: `/jstack:mole-linear` — 인자 없음. 자동 실행: "linear", "이슈 등록", "이슈 댓글", "MOLE-", "linear 설치" 처럼 Linear 를 다루는 요청이면 Claude 가 고른다
- **언제**: Linear 이슈를 찾거나 만들거나 상태·댓글을 바꾸기 전

**동작**
1. Linear 도구가 없거나 설치를 요청하면 `setup.md` 대로 옛 Linear MCP 서버와 옛 규칙 파일을 정리한다. claude.ai 커넥터가 있으면 MCP 서버는 모두 지우고, 커넥터도 `linear-server` 도 없을 때만 user scope `linear-server` 를 설치한다. 지우거나 설치할 때마다 묻는다 (질문)
2. 프로젝트 `CLAUDE.md` 의 `Linear project: <이름>` 줄로 프로젝트를 정한다. 없으면 묻고 그 줄을 써 넣는다 (질문)
3. 보관된 이슈까지 먼저 검색하고 없을 때만 만든다. 기본값은 우선순위 Medium, 담당자 본인, 기존 라벨. 큰 작업은 상위 이슈 + 결과물마다 하위 이슈
4. 작업 전에 댓글과 그 안의 `+++ Agent notes` 블록을 모두 읽는다
5. 진행에 맞춰 상태를 바꾸고 정해진 양식으로 댓글을 단다: 계획 → `Plan` + Plan 댓글, 작업 → `In Progress`, 막힘 → BLOCKED 댓글 후 중단, 완료 → Done 댓글 + `Done`(검토가 필요하면 `Feedback`)
6. 모든 커밋·PR 에 이슈 ID 를 넣는다 (커밋 제목 `✨ [MOLE-123] …`). 브랜치는 `<user>/<issue-id>` 소문자다 (예: `jin/mole-123`)

**결과물**: Linear 이슈·댓글·상태, 프로젝트 `CLAUDE.md` 의 `Linear project:` 줄, 설치 시 user scope MCP `linear-server`, 정리 시 `~/.claude/linear.md`·`~/.claude/mcp-linear.md`·`<project>/linear.md` 삭제와 `CLAUDE.md`·`AGENTS.md` 의 `@linear.md`·`@mcp-linear.md` 줄 제거
**주의**: 라벨·상태를 만들지 않고 이슈를 삭제하지 않는다. 이슈 설명은 As-is·To-be 양식이 필수고, Plan 단계에서는 설명을 고치지 않는다. `linear-server` 를 설치했으면 `/mcp` 에서 OAuth 인증을 직접 해야 하고, 세션 중 추가한 서버는 새 세션에서 보인다.

---

# 메타

<a name="manage-skills"></a>

## `manage-skills` — 변경 파일 기준으로 프로젝트 `verify-*` 스킬 점검·생성·갱신

- **호출**: `/jstack:manage-skills [verify 스킬 이름 또는 영역]` — 주면 관련 변경 파일만 본다. 자동 실행: 없음 (`disable-model-invocation`)
- **언제**: 기능 구현 후, PR 전, 또는 verify 스킬이 문제를 놓쳤을 때

**동작**
1. 미커밋 변경, 기본 브랜치 분기 이후 커밋, 새 파일을 모아 변경 파일 목록을 만든다
2. 프로젝트 `.claude/skills/verify-*/SKILL.md` 를 찾아 각 스킬의 Related Files·Workflow 경로와 변경 파일을 맞춰 본다. 어느 스킬에도 안 걸린 파일은 `UNCOVERED` 다
3. 걸린 스킬마다 갭(파일 누락, 깨진 참조, 오래된 명령, 새 패턴, 바뀐 값)을 찾는다. 탐지 명령은 실제로 실행해 본다
4. 갱신할 스킬·새로 만들 스킬·면제 파일을 제안하고 무엇을 할지 고르게 한다 (질문)
5. 승인된 스킬만 고친다. 추가·수정만 하고 아직 동작하는 검사는 지우지 않는다
6. 새 스킬은 이름을 확인받아 템플릿대로 만든다. 이름에 `verify-` 접두사가 없으면 붙인다 (질문)
7. 프로젝트 `CLAUDE.md` 의 `## Skills` 표에 등록할지 묻는다 (질문)
8. 형식·경로·탐지 명령을 확인하고, 보고서와 실행할 `/verify-<name>` 목록을 보여준다

**결과물**: 프로젝트 `.claude/skills/verify-<name>/SKILL.md` 생성·수정, 승인 시 `CLAUDE.md` 의 `## Skills` 표
**주의**: verify 스킬을 직접 실행하지 않고 제안만 한다. 승인 없이 파일을 쓰지 않는다. 개인 `~/.claude/skills/manage-skills` 사본은 세션 시작 hook 이 `~/.claude/backups/` 로 옮긴다.
