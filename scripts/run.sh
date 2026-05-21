#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(dirname "$(readlink -f "$0")")")"
export TERM="${TERM:-linux}"
export LANG="${LANG:-C.UTF-8}"
export LC_ALL="${LC_ALL:-C.UTF-8}"
exec python3 pocket_soul.py "$@"
