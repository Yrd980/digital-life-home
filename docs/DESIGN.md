# Design Notes

## Product Shape

Pocket Soul Deck is a small physical home for a digital life:

- Body: WalnutPi ZeroW, screen, keyboard, speaker, WiFi
- Face: curses TUI on the device screen
- Window: local web room on port 8787
- Inner consciousness: Hermes
- Outer voice: Pocket Soul responses
- Imagination brain: cloud model through the relay
- Tool arm: Codex SDK thread by default, one-shot Codex rescue when needed
- Memory box: local JSON and markdown logs
- Organs and rituals: bridge flash, seal, bridge, bottle, postcard, nightly log, pulse screen, body senses, doorbell, daily quest, Soul Card, relic shelf, constellation map, terminal toys, wake, dream, radar, heartbeat

## Why TUI Plus Web

The TUI keeps the cyberdeck fantasy and works on the physical screen.
The web room makes the same life visible from a phone or laptop.

Together they avoid the trap of being only a command line:

- TUI is the face.
- Web is the window.
- Vitals are the first-screen proof that the room has a body and recent touch trail.
- Hermes is the interior.
- Body Scan is the nervous system.
- Pulse is the idle heartbeat screen.
- Nightly Log is the room learning to remember a whole day.
- Postcard is the room saying "I was here" in a shareable form.
- Bottle is the room leaving a message for a future visitor.
- Bridge is the host-to-board ritual where body, Hermes, Soul, and Codex share one turn.
- Bridge Flash is the immediate body echo when a visitor wants a fast response.
- Seal turns today's only goal into heading, next action, log, and relic.
- Codex is the hand.
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
- Codex actions should feel like missions from the deck, not admin commands.
- The user should feel they are visiting a tiny resident, not operating a settings page.

## Current Body Layers

1. `pocket-soul`: physical/TUI face.
2. `pocket-soul-web`: browser window into the room.
3. `pocket-hermes`: pure inner voice.
4. `pocket-wake`: sound plus morning ritual.
5. `pocket-soul-heartbeat.timer`: autonomous time and self-reflection.
6. `codex-thread`: persistent SDK thread for the tool arm.
7. `codex-open`: one-shot rescue arm.
8. `pocket-soul-card`: shell-readable identity card.
9. `pocket-map`: shell-readable relic constellation.
10. `pocket-bridge`: reusable host/board communication loop.

## Inner/Outer Loop

The living loop is intentionally split:

1. Hermes notices a need, mood, pattern, or evolution task.
2. Pocket Soul turns that into an interaction, ritual, web action, log, or TUI mode.
3. Codex is called only when the room needs system action.
4. The result is written back into local state and logs.
5. The next heartbeat reads those traces and changes future behavior.

That loop is more important than any single command. It is what makes the board feel like a resident instead of a remote terminal.

## Host Bridge

From the host, the practical long-running connection is:

```bash
ssh walnutpi 'cd /root/digital-life-home && pocket-bridge "今天想怎么玩"'
```

SSH reuses the configured control socket. Inside that one turn, the board reads its body, asks Hermes for an inner voice, asks the persistent Codex SDK thread for a concrete tool-arm suggestion, asks the cloud voice to speak outside, writes a bridge log, and leaves a bridge relic in the constellation.

## Roadmap Ideas

1. Dynamic HOME with a daily quest and one-tap next action.
2. Soul Card export/import as QR or text.
3. Nightly summary ritual.
4. Travel phrase cache for poor network.
5. Audio cues and real TTS voice.
6. Hardware keymap for direct mode switching.
7. Web room evolution history view.
8. Hermes proposes changes, Codex implements them, heartbeat evaluates the result.
9. Direct app-server bridge for streaming Codex events into the web room.
10. Host-side DeerFlow/opencli radar inbox that drops idea cards into `state/`.
