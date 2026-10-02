"""Tests for sot_index.py — Index.md must be derivable, not hand-maintained."""

from __future__ import annotations

from pathlib import Path

from sot_index import collect, render

ARC = """---
id: ARC-components
category: architecture
title: Service components
status: verified
updated: 2026-10-02
---

## ARC-001 — The gateway is the only public entry point
"""

OVW = """---
id: OVW-problem
category: overview
title: Problem and scope
status: draft
updated: 2026-10-02
---

## OVW-001 — The team has no shared view of the system
"""

BROKEN = "# No frontmatter here\n"


def build(root: Path) -> Path:
    (root / "architecture").mkdir(parents=True)
    (root / "overview").mkdir(parents=True)
    (root / "architecture" / "components.md").write_text(ARC, encoding="utf-8")
    (root / "overview" / "problem.md").write_text(OVW, encoding="utf-8")
    return root


def test_rows_follow_category_order(tmp_path):
    """overview precedes architecture, matching the category table, not the filesystem."""
    rows, skipped = collect(build(tmp_path / "sot"))
    assert [row["id"] for row in rows] == ["OVW-problem", "ARC-components"]
    assert skipped == []


def test_render_links_every_doc(tmp_path):
    rows, _ = collect(build(tmp_path / "sot"))
    out = render(rows)
    assert "[OVW-problem](overview/problem.md)" in out
    assert "[ARC-components](architecture/components.md)" in out
    assert "rules/sot-maintenance.md" in out  # update protocol pointer survives regeneration
    assert out.endswith("|\n")


def test_incomplete_frontmatter_is_skipped_not_guessed(tmp_path):
    root = build(tmp_path / "sot")
    (root / "overview" / "draft.md").write_text(BROKEN, encoding="utf-8")
    rows, skipped = collect(root)
    assert skipped == ["overview/draft.md"]
    assert len(rows) == 2


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
