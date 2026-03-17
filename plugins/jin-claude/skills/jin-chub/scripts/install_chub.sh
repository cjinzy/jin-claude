#!/bin/bash
# context-hub (chub) CLI 설치/업그레이드 스크립트.
#
# 실행 방법: bash plugins/jin-claude/skills/jin-chub/scripts/install_chub.sh

set -euo pipefail

PREFIX="[install-chub]"

log()  { echo "$PREFIX $*"; }
err()  { echo "$PREFIX ERROR: $*" >&2; }

# ── 1. Node.js 존재 확인 ──
if ! command -v node &>/dev/null; then
    err "Node.js가 설치되어 있지 않습니다. https://nodejs.org 에서 설치해 주세요."
    exit 1
fi

# ── 2. Node.js 버전 체크 (>= 18) ──
NODE_VERSION=$(node --version)                  # e.g. v20.11.0
MAJOR=${NODE_VERSION#v}                         # 20.11.0
MAJOR=${MAJOR%%.*}                              # 20

if [ "$MAJOR" -lt 18 ]; then
    err "Node.js >= 18 필요 (현재: $NODE_VERSION)"
    exit 1
fi

log "Node.js $NODE_VERSION 확인 완료 (major=$MAJOR)"

# ── 3. chub 설치 또는 업그레이드 ──
if command -v chub &>/dev/null; then
    CURRENT=$(chub --version 2>/dev/null || echo "unknown")
    log "기존 chub 발견 ($CURRENT) — 업그레이드합니다."
    npm install -g @anthropic-ai/context-hub
else
    log "chub를 설치합니다."
    npm install -g @anthropic-ai/context-hub
fi

# ── 4. 설치 검증 ──
if ! command -v chub &>/dev/null; then
    err "설치 후 chub를 찾을 수 없습니다. PATH를 확인해 주세요."
    exit 1
fi

INSTALLED=$(chub --version 2>/dev/null || echo "unknown")
log "설치 완료: chub $INSTALLED"
