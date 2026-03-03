#!/bin/bash
# Test: statusline-command.sh should NOT contain any "Usage" text in output
# after the usage feature was removed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$SCRIPT_DIR/.claude/script/statusline-command.sh"

passed=0
failed=0

fail() {
  echo "FAIL: $1"
  failed=$((failed + 1))
}

pass() {
  echo "PASS: $1"
  passed=$((passed + 1))
}

# Test 1: Output should not contain "Usage"
output=$(echo '{"current_dir":"/test","model":{"display_name":"Opus"},"version":"1.0","context_window":{"used_percentage":50,"current_usage":{"cache_read_input_tokens":1000}}}' | bash "$SCRIPT" 2>/dev/null)

if echo "$output" | grep -qi "Usage"; then
  fail "Output contains 'Usage' text: $output"
else
  pass "No 'Usage' text in output"
fi

# Test 2: Output should still contain model name
if echo "$output" | grep -q "Opus"; then
  pass "Model name 'Opus' present in output"
else
  fail "Model name 'Opus' missing from output"
fi

# Test 3: Output should still contain version
if echo "$output" | grep -q "v1.0"; then
  pass "Version 'v1.0' present in output"
else
  fail "Version 'v1.0' missing from output"
fi

# Test 4: Output should contain context info
if echo "$output" | grep -q "ctx:"; then
  pass "Context info present in output"
else
  fail "Context info missing from output"
fi

# Test 5: Output should contain cache info
if echo "$output" | grep -q "cache:"; then
  pass "Cache info present in output"
else
  fail "Cache info missing from output"
fi

# Test 6: Source code should not reference fetch-claude-usage.swift
if grep -q "fetch-claude-usage" "$SCRIPT"; then
  fail "Script still references fetch-claude-usage.swift"
else
  pass "No reference to fetch-claude-usage.swift in script"
fi

# Test 7: Source code should not contain show_usage variable
if grep -q "show_usage" "$SCRIPT"; then
  fail "Script still contains show_usage variable"
else
  pass "No show_usage variable in script"
fi

echo ""
echo "Results: $passed passed, $failed failed"
[ "$failed" -eq 0 ] && exit 0 || exit 1
