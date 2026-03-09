#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

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

# 주기를 초/분 단위로 변환
case "$INTERVAL" in
  1min)  INTERVAL_SEC=60;  INTERVAL_MIN=1 ;;
  3min)  INTERVAL_SEC=180; INTERVAL_MIN=3 ;;
  5min)  INTERVAL_SEC=300; INTERVAL_MIN=5 ;;
  10min) INTERVAL_SEC=600; INTERVAL_MIN=10 ;;
esac

# OS 감지
OS_TYPE="$(uname -s)"

if [ "$OS_TYPE" = "Linux" ]; then
  #── Linux: systemd timer/service ──────────────────────────────
  SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
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

elif [[ "$OS_TYPE" == MINGW* || "$OS_TYPE" == MSYS* || "$OS_TYPE" == CYGWIN* ]]; then
  #── Windows: Task Scheduler (schtasks) ────────────────────────
  TASK_NAME="jin-claude-fetch-usage"
  VENV_SCRIPTS="$HOME/.claude/.venv/Scripts"
  FETCH_CMD="$VENV_SCRIPTS/fetch-claude-usage.exe"
  LOG_FILE="$HOME/.claude/.usage-fetch-schtasks.log"

  # fetch-claude-usage.exe가 없으면 .cmd 또는 python 직접 실행 시도
  if [ ! -f "$FETCH_CMD" ]; then
    if [ -f "$VENV_SCRIPTS/fetch-claude-usage.cmd" ]; then
      FETCH_CMD="$VENV_SCRIPTS/fetch-claude-usage.cmd"
    elif [ -f "$VENV_SCRIPTS/fetch-claude-usage" ]; then
      FETCH_CMD="$VENV_SCRIPTS/fetch-claude-usage"
    fi
  fi

  # Git Bash 경로를 Windows 네이티브 경로로 변환
  WIN_FETCH_CMD="$(cygpath -w "$FETCH_CMD")"
  WIN_LOG_FILE="$(cygpath -w "$LOG_FILE")"

  echo "[install-timer] Windows Task Scheduler 설치"
  echo "[install-timer] 실행 파일: $WIN_FETCH_CMD"

  # 기존 작업 제거 (존재할 경우)
  schtasks.exe /Delete /TN "$TASK_NAME" /F 2>/dev/null || true

  # 작업 등록: 분 단위 주기, 로그온 시 시작
  schtasks.exe /Create \
    /TN "$TASK_NAME" \
    /TR "\"$WIN_FETCH_CMD\" >> \"$WIN_LOG_FILE\" 2>&1" \
    /SC MINUTE \
    /MO "$INTERVAL_MIN" \
    /F

  echo ""
  echo "[install-timer] Done. Usage will be fetched every $INTERVAL."
  echo "[install-timer] Initial fetch..."
  "$FETCH_CMD" || true

elif [ "$OS_TYPE" = "Darwin" ]; then
  #── macOS: launchd LaunchAgent ────────────────────────────────
  LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
  PLIST_NAME="com.jin-claude.fetch-usage.plist"
  PLIST_DEST="$LAUNCH_AGENTS_DIR/$PLIST_NAME"
  PLIST_TEMPLATE="$REPO_DIR/launchd/$PLIST_NAME"
  VENV_BIN="$HOME/.claude/.venv/bin"
  LABEL="com.jin-claude.fetch-usage"
  GUI_DOMAIN="gui/$(id -u)"

  echo "[install-timer] macOS LaunchAgent 설치"
  echo "[install-timer] plist 대상: $PLIST_DEST"
  mkdir -p "$LAUNCH_AGENTS_DIR"

  # 템플릿에서 플레이스홀더를 치환하여 plist 생성
  sed -e "s|__VENV_BIN__|$VENV_BIN|g" \
      -e "s|__INTERVAL_SEC__|$INTERVAL_SEC|g" \
      -e "s|__HOME__|$HOME|g" \
      "$PLIST_TEMPLATE" > "$PLIST_DEST"

  # 기존 에이전트 제거 (존재할 경우)
  if launchctl print "$GUI_DOMAIN/$LABEL" &>/dev/null; then
    echo "[install-timer] 기존 에이전트 제거 중..."
    launchctl bootout "$GUI_DOMAIN/$LABEL" 2>/dev/null || true
  fi

  # 에이전트 등록
  echo "[install-timer] 에이전트 등록 중..."
  launchctl bootstrap "$GUI_DOMAIN" "$PLIST_DEST"

  echo ""
  echo "[install-timer] Done. Usage will be fetched every $INTERVAL."
  echo "[install-timer] Initial fetch..."
  "$VENV_BIN/fetch-claude-usage" || true

else
  echo "[install-timer] 지원하지 않는 OS: $OS_TYPE"
  echo "[install-timer] Linux(systemd) 또는 macOS(launchd)만 지원됩니다."
  exit 1
fi

echo "[install-timer] Check cache: cat ~/.claude/.usage-cache.json"
