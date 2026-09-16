# MCP GBrain

Knowledge graph and RAG (Retrieval-Augmented Generation).

## When to Use
- Complex queries over personal knowledge base
- Connecting disparate pieces of information
- Building comprehensive answers from multiple sources
- Research synthesis

## Key Commands
- `mcp__gbrain__query`: Query knowledge graph
- `mcp__gbrain__add`: Add documents to knowledge base

## Examples
```
# Query knowledge base
mcp__gbrain__query("How does authentication work in microservices?")

# Add document
mcp__gbrain__add(
  content="Microservices auth patterns...",
  source="architecture-notes.md",
  tags=["auth", "microservices"]
)
```

## Workflow
1. Add relevant documents to build knowledge base
2. Query with natural language
3. Receive synthesized answers with source references

## Best For
- Connecting concepts across large document sets
- Questions requiring synthesis of multiple sources
- Building comprehensive technical explanations
