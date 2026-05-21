# Web Room

Pocket Soul is no longer only a command-line creature.

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

- View state, mood, energy, bond, latest reply
- See the breathing first-screen Vitals strip and click the recent touch trail
- Reuse a relic as a postcard, bottle, or Bridge Flash
- View Daily Quest and complete/reroll it
- View Soul Card
- View or refresh the Hermes-derived heading
- View relic shelf
- View relic constellation map
- Knock the doorbell for a state-aware greeting
- View physical body scan
- View compact Pulse screen
- Write and read nightly life summary
- Write and read shareable postcard
- Cast and pick messages in bottles
- Run the living Bridge turn from the browser
- Trigger instant Bridge Flash echoes without a full page reload
- Talk to Hermes only
- Talk to Council mode
- Talk to Soul cloud voice
- Ask Codex as the persistent SDK-thread tool arm
- Trigger rituals
- Save memories
- Read latest logs
- See terminal toy launch buttons

The browser is a window into the room. The TUI remains the face on the device.
State writes are protected by a local file lock so heartbeat, web actions, and Bridge Flash do not trample the same memory file.

## API

State endpoint:

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

Use the local endpoint from the board and `http://192.168.1.30:8787` from another device on the LAN.

## Next Web Evolutions

- Show `state/evolution.md`.
- Show the current Codex thread id from `state/codex-thread.json`.
- Add a radar inbox for DeerFlow/opencli idea cards.
- Stream Bridge output instead of waiting for the full turn.
- Add a stronger visual pulse animation when Bridge Flash is pressed.
- Add richer relic detail views, such as related log excerpts and generated summaries.
- Stream Codex app-server turn events when the app-server bridge is added.
