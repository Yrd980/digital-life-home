#!/usr/bin/env bash
set -euo pipefail
if curl -fsS --max-time 10 https://github.com >/dev/null; then
  echo "network ok"
  exit 0
fi
subscription_url="${CLASH_SUBSCRIPTION_URL:-}"
subscription_url_file="${CLASH_SUBSCRIPTION_URL_FILE:-/etc/miri/clash-subscription-url}"
if [[ -z "$subscription_url" && -r "$subscription_url_file" ]]; then
  subscription_url="$(<"$subscription_url_file")"
fi
if [[ -z "$subscription_url" ]]; then
  cat >&2 <<EOF
missing Clash subscription URL

Set CLASH_SUBSCRIPTION_URL, or put the URL in:
  $subscription_url_file

Override the file path with CLASH_SUBSCRIPTION_URL_FILE if needed.
EOF
  exit 1
fi
cd /opt
if [[ ! -d clash-for-linux-install ]]; then
  git clone --branch master --depth 1 https://gh-proxy.org/https://github.com/nelvko/clash-for-linux-install.git
fi
cd clash-for-linux-install
export URL="$subscription_url"
bash install.sh
