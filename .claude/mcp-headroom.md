# MCP Headroom

Context window optimization and compression.

## When to Use
- Large codebases exceeding context limits
- Long-running conversations with extensive history
- When you need to fit more content into limited context

## Key Commands
- `mcp__headroom__compress`: Compress content for context
- `mcp__headroom__expand`: Restore compressed content

## Examples
```
# Compress large file for inclusion
mcp__headroom__compress("src/large_module.py")

# Expand previously compressed content
mcp__headroom__expand("compression-reference-id")
```

## Workflow
1. Identify large content that exceeds context
2. Compress using Headroom
3. Reference compressed version in conversation
4. Expand when full detail is needed

## Integration
Works automatically with large outputs from other MCP servers when configured.
