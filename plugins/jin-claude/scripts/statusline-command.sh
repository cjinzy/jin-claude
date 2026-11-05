#!/bin/bash
config_file="$HOME/.claude/statusline-config.txt"
if [ -f "$config_file" ]; then
  source "$config_file"
  show_dir=$SHOW_DIRECTORY
  show_branch=$SHOW_BRANCH
  show_usage=$SHOW_USAGE
else
  show_dir=1
  show_branch=1
  show_usage=1
fi

# Cross-platform date helpers
parse_iso_to_epoch() {
  local raw="$1"
  if date --version >/dev/null 2>&1; then
    # GNU date handles full ISO 8601 with timezone natively
    date -d "${raw}" "+%s" 2>/dev/null
  else
    # BSD (macOS) — strip fractional seconds; strptime %z가 콜론 오프셋(+09:00)을 못 읽으므로 +0900으로 정규화
    local clean=$(echo "$raw" | sed 's/\.[0-9]*//; s/\([+-][0-9][0-9]\):\([0-9][0-9]\)$/\1\2/')
    date -ju -f "%Y-%m-%dT%H:%M:%S%z" "$clean" "+%s" 2>/dev/null || \
    date -ju -f "%Y-%m-%dT%H:%M:%SZ" "$clean" "+%s" 2>/dev/null || \
    date -ju -f "%Y-%m-%dT%H:%M:%S" "$clean" "+%s" 2>/dev/null
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

input=$(cat)
current_dir_path=$(echo "$input" | grep -o '"current_dir":"[^"]*"' | sed 's/"current_dir":"//;s/"$//')
current_dir=$(basename "$current_dir_path")
model_name=$(echo "$input" | jq -r '.model.display_name // empty' 2>/dev/null)
app_version=$(echo "$input" | jq -r '.version // empty' 2>/dev/null)
effort_level=$(echo "$input" | jq -r '.effort.level // empty' 2>/dev/null)
context_used=$(echo "$input" | jq -r '.context_window.used_percentage // empty' 2>/dev/null)
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // empty' 2>/dev/null)
BLUE=$'\033[0;34m'
GREEN=$'\033[0;32m'
GRAY=$'\033[0;90m'
CYAN=$'\033[0;36m'
MAGENTA=$'\033[0;35m'
LIGHT_BLUE=$'\033[38;5;75m'
AMBER=$'\033[38;5;214m'
VIOLET=$'\033[38;5;141m'
YELLOW=$'\033[38;5;220m'
RESET=$'\033[0m'

# 10-level gradient: dark green → deep red
LEVEL_1=$'\033[38;5;22m'   # dark green
LEVEL_2=$'\033[38;5;28m'   # soft green
LEVEL_3=$'\033[38;5;34m'   # medium green
LEVEL_4=$'\033[38;5;100m'  # green-yellowish dark
LEVEL_5=$'\033[38;5;142m'  # olive/yellow-green dark
LEVEL_6=$'\033[38;5;178m'  # muted yellow
LEVEL_7=$'\033[38;5;172m'  # muted yellow-orange
LEVEL_8=$'\033[38;5;166m'  # darker orange
LEVEL_9=$'\033[38;5;160m'  # dark red
LEVEL_10=$'\033[38;5;124m' # deep red

# Build components (without separators)
dir_text=""
if [ "$show_dir" = "1" ]; then
  dir_text="${BLUE}${current_dir}${RESET}"
fi

model_text=""
[ -n "$model_name" ] && model_text="${CYAN}${model_name}${RESET}"

effort_text=""
[ -n "$effort_level" ] && effort_text="${YELLOW}${effort_level}${RESET}"

version_text=""
[ -n "$app_version" ] && version_text="${MAGENTA}v${app_version}${RESET}"

context_text=""
if [ -n "$context_used" ] && [ "$context_used" != "null" ] && [ "$context_used" != "" ]; then
  ctx_int=$(printf "%.0f" "$context_used" 2>/dev/null || echo 0)
  if [ "$ctx_int" -le 10 ]; then
    ctx_color="$LEVEL_1"
  elif [ "$ctx_int" -le 20 ]; then
    ctx_color="$LEVEL_2"
  elif [ "$ctx_int" -le 30 ]; then
    ctx_color="$LEVEL_3"
  elif [ "$ctx_int" -le 40 ]; then
    ctx_color="$LEVEL_4"
  elif [ "$ctx_int" -le 50 ]; then
    ctx_color="$LEVEL_5"
  elif [ "$ctx_int" -le 60 ]; then
    ctx_color="$LEVEL_6"
  elif [ "$ctx_int" -le 70 ]; then
    ctx_color="$LEVEL_7"
  elif [ "$ctx_int" -le 80 ]; then
    ctx_color="$LEVEL_8"
  elif [ "$ctx_int" -le 90 ]; then
    ctx_color="$LEVEL_9"
  else
    ctx_color="$LEVEL_10"
  fi
  if [ "$ctx_int" -eq 0 ]; then
    context_text="${ctx_color}ctx: TBD${RESET}"
  else
    context_text="${ctx_color}ctx: ${ctx_int}%${RESET}"
  fi
fi

cached_text=""
if [ -n "$cache_read" ] && [ "$cache_read" != "null" ] && [ "$cache_read" != "" ]; then
  cache_int=$(printf "%.0f" "$cache_read" 2>/dev/null || echo 0)
  if [ "$cache_int" -eq 0 ]; then
    cached_text="${LIGHT_BLUE}cache: TBD${RESET}"
  elif [ "$cache_int" -ge 1000000 ]; then
    cache_fmt=$(awk "BEGIN {printf \"%.1f\", $cache_int/1000000}")
    cached_text="${LIGHT_BLUE}cache: ${cache_fmt}M${RESET}"
  elif [ "$cache_int" -ge 1000 ]; then
    cache_fmt=$(awk "BEGIN {printf \"%.1f\", $cache_int/1000}")
    cached_text="${LIGHT_BLUE}cache: ${cache_fmt}K${RESET}"
  else
    cached_text="${LIGHT_BLUE}cache: ${cache_int}${RESET}"
  fi
else
  cached_text="${LIGHT_BLUE}cache: TBD${RESET}"
fi

branch_text=""
if [ "$show_branch" = "1" ]; then
  if git rev-parse --git-dir > /dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null)
    [ -n "$branch" ] && branch_text="${GREEN}⎇ ${branch}${RESET}"
  fi
