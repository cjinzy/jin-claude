---
name: mole-linear
description: STEALTHMOLE(MOLE) 팀 규칙에 맞춰 Linear 이슈를 조회·생성·갱신하고 댓글을 단다 — 제목·As-is/To-be 본문 양식, Plan/Done/BLOCKED 댓글 템플릿, 상태 전환, 다음 agent 인계용 Agent notes. Linear 이슈 검색·생성·수정·상태 변경·댓글 작성, MOLE-123 같은 이슈 작업, 남은 작업·다음 작업 확인 등 Linear 를 다루는 모든 작업 전에 사용한다. "linear", "이슈 등록", "이슈 생성", "이슈 댓글", "MOLE-", "linear mcp setup", "linear 설치".
---

# mole-linear

Linear work for team STEALTHMOLE. Load this before any Linear tool call and follow it to the end of the task.

## Tools

Linear MCP tools. Names below are the tool part; the prefix depends on how Linear is connected (e.g. `mcp__claude_ai_Linear__list_issues` for the claude.ai connector). If no Linear tools are available, or the user asks to install/set up Linear, follow **Setup** first.

* `list_issues` — filter by project / state / assignee (`me`)
* `get_issue` — issue incl. sub-issues, `gitBranchName` (no comments)
* `list_comments` — comments incl. Agent notes. Read before starting work
* `save_issue` — create (no id) or update (with id): status, priority, assignee, labels, parent, due date
* `save_comment` — add a comment to an issue
* `list_projects`, `list_issue_labels` — look up existing values before setting them

## Setup

Ask before each removal or install. Team doc: [Linear MCP Setup](https://linear.app/stealthmole/document/linear-mcp-setup-38a6483987e1).

1. Clean old setups:
   * MCP: in `claude mcp list`, Linear servers = name contains `linear` or URL `mcp.linear.app` (old `mcp-remote`, `/sse`). If `mcp__claude_ai_Linear__*` tools exist (claude.ai connector), remove them all; otherwise keep only `linear-server` (HTTP `/mcp`). `claude mcp remove <name> -s <local|user|project>` (project = shared `.mcp.json`, commit needed).
   * Rules: old `linear.md` + its `@linear.md` line in project `CLAUDE.md` / `AGENTS.md` duplicate this skill → delete both.
2. Install only if there is no claude.ai connector and no `linear-server` — project root, local scope: `claude mcp add --transport http linear-server https://mcp.linear.app/mcp`
3. User runs `/mcp` → `linear-server` → Authenticate (OAuth), then a new session. Until then `claude mcp get linear-server` shows `Failed to connect`. Stop here.
4. New session: apply Rule 2, then verify with `list_issues(project=<name>, assignee="me")`.

## Statuses (team STEALTHMOLE, key `MOLE`, issue prefix `MOLE-`)

`Triage` · `Backlog` · `Todo` · `Plan` · `In Progress` · `Feedback` · `Done` · `Canceled` · `Duplicate`

## Rules

 1. Search existing issues first. Create one only if none exists.
 2. If you don't know which Linear project this directory belongs to, ask the user, then save the answer to memory (CLAUDE.md / agent memory) so you don't ask again. If none exists, ask whether to create one or pick an existing one.
 3. When creating, fill in project, priority (default Medium), assignee (default me), and an existing label. Title and description follow **Issue format**.
 4. Large tasks: create a parent issue and split into sub-issues, one per deliverable. Work through them one at a time.
 5. Picking the next task: `Todo` first, then `Backlog`.
 6. "Remaining work" = all issues except `Done` / `Canceled` / `Duplicate`.
 7. Planning → status `Plan`, post the plan as a comment. Do not edit the description.
 8. Working → status `In Progress`.
 9. Blocked → comment `BLOCKED: ...` and stop. Do not guess.
10. Done → summary comment including commit hash(es) and PR link, status `Done`, set due date. Use `Feedback` if the user must review first. Parent is Done only when all sub-issues are Done.
11. Use the issue's `gitBranchName`; put the issue ID in commits/PRs.
12. Never create labels/statuses, never delete issues.
13. Every issue and comment follows **Writing style**; every comment follows **Comment format**.
14. Before working on an issue, read `list_comments` and every `+++ Agent notes` block in them.

## Writing style (issues and comments)

* Short, plain sentences. Technical terms are fine.
* One sentence, one fact. Each section 3 lines or fewer.
* Cut anything that doesn't change what the reader does.
* Code names (error codes, file names, functions) in backticks.
* Exempt: `+++ Agent notes` blocks.

## Issue format

**Title** — one line, verb form, the core change only. No tags, brackets, or trailing period. ~70 chars max.

* ✅ `로그인 기한이 지난 사용자에게 오류 화면 대신 재로그인 안내 표시` · `Show re-login prompt instead of error page when session expires`
* ❌ `로그인 버그` · `[BE] 로그인 관련 이슈`

**Description** — these sections, in this order:

```
## As-is
현재 상태. 관찰된 동작, 에러 메시지, 수치.

## To-be
어떻게 수정·구현할지. 완료 여부를 확인할 수 있는 결과로.

## 재현 방법
1. ...
2. ...
기대: ... / 실제: ...

## 참고자료
- 링크, 로그, 스크린샷, 관련 이슈 (MOLE-123)
```

* As-is, To-be: always required.
* 재현 방법: required for bugs. Omit when nothing to reproduce (features, chores).
* 참고자료: omit when empty. Never write "없음".
* To-be must be checkable. No "빠르게", "깔끔하게", "개선" alone — state observable behavior or a number.
* One term per concept. Pre-work agent detail (file lists, implementation plan, raw logs) goes in a collapsible block at the end:

```
+++ Agent notes

...

+++
```

## Comment format

One comment, one purpose. Don't restate the description. Lead with the prefix:

```
Plan:
1. ...
2. ...
검증: <how To-be will be confirmed>
```

```
Done: <what changed, 1–3 lines, measured against To-be>
검증: <test/command run and result>
Commit: a1b2c3d · PR: <link>
```

```
BLOCKED: <cause>
필요: <what is needed, from whom>
```

* Status-change comments (Plan / Done / BLOCKED) use these templates exactly.
* Code, logs, diffs → `+++ Agent notes` block or a link, not the comment body.

Done / BLOCKED comments end with an Agent notes block for the next agent (the description is frozen, so learnings go here):

```
+++ Agent notes

결정: <what was chosen, why>
시도·실패: <what didn't work, why>
주의: <traps, side effects>
위치: <key files, commands>
다음: <where to resume>

+++
```

* Omit empty lines. Skip the block if nothing is worth handing off.

## Example

Send real newlines in `description` / `body`, never `\n` escapes.

```
list_issues(project="my-project", state="Todo", assignee="me")
save_issue(team="STEALTHMOLE", project="my-project", title="로그인 기한이 지난 사용자에게 오류 화면 대신 재로그인 안내 표시", priority=3, assignee="me", labels=["backend"], description=<Issue format>)
save_comment(issueId="MOLE-123", body=<Plan: template>)
list_comments(issueId="MOLE-123")  # read prior Agent notes first
save_issue(id="MOLE-123", state="In Progress")
save_comment(issueId="MOLE-123", body=<Done: template>)
```
