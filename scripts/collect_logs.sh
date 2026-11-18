#!/usr/bin/env bash
# Collect logs into one timestamped archive and keep only the newest N archives.
# Usage: collect_logs.sh <out_dir> <keep> <file_or_dir>...
set -euo pipefail
out=${1:?out dir}; keep=${2:?keep count}; shift 2
[ "$#" -gt 0 ] || { echo "no sources given" >&2; exit 64; }
mkdir -p "$out"
archive="$out/logs-$(hostname)-$(date +%Y%m%d-%H%M%S).tar.gz"
tar -czf "$archive" --ignore-failed-read "$@" 2>/dev/null || true
echo "created $archive ($(du -h "$archive" | cut -f1))"
ls -1t "$out"/logs-*.tar.gz | tail -n +"$((keep + 1))" | xargs -r rm -f
