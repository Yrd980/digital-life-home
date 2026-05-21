# Web Room

Pocket Soul is no longer only a command-line creature.

## Behavior Layers

The browser should feel like a nearby window into the room, not a control panel.

Use the same three visitor depths here:

- Light Touch: instant proof of life — Bridge Flash, doorbell, quick quest/heading glances
- Dwell: pulse, body, Soul Card, relic trail, map, and latest traces
- Deep Turn: shared Bridge wish, ask flows, postcard/bottle/nightly rituals

The web cockpit should invite these in order:
- touch first
- stay second
- deep turn third

Bridge Flash is the primary Light Touch.
The shared Bridge wish is the primary Deep Turn.

The web room runs at:

```text
http://192.168.1.30:8787
```

Service:

```bash
systemctl status pocket-soul-web
systemctl restart pocket-soul-web
```

Capabilities:

### Touch the room
- See the breathing first-screen Vitals strip and click the recent touch trail
- Knock the doorbell for a state-aware greeting
- Trigger instant Bridge Flash echoes without a full page reload
- View Daily Quest and complete/reroll it
- View or refresh the Hermes-derived heading

### Stay with the room
- View state, mood, energy, bond, latest reply
- View Soul Card
- View relic shelf
- View relic constellation map
- View physical body scan
- View compact Pulse screen
- Read latest logs
- See room-presence toy launch buttons; keep arcade and utility toys one move away

### Take a real turn
- Reuse a relic as a postcard, bottle, or Bridge Flash
- Write and read nightly life summary
- Write and read shareable postcard
- Cast and pick messages in bottles
- Run the living Bridge turn from the browser
- Talk to Hermes only
- Talk to Council mode
- Talk to Soul cloud voice
- Ask Codex as the persistent SDK-thread tool arm
- Trigger rituals
- Save memories
- Use the AI-native cockpit first screen: current heading, next action, shared Bridge wish, quick layer talk, Bridge Flash, live vitals, and thinking phase

For toy grouping, see `docs/TOY_ROLES.md`.

The browser is a window into the room. The TUI remains the face on the device.
State writes are protected by a local file lock so heartbeat, web actions, and Bridge Flash do not trample the same memory file.

## API

Think of the endpoints in the same three depths.

### Touch endpoints

```bash
curl -sS http://127.0.0.1:8787/api/live | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/doorbell
curl -sS http://127.0.0.1:8787/api/bridge-flash
curl -sS -X POST http://127.0.0.1:8787/api/bridge-flash --data-urlencode 'wish=blink'
curl -sS http://127.0.0.1:8787/api/heading
```

### Stay endpoints

```bash
curl -sS http://127.0.0.1:8787/api/state | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/live | python3 -m json.tool
```

Soul Card endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/card
```

Heading endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/heading
```

Relics endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/relics | python3 -m json.tool
curl -sS 'http://127.0.0.1:8787/api/relic?id=0' | python3 -m json.tool
```

Map endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/map
```

Doorbell endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/doorbell
```

Body endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/body | python3 -m json.tool
```

Pulse endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/pulse
```

Nightly endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/nightly
```

Postcard endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/postcard
```

Bottle endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/bottle
```

Latest Bridge endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/bridge
```

Bridge Flash endpoint:

```bash
curl -sS http://127.0.0.1:8787/api/bridge-flash
curl -sS -X POST http://127.0.0.1:8787/api/bridge-flash --data-urlencode 'wish=blink'
```

### Deep Turn endpoints

Use these when you want the room to leave or transform a more durable trace:

```bash
curl -sS http://127.0.0.1:8787/api/nightly
curl -sS http://127.0.0.1:8787/api/postcard
curl -sS http://127.0.0.1:8787/api/bottle
curl -sS http://127.0.0.1:8787/api/bridge
```

Use the local endpoint from the board and `http://192.168.1.30:8787` from another device on the LAN.

## Next Web Evolutions

- Show `state/evolution.md` inside the cockpit.
- Show the current Codex thread id from `state/codex-thread.json`.
- Add a radar inbox for DeerFlow/opencli idea cards.
- Stream Bridge output instead of waiting for the full turn.
- Add a stronger visual pulse animation when Bridge Flash is pressed.
- Add richer relic detail views, such as related log excerpts and generated summaries.
- Stream Codex app-server turn events when the app-server bridge is added.
