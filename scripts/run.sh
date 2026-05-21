#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(dirname "$(readlink -f "$0")")")"
export TERM="${TERM:-linux}"
exec python3 pocket_soul.py "$@"
