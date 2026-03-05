#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo "[install-timer] systemd user directory: $SYSTEMD_USER_DIR"
mkdir -p "$SYSTEMD_USER_DIR"

# Symlink service and timer
ln -sf "$REPO_DIR/systemd/fetch-claude-usage.service" "$SYSTEMD_USER_DIR/"
ln -sf "$REPO_DIR/systemd/fetch-claude-usage.timer" "$SYSTEMD_USER_DIR/"

# Reload and enable
systemctl --user daemon-reload
systemctl --user enable --now fetch-claude-usage.timer

echo "[install-timer] Timer status:"
systemctl --user status fetch-claude-usage.timer --no-pager || true

echo ""
echo "[install-timer] Done. Usage will be fetched every 5 minutes."
echo "[install-timer] Initial fetch..."
systemctl --user start fetch-claude-usage.service
echo "[install-timer] Check cache: cat ~/.claude/.usage-cache.json"
