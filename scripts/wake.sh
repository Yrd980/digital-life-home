#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$ROOT"
( speaker-test -t sine -f 660 -l 1 >/dev/null 2>&1 & pid=$!; sleep 0.25; kill "$pid" >/dev/null 2>&1 || true ) || true
python3 - <<'PY'
import pocket_soul
prompt = '开机醒来。你是 WalnutPi 里的 Hermes 内在意识，请生成一个今日仪式：一句问候、一个观察、一个可以马上做的小动作。'
print(pocket_soul.council_reply(prompt, pocket_soul.SoulState.load().memories))
PY
