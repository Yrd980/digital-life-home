#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
PROMPT="${*:-}"
python3 - "$PROMPT" <<'PY'
import sys

import pocket_soul

prompt = sys.argv[1].strip() if len(sys.argv) > 1 else ""
print(pocket_soul.bridge_turn(prompt))
PY
