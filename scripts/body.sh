#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
python3 - <<'PY'
import pocket_soul

print(pocket_soul.body_text())
print()
print(pocket_soul.body_whisper())
PY
