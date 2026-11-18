#!/usr/bin/env python3
"""SSOT docset validator for `sot/`.

Checks the invariants that make a Source of Truth safe for a coding agent to trust:

    1. every doc carries the required frontmatter keys
    2. doc ids and fact ids use their category's prefix and are globally unique
    3. Index.md links every doc, and every Index.md link resolves
    4. drift — a doc is stale when its `verified_paths` changed since `verified_commit`

Drift is the reason this script exists. Without it a stale doc and a fresh doc look
identical, and an agent believes both.

Output is JSON on stdout so an agent can act on findings without reading every doc.
Exit code: 0 = no errors, 1 = at least one error.

    python3 sot_validate.py --root sot
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Category -> fact id prefix. Fixed set: a new top-level category would split ownership
# of facts that already have an owner.
CATEGORY_PREFIXES = {
    "overview": "OVW",
    "tech-stack": "STK",
    "database-schema": "DBS",
    "architecture": "ARC",
    "workflow": "WFL",
    "design": "DSN",
    "rules": "RUL",
}

# Root design system file (tokens: color, type, spacing). Owned outside `sot/` because design
# tools read it at the repo root; `design/` docs cite it instead of copying tokens.
DESIGN_FILENAME = "DESIGN.md"

# Categories with no code counterpart: a `verified` doc here has nothing to drift against.
INTENT_ONLY_CATEGORIES = ("overview", "rules")

REQUIRED_KEYS = ("id", "category", "title", "status", "updated")
VALID_STATUSES = ("draft", "verified", "stale")

INDEX_FILENAME = "Index.md"
# One doc = one sub-topic, whatever its length. Length is deliberately not checked: splitting a
# long single-topic doc would give one sub-topic two owners. This is only a hint that a file may
# have grown past its topic.
# Why 8: a sub-topic doc should be readable in one pass; past ~8 addressable claims it usually
# answers a second question. Tuned heuristic, not a spec — raise it if warnings are mostly noise.
MANY_FACTS_HINT = 8

FRONTMATTER_DELIMITER = "---"
# `## ARC-002 — The gateway is the only public entry point`
FACT_HEADING = re.compile(r"^##\s+([A-Z]{3}-\d{3})\s*[—-]\s*(\S.*)$")
MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")
OPEN_QUESTION = re.compile(r"TODO\(sot\):")


def parse_frontmatter(text: str) -> tuple[dict[str, str], int]:
    """Parse flat `key: value` frontmatter.

    This repo has no PyYAML dependency, so the document contract keeps frontmatter flat and
    writes lists as comma-separated values. Returns (values, body_start_line).
    An unterminated or absent block yields ({}, 0).
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, 0
    values: dict[str, str] = {}
    for offset, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            return values, offset + 1
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = value.strip()
    return {}, 0


def split_list(value: str) -> list[str]:
    """Comma-separated frontmatter value -> list."""
    return [item.strip() for item in value.split(",") if item.strip()]