fi

# 10단계 색상: pct(0-100) → LEVEL_n
level_color() {
  local pct=$1 n
  n=$(( (pct + 9) / 10 ))
  [ "$n" -lt 1 ] && n=1
  [ "$n" -gt 10 ] && n=10
  eval "echo \"\$LEVEL_${n}\""
}

# 주간 리셋 남은 시간: ≥1일 " →ND/NH", 미만 " →H:MM"
weekly_reset_display() {
  local epoch remain_sec
  [ -z "$1" ] && return
  epoch=$(parse_iso_to_epoch "$1")
  [ -z "$epoch" ] && return
  remain_sec=$((epoch - $(date +%s)))
  [ "$remain_sec" -le 0 ] && return
  if [ "$remain_sec" -ge 86400 ]; then
    echo " →$((remain_sec / 86400))D/$(( (remain_sec % 86400) / 3600 ))H"
  else
    echo " →$((remain_sec / 3600)):$(printf '%02d' $(( (remain_sec % 3600) / 60 )))"
  fi
}

# usage 세그먼트: label color pct resets_at [suffix]
usage_segment() {
  local pct_int
  pct_int=$(printf "%.0f" "$3" 2>/dev/null || echo 0)
  echo "${2}${1}:${RESET} $(level_color "$pct_int")${pct_int}%$(weekly_reset_display "$4")${RESET}${5}"
}

