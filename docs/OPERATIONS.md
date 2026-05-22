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

## Check

```sh
systemctl status miri-mind --no-pager -l
systemctl status pocket-soul-web --no-pager -l
curl -sS http://127.0.0.1:8791/health
curl -sS http://127.0.0.1:8787/api/live
pocket-miri "say one short line about your body"
```

## Device Rules

- Miri speaks English on the WalnutPi screen.
- `state/miri-home/` is Miri's mind profile and runtime memory.
- `state/soul.json` is the body memory and room state.
- Logs are room traces, not product analytics.
- Do not reintroduce split-persona routes.
