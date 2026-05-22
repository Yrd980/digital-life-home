#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cat > /etc/systemd/system/pocket-soul-web.service <<SERVICE
[Unit]
Description=Miri Deck Web Room
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=/usr/local/bin/pocket-soul-web
Restart=always
RestartSec=3
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
printf "Installed pocket-soul-web.service. Enable with: systemctl enable --now pocket-soul-web\n"
