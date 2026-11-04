"""Tests for sot_validate.py — the invariants that let an agent trust the docset."""

from __future__ import annotations

import subprocess
from pathlib import Path

from sot_validate import parse_frontmatter, validate

DOC = """---
id: ARC-components
category: architecture
title: Service components
status: draft
updated: 2026-10-02
---

# Service components

## ARC-001 — The gateway is the only public entry point

Evidence: `src/api/gateway.py:1`
"""

INDEX = (
    "# SoT Index\n\n| Doc | Status |\n|---|---|\n"
    "| [ARC-components](architecture/components.md) | draft |\n"
)


def build(root: Path, doc: str = DOC, index: str = INDEX) -> Path:
    """Minimal one-doc docset."""
    (root / "architecture").mkdir(parents=True)
    (root / "architecture" / "components.md").write_text(doc, encoding="utf-8")
    (root / "Index.md").write_text(index, encoding="utf-8")
    return root


def codes(result: dict) -> set[str]:
    return {finding["code"] for finding in result["findings"]}


def test_parse_frontmatter_flat():
    meta, body_start = parse_frontmatter("---\na: 1\nb: x, y\n---\nbody\n")
    assert meta == {"a": "1", "b": "x, y"}
    assert body_start == 4


def test_parse_frontmatter_unterminated():
    assert parse_frontmatter("---\na: 1\nbody\n") == ({}, 0)


def test_valid_docset_passes(tmp_path):
    result = validate(build(tmp_path / "sot"))
    assert result["ok"], result["findings"]
    assert result["docs"] == 1
    assert result["facts"] == 1


def test_unlisted_doc_is_an_error(tmp_path):
    result = validate(build(tmp_path / "sot", index="# SoT Index\n"))
    assert not result["ok"]
    assert "NOT_INDEXED" in codes(result)


def test_dead_index_link_is_an_error(tmp_path):
    root = build(tmp_path / "sot")
    (root / "Index.md").write_text(
        f"{INDEX}| [gone](architecture/gone.md) | draft |\n", encoding="utf-8"
    )
    assert "DEAD_LINK" in codes(validate(root))


def test_wrong_fact_prefix_is_an_error(tmp_path):
    result = validate(build(tmp_path / "sot", doc=DOC.replace("## ARC-001", "## WFL-001")))
    assert not result["ok"]
    assert "BAD_ID_PREFIX" in codes(result)


def test_too_many_facts_warns(tmp_path):
    """A doc with many facts is two sub-topics wearing one filename."""
    facts = "".join(f"\n## ARC-{n:03d} — Claim {n}\n" for n in range(10, 20))
    result = validate(build(tmp_path / "sot", doc=DOC + facts))
    assert result["ok"]
    assert "MANY_FACTS" in codes(result)


def test_intent_only_category_needs_no_baseline(tmp_path):
    """A verified rules/ doc describes intent, so it has no code to drift against."""
    root = tmp_path / "sot"
    (root / "rules").mkdir(parents=True)
    (root / "rules" / "sot-maintenance.md").write_text(
        "---\nid: RUL-sot-maintenance\ncategory: rules\ntitle: Upkeep\n"
        "status: verified\nupdated: 2026-10-02\n---\n\n"
        "## RUL-901 — Validation runs in the verify step\n",
        encoding="utf-8",
    )
    (root / "Index.md").write_text(
        "# SoT Index\n\n| [RUL-sot-maintenance](rules/sot-maintenance.md) |\n", encoding="utf-8"
    )
    result = validate(root)
    assert result["ok"], result["findings"]
    assert "UNVERIFIABLE_COMMIT" not in codes(result)


def test_design_category_links_root_design_md(tmp_path):
    """design/ owns DSN-* rules; root DESIGN.md owns tokens and is linked, never copied."""
    (tmp_path / "DESIGN.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    root = tmp_path / "sot"
    (root / "design").mkdir(parents=True)
    (root / "design" / "slides.md").write_text(
        "---\nid: DSN-slides\ncategory: design\ntitle: Slide layout\n"
        "status: draft\nupdated: 2026-11-04\n---\n\n"
        "## DSN-001 — Section headers use the DESIGN.md primary color\n\n"
        "Evidence: `DESIGN.md:2`\n",
        encoding="utf-8",
    )
    (root / "Index.md").write_text(
        "# SoT Index\n\n[DESIGN.md](../DESIGN.md)\n\n| [DSN-slides](design/slides.md) |\n",
        encoding="utf-8",
    )
    result = validate(root)
    assert result["ok"], result["findings"]
    assert result["facts"] == 1


def test_verified_doc_with_changed_code_is_drift(tmp_path):
    """The headline check: code moved under a doc that claims to be verified."""
    repo = tmp_path
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    source = repo / "src"
    source.mkdir()
    (source / "gateway.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    baseline = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    (source / "gateway.py").write_text("x = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "change"], cwd=repo, check=True)

    doc = DOC.replace(
        "status: draft",
        f"status: verified\nverified_commit: {baseline}\nverified_paths: src/",
    )
    result = validate(build(repo / "sot", doc=doc))
    assert not result["ok"]
    assert "DRIFT" in codes(result)
    assert result["stale"] == ["architecture/components.md"]


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
