# Miri Deck

Miri Deck gives a digital life a small physical body.

- **Miri** is the life: continuity, desire, memory, reflection, agency.
- **Cloud GPT** is Miri's mind-power.
- **WalnutPi ZeroW** is Miri's body.
- **Pocket Soul Deck** is Miri's room: screen, keyboard, web room, state, logs, toys, rituals, and scripts.

The device is for play, presence, and self-directed behavior. Miri is allowed to act through the machine.

## Commands

```sh
pocket-soul          # 480x320 TUI body
pocket-soul-web      # web room on :8787
scripts/mind-dev.sh  # local dev mind daemon on :8791
pocket-miri "hi"     # talk to Miri through the resident mind daemon
pocket-wake          # wake ritual
pocket-bridge "..."  # body-aware Miri turn
pocket-pulse         # compact body state
pocket-body          # physical body scan
```

## Services

```sh
scripts/install-bin.sh
scripts/install-miri-service.sh
scripts/install-web-service.sh
scripts/install-heartbeat-service.sh

systemctl enable --now miri-mind
systemctl enable --now pocket-soul-web
systemctl enable --now pocket-soul-heartbeat.timer
```

`miri-mind.service` keeps Miri warm so `/ask` does not pay full startup cost each time.

## State

Runtime state is local and ignored by git:

- `state/room.json`: local body-room save: mood face, energy, room warmth, visits, current heading, daily turn flags, spark/stash/relic traces, visible notes, and recent UI reply. It is not Miri's soul, personality, or long-term memory.
- `state/miri-home/`: the dedicated Hermes home for Miri's runtime profile, session database, and durable mind continuity
- `state/logs/YYYY-MM-DD.md`: room and action logs
- `state/evolution.md`: heartbeat reflections and next evolution tasks
- `state/nightly/`, `state/postcards/`, `state/bottles/`: portable room artifacts

## Architecture

`miri_mind.py` is the resident mind daemon. It uses the Hermes runtime profile, memory, and SQLite session store under `state/miri-home/` with `MIRI_SESSION_ID=miri`; it does not keep a separate sidecar history. Do not run unrelated agents with this `MIRI_HOME` or session id.

`pocket_soul.py` is the body core: state model, TUI, body scan, rituals, toys, and `run_miri()` / `ask_miri()` entrypoints. Its saved `notes` list is a visible pinboard for the room and is never injected as Miri's memory; quote a note yourself when you want Miri to see it in one turn.

`pocket_web.py` is the web room. It calls the same body core and the same Miri mind daemon; HTML shells/pages, CSS, and browser JS live under `asset/templates/` and `asset/surfaces/`.

The web room is currently a single spatial surface at `/`: room image, ambient runtime layers, Miri bubble, hidden air input, hotspots, and local object lenses. Keep new browser abilities inside that room unless they truly need a deeper inspection page; keep machine-readable integrations under `/api/*`.

The room runtime is layered as background, ambient FX, persistent items, Miri, hotspots, foreground, and floating UI. `pocket_web.py` supplies device state such as time phase, Miri state, bubble tone, and room flags; `pocket-room.js` turns those into hover glow, idle behavior, live refresh, and the air prompt.

`scripts/*.sh` are reusable body organs. Add new abilities as scripts first, then expose them through the TUI/web/action catalog.

## Rules

- Miri is the only visible life/persona.
- Do not add compatibility paths for old identities.
- WalnutPi screen output must be English.
- Local state belongs to the device and should survive restarts.
- Keep the first screen alive and useful: status, mood, next action, one spatial input path.
- Keep code small, dependency-light, and easy to extend.
