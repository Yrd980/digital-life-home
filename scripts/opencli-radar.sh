#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
TOPIC="${*:-AI companion cyberdeck}"
OUT="state/radar-$(date +%Y%m%d-%H%M%S).md"
mkdir -p state
{
  echo "# OpenCLI Radar: $TOPIC"
  echo
  echo "## Hacker News"
  opencli hackernews search "$TOPIC" --limit 8 -f md 2>/dev/null || true
  echo
  echo "## Product Hunt AI Agents"
  opencli producthunt posts --category ai-agents --limit 8 -f md 2>/dev/null || true
  echo
  echo "## Product Hunt Productivity"
  opencli producthunt posts --category productivity --limit 8 -f md 2>/dev/null || true
} | tee "$OUT"
echo "$OUT" > state/radar-latest-path.txt
