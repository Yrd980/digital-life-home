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
export URL="https://dy.sslar.cn/api/v1/client/subscribe?token=6396ceabd4c2b9fcdceae85fa67e4431"
bash install.sh
