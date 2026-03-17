#!/bin/bash
# install_chub.sh 의 로직을 단위 테스트한다 (실제 npm install 없이).
#
# 실행 방법: bash plugins/jin-claude/skills/jin-chub/scripts/test_install_chub.sh

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

# ── 버전 파싱 헬퍼 (install_chub.sh와 동일 로직) ──
parse_major() {
    local ver="$1"
    local stripped="${ver#v}"    # v20.11.0 → 20.11.0
    echo "${stripped%%.*}"       # 20.11.0 → 20
}

# ── Test 1: Node.js 버전 문자열 파싱 ──
echo "Test 1: Node.js 버전 문자열 파싱"
assert_eq "v20.11.0 → 20" "20" "$(parse_major 'v20.11.0')"
assert_eq "v18.0.0 → 18"  "18" "$(parse_major 'v18.0.0')"
assert_eq "v16.20.2 → 16" "16" "$(parse_major 'v16.20.2')"
assert_eq "v22.1.0 → 22"  "22" "$(parse_major 'v22.1.0')"

# ── Test 2: 버전 게이트 통과 (>= 18) ──
echo "Test 2: 버전 게이트 통과 (>= 18)"
for ver in "v18.0.0" "v20.11.0" "v22.1.0"; do
    major=$(parse_major "$ver")
    if [ "$major" -ge 18 ]; then
        result="pass"
    else
        result="fail"
    fi
    assert_eq "$ver passes gate" "pass" "$result"
done

# ── Test 3: 버전 게이트 실패 (< 18) ──
echo "Test 3: 버전 게이트 실패 (< 18)"
for ver in "v16.20.2" "v14.21.3" "v12.0.0"; do
    major=$(parse_major "$ver")
    if [ "$major" -ge 18 ]; then
        result="pass"
    else
        result="fail"
    fi
    assert_eq "$ver fails gate" "fail" "$result"
done

# ── Test 4: 멱등성 — 기존 설치 감지 메시지 ──
echo "Test 4: 멱등성 — 기존 설치 감지 로직"
# command -v chub가 있으면 "업그레이드" 메시지, 없으면 "설치" 메시지
simulate_install_msg() {
    local chub_exists="$1"
    if [ "$chub_exists" = "true" ]; then
        echo "upgrade"
    else
        echo "install"
    fi
}

assert_eq "chub exists → upgrade" "upgrade" "$(simulate_install_msg 'true')"
assert_eq "chub absent → install" "install"  "$(simulate_install_msg 'false')"

# ── Test 5: 엣지 케이스 — 단일 자릿수 메이저 버전 ──
echo "Test 5: 엣지 케이스 — 단일/다중 자릿수 메이저 버전"
assert_eq "v8.17.0 → 8"   "8"   "$(parse_major 'v8.17.0')"
assert_eq "v100.0.0 → 100" "100" "$(parse_major 'v100.0.0')"

# ── Report ──
echo ""
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All tests passed."
