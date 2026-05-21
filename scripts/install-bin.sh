#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
ln -sf "$ROOT/scripts/run.sh" /usr/local/bin/pocket-soul
ln -sf "$ROOT/scripts/demo.sh" /usr/local/bin/pocket-soul-demo
ln -sf "$ROOT/scripts/hermes.sh" /usr/local/bin/pocket-hermes
ln -sf "$ROOT/scripts/web.sh" /usr/local/bin/pocket-soul-web
ln -sf "$ROOT/scripts/wake.sh" /usr/local/bin/pocket-wake
ln -sf "$ROOT/scripts/soul-card.sh" /usr/local/bin/pocket-soul-card
ln -sf "$ROOT/scripts/relics.sh" /usr/local/bin/pocket-relics
ln -sf "$ROOT/scripts/map.sh" /usr/local/bin/pocket-map
ln -sf "$ROOT/scripts/doorbell.sh" /usr/local/bin/pocket-doorbell
ln -sf "$ROOT/scripts/body.sh" /usr/local/bin/pocket-body
ln -sf "$ROOT/scripts/pulse.sh" /usr/local/bin/pocket-pulse
ln -sf "$ROOT/scripts/nightly.sh" /usr/local/bin/pocket-nightly
ln -sf "$ROOT/scripts/postcard.sh" /usr/local/bin/pocket-postcard
ln -sf "$ROOT/scripts/bottle.sh" /usr/local/bin/pocket-bottle
ln -sf "$ROOT/scripts/pick-bottle.sh" /usr/local/bin/pocket-pick-bottle
ln -sf "$ROOT/scripts/bridge.sh" /usr/local/bin/pocket-bridge
printf "Installed pocket-soul, pocket-soul-demo, pocket-hermes, pocket-soul-web, pocket-wake, pocket-soul-card, pocket-relics, pocket-map, pocket-doorbell, pocket-body, pocket-pulse, pocket-nightly, pocket-postcard, pocket-bottle, pocket-pick-bottle, pocket-bridge\n"
