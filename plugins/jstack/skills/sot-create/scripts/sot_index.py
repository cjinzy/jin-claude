#!/usr/bin/env python3
"""Generate `sot/Index.md` from the docset's own frontmatter.

`Index.md` is the only entry point, so a doc missing from it does not exist for any reader.
With one file per sub-topic a docset has many small files, and assembling that table by hand on
every change is exactly how entries go missing. So it is rendered from the source of truth —
each doc's frontmatter — rather than maintained separately.

    python3 sot_index.py --root sot            # write Index.md
    python3 sot_index.py --root sot --check     # exit 1 if Index.md is out of date

Docs with unreadable frontmatter are reported on stderr and left out; `sot_validate.py` is what
turns that into an error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sot_validate import (
    CATEGORY_PREFIXES,
    DESIGN_FILENAME,
    INDEX_FILENAME,
    REQUIRED_KEYS,
    parse_frontmatter,
)

# Read rules belong at the point a reader lands. The update protocol does not: it lives in
# `rules/sot-maintenance.md` so this entry point stays short.
INDEX_HEADER = """# SoT Index

> Start here, then load only the docs your task touches. Cite facts by id (`ARC-002`).
> `draft` / `stale` is unverified input, not fact; doc vs. code conflict → report both.
> Keeping this docset true: [RUL-sot-maintenance](rules/sot-maintenance.md).
"""
DESIGN_POINTER = f"> Design tokens: [{DESIGN_FILENAME}](../{DESIGN_FILENAME}) (cited by design/).\n"
TABLE_HEADER = """
| Doc | Category | Status | Updated | Summary |
|---|---|---|---|---|
"""

CATEGORY_ORDER = list(CATEGORY_PREFIXES)


def collect(root: Path) -> tuple[list[dict[str, str]], list[str]]:
    """Frontmatter of every doc, ordered by category then id. Returns (rows, skipped)."""
    rows: list[dict[str, str]] = []
    skipped: list[str] = []
    for path in sorted(root.rglob("*.md")):
        if path.name == INDEX_FILENAME:
            continue
        rel = path.relative_to(root).as_posix()
        meta, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        if not all(meta.get(key) for key in REQUIRED_KEYS):
            skipped.append(rel)
            continue
        rows.append({**meta, "path": rel})

    def sort_key(row: dict[str, str]) -> tuple[int, str]:
        category = row.get("category", "")
        known = category in CATEGORY_ORDER
        order = CATEGORY_ORDER.index(category) if known else len(CATEGORY_ORDER)
        return order, row.get("id", "")

    return sorted(rows, key=sort_key), skipped


def render(rows: list[dict[str, str]], root: Path | None = None) -> str:
    """Index.md text. Links root DESIGN.md only when it exists next to `root`."""
    lines = [
        f"| [{row['id']}]({row['path']}) | {row['category']} | {row['status']} "
        f"| {row['updated']} | {row['title']} |"
        for row in rows
    ]
    has_design = root is not None and (root.parent / DESIGN_FILENAME).is_file()
    header = INDEX_HEADER + (DESIGN_POINTER if has_design else "") + TABLE_HEADER
    return header + "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate sot/Index.md from frontmatter")
    parser.add_argument("--root", default="sot", help="SoT root directory (default: sot)")
    parser.add_argument(
        "--check", action="store_true", help="exit 1 if Index.md differs instead of writing"
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"{root} is not a directory", file=sys.stderr)
        return 1

    rows, skipped = collect(root)
    for rel in skipped:
        print(f"skipped (frontmatter incomplete): {rel}", file=sys.stderr)

    content = render(rows, root)
    index = root / INDEX_FILENAME

    if args.check:
        current = index.read_text(encoding="utf-8") if index.is_file() else ""
        if current == content:
            print(f"{index} is up to date ({len(rows)} docs)")
            return 0
        print(f"{index} is out of date; run without --check", file=sys.stderr)
        return 1

    index.write_text(content, encoding="utf-8")
    print(f"wrote {index} ({len(rows)} docs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
