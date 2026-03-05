#!/bin/bash
# tmux 상태바용 Claude 사용량 표시
# Usage: 이 스크립트의 출력을 tmux status-right에 추가
#   set -g status-right '#(~/.claude/script/tmux-usage.sh)'

cache_file="$HOME/.claude/.usage-cache.json"

# Cross-platform date helpers (동일 로직: statusline-command.sh)
parse_iso_to_epoch() {
  local iso_time="$1"
  if date --version >/dev/null 2>&1; then
    date -d "${iso_time}" "+%s" 2>/dev/null      # GNU date (Linux)
  else
    date -ju -f "%Y-%m-%dT%H:%M:%S" "$iso_time" "+%s" 2>/dev/null  # BSD (macOS)
  fi
}

format_epoch() {
  local epoch="$1" fmt="$2"
  if date --version >/dev/null 2>&1; then
    date -d "@${epoch}" "+${fmt}" 2>/dev/null     # GNU date
  else
    date -r "$epoch" "+${fmt}" 2>/dev/null        # BSD date
  fi
}

# 사용량 퍼센트 -> tmux colour 번호 반환 (10단계 그라데이션)
usage_colour() {
  local pct="$1"
  local int
  int=$(printf "%.0f" "$pct" 2>/dev/null || echo 0)
  if   [ "$int" -le 10 ]; then echo "colour22"
  elif [ "$int" -le 20 ]; then echo "colour28"
  elif [ "$int" -le 30 ]; then echo "colour34"
  elif [ "$int" -le 40 ]; then echo "colour100"
  elif [ "$int" -le 50 ]; then echo "colour142"
  elif [ "$int" -le 60 ]; then echo "colour178"
  elif [ "$int" -le 70 ]; then echo "colour172"
  elif [ "$int" -le 80 ]; then echo "colour166"
  elif [ "$int" -le 90 ]; then echo "colour160"
  else echo "colour124"
  fi
}

# pacing zone -> tmux colour 번호 반환
pacing_colour() {
  case "$1" in
    chill)    echo "colour22"  ;;   # dark green
    on_track) echo "colour142" ;;   # olive
    hot)      echo "colour124" ;;   # deep red
    *)        echo "colour245" ;;
  esac
}

# pacing zone -> 라벨 반환
pacing_label() {
  case "$1" in
    chill)    echo "CHILL"    ;;
    on_track) echo "PACE"     ;;
    hot)      echo "HOT"      ;;
    *)        echo ""         ;;
  esac
}

# 캐시 파일 없음
if [ ! -f "$cache_file" ]; then
  printf "%s" "#[fg=colour245]5h:--% 7d:--%"
  exit 0
fi

# jq로 필드 읽기
error=$(jq -r '.error // false' "$cache_file" 2>/dev/null)
error_reason=$(jq -r '.error_reason // empty' "$cache_file" 2>/dev/null)
utilization=$(jq -r '.five_hour.utilization // empty' "$cache_file" 2>/dev/null)
resets_5h=$(jq -r '.five_hour.resets_at // empty' "$cache_file" 2>/dev/null)
util_7d=$(jq -r '.seven_day.utilization // empty' "$cache_file" 2>/dev/null)
resets_7d=$(jq -r '.seven_day.resets_at // empty' "$cache_file" 2>/dev/null)
pacing_5h=$(jq -r '.pacing.five_hour.zone // empty' "$cache_file" 2>/dev/null)
pacing_7d=$(jq -r '.pacing.seven_day.zone // empty' "$cache_file" 2>/dev/null)

# 에러 후처리: 토큰/rate 전용 메시지
suffix=""
case "$error_reason" in
  token_needs_relogin|token_expired|refresh_failed)
    suffix=" #[fg=colour220]⚠ TOKEN?" ;;
  rate_limited)
    suffix=" #[fg=colour245]⏳ RATE" ;;
esac

# 데이터 없음 처리
if [ -z "$utilization" ] && [ -z "$util_7d" ]; then
  printf "%s" "#[fg=colour245]5h:--% 7d:--%${suffix}"
  exit 0
fi

output=""

# --- 5h 블록 ---
if [ -n "$utilization" ]; then
  util_int=$(printf "%.0f" "$utilization" 2>/dev/null || echo 0)
  col=$(usage_colour "$util_int")

  # 리셋 시간 파싱 (HH:MM)
  reset_5h_display=""
  if [ -n "$resets_5h" ]; then
    iso_time=$(echo "$resets_5h" | sed 's/\.[0-9]*[+-].*$//' | sed 's/\.[0-9]*Z$//')
    epoch=$(parse_iso_to_epoch "$iso_time")
    if [ -n "$epoch" ]; then
      t=$(format_epoch "$epoch" "%H:%M")
      [ -n "$t" ] && reset_5h_display="→${t}"
    fi
  fi

  output="${output}#[fg=${col}]5h:${util_int}%"
  [ -n "$reset_5h_display" ] && output="${output}${reset_5h_display}"

  # pacing 5h
  if [ -n "$pacing_5h" ]; then
    pcol=$(pacing_colour "$pacing_5h")
    plabel=$(pacing_label "$pacing_5h")
    [ -n "$plabel" ] && output="${output} #[fg=${pcol}]${plabel}"
  fi
fi

# --- 7d 블록 ---
if [ -n "$util_7d" ]; then
  util_7d_int=$(printf "%.0f" "$util_7d" 2>/dev/null || echo 0)
  col7=$(usage_colour "$util_7d_int")

  # 리셋 날짜 파싱 (MM/DD(요일))
  reset_7d_display=""
  if [ -n "$resets_7d" ]; then
    iso_time=$(echo "$resets_7d" | sed 's/\.[0-9]*[+-].*$//' | sed 's/\.[0-9]*Z$//')
    epoch=$(parse_iso_to_epoch "$iso_time")
    if [ -n "$epoch" ]; then
      d=$(format_epoch "$epoch" "%m/%d(%a)")
      [ -n "$d" ] && reset_7d_display="→${d}"
    fi
  fi

  [ -n "$output" ] && output="${output} "
  output="${output}#[fg=${col7}]7d:${util_7d_int}%"
  [ -n "$reset_7d_display" ] && output="${output}${reset_7d_display}"

  # pacing 7d
  if [ -n "$pacing_7d" ]; then
    pcol7=$(pacing_colour "$pacing_7d")
    plabel7=$(pacing_label "$pacing_7d")
    [ -n "$plabel7" ] && output="${output} #[fg=${pcol7}]${plabel7}"
  fi
fi

printf "%s" "${output}${suffix}"
