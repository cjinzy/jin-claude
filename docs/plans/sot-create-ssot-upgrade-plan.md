# Plan — jin-sot-create: SSOT upgrade for coding agents

## Problem

The current skill scaffolds six directories and an index. That is a folder layout, not a
Source of Truth. An agent reading it cannot answer three questions it must answer before
acting:

1. *Where does this fact belong?* — no ownership declaration, so facts get duplicated into
   two docs and then diverge.
2. *How do I cite this fact?* — no stable identifier, so plans and commits paraphrase docs
   instead of referencing them.
3. *Is this still true?* — no link to code, no commit baseline, so a stale doc is
   indistinguishable from a fresh one. An agent trusts both equally. This is the failure
   that makes a bad docset worse than no docset.

## Scope

### 1. Rewrite `skills/jin-sot-create/SKILL.md` (English)

- **SSOT invariants** — six rules: one owner per fact, Index.md as sole entry point,
  addressable facts, intent-vs-behavior precedence, `TODO(sot):` over invention, computed
  freshness.
- **Category table** — fixed set of six, each with an ID prefix (`OVW`/`STK`/`DBS`/`ARC`/
  `WFL`/`RUL`) and an explicit "authoritative for" column.
- **Document contract** — flat frontmatter (`id`, `category`, `title`, `status`, `updated`,
  `verified_commit`, `verified_paths`) plus `## <PREFIX>-NNN — <claim>` fact headings with
  `Evidence: path:line`.
- **Workflow** — interview → repo probe → scaffold/reconcile → write facts → generate index
  → validate.
- **Maintenance protocol** — slot SoT refresh into the project's
  `deploy → verify → jin-commit` order, before the commit.
- **Agent usage contract** — read Index.md first, load only touched docs, cite fact IDs,
  report conflicts instead of guessing.

### 2. Add `skills/jin-sot-create/scripts/sot_validate.py`

Stdlib only (no PyYAML in this repo — hence flat, comma-separated frontmatter values).
JSON on stdout, exit 1 on errors. Checks:

| Code | Level | Check |
|---|---|---|
| `MISSING_FRONTMATTER` / `MISSING_KEY` | error | document contract |
| `BAD_CATEGORY` / `BAD_ID_PREFIX` / `DUPLICATE_ID` / `BAD_STATUS` | error | addressability |
| `NOT_INDEXED` / `DEAD_LINK` | error | Index.md is the entry point |
| `DRIFT` | error when `status: verified`, warning otherwise | `git diff verified_commit..HEAD -- verified_paths` |
| `UNVERIFIABLE_COMMIT` / `OVER_BUDGET` / `NO_FACTS` | warning | freshness claim, context cost |
| `TODO_OPEN` | info | open questions |

### 3. Test — `scripts/test_sot_validate.py`

Matches the repo convention (`skills/*/scripts/test_*.py` are committed): happy path,
`NOT_INDEXED`, `BAD_ID_PREFIX`, `OVER_BUDGET`, and one real `git init` fixture for `DRIFT`.

### 4. Reference updates

`README.md` and `plugins/jin-claude/README.md` skill-table rows, plus a patch version bump.

## Out of scope

- Generating SoT content itself — that stays a follow-up request per category.
- Committing `sot/`. Per `.claude/CLAUDE.md` it is local-only and `.gitignore`d; the
  scaffold step enforces that instead.

## Results (2026-10-02)

Six non-interactive subagent runs, three prompts × (rewritten skill, `git HEAD` original),
graded from the produced files by `sot_validate.py` plus per-eval assertions.

| | greenfield | reconcile | db-schema | total |
|---|---|---|---|---|
| rewritten | 7/7 | 8/8 | 7/7 | **22/22** |
| original | 3/7 | 4/8 | 3/7 | 10/22 |

The original failed identically in all three runs — no frontmatter (6 × `MISSING_FRONTMATTER`),
zero addressable facts, zero `Evidence:` lines, one file per category, and no awareness that a
doc had drifted. Identical failure across different prompts is a skill gap, not model variance.

Two defects the runs exposed, both since fixed:

1. **`DRIFT` left unresolved.** Step 2's "never overwrite" was read as "existing docs are
   frozen", which blocked the `RUL-902` fix path — the run reported "re-verifying it is a human
   call" and left the error standing. Step 2 now scopes the protection to scaffolding and makes
   both drift outcomes (re-baseline, or `stale` + `TODO(sot):`) explicit actions. A rerun scored
   8/8 with the hand-written sentinel fact byte-identical.
2. **No interactive channel handling.** Step 0 required `jin-interview`, which does not exist in
   a subagent or CI run. Step 0 now has an evidence-only fallback: `status: draft` everywhere,
   interview questions as `TODO(sot):`.

Also added because the runs showed the work was deterministic and repeated: `scripts/sot_index.py`
(`RUL-904` demanded a regenerated index but nothing regenerated it).

Known limits of this evaluation: the interactive interview path is untested (subagents have no
`AskUserQuestion`), the assertions do not measure coverage completeness, and each configuration
ran once.
