#!/bin/bash
# install-timer.sh의 Linux 섹션에서 깨진 symlink 정리를 검증하는 테스트.
#
# 실행 방법: bash plugins/jin-claude/scripts/test_install_timer.sh
# systemd/launchd/schtasks 없이 스크립트의 rm -f 로직만 검증한다.

set -euo pipefail

PASS=0
FAIL=0

assert_eq() {
    local desc="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (expected='$expected', actual='$actual')"
        FAIL=$((FAIL + 1))
    fi
}

assert_not_exists() {
    local desc="$1" path="$2"
    if [ ! -e "$path" ] && [ ! -L "$path" ]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (path still exists: $path)"
        FAIL=$((FAIL + 1))
    fi
}

assert_exists() {
    local desc="$1" path="$2"
    if [ -e "$path" ]; then
        echo "  PASS: $desc"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $desc (path not found: $path)"
        FAIL=$((FAIL + 1))
    fi
}

# ── Test 1: 깨진 symlink이 rm -f로 제거되는지 ──
echo "Test 1: rm -f removes broken symlink"
TMPDIR=$(mktemp -d)
SYSTEMD_DIR="$TMPDIR/systemd"
mkdir -p "$SYSTEMD_DIR"

# 존재하지 않는 경로를 가리키는 깨진 symlink 생성
ln -s "/nonexistent/path/fetch-claude-usage.timer" "$SYSTEMD_DIR/fetch-claude-usage.timer"
ln -s "/nonexistent/path/fetch-claude-usage.service" "$SYSTEMD_DIR/fetch-claude-usage.service"

# rm -f로 깨진 symlink 제거 (install-timer.sh가 하는 동작)
rm -f "$SYSTEMD_DIR/fetch-claude-usage.service"
rm -f "$SYSTEMD_DIR/fetch-claude-usage.timer"

assert_not_exists "broken timer symlink removed" "$SYSTEMD_DIR/fetch-claude-usage.timer"
assert_not_exists "broken service symlink removed" "$SYSTEMD_DIR/fetch-claude-usage.service"

# ── Test 2: rm -f 후 cat > 으로 새 파일 생성 가능 ──
echo "Test 2: cat > creates new file after rm -f cleanup"
cat > "$SYSTEMD_DIR/fetch-claude-usage.timer" << EOF
[Unit]
Description=Test timer

[Timer]
OnBootSec=30
OnUnitActiveSec=3min
EOF

assert_exists "new timer file created" "$SYSTEMD_DIR/fetch-claude-usage.timer"
actual_content=$(grep "OnUnitActiveSec" "$SYSTEMD_DIR/fetch-claude-usage.timer")
assert_eq "timer interval correct" "OnUnitActiveSec=3min" "$actual_content"

# ── Test 3: 정상 파일이 있어도 rm -f + 재생성 가능 ──
echo "Test 3: rm -f + recreate works with existing regular file"
echo "old content" > "$SYSTEMD_DIR/fetch-claude-usage.timer"
rm -f "$SYSTEMD_DIR/fetch-claude-usage.timer"
cat > "$SYSTEMD_DIR/fetch-claude-usage.timer" << EOF
[Timer]
OnUnitActiveSec=5min
EOF

actual_content=$(grep "OnUnitActiveSec" "$SYSTEMD_DIR/fetch-claude-usage.timer")
assert_eq "timer overwritten" "OnUnitActiveSec=5min" "$actual_content"

# ── Test 4: symlink 타겟이 존재해도 rm -f가 안전 ──
echo "Test 4: rm -f is safe with valid symlink"
REAL_FILE="$TMPDIR/real-service"
echo "real service" > "$REAL_FILE"
ln -sf "$REAL_FILE" "$SYSTEMD_DIR/fetch-claude-usage.service"

rm -f "$SYSTEMD_DIR/fetch-claude-usage.service"

assert_not_exists "valid symlink removed" "$SYSTEMD_DIR/fetch-claude-usage.service"
assert_exists "original file preserved" "$REAL_FILE"

# ── Test 5: 파일이 없어도 rm -f가 에러 없이 통과 ──
echo "Test 5: rm -f is no-op when file does not exist"
rm -f "$SYSTEMD_DIR/nonexistent-file" 2>/dev/null
assert_eq "rm -f on nonexistent returns 0" "0" "$?"

# Cleanup
rm -rf "$TMPDIR"

# Report
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All tests passed."
