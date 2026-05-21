#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
PROMPT="${*:-}"
if [[ -z "$PROMPT" ]]; then
  exec hermes chat
fi
exec hermes -z "$PROMPT"
