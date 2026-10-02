---
name: jin-sot-create
description: SoT(Source of Truth) 문서셋을 코딩 에이전트가 인용·검증할 수 있는 형태로 생성한다 — 세부항목별 파일, 머신리더블 frontmatter, fact ID, Index.md 생성기, drift 검증기. "jin sot", "sot create", "SoT 생성" 외에도 프로젝트 문서 체계를 처음 세우거나, 아키텍처·DB 스키마·워크플로를 문서로 정리해 달라는 요청, AGENTS.md/CLAUDE.md 가 담기엔 큰 프로젝트 지식을 남겨야 하는 상황이면 먼저 이 스킬을 사용한다.
triggers:
  - jin sot
  - sot create
  - SoT 생성
  - source of truth
argument-hint: "[project path (default: cwd)]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# jin-sot-create: SSOT docset for coding agents

Build `sot/` as a Single Source of Truth an agent can **query, cite, and keep honest** — not a
folder of prose. Every rule below exists to make one of those three possible.

## SSOT invariants

Non-negotiable. A docset that breaks one of these is worse than no docset, because an agent
trusts it anyway.

1. **One owner per fact.** A fact lives in exactly one file. Everywhere else links to it.
   Never copy — two copies drift, and then neither is the truth.
2. **`Index.md` is the only entry point.** A doc not listed there does not exist.
3. **Every fact is addressable.** `## ARC-002 — <claim>`, so plans, commits, code comments,
   and issues cite `ARC-002` instead of paraphrasing.
4. **Intent vs. behavior.** SoT is authoritative for *intent and contracts*. The code is
   authoritative for *current behavior*. On conflict: stop, report both sides, ask. Never
   silently align one to the other.
5. **Unknown beats invented.** Write `TODO(sot): <question>` instead of a plausible guess.
   An agent-written guess that reads like a fact is this format's main failure mode.
6. **Freshness is computed, not claimed.** Each doc records the code paths and commit it was
   last checked against; `sot_validate.py` derives staleness from git.

## Categories

Fixed set. Do not invent a top-level category — add a file inside an existing one.

| Directory | ID prefix | Authoritative for |
|---|---|---|
| `overview/` | `OVW` | problem, scope, non-goals, stakeholders, success criteria |
| `tech-stack/` | `STK` | languages, frameworks, versions, package managers, tooling |
| `database-schema/` | `DBS` | tables, columns, types, constraints, indexes, migrations |
| `architecture/` | `ARC` | components, boundaries, data flow, API contracts |
| `workflow/` | `WFL` | business logic flow, user journeys, state transitions |
| `rules/` | `RUL` | coding standards, naming, commit/review rules, accepted shortcuts |

`RUL-9xx` is reserved for docset governance (`rules/sot-maintenance.md`); project rules use
`RUL-0xx`. `overview/` and `rules/` are intent-only — they need no `verified_paths`.

## Layout

One doc = one sub-topic. A category is a directory of small docs, never a single growing file.

```
sot/
├── Index.md                     # generated — the only entry point
├── overview/
│   ├── problem.md               # OVW-*
│   └── scope.md
├── tech-stack/
│   ├── backend.md               # STK-*
│   └── frontend.md
├── database-schema/
│   ├── users.md                 # DBS-* — one file per table
│   └── orders.md
├── architecture/
│   ├── components.md            # ARC-*
│   ├── api-contracts.md
│   └── data-flow.md
├── workflow/
│   ├── signup.md                # WFL-* — one file per journey
│   └── checkout.md
└── rules/
    ├── sot-maintenance.md       # RUL-9xx — copied in at Step 2
    └── naming.md                # RUL-0xx
```

A file never holds two categories, and never two sub-topics.

## Document contract

Frontmatter is flat and lists are comma-separated — this repo has no PyYAML, and the
validator parses stdlib-only.

