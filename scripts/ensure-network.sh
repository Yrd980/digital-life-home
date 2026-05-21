#!/usr/bin/env bash
set -euo pipefail
if curl -fsS --max-time 10 https://github.com >/dev/null; then
  echo "network ok"
  exit 0
fi
cd /opt
if [[ ! -d clash-for-linux-install ]]; then
  git clone --branch master --depth 1 https://gh-proxy.org/https://github.com/nelvko/clash-for-linux-install.git
fi
cd clash-for-linux-install
if [[ -z "${CLASH_SUBSCRIBE_URL:-}" ]]; then
  echo "network unavailable and CLASH_SUBSCRIBE_URL is not set"
  exit 1
fi
export URL="$CLASH_SUBSCRIBE_URL"
bash install.sh
