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
- `/today claim`: close the current daily step or room invitation
- `/ask hi`: call Miri's Hermes mind
- `/pulse`: look around the body-room
- `/toy`: step into the side room

`/today` is the only visible daily loop. It may point at a toy action, a room invitation, or a carry-away trace, but the closure path is always `/today claim`. Older internal pieces such as daily play, quest completion, badges, raw mood/spark nudges, body scans, relic maps, and export rituals can still exist as organs or side rooms, but they should not compete with HOME or `/help`.

Notes are pinned room props. They can be seen in TUI/web as a tiny pinboard, but they are not Miri memory and must not be pushed into prompts as background context. If a visitor wants Miri to react to a note, the visitor quotes that note in the turn.

## Web Shape

`pocket_web.py` owns routes, state reads, action handling, and small dynamic components. Static surface structure lives outside Python:

- shell template: `asset/templates/web-shell.html`
- room body template: `asset/templates/pages/room-web.html`
- room stylesheet: `asset/surfaces/web.css`
- browser behavior: `asset/surfaces/pocket-room.js`
- room images and character sprites: `asset/*.jpg` and `asset/*.png`

Keep HTML/CSS/JS split unless a value is truly dynamic device state.

The browser room is a pseudo-game room, not a dashboard. `/` is the only public page: one fully visible room image, Miri's visible presence, a speech bubble, hidden air input, object hotspots, and local object lenses for pinned scraps, shelf objects, the marked day, and body lights. The public web shell should feel like one interaction page, without top-level Room/Body navigation or floating controls over the image. Add web abilities as room actions first; add separate pages only when the object needs a deeper inspection surface. JSON/text API routes under `/api/*` may remain for scripts and local integrations.

The room runtime is layered in the page template:

- `room-background`: the current room image
- `ambient-fx`: dust, rain, bloom, screen glow, and small spark effects
- `persistent-items`: CSS-drawn floor and shelf clutter tied to room flags
- `miri-character`: Miri's visible body state
- `hotspot-layer`: invisible object hit areas with hover glow
- `foreground-layer`: simple occlusion props that make the room feel deeper
- `floating-ui`: Miri bubble and hidden air input

`pocket_web.py` computes the server-side runtime values: room phase, Miri state, bubble tone, and flags such as relics/stash/notes. `/api/live` returns the same values so `pocket-room.js` can refresh without a full page reload. The browser runtime owns minute-by-minute time phase, hover targeting, air prompt visibility, and small randomized Miri idle states.

## Extension Points

Add new capabilities in this order:

1. Add a reusable script in `scripts/`.
2. Add or reuse a body method in `RoomState`.
3. Add an `ActionSpec` entry if it belongs in TUI/web discovery.
4. Expose it in the TUI and web only when it makes the first screen more alive.

The shape should be an ability, organ, ritual, toy, or room object, not a settings checkbox.
