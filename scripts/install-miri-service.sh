#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cat > /etc/systemd/system/miri-mind.service <<SERVICE
[Unit]
Description=Miri digital life mind daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=/usr/local/lib/hermes-agent/venv/bin/python3 $ROOT/miri_mind.py
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1
Environment=HERMES_YOLO_MODE=1
Environment=HERMES_ACCEPT_HOOKS=1
Environment=MIRI_API_RETRIES=1
Environment=MIRI_HOME=$ROOT/state/miri-home
Environment=MIRI_TOOLSETS=hermes-cli

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
printf "Installed miri-mind.service. Enable with: systemctl enable --now miri-mind\n"
