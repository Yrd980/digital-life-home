#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(dirname "$(readlink -f "$0")")")"
exec codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox "$@"
