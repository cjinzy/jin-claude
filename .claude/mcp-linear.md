# linear.md

# Linear (MCP)

Issue tracking for this project. Always check Linear before starting work.

## Tools

* `list_issues` — filter by project / state / assignee (`me`)
* `get_issue` — full issue incl. sub-issues, comments, `gitBranchName`
* `save_issue` — create (no id) or update (with id): status, priority, assignee, labels, parent, due date
* `save_comment` — add a comment to an issue
* `list_projects`, `list_issue_labels` — look up existing values before setting them

## Statuses (team STEATLHMOLE, issue prefix `MOLE-`)

`Triage` · `Backlog` · `Todo` · `Plan` · `In Progress` · `Feedback` · `Done` · `Canceled` · `Duplicate`

## Rules

 1. Search existing issues first. Create one only if none exists.
 2. If you don't know which Linear project this directory belongs to, ask the user, then save the answer to memory (CLAUDE.md / agent memory) so you don't ask again. If none exists, ask whether to create one or pick an existing one.
 3. When creating, fill in project, priority (default Medium), assignee (default me), and an existing label.
 4. Large tasks: create a parent issue and split into sub-issues, one per deliverable. Work through them one at a time.
 5. Picking the next task: `Todo` first, then `Backlog`.
 6. "Remaining work" = all issues except `Done` / `Canceled` / `Duplicate`.
 7. Planning → status `Plan`, post the plan as a comment. Do not edit the description.
 8. Working → status `In Progress`.
 9. Blocked → comment `BLOCKED: ...` and stop. Do not guess.
10. Done → summary comment including commit hash(es) and PR link, status `Done`, set due date. Use `Feedback` if the user must review first. Parent is Done only when all sub-issues are Done.
11. Use the issue's `gitBranchName`; put the issue ID in commits/PRs.
12. Never create labels/statuses, never delete issues.

## Example

```
list_issues(project="my-project", state="Todo", assignee="me")
save_issue(team="STEATLHMOLE", project="my-project", title="Add authentication", priority=3, assignee="me", labels=["backend"])
save_comment(issueId="MOLE-123", body="Plan: ...")
save_issue(id="MOLE-123", state="In Progress")
save_comment(issueId="MOLE-123", body="Done: ... (commit a1b2c3d, PR #45)")
```
