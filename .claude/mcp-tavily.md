# MCP Tavily

Web search and content extraction with AI summarization.

## Status
⚠️ **Requires authentication**: Needs API key configuration

## When to Use
- Current information lookup (news, prices, versions)
- Research requiring web sources
- Fact verification with citations
- Competitor analysis and market research

## Key Commands
- `mcp__tavily__search`: Web search with filters
- `mcp__tavily__extract`: Extract content from URL

## Examples
```
# Web search
mcp__tavily__search("latest Python 3.13 features", max_results=5)

# Extract specific page content
mcp__tavily__extract("https://docs.python.org/3.13/whatsnew.html")

# Search with domain filter
mcp__tavily__search("react hooks", include_domains=["react.dev"])
```

## Authentication
Set `TAVILY_API_KEY` environment variable or configure in MCP settings.

## Workflow
1. Search with specific queries
2. Extract full content from promising URLs
3. Verify facts with multiple sources
