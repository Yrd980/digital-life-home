#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
PROMPT="${*:-}"
if [[ -z "$PROMPT" ]]; then
  uv run python - <<'PY'
import pocket_soul

print("Miri mind. Ctrl-D exits.")
while True:
    try:
        prompt = input("> ").strip()
    except EOFError:
        print()
        break
    if prompt:
        print(pocket_soul.run_miri(prompt))
PY
  exit 0
fi
uv run python - "$PROMPT" <<'PY'
import sys
import pocket_soul

print(pocket_soul.run_miri(sys.argv[1]))
PY