```markdown
---
id: ARC-components
category: architecture
title: Service components and boundaries
status: verified
updated: 2026-10-02
verified_commit: a65df10
verified_paths: src/api/, src/worker/
---

# Service components and boundaries

> Authoritative for: component list, ownership boundaries, sync/async edges.
> Not authoritative for: deployment topology — see [STK-stack](../tech-stack/stack.md).

## ARC-001 — The API gateway is the only public entry point

All external traffic terminates at the gateway; workers are reachable only over the internal
queue. Adding a second public listener breaks this contract.

Evidence: `src/api/gateway.py:34`

## ARC-002 — Workers never write to the primary database directly

TODO(sot): confirm whether the reporting job is an exception.
```

| Field | Rule |
|---|---|
| `id` | `<PREFIX>-<slug>`, globally unique |
| `status` | `draft` (incomplete) · `verified` (checked against code) · `stale` (known out of date) |
| `updated` | ISO date of the last human- or agent-verified edit |
| `verified_commit` | commit SHA the doc was last checked against — required for `verified` |
| `verified_paths` | repo-relative code paths this doc describes — the drift input |

Body rules:

- One fact per `##` heading. The heading **is** the claim, written as a full sentence.
- An implemented fact cites at least one `path:line` as `Evidence:`.
- One sub-topic per doc. Length is not a split criterion: a long doc about one sub-topic
  stays one doc, and a short doc covering two sub-topics gets split.
- Reference other facts by link, never by restating them.

## Workflow

### Step 0 — Interview first (required)

Call `jin-interview` before writing anything. No SoT without a spec; an interview-free docset
is invention at scale. Carry the spec's `## Accepted shortcuts` into `rules/` as `RUL-*` facts
so the ceiling and its upgrade trigger survive in the SoT.

**No interactive channel** (subagent, CI, `-p` run): do not stall, and do not substitute your
own assumptions for the interview. Build an evidence-only docset instead — every fact carries
`Evidence:` from Step 1, every doc stays `status: draft`, and each question the interview would
have asked becomes a `TODO(sot):` in the doc that would own the answer. Say in the summary that
the docset is evidence-only and needs an interview pass. A `draft` doc full of honest gaps is
useful; a `verified`-looking doc full of guesses is the failure this skill exists to prevent.

### Step 1 — Probe the repo (read-only)

Collect ground truth before writing prose:

```bash
python3 "../jin-deepinit/scripts/project_analyzer.py" .   # languages, frameworks, structure
git log --oneline -1                                      # baseline for verified_commit
```

Repo evidence outranks the interview when the two disagree. Report the conflict (invariant 4)
rather than picking a side.

### Step 2 — Scaffold or reconcile

```bash
mkdir -p sot/{overview,tech-stack,database-schema,architecture,workflow,rules}
grep -qxF 'sot/' .gitignore || echo 'sot/' >> .gitignore   # SoT is local-only

# The maintenance trigger has to live in the auto-loaded CLAUDE.md. An agent changing
# unrelated code loads neither this skill nor sot/Index.md, so nothing else would make it look.
grep -q 'sot_validate' CLAUDE.md 2>/dev/null || cat >> CLAUDE.md <<'TRIGGER'

## SoT
`sot/` is the Source of Truth; `sot/Index.md` lists every doc. In the verify step, before
jin-commit, run the jin-sot-create skill's `scripts/sot_validate.py --root sot` and fix every
error. Update protocol: `sot/rules/sot-maintenance.md`.
TRIGGER

# The update protocol ships as a RUL-9xx fact doc, not as prose in Index.md.
[ -f sot/rules/sot-maintenance.md ] || cp "SKILL_DIR/templates/sot-maintenance.md" sot/rules/
```

`sot/` already exists → add only what is missing and regenerate `Index.md`, then run Step 5.

"Never overwrite" means never replace an existing doc with a template or rewrite it from
scratch — the facts in it were someone's work. It does **not** mean the doc is frozen. Editing
an existing doc to correct a fact or refresh its baseline is the normal update path, and when
Step 5 reports `DRIFT` that edit is the job, not a question to defer:

