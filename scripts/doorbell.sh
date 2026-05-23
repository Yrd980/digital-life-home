#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
python3 - <<'PY'
import pocket_soul

state = pocket_soul.RoomState.load()
print(state.doorbell("cli"))
state.save()
PY
