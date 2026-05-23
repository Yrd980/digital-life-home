#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
( speaker-test -t sine -f 660 -l 1 >/dev/null 2>&1 & pid=$!; sleep 0.25; kill "$pid" >/dev/null 2>&1 || true ) || true
python3 - <<'PY'
import pocket_soul
prompt = "Wake up as Miri inside the WalnutPi room. Generate today's ritual: one greeting, one observation, and one small action that can be done immediately. Reply in English."
print(pocket_soul.ask_miri(prompt))
PY