- read the diff (`git diff <verified_commit>..HEAD -- <verified_paths>`), correct whatever it
  invalidated, bump `updated` and `verified_commit`
- the diff leaves the answer genuinely undetermined → set `status: stale` and add a
  `TODO(sot):` naming what to check

Both outcomes are actions. Leaving a `DRIFT` error standing is the one thing that is not a
valid outcome: the next reader cannot tell that doc from a fresh one.

### Step 3 — Split into sub-topic files, then write facts

List the sub-topics from the interview and Step 1 evidence **before** writing, then create one
file per sub-topic. One file per category that grows forever is the format this skill replaces.

| Category | One file per | Examples |
|---|---|---|
| `overview/` | concern | `problem.md`, `scope.md` |
| `tech-stack/` | side | `backend.md`, `frontend.md` |
| `database-schema/` | table, or tightly coupled table group | `users.md`, `orders.md` |
| `architecture/` | component or contract | `components.md`, `api-contracts.md` |
| `workflow/` | journey or flow | `signup.md`, `checkout.md` |
| `rules/` | rule area | `naming.md`, `commits.md` |

The sub-topic is the only split criterion. Splitting a long single-topic doc would give one
sub-topic two owners and break invariant 1, so never split on length. Instead, split the moment
a doc starts answering a second question — and if a sub-topic is hard to name, it is usually
two.

The validator cannot judge topic scope; its `MANY_FACTS` warning is only a hint that a file may
have outgrown its topic. Confirm or dismiss it by reading, not by counting.

Number facts sequentially within the prefix and never renumber an existing one; external
citations break. The next free number:

```bash
grep -rh '^## ARC-' sot/architecture/ | sort | tail -1
```

Anything unresolved becomes `TODO(sot):`, not a guess.

### Step 4 — Generate `Index.md`

```bash
python3 "SKILL_DIR/scripts/sot_index.py" --root sot          # write
python3 "SKILL_DIR/scripts/sot_index.py" --root sot --check   # exit 1 if out of date
```

Rendered from each doc's frontmatter, ordered by the category table, with the read contract as a
three-line header. Never hand-edit it: with one file per sub-topic there are many docs, and a
hand-assembled table is how entries go missing. Docs with incomplete frontmatter are listed on
stderr and left out — fix them rather than adding the row yourself.

### Step 5 — Validate

```bash
python3 "SKILL_DIR/scripts/sot_validate.py" --root sot
```

JSON on stdout, exit 1 on errors. Fix every `error` before reporting the SoT as done;
`warning` and `info` go in the summary.

| Code | Level | Meaning |
|---|---|---|
| `MISSING_FRONTMATTER` / `MISSING_KEY` | error | document contract broken |
| `BAD_CATEGORY` / `BAD_ID_PREFIX` / `BAD_STATUS` | error | not addressable |
| `DUPLICATE_ID` | error | two owners for one id |
| `NOT_INDEXED` / `DEAD_LINK` | error | `Index.md` is not the entry point |
| `DRIFT` | error if `verified`, else warning | code changed since `verified_commit` |
| `UNVERIFIABLE_COMMIT` | warning | freshness claimed but not checkable |
| `MANY_FACTS` | warning | hint: may cover more than one sub-topic — verify by reading |
| `NO_FACTS` | warning | nothing stated |
| `TODO_OPEN` | info | open questions remain |

## Guardrails

- One doc = one sub-topic. Never one file per category, never one file for the whole SoT.
- Do not invent categories; add sub-topic files inside the six.
- Do not overwrite existing `sot/` files.
- Do not state a fact you cannot evidence — `TODO(sot):` instead.
- `sot/` stays `.gitignore`d (local-only, per project `CLAUDE.md`).

## Files

- `templates/sot-maintenance.md` — the `RUL-9xx` update protocol, copied in at Step 2
- `scripts/sot_index.py` — renders `Index.md` from frontmatter (`--check` to verify only)
- `scripts/sot_validate.py` — docset validator (structure, addressability, index, drift)
- `scripts/test_sot_validate.py` — validator tests
