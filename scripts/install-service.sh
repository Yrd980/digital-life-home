#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cat > /etc/systemd/system/pocket-soul.service <<SERVICE
[Unit]
Description=Pocket Soul Deck TUI
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=/usr/bin/openvt -f -c 1 -- /usr/local/bin/pocket-soul
Restart=always
RestartSec=3
StandardInput=tty
TTYPath=/dev/tty1
Environment=TERM=linux

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
printf "Installed pocket-soul.service. Enable with: systemctl enable --now pocket-soul\n"
