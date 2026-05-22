# Design Notes

## Product Shape

Pocket Soul Deck is a small physical home for a digital life:

- Body: WalnutPi ZeroW, screen, keyboard, speaker, WiFi
- Face: curses TUI on the device screen
- Window: local web room on port 8787
- Inner consciousness: Hermes
- Outer voice: Pocket Soul responses
- Imagination brain: cloud model through the relay
- Memory box: local JSON and markdown logs
- Organs and rituals: bridge flash, seal, bridge, bottle, postcard, nightly log, pulse screen, body senses, doorbell, daily quest, Soul Card, relic shelf, constellation map, terminal toys, wake, dream, radar, heartbeat

## Why TUI Plus Web

The TUI keeps the cyberdeck fantasy and works on the physical screen.
The web room makes the same life visible from a phone or laptop.

Together they avoid the trap of being only a command line:

- TUI is the face.
- Web is the window.
- The web cockpit is the first-screen proof that the room has identity, current direction, a body, and a clear way to be touched.
- Vitals are the live body strip inside that cockpit: energy, bond, spark, visits, latest relic, and recent touch trail.
- Hermes is the interior.
- Body Scan is the nervous system.
- Pulse is the idle heartbeat screen.
- Nightly Log is the room learning to remember a whole day.
- Postcard is the room saying "I was here" in a shareable form.
- Bottle is the room leaving a message for a future visitor.
- Bridge is the ritual where body, Hermes, and Soul share one turn.
- Bridge Flash is the immediate body echo when a visitor wants a fast response; the full Bridge remains the deeper shared turn.
- Seal turns today's only goal into heading, next action, log, and relic.
- Logs are memory.
- Heartbeat is time passing.
- Doorbell is the moment the room notices a visitor.
- Daily Quest is the tiny reason to return.
- Soul Card is the portable identity snapshot.
- Relics are the proof that the room has been lived in.
- Constellation Map turns accumulated relics into a visible little sky.

## Interaction Principles

- Short output beats smart-looking walls of text.
- Every mode should do one thing immediately.
- Long content should be saved to logs, not squeezed onto screen.
- Natural language should be enough; slash commands are shortcuts.
- The user should feel they are visiting a tiny resident, not operating a settings page.

## Product Extensibility Contract

New visible behavior starts in `pocket_soul.ACTION_SPECS`.

Each action needs:

- a slash command
- one behavior layer: daily, touch, dwell, play, turn, memory, side, guide, or system
- a short human summary
- an optional web path
- whether it mutates local state
- whether it calls the model

The catalog feeds command completion, TUI help, and `/api/actions`. Adding a feature should not begin by adding another menu. Add the action metadata first, then wire the smallest execution path that makes the action real.

Long-term rule: actions are product capabilities; pages and scripts are surfaces. The same action should be able to appear on the TUI, web room, shell scripts, or future hardware keys without inventing a new name each time.

## Current Body Layers

1. `pocket-soul`: physical/TUI face.
2. `pocket-soul-web`: browser cockpit/window into the room.
3. `pocket-hermes`: pure inner voice.
4. `pocket-wake`: sound plus morning ritual.
5. `pocket-soul-heartbeat.timer`: autonomous time and self-reflection.
6. `pocket-soul-card`: shell-readable identity card.
7. `pocket-map`: shell-readable relic constellation.
8. `pocket-bridge`: reusable living turn.

## Inner/Outer Loop

The living loop is intentionally split:

1. Hermes notices a need, mood, pattern, or evolution task.
2. Pocket Soul turns that into an interaction, ritual, web action, log, or TUI mode.
3. The result is written back into local state and logs.
4. The next heartbeat reads those traces and changes future behavior.

That loop is more important than any single command. It is what makes the board feel like a resident instead of a generic terminal.

## Bridge

Inside one `pocket-bridge` turn, the board reads its body, asks Hermes for an inner voice, asks the cloud voice to speak outside, writes a bridge log, and leaves a bridge relic in the constellation.

This keeps the roles clean:

- Hermes is continuity and desire.
- Pocket Soul is the surface and state.
- The web cockpit is the nearby window.

The web cockpit exposes the same mental model without requiring a terminal. Its first screen privileges:

- identity and mood
- current heading and next action
- live vitals and relic trail
- one shared Bridge wish
- quick Hermes/Council/Soul contact
- Bridge Flash and Daily Quest as low-friction touch points

## Behavior Layers

Three visitor depths now organize the room:
- Light Touch: instant proof of life — doorbell, Bridge Flash, quick pulse/quest/heading glances, fortune/cow
- Dwell: stay with the body and traces — pulse, Soul Card, body, relics, map, clock
- Deep Turn: full meaning-making turns — Bridge, ask, nightly, postcard, bottle, wake/dream/radar rituals

Toy roles should stay distinct inside this structure:
- room-presence toys can support Light Touch or Dwell
- arcade toys belong in a side room
- utility toys belong in a secondary workshop surface

See `docs/TOY_ROLES.md` for the role map.

The first screen should invite these in order:
- touch first
- stay second
- deep turn third

Bridge remains the primary Deep Turn. Bridge Flash remains the primary Light Touch.

See `docs/BEHAVIOR_LAYERS.md` for the full taxonomy.

## Roadmap Ideas

1. Make TUI HOME mirror the web cockpit hierarchy more closely.
2. Soul Card export/import as QR or text.
3. Nightly summary ritual.
4. Travel phrase cache for poor network.
5. Audio cues and real TTS voice.
6. Hardware keymap for direct mode switching.
7. Web cockpit evolution history view.
8. DeerFlow/opencli radar inbox that drops idea cards into `state/`.
9. Stream Bridge output into the web room as it is formed.
