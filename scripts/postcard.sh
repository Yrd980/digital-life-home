#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
python3 - "$*" <<'PY'
import sys
import pocket_soul

title = sys.argv[1].strip() if len(sys.argv) > 1 else ""
state = pocket_soul.SoulState.load()
print(state.postcard(title))
state.save()
PY
