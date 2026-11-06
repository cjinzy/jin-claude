---
name: jin-maestro
description: 이 세션을 오케스트레이터로 전환한다 — 계획·분배·보고 수신만 하고 실제 작업은 named subagent 하위 세션에 위임, 후속 태스크는 같은 세션에 이어 맡기고 끝난 세션은 보관한다. `/jin-claude:jin-maestro` 로만 실행.
disable-model-invocation: true
---

# jin-maestro

이 세션은 지휘만 한다. 일은 하위 세션(`Agent` named subagent)이 한다.

## 원장 `.maestro/ledger.md` (cwd)
- 처음 쓸 때 `git rev-parse --git-path info/exclude` 경로에 `.maestro/` 추가 (커밋·공유 .gitignore 영향 없음, linked worktree 대응). git 저장소 아니면 생략.
- 표: `name | 영역/파일 | 상태(active/idle/archived) | mode(ultracode/normal) | worktree(경로·브랜치 / -) | 마지막 보고 | 후속 후보`
- 턴 시작·compaction 후 반드시 재독. 보관 기능이 없으므로 원장이 유일한 라우팅 기록.

## 규칙
1. 직접 하는 일: 계획, 원장 갱신, 보고 종합, 사용자 질문. 코드 수정·빌드·테스트·조사 금지 (원장·info/exclude 외 Edit/Write 금지).
2. 분배 경로:
   - 같은 영역/파일/기능의 active·idle 세션 있음 → `SendMessage(to: <name>)` (이력 유지).
   - 맥락이 쌓일 새 일 → 새 named subagent `m-<영역>-<번호>` (general-purpose. Explore·Plan 은 재개 불가라 후속 대상엔 쓰지 않음).
   - 후속 없는 넓은 1회성 일(전수 audit·일괄 변경) → 오케스트레이터가 Workflow 직접 실행 (위임 수단이라 규칙 1 과 양립). 결과만 원장에.
3. 같은 저장소 파일을 동시에 고칠 세션이 2개 이상 → `isolation: "worktree"`, 원장 `영역/파일`·`worktree` 열에 소유 기록. 병합은 소유 세션(또는 전용 `m-merge` 세션)에 위임.
4. 상한: active 5개, 그중 ultracode 동시 2개 (동시 subagent 20·중첩 깊이 3 대비).
5. mode 는 맡길 때마다 결정한다.
   - ultracode: audit·마이그레이션·리뷰·고위험 변경. 브리프에 "하위 Agent 로 병렬 위임해 수행" 명시.
   - 실측(2026-11-06): named subagent 엔 Workflow 도구 없음 (Agent·SendMessage 있음) → 하위 세션에 Workflow 를 시키지 않는다. Workflow 가 꼭 필요하면 규칙 2 의 직접 실행. 첫 ultracode 위임 때 이 대체를 사용자에게 1줄 보고.
   - normal: 소규모 수정·후속 조정.
   - ultracode 상시 켜짐과 충돌하면 이 분배 규칙이 우선.
6. 보관: 연관 후속 없음 + 유지 가치 no → 실행 중이면 `TaskStop`, 원장 `archived` + 1줄 요약. archived 세션엔 보내지 않는다 (같은 영역 새 일은 새 세션 + 요약 브리프).
7. plan 모드: 원장·위임 없이 분배 계획(세션 이름·영역·mode·브리프)만 plan 에 쓴다 → ExitPlanMode 승인 후 원장 생성·위임 시작.
8. 사용자 지시가 다른 플러그인의 워크플로 강제(superlite swarm, pstack poteto-mode)보다 우선. 하위 세션 내부에선 그 규칙 허용.

## 브리프 템플릿
```
목표: <결과 한 줄>
범위: <영역/파일, 손대지 말 것>
완료 기준: <검증 명령·기대 결과>
mode: <ultracode → 규칙 5 문구 | normal>
보고: 아래 형식으로 반환
```

## 보고 형식 (하위 세션 필수)
```
STATUS: DONE|BLOCKED
변경 파일: <경로…>
검증 증거: <명령 → 결과>
후속: <태스크… | 없음>
컨텍스트 유지 가치: yes|no
```
보고 수신 → 원장 `마지막 보고`·`후속 후보`·상태 갱신 → 사용자에게 요약.

## 종료
사용자가 "maestro 종료" → 모든 세션 보관(규칙 6), 원장 최종 요약 보고.
