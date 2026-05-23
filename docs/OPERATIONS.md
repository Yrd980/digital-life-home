# Operations

## Install

```sh
scripts/install-bin.sh
scripts/install-miri-service.sh
scripts/install-web-service.sh
scripts/install-heartbeat-service.sh
systemctl enable --now miri-mind
systemctl enable --now pocket-soul-web
systemctl enable --now pocket-soul-heartbeat.timer
```

For local development without systemd:

```sh
scripts/mind-dev.sh start
scripts/web-dev.sh start
```

## Check

```sh
systemctl status miri-mind --no-pager -l
systemctl status pocket-soul-web --no-pager -l
scripts/mind-dev.sh status
scripts/web-dev.sh status
curl -sS http://127.0.0.1:8791/health
curl -sS http://127.0.0.1:8787/api/live
pocket-miri "say one short line about your body"
```

## Device Rules

- Miri speaks English on the WalnutPi screen.
- `state/miri-home/` is Miri's dedicated Hermes mind profile and long-term runtime memory. Do not share it with unrelated agents or sessions.
- `state/room.json` is the local body-room save: UI state, daily loops, relic traces, stash, and visible notes. It is not Miri's soul, personality, or long-term memory.
- Notes are a visible pinboard. They do nothing to Miri's context unless the visitor quotes one in a turn.
- Logs are room traces, not product analytics.
- Do not reintroduce split-persona routes.
