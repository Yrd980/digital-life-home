#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
PROMPT="${*:-}"
if [[ -z "$PROMPT" ]]; then
  echo "Usage: scripts/summon.sh <prompt>"
  exit 2
fi
python3 - "$PROMPT" <<'PY'
import sys
import pocket_soul
prompt = sys.argv[1]
print("== Hermes inner voice ==")
inner = pocket_soul.run_hermes(prompt)
print(inner)
print("\n== Pocket Soul council ==")
print(pocket_soul.council_reply(prompt, pocket_soul.SoulState.load().memories))
PY
