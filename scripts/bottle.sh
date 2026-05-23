#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
python3 - "$*" <<'PY'
import sys
import pocket_soul

wish = sys.argv[1].strip() if len(sys.argv) > 1 else ""
state = pocket_soul.RoomState.load()
print(state.bottle_message(wish))
state.save()
PY
