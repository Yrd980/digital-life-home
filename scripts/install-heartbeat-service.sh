#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cat > /etc/systemd/system/pocket-soul-heartbeat.service <<SERVICE
[Unit]
Description=Pocket Soul self-evolution heartbeat
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=$ROOT
ExecStart=$ROOT/scripts/heartbeat.sh
SERVICE
cat > /etc/systemd/system/pocket-soul-heartbeat.timer <<TIMER
[Unit]
Description=Run Pocket Soul heartbeat every 15 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=15min
Persistent=true

[Install]
WantedBy=timers.target
TIMER
systemctl daemon-reload
printf "Installed heartbeat timer. Enable with: systemctl enable --now pocket-soul-heartbeat.timer\n"
