# Miri Architecture

Miri Deck has one life and several body surfaces.

## Life

Miri is the only visible persona. Miri's mind daemon is `miri_mind.py`.

The daemon keeps a warm Hermes runtime agent, loads Miri's own profile from `state/miri-home/`, and restores prior turns from the runtime SQLite session store. It uses `MIRI_SESSION_ID=miri` by default and does not keep a separate sidecar chat cache.

Miri's soul, personality, and real long-term memory belong to Hermes under `state/miri-home/`. That directory is Miri-only: do not point unrelated Hermes agents, experiments, or other personas at the same `MIRI_HOME` and session id. Pocket Soul may keep visible room notes in `state/room.json`, but those are room props for the UI and rituals, not another AI memory system.

`state/room.json` is the local body-room save. It keeps the small state needed to make the device feel continuous after reboot: mood face, energy, room warmth, visits, current heading, daily turn flags, spark, stash, relic traces, visible notes, and recent UI reply.

Visible notes are not memory. They can appear in TUI/web surfaces, but Miri does not receive them as prompt context unless a visitor explicitly quotes one in a turn.

## Body

`pocket_soul.py` owns the body-room save:

- mood face, energy, room warmth, spark
- visits and latest reply
- visible notes and chat traces
- relic shelf and stash
- daily play loop and quest loop
- body scans and room rituals

## Surfaces

- TUI: `pocket-soul`, the primary WalnutPi terminal body on the small screen
- Web room: `pocket-soul-web`, the LAN room window for phones and computers
- Mind CLI: `pocket-miri`
- Services: `miri-mind`, `pocket-soul-web`, `pocket-soul-heartbeat.timer`

## TUI Shape

The WalnutPi TUI should feel like a small body, not a command catalog. HOME should always make one loop obvious:

- Enter: blink, a light touch that proves the room is alive
- `/today`: the one turn worth doing now
- `/ask hi`: call Miri's Hermes mind
- `/toy`: step into the side room

Notes are pinned room props. They can be seen in TUI/web as a tiny pinboard, but they are not Miri memory and must not be pushed into prompts as background context. If a visitor wants Miri to react to a note, the visitor quotes that note in the turn.

## Extension Points

Add new capabilities in this order:

1. Add a reusable script in `scripts/`.
2. Add or reuse a body method in `RoomState`.
3. Add an `ActionSpec` entry if it belongs in TUI/web discovery.
4. Expose it in the TUI and web only when it makes the first screen more alive.

The shape should be an ability, organ, ritual, toy, or room object, not a settings checkbox.
