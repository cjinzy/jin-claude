# Memory Routing (Hindsight First)

Persistent memory uses a per-project Hindsight bank as the Primary (Source of Truth), with file-based memory acting as a Mirror/Backup. Storage, recall, and conflict resolution always prioritize Hindsight, mirroring one-way (Hindsight → File) to prevent drift.

- **bank_id Convention**: Current git repo basename (e.g., `/Users/x/git/4kd` → `4kd`); if outside git, use the working directory basename. Auto-generate with `mcp__hindsight__create_bank` if missing (do not mix with the generic `hermes` bank — isolate per project). If the project CLAUDE.md specifies a bank binding, that takes precedence.
- **Primary**: Project Hindsight bank. First source for recall and the winner in conflicts.
- **Mirror/Backup**: Harness file memory (`~/.claude/projects/<proj>/memory/<slug>.md` + `MEMORY.md`).
  Retention rationale: ① Automatic `MEMORY.md` load every session (free context) ② Durable backup if Hindsight is unavailable ③ Stores full details, `[[links]]`, and frontmatter.
- **Storage (New/Update)**: ① `mcp__hindsight__retain(bank_id=<repo>, content="[<slug>] <description>",
  context=<type>, document_id=<slug>, tags=["project:<repo>","type:<type>","name:<slug>"],
  metadata={"source":"file-memory","file":"<slug>.md"})` (Primary first) → ② Update file `<slug>.md` +
  `MEMORY.md` index (Mirror). `document_id=<slug>` makes re-saving idempotent. On delete, use
  `mcp__hindsight__delete_document` and remove from both file and index.
- **Recall**: Primary `mcp__hindsight__recall(bank_id=<repo>, query=..., tags=["name:<slug>"])`.
  The auto-loaded `MEMORY.md` serves as a secondary index. Open the file from `metadata.file` in the召回 result to check full details (Hindsight stores `description` summary; deep details live in the file).
- **Conflict**: Hindsight wins (Primary). Since files hold richer details, treat Hindsight as authoritative facts and files as extended details — update the file mirror based on Hindsight on any mismatch.