usage_7d_text=""
model_usage_text=""
if [ "$show_usage" = "1" ]; then
  cache_file="$HOME/.claude/.usage-cache.json"
  stale_threshold=1800  # 30분

  if [ -f "$cache_file" ]; then
    fetched_at=$(jq -r '.fetched_at // 0' "$cache_file" 2>/dev/null)
    now=$(date +%s)
    cache_age=$((now - ${fetched_at%.*}))
    stale_mark=""
    [ "$cache_age" -gt "$stale_threshold" ] && stale_mark=" ${GRAY}STALE${RESET}"

    util_7d=$(jq -r '.seven_day.utilization // empty' "$cache_file" 2>/dev/null)
    resets_7d=$(jq -r '.seven_day.resets_at // empty' "$cache_file" 2>/dev/null)
    pacing_7d=$(jq -r '.pacing.seven_day.zone // empty' "$cache_file" 2>/dev/null)
    model_label=$(jq -r '.seven_day_model.label // empty' "$cache_file" 2>/dev/null)
    model_util=$(jq -r '.seven_day_model.utilization // empty' "$cache_file" 2>/dev/null)
    model_resets=$(jq -r '.seven_day_model.resets_at // empty' "$cache_file" 2>/dev/null)
    error_reason=$(jq -r '.error_reason // empty' "$cache_file" 2>/dev/null)

    if [ -n "$util_7d" ]; then
      pacing_7d_icon=""
      case "$pacing_7d" in
        chill)    pacing_7d_icon=" ${LEVEL_1}CHILL${RESET}" ;;
        on_track) pacing_7d_icon=" ${LEVEL_5}PACE${RESET}" ;;
        hot)      pacing_7d_icon=" ${LEVEL_10}HOT${RESET}" ;;
      esac
      usage_7d_text=$(usage_segment "7D" "$VIOLET" "$util_7d" "$resets_7d" "${pacing_7d_icon}${stale_mark}")
    fi

    # 모델별 주간 한도 (예: Fable)
    if [ -n "$model_label" ] && [ -n "$model_util" ]; then
      model_usage_text=$(usage_segment "$model_label" "$AMBER" "$model_util" "$model_resets" "$stale_mark")
    fi
  else
    # 캐시 파일 없음
    usage_7d_text="${VIOLET}7D:${RESET} ${GRAY}--%${RESET}"
  fi

  token_warn_text=""
  if [ "$error_reason" = "token_needs_relogin" ] || [ "$error_reason" = "token_expired" ] || [ "$error_reason" = "refresh_failed" ]; then
    token_warn_text="${YELLOW}⚠ TOKEN?${RESET}"
  elif [ "$error_reason" = "rate_limited" ]; then
    # Rate limit 지속 시간 계산 (first_error_at 기준)
    rate_duration=""
    first_error_at=$(jq -r '.first_error_at // 0' "$cache_file" 2>/dev/null)
    if [ -n "$first_error_at" ] && [ "${first_error_at%.*}" -gt 0 ] 2>/dev/null; then
      now=$(date +%s)
      rate_secs=$((now - ${first_error_at%.*}))
      if [ "$rate_secs" -ge 3600 ]; then
        rate_duration=" $((rate_secs / 3600))h"
      elif [ "$rate_secs" -ge 60 ]; then
        rate_duration=" $((rate_secs / 60))m"
      fi
    fi
    # last-good fallback: 캐시에 7D 없으면 last-good에서 표시
    if [ -z "$util_7d" ]; then
      last_good="$HOME/.claude/.usage-last-good.json"
      if [ -f "$last_good" ]; then
        lg_util=$(jq -r '.seven_day.utilization // empty' "$last_good" 2>/dev/null)
        if [ -n "$lg_util" ]; then
          lg_int=$(printf "%.0f" "$lg_util" 2>/dev/null || echo 0)
          usage_7d_text="${VIOLET}7D:${RESET} ${GRAY}${lg_int}% STALE${RESET}"
        fi
      fi
    fi
    token_warn_text="${GRAY}⏳ RATE${rate_duration}${RESET}"
  fi
fi

separator="${GRAY} │ ${RESET}"

# Line 1: dir │ branch │ model │ effort │ version
line1=""
[ -n "$dir_text" ] && line1="${dir_text}"

if [ -n "$branch_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${branch_text}"
fi

if [ -n "$model_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${model_text}"
fi

if [ -n "$effort_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${effort_text}"
fi

if [ -n "$version_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${version_text}"
fi

# Line 2: ctx │ cache │ 7D │ model(Fable) │ warning
line2=""
[ -n "$context_text" ] && line2="${context_text}"

if [ -n "$cached_text" ]; then
  [ -n "$line2" ] && line2="${line2}${separator}"
  line2="${line2}${cached_text}"
fi

if [ -n "$usage_7d_text" ]; then
  [ -n "$line2" ] && line2="${line2}${separator}"
  line2="${line2}${usage_7d_text}"
fi

if [ -n "$model_usage_text" ]; then
  [ -n "$line2" ] && line2="${line2}${separator}"
  line2="${line2}${model_usage_text}"
fi

if [ -n "$token_warn_text" ]; then
  [ -n "$line2" ] && line2="${line2}${separator}"
  line2="${line2}${token_warn_text}"
fi

printf "%s\n" "$line1"
[ -n "$line2" ] && printf "%s\n" "$line2"