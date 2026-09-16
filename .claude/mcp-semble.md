# MCP Semble

Semantic code search using vector embeddings. Find code by meaning, not just keywords.

## When to Use
- **Natural language search**: "Where is the authentication flow?" instead of exact keyword matching
- **Finding similar code**: Discover duplicate logic or related implementations
- **Documentation search**: Search through markdown, config files, and comments
- **Code discovery**: Understand how features are implemented across the codebase

## Key Commands
- `mcp__semble__search`: Natural language or code query search
- `mcp__semble__find_related`: Find code similar to a specific file and line

## Search Options
- `--content docs`: Search documentation and prose files only
- `--content config`: Search configuration files only  
- `--content all`: Search code, docs, and config together

## Examples
```bash
# Natural language search
mcp__semble__search("user authentication flow")
mcp__semble__search("database connection pool setup", --content config)

# Find similar implementations
mcp__semble__find_related("src/auth.py", 42)

# Search all content types
mcp__semble__search("error handling middleware", --content all)
```

## Workflow
Use Semble when you know *what* you're looking for conceptually, but not the exact symbol name or location. Start with Semble to locate relevant files, then use Serena for precise manipulation.
