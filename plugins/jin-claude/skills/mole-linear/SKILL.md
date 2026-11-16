---
name: mole-linear
description: STEALTHMOLE(MOLE) 팀 규칙에 맞춰 Linear 이슈를 조회·생성·갱신하고 댓글을 단다 — 제목·As-is/To-be 양식, Plan/Done/BLOCKED 댓글, 상태 전환, Agent notes 인계. Linear 를 다루는 모든 작업 전에 사용한다. "linear", "이슈 등록", "이슈 생성", "이슈 댓글", "MOLE-", "linear mcp setup", "linear 설치".
---

# mole-linear

Team STEALTHMOLE (key `MOLE`). Load before any Linear tool call; follow to the end of the task.
No Linear tools, or the user asks to install/set up Linear → follow `setup.md` first.

Statuses: `Triage` · `Backlog` · `Todo` · `Plan` · `In Progress` · `Feedback` · `Done` · `Canceled` · `Duplicate`

## Rules

1. Project: use the `Linear project: <name>` line in the project `CLAUDE.md`. Missing → ask (`list_projects(team="STEALTHMOLE")`), then write that line.
2. Search existing issues first, archived included. Create only if none exists.
3. Create with project, priority (default Medium), assignee (default me), an existing label. Large task → parent + one sub-issue per deliverable.
4. Before work, read `list_comments` and every `+++ Agent notes` block in them.
5. Next task: `Todo`, then `Backlog`. Remaining work = all except `Done` / `Canceled` / `Duplicate`.
6. Status flow:
   * plan → `Plan` + Plan comment. Never edit the description
   * work → `In Progress`
   * blocked → BLOCKED comment, then stop. Don't guess
   * done → Done comment, `Done` + due date (`Feedback` if the user must review). Parent is Done only when all sub-issues are
7. Git is required: issue ID in every commit and PR. Branch from the issue's `gitBranchName` (`get_issue`) when it has one.
8. Never create labels/statuses, never delete issues.

## Writing

Short, plain sentences. One fact each, ≤3 lines per section, one term per concept, code names in backticks. Cut what doesn't change what the reader does. Agent detail (file lists, plans, logs) goes in a `+++ Agent notes` block at the end, exempt from these rules.

**Title**: one line, verb form, core change only. No tags, brackets, or trailing period. ~70 chars.
✅ `로그인 기한이 지난 사용자에게 오류 화면 대신 재로그인 안내 표시` · ❌ `[BE] 로그인 관련 이슈`

**Description**, in this order. As-is and To-be required. 재현 방법 only for bugs. Omit empty 참고자료, never write "없음". To-be is checkable: behavior or a number, not "개선" alone.

```
## As-is
현재 상태. 관찰된 동작, 에러 메시지, 수치.

## To-be
완료 여부를 확인할 수 있는 결과.

## 재현 방법
1. ...
기대: ... / 실제: ...

## 참고자료
- 링크, 로그, 스크린샷, 관련 이슈 (MOLE-123)
```

**Comments**: one purpose each, don't restate the description, use these templates exactly. Code, logs, diffs → Agent notes or a link.

```
Plan:
1. ...
검증: <how To-be will be confirmed>

Done: <what changed vs To-be, 1–3 lines>
검증: <command run and result>
Commit: a1b2c3d · PR: <link>

BLOCKED: <cause>
필요: <what is needed, from whom>
```

Done / BLOCKED end with a handoff block. Omit empty lines; skip it if nothing is worth handing off.

```
+++ Agent notes

결정: <what was chosen, why>
시도·실패: <what didn't work, why>
주의: <traps, side effects>
위치: <key files, commands>
다음: <where to resume>

+++
```
