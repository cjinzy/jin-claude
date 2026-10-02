---
id: RUL-sot-maintenance
category: rules
title: How this docset is kept true
status: verified
updated: 2026-10-02
---

# How this docset is kept true

> Authoritative for: the update protocol of `sot/` itself.
> Not authoritative for: what the docs say — each category owns its own facts.

Reserved id block: `RUL-9xx` is docset governance. Project rules use `RUL-0xx`.

## RUL-901 — SoT revalidation runs in the verify step, before jin-commit

Order is `deploy → verify → jin-commit`. In verify, run the jin-sot-create skill's
`scripts/sot_validate.py --root sot`. Every `error` is fixed before the commit; `warning` and
`info` go in the change summary. A green run is the only evidence this docset is still true.

## RUL-902 — A `DRIFT` doc is corrected or explicitly marked stale — never left silently wrong

`DRIFT` means the code under `verified_paths` moved after `verified_commit`. Two legal
outcomes:

- re-read the changed code, correct the facts, bump `updated` and `verified_commit`, keep
  `status: verified`
- cannot verify it now → `status: stale` plus a `TODO(sot)` marker naming what to check

Leaving `status: verified` on a drifted doc is the one failure that makes this docset harmful:
a reader cannot tell it from a fresh one.

## RUL-903 — A new fact goes to the category that owns it, never to a second copy

The category table in the jin-sot-create skill decides the file. If a fact seems to belong in
two places, one of them links to the other. Two copies drift, and then neither is the truth.

## RUL-904 — `Index.md` is regenerated from frontmatter, never hand-edited

Add or remove a doc → `scripts/sot_index.py --root sot` (jin-sot-create skill). A doc missing
from the index does not exist as far as any reader is concerned, and `--check` in the verify step
catches the omission before anyone relies on it.
