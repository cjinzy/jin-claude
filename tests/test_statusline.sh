#!/bin/bash
# Test: statusline-command.sh 기능 검증
# - usage 기능 존재 확인
# - 크로스 플랫폼 date 헬퍼 존재 확인

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

# Test 1: Script should contain show_usage variable
if grep -q "show_usage" "$SCRIPT"; then
  pass "show_usage variable exists in script"
else
  fail "show_usage variable missing from script"
fi

# Test 2: Script should reference fetch-claude-usage
if grep -q "fetch-claude-usage" "$SCRIPT"; then
  pass "Script references fetch-claude-usage"
else
  fail "Script does not reference fetch-claude-usage"
fi

# Test 3: Cross-platform date helper parse_iso_to_epoch exists
if grep -q "parse_iso_to_epoch" "$SCRIPT"; then
  pass "parse_iso_to_epoch helper function exists"
else
  fail "parse_iso_to_epoch helper function missing"
fi

# Test 4: Cross-platform date helper format_epoch exists
if grep -q "format_epoch" "$SCRIPT"; then
  pass "format_epoch helper function exists"
else
  fail "format_epoch helper function missing"
fi

# Test 5: No hardcoded BSD-only date -ju calls outside helper functions
# date -ju inside parse_iso_to_epoch/format_epoch is expected (BSD branch)
outside_helper_count=$(awk '
  /^parse_iso_to_epoch|^format_epoch/ { in_helper=1 }
  in_helper && /^}/ { in_helper=0; next }
  !in_helper && /date -ju/ { count++ }
  END { print count+0 }
' "$SCRIPT")
if [ "$outside_helper_count" -eq 0 ]; then
  pass "No hardcoded BSD-only date calls outside helpers"
else
  fail "Hardcoded BSD-only 'date -ju' calls found outside helper functions"
fi

# Test 6: GNU date support (date -d) exists in helpers
if grep -q 'date -d' "$SCRIPT"; then
  pass "GNU date (date -d) support present"
else
  fail "GNU date (date -d) support missing"
fi

# Test 7: Output should contain model name
output=$(echo '{"current_dir":"/test","model":{"display_name":"Opus"},"version":"1.0","context_window":{"used_percentage":50,"current_usage":{"cache_read_input_tokens":1000}}}' | bash "$SCRIPT" 2>/dev/null)

if echo "$output" | grep -q "Opus"; then
  pass "Model name 'Opus' present in output"
else
  fail "Model name 'Opus' missing from output"
fi

# Test 8: Output should contain context info
if echo "$output" | grep -q "ctx:"; then
  pass "Context info present in output"
else
  fail "Context info missing from output"
fi

# Test 9: STATUSLINE_DEBUG variable support
if grep -q "STATUSLINE_DEBUG" "$SCRIPT"; then
  pass "STATUSLINE_DEBUG debug logging support exists"
else
  fail "STATUSLINE_DEBUG debug logging support missing"
fi

echo ""
echo "Results: $passed passed, $failed failed"
[ "$failed" -eq 0 ] && exit 0 || exit 1
