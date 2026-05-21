#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cat > /etc/systemd/system/pocket-soul.service <<SERVICE
[Unit]
Description=Pocket Soul Deck TUI
After=network-online.target
Wants=network-online.target
Conflicts=getty@tty1.service

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=/usr/local/bin/pocket-soul
Restart=always
RestartSec=3
StandardInput=tty
StandardOutput=tty
StandardError=tty
TTYPath=/dev/tty1
TTYReset=yes
TTYVTDisallocate=yes
Environment=TERM=linux
Environment=LANG=C.UTF-8
Environment=LC_ALL=C.UTF-8

[Install]
WantedBy=multi-user.target
SERVICE
systemctl daemon-reload
printf "Installed pocket-soul.service. Enable with: systemctl enable --now pocket-soul\n"
