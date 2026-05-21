#!/usr/bin/env bash
set -euo pipefail
TOPIC="${*:-Pocket Soul Deck AI companion cyberdeck}"
SKILL_DIR="/root/.hermes/skills/last30days-skill"
if [[ ! -f "$SKILL_DIR/scripts/last30days.py" ]]; then
  echo "last30days engine not found at $SKILL_DIR"
  exit 1
fi
cd "$SKILL_DIR"
export LAST30DAYS_MEMORY_DIR="/root/digital-life-home/state/last30days"
mkdir -p "$LAST30DAYS_MEMORY_DIR"
python3 scripts/last30days.py "$TOPIC" --emit=compact --quick 2>&1 | tee "/root/digital-life-home/state/last30days/latest.txt"
