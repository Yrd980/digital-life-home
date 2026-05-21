#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
python3 - "$@" <<'PY'
import sys
import pocket_soul

date = sys.argv[1] if len(sys.argv) > 1 else ""
state = pocket_soul.SoulState.load()
print(state.nightly_summary(date))
state.save()
PY
