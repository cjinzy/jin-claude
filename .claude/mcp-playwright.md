# MCP Playwright

Browser automation and interaction.

## When to Use
- Web scraping and data extraction
- Automated UI testing
- Form filling and submission
- Screenshot capture
- Multi-step web workflows

## Key Commands
- `mcp__playwright__navigate`: Navigate to URL
- `mcp__playwright__click`: Click element
- `mcp__playwright__fill`: Fill form fields
- `mcp__playwright__screenshot`: Capture screenshot
- `mcp__playwright__extract`: Extract page content

## Examples
```
# Navigate and screenshot
mcp__playwright__navigate("https://example.com")
mcp__playwright__screenshot("page.png")

# Fill and submit form
mcp__playwright__fill("#username", "user")
mcp__playwright__fill("#password", "pass")
mcp__playwright__click("#login-button")

# Extract data
mcp__playwright__extract("table.data", format="json")
```

## Workflow
1. Navigate to target page
2. Inspect page structure if needed
3. Perform actions (click, fill, extract)
4. Capture final state (screenshot, data export)
