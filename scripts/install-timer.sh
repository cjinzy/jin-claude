#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

# 주기 선택: CLI 인자 또는 대화형 입력
# Usage: install-timer.sh [1|3|5|10]
if [ -n "${1:-}" ]; then
  # CLI 인자로 전달된 경우
  arg_min="$1"
  case "$arg_min" in
    1)  INTERVAL="1min" ;;
    3)  INTERVAL="3min" ;;
    5)  INTERVAL="5min" ;;
    10) INTERVAL="10min" ;;
    *)  echo "[install-timer] 잘못된 인자 '$arg_min', 기본값 5분 사용"; INTERVAL="5min" ;;
  esac
else
  # 대화형 입력
  echo "[install-timer] 사용량 수집 주기를 선택하세요:"
  echo "  1) 1분"
  echo "  2) 3분"
  echo "  3) 5분 (권장)"
  echo "  4) 10분"
  read -rp "선택 [1-4, 기본=3]: " choice

  case "${choice:-3}" in
    1) INTERVAL="1min" ;;
    2) INTERVAL="3min" ;;
    3) INTERVAL="5min" ;;
    4) INTERVAL="10min" ;;
    *) echo "[install-timer] 잘못된 선택, 기본값 5분 사용"; INTERVAL="5min" ;;
  esac
fi

echo "[install-timer] 수집 주기: $INTERVAL"
echo "[install-timer] systemd user directory: $SYSTEMD_USER_DIR"
mkdir -p "$SYSTEMD_USER_DIR"

# Service는 symlink
ln -sf "$REPO_DIR/systemd/fetch-claude-usage.service" "$SYSTEMD_USER_DIR/"

# Timer는 선택한 주기로 생성
cat > "$SYSTEMD_USER_DIR/fetch-claude-usage.timer" << EOF
[Unit]
Description=Fetch Claude API usage every $INTERVAL

[Timer]
OnBootSec=30
OnUnitActiveSec=$INTERVAL
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable --now fetch-claude-usage.timer

echo "[install-timer] Timer status:"
systemctl --user status fetch-claude-usage.timer --no-pager || true

echo ""
echo "[install-timer] Done. Usage will be fetched every $INTERVAL."
echo "[install-timer] Initial fetch..."
systemctl --user start fetch-claude-usage.service || true
echo "[install-timer] Check cache: cat ~/.claude/.usage-cache.json"
