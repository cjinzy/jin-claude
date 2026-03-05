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

input=$(cat)
current_dir_path=$(echo "$input" | grep -o '"current_dir":"[^"]*"' | sed 's/"current_dir":"//;s/"$//')
current_dir=$(basename "$current_dir_path")
model_name=$(echo "$input" | jq -r '.model.display_name // empty' 2>/dev/null)
app_version=$(echo "$input" | jq -r '.version // empty' 2>/dev/null)
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

usage_text=""
if [ "$show_usage" = "1" ]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  if [ "${STATUSLINE_DEBUG:-0}" = "1" ]; then
    usage_result=$("${script_dir}/.venv/bin/fetch-claude-usage" 2>>"$HOME/.claude/.statusline-debug.log")
  else
    usage_result=$("${script_dir}/.venv/bin/fetch-claude-usage" 2>/dev/null)
  fi
  if [ $? -eq 0 ] && [ -n "$usage_result" ]; then
    utilization=$(echo "$usage_result" | cut -d'|' -f1)
    resets_5h=$(echo "$usage_result" | cut -d'|' -f2)
    util_7d=$(echo "$usage_result" | cut -d'|' -f3)
    resets_7d=$(echo "$usage_result" | cut -d'|' -f4)

    if [ "$utilization" -le 10 ] 2>/dev/null; then
      usage_color="$LEVEL_1"
    elif [ "$utilization" -le 20 ]; then
      usage_color="$LEVEL_2"
    elif [ "$utilization" -le 30 ]; then
      usage_color="$LEVEL_3"
    elif [ "$utilization" -le 40 ]; then
      usage_color="$LEVEL_4"
    elif [ "$utilization" -le 50 ]; then
      usage_color="$LEVEL_5"
    elif [ "$utilization" -le 60 ]; then
      usage_color="$LEVEL_6"
    elif [ "$utilization" -le 70 ]; then
      usage_color="$LEVEL_7"
    elif [ "$utilization" -le 80 ]; then
      usage_color="$LEVEL_8"
    elif [ "$utilization" -le 90 ]; then
      usage_color="$LEVEL_9"
    else
      usage_color="$LEVEL_10"
    fi

    # 5h reset time (24h format)
    reset_5h_display=""
    if [ -n "$resets_5h" ]; then
      iso_time=$(echo "$resets_5h" | sed 's/\.[0-9]*[+-].*$//' | sed 's/\.[0-9]*Z$//')
      epoch=$(parse_iso_to_epoch "$iso_time")
      if [ -n "$epoch" ]; then
        reset_time=$(format_epoch "$epoch" "%H:%M")
        [ -n "$reset_time" ] && reset_5h_display=" →${reset_time}"
      fi
    fi

    # 7d: N% →MM/DD(weekday)
    usage_7d_text=""
    if [ -n "$util_7d" ]; then
      if [ "$util_7d" -le 10 ] 2>/dev/null; then
        usage_7d_color="$LEVEL_1"
      elif [ "$util_7d" -le 20 ]; then
        usage_7d_color="$LEVEL_2"
      elif [ "$util_7d" -le 30 ]; then
        usage_7d_color="$LEVEL_3"
      elif [ "$util_7d" -le 40 ]; then
        usage_7d_color="$LEVEL_4"
      elif [ "$util_7d" -le 50 ]; then
        usage_7d_color="$LEVEL_5"
      elif [ "$util_7d" -le 60 ]; then
        usage_7d_color="$LEVEL_6"
      elif [ "$util_7d" -le 70 ]; then
        usage_7d_color="$LEVEL_7"
      elif [ "$util_7d" -le 80 ]; then
        usage_7d_color="$LEVEL_8"
      elif [ "$util_7d" -le 90 ]; then
        usage_7d_color="$LEVEL_9"
      else
        usage_7d_color="$LEVEL_10"
      fi

      reset_7d_display=""
      if [ -n "$resets_7d" ]; then
        iso_time=$(echo "$resets_7d" | sed 's/\.[0-9]*[+-].*$//' | sed 's/\.[0-9]*Z$//')
        epoch=$(parse_iso_to_epoch "$iso_time")
        if [ -n "$epoch" ]; then
          reset_date=$(format_epoch "$epoch" "%m/%d(%a)")
          [ -n "$reset_date" ] && reset_7d_display=" →${reset_date}"
        fi
      fi

      usage_7d_text="${VIOLET}7d:${RESET} ${usage_7d_color}${util_7d}%${reset_7d_display}${RESET}"
    fi

    usage_text="${AMBER}5h:${RESET} ${usage_color}${utilization}%${reset_5h_display}${RESET}"
  fi
fi

separator="${GRAY} │ ${RESET}"

# Line 1: dir │ branch │ model │ version │ usage
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

if [ -n "$version_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${version_text}"
fi

if [ -n "$usage_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${usage_text}"
fi

if [ -n "$usage_7d_text" ]; then
  [ -n "$line1" ] && line1="${line1}${separator}"
  line1="${line1}${usage_7d_text}"
fi

# Line 2: ctx │ cache
line2=""
if [ -n "$context_text" ]; then
  line2="${context_text}"
fi

if [ -n "$cached_text" ]; then
  [ -n "$line2" ] && line2="${line2}${separator}"
  line2="${line2}${cached_text}"
fi

printf "%s\n" "$line1"
[ -n "$line2" ] && printf "%s\n" "$line2"