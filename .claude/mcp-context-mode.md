# MCP Context-Mode

Handles large outputs and external resource processing.

## When to Use
- Command output exceeds 20 lines
- Fetching external URLs for analysis
- Batch processing multiple commands
- Protecting context window from large outputs

## Key Commands
- `ctx_execute`: Execute commands, output stored externally
- `ctx_batch_execute`: Execute multiple commands in parallel
- `ctx_fetch_and_index`: Fetch URL content and index for querying

## Examples
```
# Large build output
ctx_execute("npm run build")

# Fetch external resource
ctx_fetch_and_index("https://example.com/api-docs")

# Batch analysis
ctx_batch_execute(["cmd1", "cmd2", "cmd3"])
```

## Workflow
1. Execute command with ctx_execute
2. View summary in context
3. Use returned reference to access full output if needed
