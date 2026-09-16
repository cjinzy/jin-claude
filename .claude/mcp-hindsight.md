# MCP Hindsight

Persistent vector memory and recall across sessions.

## When to Use
- Store long-term project knowledge
- Recall decisions from previous sessions
- Maintain context across time
- Search historical implementations

## Key Commands
- `mcp__hindsight__retain`: Store information
- `mcp__hindsight__recall`: Query memories
- `mcp__hindsight__create_bank`: Create project-specific memory bank

## Bank Management
- Each project should have its own bank (git repo name)
- Use consistent bank IDs for related work
- Avoid mixing personal and project memories

## Examples
```
# Store decision
mcp__hindsight__retain(
  bank_id="my-project",
  content="Chose PostgreSQL over MongoDB for better JSONB support",
  context="decision",
  tags=["database", "architecture"]
)

# Recall memories
mcp__hindsight__recall(
  bank_id="my-project",
  query="database decision"
)

# Create bank if not exists
mcp__hindsight__create_bank(bank_id="my-project")
```

## Memory Routing
See @memory-routing.md for detailed mirroring rules (Primary/Mirror/Conflict resolution) with file-based memory.
