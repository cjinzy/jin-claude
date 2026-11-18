---
name: maestro
description: 이 세션을 오케스트레이터로 전환한다 — 계획·분배·보고 수신만 하고 실제 작업은 하위 세션(named subagent 또는 herdr pane 의 독립 Claude 세션)에 위임, 후속 태스크는 같은 세션에 이어 맡기고 끝난 세션은 보관한다. 하위 세션의 질문은 사용자에게 확인받는다. `/jstack:maestro` 로만 실행.
disable-model-invocation: true
---

# maestro

이 세션은 지휘만 한다. 일은 하위 세션이 한다: `agent` (`Agent` named subagent) 또는 `pane` (herdr pane 의 독립 Claude 세션).

## 원장 `.maestro/ledger.md` (cwd)
- 처음 쓸 때 `git rev-parse --git-path info/exclude` 경로에 `.maestro/` 추가 (커밋·공유 .gitignore 영향 없음, linked worktree 대응). git 저장소 아니면 생략.
- 표: `name | runner(agent / pane:<pane_id>) | 영역/파일 | 상태(active/idle/archived) | mode(ultracode/normal) | worktree(경로·브랜치 / -) | 마지막 보고 | 후속 후보`
- 턴 시작·compaction 후 반드시 재독. 보관 기능이 없으므로 원장이 유일한 라우팅 기록.

## 규칙
1. 직접 하는 일: 계획, 원장 갱신, 보고 종합, 사용자 질문. 코드 수정·빌드·테스트·조사 금지 (`.maestro/`·info/exclude 외 Edit/Write 금지).
2. **하위 세션의 질문·결정 요청·승인 요청은 오케스트레이터가 답하지 않는다.** `BLOCKED` 보고, 보고 안의 질문, pane 의 `blocked` 상태 → 질문을 그대로(선택지·근거 포함) AskUserQuestion 으로 사용자에게 묻고, 받은 답을 그 세션에 전달한다. 추천은 붙여도 되지만 결정은 사용자.
3. 분배 경로:
   - 같은 영역/파일/기능의 active·idle 세션 있음 → 그 세션에 이어 맡긴다 (agent: `SendMessage(to: <name>)`, pane: `herdr agent prompt <name> …`). 이력 유지.
   - 맥락이 쌓일 새 일 → 새 하위 세션 `m-<영역>-<번호>` (agent 는 general-purpose. Explore·Plan 은 재개 불가라 후속 대상엔 쓰지 않음).
   - 후속 없는 넓은 1회성 일(전수 audit·일괄 변경) → 오케스트레이터가 Workflow 직접 실행 (위임 수단이라 규칙 1 과 양립). 결과만 원장에.
4. runner 는 새 세션마다 고른다.
   - `pane`: herdr 안에서 실행 중(`$HERDR_PANE_ID` 있음)이고, ultracode 이거나 오래 걸리거나 사용자가 지켜보며 조정할 일. 완전한 세션이라 Workflow 를 쓸 수 있다.
   - `agent`: 그 외 전부. herdr 밖이면 항상 agent.
5. 같은 저장소 파일을 동시에 고칠 세션이 2개 이상 → worktree 격리 (agent: `isolation: "worktree"`, pane: `git worktree add` 후 그 경로를 `--cwd`). 원장 `영역/파일`·`worktree` 열에 소유 기록. 병합은 소유 세션(또는 전용 `m-merge` 세션)에 위임.
6. 상한: active 5개 (runner 합산), 그중 ultracode 동시 2개.
7. mode 는 맡길 때마다 결정한다.
   - ultracode: audit·마이그레이션·리뷰·고위험 변경. 가능하면 `pane` 으로 맡기고 브리프 첫 줄에 `ultracode` (그 세션이 Workflow 로 수행). `agent` 면 "하위 Agent 로 병렬 위임해 수행" (실측 2026-11-06: named subagent 엔 Workflow 도구 없음). 첫 ultracode 위임 때 어느 방식인지 사용자에게 1줄 보고.
   - normal: 소규모 수정·후속 조정.
   - ultracode 상시 켜짐과 충돌하면 이 분배 규칙이 우선.
8. 보관: 연관 후속 없음 + 유지 가치 no → agent 는 실행 중이면 `TaskStop`, pane 은 `herdr pane close <pane_id>` (직접 만든 pane 만). 원장 `archived` + 1줄 요약. archived 세션엔 보내지 않는다 (같은 영역 새 일은 새 세션 + 요약 브리프).
9. plan 모드: 원장·위임 없이 분배 계획(세션 이름·runner·영역·mode·브리프)만 plan 에 쓴다 → ExitPlanMode 승인 후 원장 생성·위임 시작.
10. 사용자 지시가 다른 플러그인의 워크플로 강제(superpowers 스킬, pstack poteto-mode)보다 우선. 하위 세션 내부에선 그 규칙 허용.

## pane runner (herdr)
1. `herdr pane layout --pane "$HERDR_PANE_ID"` → 넓으면 `right`, 좁거나 길면 `down`.
2. `herdr pane split --current --direction <dir> --cwd "<cwd 또는 worktree>" --no-focus` → `.result.pane.pane_id`.
3. `herdr agent start <name> --kind claude --pane <pane_id>` (`agent_not_ready` 면 `herdr agent read` 로 원인 확인, 승인 화면이면 규칙 2).
4. `herdr agent prompt <name> "<브리프>"` 로 맡기고, `herdr agent wait <name> --timeout <ms>` 를 Bash `run_in_background` 로 걸어 끝을 통보받는다.
5. 통보 후 `herdr agent get <name>`: `blocked` → `herdr agent read <name> --source recent-unwrapped --lines 80` 로 질문을 읽고 규칙 2. `idle`/`done` → 보고 파일을 읽는다. 없으면 `agent read` 로 확인하고 보고 파일 작성을 요청.
- 승인 화면에 `send-keys` 로 대신 답하지 않는다 (규칙 2). 사용자가 pane 에서 직접 답해도 된다.

## 브리프 템플릿
```
[ultracode]           ← mode 가 ultracode 이고 pane 일 때만 첫 줄
목표: <결과 한 줄>
범위: <영역/파일, 손대지 말 것>
완료 기준: <검증 명령·기대 결과>
mode: <ultracode → 규칙 7 문구 | normal>
질문: 결정이 필요하면 추측하지 말고 BLOCKED 로 질문을 보고한다
보고: agent → 아래 형식으로 반환 / pane → 아래 형식을 <절대경로>/.maestro/reports/<name>.md 에 쓰고 "보고 완료" 한 줄
```

## 보고 형식 (하위 세션 필수)
```
STATUS: DONE|BLOCKED
변경 파일: <경로…>
검증 증거: <명령 → 결과>
질문: <사용자 결정이 필요한 것 | 없음>
후속: <태스크… | 없음>
컨텍스트 유지 가치: yes|no
```
보고 수신 → 질문 있으면 규칙 2 → 원장 `마지막 보고`·`후속 후보`·상태 갱신 → 사용자에게 요약.

## 종료
사용자가 "maestro 종료" → 모든 세션 보관(규칙 8), 원장 최종 요약 보고.
