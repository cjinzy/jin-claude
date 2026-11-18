# How each skill works

[한국어](skills.md) · English · [README](../README.en.md)

What each of the 13 jstack skills does, step by step. Call them with `/jstack:<skill>`; "(asks)" marks where the skill stops to ask you.

| Area | Skills |
|---|---|
| Start | [`claude-init`](#claude-init) · [`onboard`](#onboard) |
| Plan | [`interview`](#interview) · [`ambition`](#ambition) · [`maestro`](#maestro) |
| Document | [`deepinit`](#deepinit) · [`sot-create`](#sot-create) · [`sot-verify`](#sot-verify) |
| Review | [`cleanser`](#cleanser) · [`codex-side`](#codex-side) |
| Finish | [`commit`](#commit) · [`mole-linear`](#mole-linear) |
| Meta | [`manage-skills`](#manage-skills) |

---

# Start

<a name="claude-init"></a>

## `claude-init` — Installs or refreshes the author's Claude Code setup (plugins, settings, statusline) in one go

- **Invocation**: `/jstack:claude-init` — no arguments. Auto-run: Claude picks it for requests like "jin init", "환경 세팅" (environment setup), "새 머신 세팅" (new machine setup)
- **When**: Right after installing Claude Code on a new machine, or to bring team plugins and settings up to date

**How it works**
1. `preflight.py` checks the install and only the steps for missing items run. If nothing is missing, you pick rerun, change plugin selection only, conflict audit only, or quit (asks)
2. It lists the files it will overwrite and asks for consent and a usage-polling interval (1/3/5/10 min, 5 recommended). Decline and plugin install, repo sync and settings merge are skipped (asks)
3. You pick optional plugins. Missing required plugins (`context-mode`, `serena`, `i-have-adhd`) and missing picked ones are installed (asks)
4. Clones or pulls the `jstack` repo into `~/.claude/.jin-claude-repo/` and copies the statusline, `CLAUDE.md` and its include docs to `~/.claude/`. Also sets up a venv and a usage timer
5. Merges `~/.claude/settings.json`: team-required keys are overwritten, personal keys (`model`, `language`, …) are added only if absent
6. Re-checks the install, checks MCP connections, then runs a conflict audit. You pick which fixes to apply (asks)
7. Shows what changed, backup paths and how to roll back, then runs `onboard`

**Output**: Updates `~/.claude/CLAUDE.md`, its include docs, `statusline-command.sh` and `settings.json` (changed files backed up as `<name>_backup_<YYYYMMDD>.<ext>`); creates `~/.claude/.jin-claude-repo/`, `~/.claude/.venv/`, a launchd/systemd usage timer and `~/.claude/.jin-claude-plugins.json`; installs plugins
**Notes**: Team-required keys such as `statusLine` and `skipDangerousModePermissionPrompt` overwrite your values. Deselected plugins are not uninstalled. If the timer disappears, the session-start hook re-registers it with the interval chosen at init (`~/.claude/.jin-claude-usage-interval`, 5 minutes if absent).

<a name="onboard"></a>

## `onboard` — Walk through jstack workflows by situation

- **Invocation**: `/jstack:onboard [situation]` — one of `새 프로젝트` (new project), `기능` (feature), `버그` (bug), `큰 작업` (large task), `리뷰` (review), `이슈` (issue), `환경` (environment); omit for the full guide. Auto-run: at the end of `claude-init`, or for requests like "온보딩" (onboarding), "사용법" (how to use), "뭐부터 해야" (where to start)
- **When**: You are new to jstack, or unsure which skill fits what you are doing

**How it works**
1. With a situation argument, it shows only that situation's flow
2. Without one, it shows the basic flow (plan in plan mode → approve → execute → verify → `commit`; you push yourself) and the list of situations
3. You pick what you are about to do (asks)
4. It explains that situation in detail: which skills to call, in what order

**Output**: None
**Notes**: Calling a skill by keyword lets Claude choose it, but that is not guaranteed. Use `/jstack:<skill>` to be sure it runs.

---

# Plan

<a name="interview"></a>

## `interview` — Settle decisions by questioning you, then write a spec file

- **Invocation**: `/jstack:interview [instructions]` — the feature or topic to interview about. Auto-run: when Claude recognizes requests like "jin interview", "인터뷰", "스펙 작성", "요구사항 정리", "spec", or a request to settle decisions before building a vague feature
- **When**: Requirements are vague and you need to decide technical, UI/UX and trade-off questions before building.

**How it works**
1. Reads relevant code first so questions are grounded.
2. Skips the obvious and asks about implementation, UI/UX, concerns and trade-offs (asks).
3. Each question is a decision brief numbered `D1`, `D2`, …: plain explanation, recommendation with reason, pros and cons per option, one-line net trade-off.
4. The recommended option always comes first, labeled `(recommended)`. When options differ in coverage, each gets a `Completeness` score out of 10.
5. Keeps asking until every decision is settled.
6. Writes the spec to `docs/specs/<topic>-spec.md`, where `<topic>` is kebab-case from your instructions. If the file exists, asks before overwriting (asks).

**Output**: `docs/specs/<topic>-spec.md` with sections `Goal`, `Scope`, `Decisions`, `Accepted shortcuts`, `Open questions`, `Success criteria`.
**Notes**: Choosing an option with `Completeness` 7 or below records its ceiling and upgrade trigger under `## Accepted shortcuts`. `sot-create` calls this skill first when it starts.

<a name="ambition"></a>

## `ambition` — Make a plan higher, deeper, and wider, not just bigger

- **Invocation**: `/jstack:ambition [altitude|depth|range]` — apply one axis only. Omit it for all three. Auto-run: a hook loads it without asking when the prompt contains `ambition` or `앰비션`. In plan mode without that word, it asks once per conversation whether to plan in ambition mode. Claude also runs it when it recognizes requests like "altitude", "depth", "range", "깊게", "다른 분야"
- **When**: You want the plan to cover the outcome beyond the task, expert-level depth, or techniques from other fields.

**How it works**
1. Outside plan mode, asks to enter plan mode. If you decline, continues in the current mode. (asks)
2. Altitude: writes a 2–3 rung ladder of goals beyond the goal (e.g. fix one crash → zero crashes this release → app stays crash-free).
3. You pick the rung to plan for. The original task is an option. (asks)
4. Checks what it takes to hold that rung without a human: data access, mapping results to causes, an environment to reproduce and verify. Gaps become the plan's first step.
5. Depth: answers in one line each what top experts do unasked, which raw data to start from, which tools to use, and what external judge proves the result. Adds a step that tries to disprove one key assumption from raw data.
6. Range: restates the deliverable as a verb (what it does), then forms 2–4 fields plus 1 red team. Lists each field's real technique or tool in one line.
7. You pick which techniques to adopt (multi-select). (asks)
8. Adds a `## Ambition` section to the plan: one item per applied axis, or `N/A — reason`.

**Output**: A `## Ambition` section in the plan.
**Notes**: The hook matches `ambition`/`앰비션` as a case-insensitive substring. Merely mentioning the word loads the skill. Results are checked only by external judges (tests, benchmarks, metrics); without one, the goal is not raised.

<a name="maestro"></a>

## `maestro` — Turn this session into an orchestrator that only directs

- **Invocation**: `/jstack:maestro` — no arguments. Auto-run: none (`disable-model-invocation`)
- **When**: You want work split across sub-sessions while this session only plans, dispatches, and collects reports.

**How it works**
1. This session only plans, keeps the ledger, consolidates reports, and asks you questions. Code edits, builds, tests, and research go to sub-sessions.
2. In plan mode, it writes only the dispatch plan (session names, areas, mode, briefs). After approval it creates the ledger and starts delegating. (asks)
3. Creates the ledger `.maestro/ledger.md` in the current directory. In a git repo, adds `.maestro/` to `info/exclude`.
4. If an active or idle session owns the same area, it gets the work. New work goes to a new sub-session `m-<area>-<n>`: inside herdr, ultracode or long jobs get an independent Claude session in a herdr pane (Workflow available); everything else gets a named subagent. Broad one-off jobs with no follow-up run directly as a Workflow.
5. When two or more sessions will edit files in the same repo at once, each gets its own worktree. Merging is delegated too.
6. Picks a mode per hand-off: `ultracode` for audits, migrations, reviews, and high-risk changes; `normal` for small fixes.
7. When a sub-session asks a question or needs a decision or approval, the orchestrator does not answer it. It asks you as-is and passes your answer back. (asks)
8. Takes each sub-session report (`STATUS: DONE|BLOCKED`, changed files, verification evidence, questions, follow-ups), updates the ledger, and summarizes for you.
9. Archives sessions with no follow-up and no context worth keeping. Say "maestro 종료" to archive all and get a final summary.

**Output**: `.maestro/ledger.md`, pane-session reports `.maestro/reports/<name>.md`, a `.maestro/` line in git `info/exclude`, sub-sessions, and worktrees when needed.
**Notes**: At most 5 active sessions, of which at most 2 run `ultracode` at once. Archiving means marking `archived` in the ledger and stopping the session if running (panes are closed). Archived sessions get no new work; new work in that area goes to a new session.

---

# Document

<a name="deepinit"></a>

## `deepinit` — Analyze the project and write an `AGENTS.md` for agents

- **Invocation**: `/jstack:deepinit [project path]` — defaults to the current directory. Auto-run: when Claude recognizes requests like "jin deepinit", "프로젝트 분석", "AGENTS.md 생성", "analyze project", "generate AGENTS.md", or a request to create a first agent guide for a new project
- **When**: A new project has no `AGENTS.md` for agents to read.

**How it works**
1. `project_analyzer.py` detects languages (by file-extension frequency), frameworks, and structure (`monorepo`, `standard`, `flat`). It skips `.git`, `.venv`, `node_modules`, `dist`, `build`, and similar.
2. The same script prints an `AGENTS.md` draft: project overview, a directory tree of the root plus one level down (up to 5 entries per folder), and a table of available skills.
3. The skills table is built at run time from the plugin's `skills/*/SKILL.md` `name` and `description`.
4. Reads `README.md`, config files and entry points to add architecture, dev patterns and coding conventions. Nothing without evidence.
5. If `AGENTS.md` exists, shows the diff and lets you pick overwrite, merge, or cancel (asks).
6. If not, shows what it will create and asks whether to create it (asks). Writes only approved content.

**Output**: `AGENTS.md` at the project root, only if approved.
**Notes**: Frameworks come only from config files at the project root (`package.json`, `pyproject.toml`, `requirements.txt`, etc.), matched by whether the package name appears in the file. Draft headings and labels are in Korean. Needs `python3` (stdlib only).

<a name="sot-create"></a>

## `sot-create` — Build a SoT docset in `sot/` that agents can cite and verify

- **Invocation**: `/jstack:sot-create [project path]` — defaults to the current directory. Auto-run: when Claude recognizes requests like "jin sot", "SoT 생성", "source of truth", "document this project", or a request to document architecture, DB schema, workflows or design rules
- **When**: Project knowledge is too big for `AGENTS.md` or `CLAUDE.md`, or you are setting up project docs for the first time.

**How it works**
1. Runs the `interview` skill first to settle a spec (asks).
2. Probes the repo read-only: the `deepinit` analyzer (languages, frameworks, structure), the latest commit, and whether a root `DESIGN.md` exists.
3. Creates the seven category directories under `sot/` (`overview`, `tech-stack`, `database-schema`, `architecture`, `workflow`, `design`, `rules`) plus `rules/sot-maintenance.md`. No confirmation for this.
4. Shows the exact lines to append, `sot/` to `.gitignore` and a `## SoT` block to `CLAUDE.md`, and asks for each (asks). Appends only what you approve.
5. Writes one file per sub-topic. Each fact gets an ID heading like `## ARC-001 — <claim>` and an `Evidence: path:line`. Unknowns become `TODO(sot):`.
6. `sot_index.py` generates `Index.md` from each doc's frontmatter.
7. Validates with `sot_validate.py` and fixes every error. On `DRIFT` it reads the diff and corrects the facts, or marks the doc `status: stale`. Warnings and info go in the summary.

**Output**: The `sot/` docset (`Index.md`, per-category docs, `rules/sot-maintenance.md`) and the interview spec `docs/specs/<topic>-spec.md`. If approved, a few lines added to `.gitignore` and `CLAUDE.md`.
**Notes**: If `sot/` already exists, existing docs are never overwritten; it adds what is missing and revalidates. It never creates or edits `DESIGN.md`, only cites it. With no interactive channel (subagent, CI, `-p`), every doc stays `draft` and nothing outside `sot/` is touched.

<a name="sot-verify"></a>

## `sot-verify` — Check that `sot/` still matches the code, and fix errors

- **Invocation**: `/jstack:sot-verify` — no arguments. Auto-run: none (`disable-model-invocation`)
- **When**: After editing `sot/`, or after code under a doc's `verified_paths` changed.

**How it works**
1. If `sot/` is missing, it stops with one line: "SoT 없음 — `/jstack:sot-create`".
2. Runs `sot-create`'s `sot_index.py --check` to see if `Index.md` is current. If stale, regenerates it.
3. Runs `sot_validate.py`: required frontmatter keys, ID prefix and uniqueness, `Index.md` links, and drift.
4. Drift comes from `git diff <verified_commit>..HEAD -- <verified_paths>`. It is an error for `status: verified` docs, a warning otherwise.
5. Structural errors: fixes the doc's frontmatter or ID, then regenerates `Index.md`.
6. `DRIFT`: reads the diff, corrects the facts, and bumps `updated` and `verified_commit`. If it cannot tell, sets `status: stale` and adds a `TODO(sot):` naming what to check.
7. Re-runs until errors are zero, then reports doc and fact counts, files with suspected drift, errors fixed and left, and warning counts.

**Output**: Edits to `sot/` docs; regenerated `sot/Index.md`.
**Notes**: It edits `sot/` docs without asking (edits only, never overwrites with a template). The path is fixed to `sot`, so run it from the project root. Drift sees committed changes only; uncommitted edits are not caught.

---

# Review

<a name="cleanser"></a>

## `cleanser` — Find AI-generated code slop and report it, nothing more

- **Invocation**: `/jstack:cleanser [path]` — file or directory to scan. Omit it to scan git changes. Auto-run: when Claude recognizes requests like "deslop", "slop", "슬롭 검사", "AI 코드 정리", "디버그 코드 남았는지"
- **When**: Before a commit, to check the diff for AI leftovers such as debug code or commented-out code.

**How it works**
1. With a path, scans everything under it.
2. Without a path, scans uncommitted changes plus untracked files. If both are empty, scans the last commit (vs `HEAD~1`).
3. Runs `slop_patterns.py` for static checks: debug output (`print(`, `console.log(`, `debugger`, `pdb`, `breakpoint(`), code commented out with `#`, and TODO/FIXME-style comments. Python patterns apply only to `.py` files, JS patterns (`console.log`, `debugger`) only to JS/TS files.
4. If `ruff` is installed, also finds unused Python imports (F401). If not, skips that and says so in the report.
5. Claude reads the files for what regex misses: obvious comments, excessive or empty exception handling, boilerplate docstrings, single-use wrappers, self-evident type annotations.
6. In diff mode, keeps only changed lines. Untracked files count in full.
7. Drops false positives (an intended `print`, say) and merges everything into one report: summary by severity (critical, warning, info), issue table, per-category details.

**Output**: None. Prints a Markdown report; never edits code.
**Notes**: Directories are scanned recursively for `.py .js .jsx .ts .tsx .mjs .cjs` only (`node_modules`, `.venv`, `dist`, `build`, etc. skipped). Static checks are line regexes, so false positives happen.

<a name="codex-side"></a>

## `codex-side` — Get an independent second opinion from the OpenAI Codex CLI

- **Invocation**: `/jstack:codex-side [review [focus] | challenge [focus] | <question>]` — `review` is a diff code review, `challenge` is an adversarial attempt to break the change, any other text is a question or plan review. `focus` narrows the angle (e.g. `challenge security`). Omit all to pick from a menu. Auto-run: when Claude recognizes requests like "codex review", "2차 의견", "second opinion", "교차 검토"
- **When**: You want another model's independent review before a merge, or another AI to check a design or plan.

**How it works**
1. Checks `codex` install and auth, the base branch, commits ahead, and uncommitted changes. Stops if install or auth is missing.
2. With no argument, picks the mode. With changes, you choose review, adversarial check, or question; without changes, it asks for your question. (asks)
3. Validates any base, sha, model, or effort you pass. Asks again if a value fails. (asks)
4. States the mode and scope, that the prompt and repo content go to OpenAI, the paid call, and up to ~9 minutes of runtime, then asks to send. Cancel sends nothing. (asks)
5. Runs Codex in a read-only sandbox. Kills it after 540 seconds.
6. Shows Codex's answer verbatim. `review` adds a gate: `[P0]`/`[P1]` present is FAIL, only `P2`/`P3` is PASS, no tags is UNVERIFIED.
7. Claude notes where it agrees or disagrees and gives one `Recommendation:` line. You decide.
8. On a consult follow-up, asks whether to resume the earlier Codex conversation or start fresh. (asks)

**Output**: No repo files change. A temp dir holds `last.md` and `transcript.log`, deleted at the end. The prompt and repo content go to OpenAI.
**Notes**: Needs the `codex` CLI (`npm install -g @openai/codex`) and `codex login` (or `CODEX_API_KEY`/`OPENAI_API_KEY`). A failed run, timeout, or empty output counts as review FAIL. `xhigh` effort tends to time out; retry with `high`.

---

# Finish

<a name="commit"></a>

## `commit` — Analyze changes and commit right away with a gitmoji + Korean message

- **Invocation**: `/jstack:commit [message]` — optional text to fold into the message. Auto-run: Claude picks it for "커밋", "commit", "jin commit" requests, or when committing after finished work
- **When**: You finished a piece of work and want it committed

**How it works**
1. Analyzes changes with `git status` and `git diff` (`git diff --staged` if files are staged)
2. Selects only the files you named or the files belonging to this change. Unrelated changes and secrets (`.env` etc.) are left out and reported. Asks only when the target files are ambiguous (asks)
3. Picks a gitmoji for the kind of change and writes `<emoji> [<issue ID>] <Korean title> [— scope] [+ extras]`. The issue ID (e.g. `[MOLE-123]`) is added only when the branch name or conversation gives it. Uses the argument if given
4. Runs `git add <files>` → `git commit` without confirmation. Invoking the skill is the approval
5. Reports the commit hash, message, and included/excluded files

**Output**: One local git commit
**Notes**: Never pushes. Never uses `git add -A` or `git add .`. Adds no `Co-Authored-By` line.

<a name="mole-linear"></a>

## `mole-linear` — Work Linear issues and comments by STEALTHMOLE team rules

- **Invocation**: `/jstack:mole-linear` — no arguments. Auto-run: Claude picks it for Linear requests such as "linear", "이슈 등록" (create issue), "이슈 댓글" (issue comment), "MOLE-", "linear 설치" (install linear)
- **When**: Before searching, creating, or updating Linear issues, statuses, or comments

**How it works**
1. If Linear tools are missing or you ask for setup, follows `setup.md`: cleans old Linear MCP servers and old rule files. With the claude.ai connector, every Linear MCP server is removed; user-scope `linear-server` is installed only when there is neither a connector nor a `linear-server`. Asks before each removal or install (asks)
2. Takes the project from the `Linear project: <name>` line in the project `CLAUDE.md`. If missing, asks and writes that line (asks)
3. Searches existing issues first, archived included, and creates only if none exists. Defaults: priority Medium, assignee me, an existing label. Large tasks get a parent plus one sub-issue per deliverable
4. Before work, reads the comments and every `+++ Agent notes` block in them
5. Moves status and comments with fixed templates: plan → `Plan` + Plan comment; work → `In Progress`; blocked → BLOCKED comment, then stops; done → Done comment + `Done` (`Feedback` if you must review)
6. Puts the issue ID in every commit and PR (commit title `✨ [MOLE-123] …`). Branch is `<user>/<issue-id>` in lowercase (e.g. `jin/mole-123`)

**Output**: Linear issues, comments, and statuses; the `Linear project:` line in the project `CLAUDE.md`; user-scope MCP `linear-server` when installed; on cleanup, deletes `~/.claude/linear.md`, `~/.claude/mcp-linear.md`, `<project>/linear.md` and removes `@linear.md` / `@mcp-linear.md` lines from `CLAUDE.md` / `AGENTS.md`
**Notes**: Never creates labels or statuses, never deletes issues. Descriptions must use the As-is / To-be template, and the description is never edited at the Plan stage. If `linear-server` was installed, you must authenticate via `/mcp` (OAuth) yourself; a server added mid-session shows up only in a new session.

---

# Meta

<a name="manage-skills"></a>

## `manage-skills` — Check, create, and update project `verify-*` skills against changed files

- **Invocation**: `/jstack:manage-skills [verify skill name or area]` — if given, only related changed files are considered. Auto-run: none (`disable-model-invocation`)
- **When**: After implementing a feature, before a PR, or when a verify skill missed an issue

**How it works**
1. Collects changed files: uncommitted changes, commits since branching from the default branch, and new files
2. Finds the project's `.claude/skills/verify-*/SKILL.md` and maps changed files to each skill's Related Files and Workflow paths. Files no skill covers are `UNCOVERED`
3. For each matched skill, looks for gaps (missing files, broken references, stale commands, new patterns, changed values). Detection commands are actually run
4. Proposes skills to update, skills to create, and exempt files; you choose what to do (asks)
5. Edits only approved skills. Adds or modifies only; checks that still work are never removed
6. For a new skill, confirms the name and builds it from the template. Adds the `verify-` prefix if missing (asks)
7. Asks whether to list verify skills in a `## Skills` table in the project `CLAUDE.md` (asks)
8. Checks format, paths, and detection commands, then shows a report and the `/verify-<name>` commands to run

**Output**: Created or updated `.claude/skills/verify-<name>/SKILL.md` in the project; the `## Skills` table in `CLAUDE.md` if approved
**Notes**: Does not run verify skills; it only suggests them. Writes no file without approval. A personal `~/.claude/skills/manage-skills` copy is moved to `~/.claude/backups/` by the session-start hook.