def changed_since(repo: Path, commit: str, paths: list[str]) -> list[str] | None:
    """Files under `paths` touched since `commit`. None when `commit` is not resolvable."""
    result = subprocess.run(
        ["git", "-C", str(repo), "diff", "--name-only", f"{commit}..HEAD", "--", *paths],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return [line for line in result.stdout.splitlines() if line]


class Report:
    """Findings accumulator. `error` blocks the agent; `warning`/`info` inform it."""

    def __init__(self) -> None:
        self.findings: list[dict[str, str]] = []

    def add(self, level: str, code: str, file: str, message: str) -> None:
        self.findings.append({"level": level, "code": code, "file": file, "message": message})

    def count(self, level: str) -> int:
        return sum(1 for finding in self.findings if finding["level"] == level)


def _validate_doc(
    path: Path, root: Path, repo: Path, report: Report, seen_ids: dict[str, str]
) -> tuple[str | None, int]:
    """Validate one doc. Returns (doc_id, fact_count)."""
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")
    meta, _ = parse_frontmatter(text)

    if not meta:
        report.add("error", "MISSING_FRONTMATTER", rel, "no terminated `---` frontmatter block")
        return None, 0

    for key in REQUIRED_KEYS:
        if not meta.get(key):
            report.add("error", "MISSING_KEY", rel, f"frontmatter is missing `{key}`")

    directory = path.parent.relative_to(root).as_posix()
    expected_prefix = CATEGORY_PREFIXES.get(directory)
    if expected_prefix is None:
        report.add("error", "BAD_CATEGORY", rel, f"`{directory}` is not a SoT category")
        return meta.get("id"), 0
    if meta.get("category") != directory:
        report.add(
            "error",
            "BAD_CATEGORY",
            rel,
            f"frontmatter category `{meta.get('category')}` != directory `{directory}`",
        )

    doc_id = meta.get("id")
    if doc_id:
        if not doc_id.startswith(f"{expected_prefix}-"):
            report.add(
                "error", "BAD_ID_PREFIX", rel, f"id `{doc_id}` must start with `{expected_prefix}-`"
            )
        if doc_id in seen_ids:
            report.add(
                "error", "DUPLICATE_ID", rel, f"id `{doc_id}` already used by {seen_ids[doc_id]}"
            )
        else:
            seen_ids[doc_id] = rel

    status = meta.get("status")
    if status and status not in VALID_STATUSES:
        report.add("error", "BAD_STATUS", rel, f"status `{status}` not in {VALID_STATUSES}")

    fact_ids: list[str] = []
    for line in text.splitlines():
        match = FACT_HEADING.match(line)
        if not match:
            continue
        fact_id = match.group(1)
        fact_ids.append(fact_id)
        if not fact_id.startswith(f"{expected_prefix}-"):
            report.add(
                "error",
                "BAD_ID_PREFIX",
                rel,
                f"fact `{fact_id}` must start with `{expected_prefix}-`",
            )
        elif fact_id in seen_ids:
            report.add(
                "error",
                "DUPLICATE_ID",
                rel,
                f"fact `{fact_id}` already used by {seen_ids[fact_id]}",
            )
        else:
            seen_ids[fact_id] = rel

    if not fact_ids and status != "draft":
        report.add("warning", "NO_FACTS", rel, "no `## PREFIX-NNN — claim` headings found")
    elif len(fact_ids) > MANY_FACTS_HINT:
        report.add(
            "warning",
            "MANY_FACTS",
            rel,
            f"{len(fact_ids)} facts — check whether this doc covers more than one sub-topic",
        )

    open_questions = sum(1 for line in text.splitlines() if OPEN_QUESTION.search(line))
    if open_questions:
        report.add("info", "TODO_OPEN", rel, f"{open_questions} open `TODO(sot):` question(s)")

    _check_drift(meta, rel, repo, status, report)
    return doc_id, len(fact_ids)


def _check_drift(
    meta: dict[str, str], rel: str, repo: Path, status: str | None, report: Report
) -> None:
    """A doc claiming `verified` while its code moved underneath it is lying."""
    commit = meta.get("verified_commit", "")
    paths = split_list(meta.get("verified_paths", ""))
    if not commit or not paths:
        if status == "verified" and meta.get("category") not in INTENT_ONLY_CATEGORIES:
            report.add(
                "warning",
                "UNVERIFIABLE_COMMIT",
                rel,
                "status is `verified` but verified_commit/verified_paths are missing",
            )
        return

    changed = changed_since(repo, commit, paths)
    if changed is None:
        report.add("warning", "UNVERIFIABLE_COMMIT", rel, f"commit `{commit}` is not resolvable")
        return
    if changed:
        level = "error" if status == "verified" else "warning"
        preview = ", ".join(changed[:3]) + (" …" if len(changed) > 3 else "")
        report.add(
            level,
            "DRIFT",
            rel,
            f"{len(changed)} file(s) changed since `{commit}`: {preview}",
        )


def _check_index(root: Path, doc_paths: list[Path], report: Report) -> None:
    """Index.md is the only entry point: it must list every doc and link nothing missing."""
    index = root / INDEX_FILENAME
    if not index.is_file():
        report.add("error", "DEAD_LINK", INDEX_FILENAME, f"{INDEX_FILENAME} does not exist")
        return

    linked: set[str] = set()
    for target in MARKDOWN_LINK.findall(index.read_text(encoding="utf-8")):
        target = target.split("#", 1)[0].strip()
        if not target or not target.endswith(".md") or "://" in target:
            continue
        resolved = (root / target).resolve()
        if not resolved.is_file():
            report.add("error", "DEAD_LINK", INDEX_FILENAME, f"link `{target}` does not resolve")
            continue
        linked.add(resolved.as_posix())

    for path in doc_paths:
        if path.resolve().as_posix() not in linked:
            rel = path.relative_to(root).as_posix()
            report.add("error", "NOT_INDEXED", rel, f"not linked from {INDEX_FILENAME}")


def validate(root: Path) -> dict:
    """Validate the docset at `root`. Returns the JSON report."""
    report = Report()
    if not root.is_dir():
        report.add("error", "MISSING_FRONTMATTER", str(root), f"`{root}` is not a directory")
        return _summary(root, report, 0, 0, [])

    repo = root.parent
    doc_paths = sorted(p for p in root.rglob("*.md") if p.name != INDEX_FILENAME)
    seen_ids: dict[str, str] = {}
    fact_total = 0
    for path in doc_paths:
        _, facts = _validate_doc(path, root, repo, report, seen_ids)
        fact_total += facts

    _check_index(root, doc_paths, report)

    stale = sorted(
        {f["file"] for f in report.findings if f["code"] in ("DRIFT", "UNVERIFIABLE_COMMIT")}
    )
    return _summary(root, report, len(doc_paths), fact_total, stale)


def _summary(root: Path, report: Report, docs: int, facts: int, stale: list[str]) -> dict:
    return {
        "root": str(root),
        "ok": report.count("error") == 0,
        "docs": docs,
        "facts": facts,
        "errors": report.count("error"),
        "warnings": report.count("warning"),
        "stale": stale,
        "findings": report.findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a SoT docset")
    parser.add_argument("--root", default="sot", help="SoT root directory (default: sot)")
    args = parser.parse_args()

    result = validate(Path(args.root))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
