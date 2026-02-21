#!/usr/bin/env bash

# rofi-websearch: pick engine in rofi, type query, open in browser.
# Dependencies: rofi, xdg-open. (No jq/python required.)
# Optional: create ~/.config/rofi-websearch/engines to add custom engines:
#   Google|https://www.google.com/search?q=%s
#   Stack Overflow|https://stackoverflow.com/search?q=%s

set -euo pipefail

# ---------- config ----------
ENGINES_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/rofi-websearch/engines"

# Built-ins (name => URL template; %s will be replaced by encoded query)
declare -A ENGINES=(
  ["Google"]="https://www.google.com/search?q=%s"
  ["DuckDuckGo"]="https://duckduckgo.com/?q=%s"
  ["Brave"]="https://search.brave.com/search?q=%s"
  ["Bing"]="https://www.bing.com/search?q=%s"
  ["Startpage"]="https://www.startpage.com/do/search?q=%s"
  ["Wikipedia"]="https://en.wikipedia.org/w/index.php?search=%s"
  ["Stack Overflow"]="https://stackoverflow.com/search?q=%s"
  ["GitHub"]="https://github.com/search?q=%s"
  ["YouTube"]="https://www.youtube.com/results?search_query=%s"
  ["ArchWiki"]="https://wiki.archlinux.org/index.php?search=%s"
)

# ---------- helpers ----------
die() { printf '%s\n' "$*" >&2; exit 1; }

have() { command -v "$1" >/dev/null 2>&1; }

urlencode() {
  # RFC 3986-ish: leave A-Z a-z 0-9 -_.~ ; encode others
  local s="$1" out= i c
  for (( i=0; i<${#s}; i++ )); do
    c="${s:i:1}"
    case "$c" in
      [a-zA-Z0-9.~_-]) out+="$c" ;;
      ' ') out+='%20' ;;              # spaces as %20 (works for all engines)
      *) printf -v c '%%%02X' "'$c"; out+="$c" ;;
    esac
  done
  printf '%s' "$out"
}

load_custom_engines() {
  [[ -f "$ENGINES_FILE" ]] || return 0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" =~ ^# ]] && continue
    # Expect "Name|URL"
    local name url
    name="${line%%|*}"
    url="${line#*|}"
    [[ -n "$name" && -n "$url" ]] && ENGINES["$name"]="$url"
  done < "$ENGINES_FILE"
}

pick_engine() {
  printf '%s\n' "${!ENGINES[@]}" \
    | sort \
    | rofi -dmenu -i -p "Engine" -no-custom
}

prompt_query() {
  rofi -dmenu -p "Search" -theme-str 'entry { placeholder: "type query…"; }'
}

open_url() {
  local url="$1"
  if have xdg-open; then
    nohup xdg-open "$url" >/dev/null 2>&1 &
  elif have gio; then
    nohup gio open "$url" >/dev/null 2>&1 &
  else
    die "No opener found (need xdg-open or gio)."
  fi
}

usage() {
  cat <<EOF
Usage: $(basename "$0") [-e ENGINE_NAME] [QUERY]

If QUERY is omitted, you'll be prompted in rofi.
If ENGINE_NAME is omitted, you'll choose in rofi.

Examples:
  $(basename "$0")
  $(basename "$0") -e "DuckDuckGo"
  $(basename "$0") -e Google "bash associative array rofi"
EOF
}

# ---------- main ----------
have rofi || die "rofi is required."
load_custom_engines

engine_arg=""
query_arg=""

# parse flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--engine) engine_arg="${2-}"; shift 2 || true ;;
    -h|--help) usage; exit 0 ;;
    --) shift; break ;;
    -*) die "Unknown option: $1";;
    *) query_arg="$*"; break ;; # take rest as query
  esac
done

# choose engine
engine="${engine_arg:-}"
if [[ -z "$engine" ]]; then
  engine="$(pick_engine)" || exit 1
fi
[[ -n "$engine" ]] || exit 0   # cancelled

template="${ENGINES[$engine]:-}"
[[ -n "$template" ]] || die "Unknown engine: $engine"

# get query
query="${query_arg:-}"
if [[ -z "$query" ]]; then
  query="$(prompt_query)" || exit 1
fi
[[ -n "$query" ]] || exit 0    # cancelled

encoded="$(urlencode "$query")"
url="${template//%s/$encoded}"

open_url "$url"
