# MCP Serena

Symbolic code manipulation and precise refactoring via LSP (Language Server Protocol).

## When to Use
- **Finding symbols**: Locate exact definitions of functions, classes, variables
- **Refactoring**: Rename, move, or restructure code safely across the project
- **Reference tracking**: Find all usages of a specific symbol
- **Code structure**: Get overview of file organization without reading entire files

## Key Commands
- `mcp__serena__find_symbol`: Find exact symbol location (`path/name` format)
- `mcp__serena__get_symbols_overview`: Get symbol structure of a file
- `mcp__serena__find_referencing_symbols`: Find all code referencing a symbol
- `mcp__serena__replace_symbol_body`: Replace symbol content safely

## Examples
```bash
# Find a specific class or function
mcp__serena__find_symbol("src/auth.py/AuthManager")

# Get file structure overview
mcp__serena__get_symbols_overview("src/utils.py")

# Find all usages before refactoring
mcp__serena__find_referencing_symbols("src/models.py/User")

# Replace method implementation
mcp__serena__replace_symbol_body("src/api.py/Client/request", "new implementation here")
```

## Workflow
Use Serena when you know exactly what symbol you need to modify or where it is located.
