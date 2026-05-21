#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
export PATH="$PATH:/usr/games"
if [[ "${1:-}" == "--list" || -z "${1:-}" ]]; then
  python3 - <<'PY'
import pocket_soul
for name, command, argv, desc in pocket_soul.available_toys():
    print(f"{name:10} {command:16} {desc}")
PY
  exit 0
fi
python3 - "$1" <<'PY'
import sys
import pocket_soul
name = sys.argv[1].lower()
for toy_name, _command, argv, _desc in pocket_soul.available_toys():
    if name in (toy_name, _command):
        raise SystemExit(__import__('subprocess').call(argv))
print(f"Unknown toy: {name}")
print("Run scripts/toys.sh --list")
raise SystemExit(2)
PY
