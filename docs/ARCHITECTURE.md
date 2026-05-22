# Miri Architecture

Miri Deck has one life and several body surfaces.

## Life

Miri is the only visible persona. Miri's mind daemon is `miri_mind.py`.

The daemon keeps a warm runtime agent, loads Miri's own profile from `state/miri-home/`, and restores prior turns from the runtime SQLite session store. It does not keep a separate sidecar chat cache.

## Body

`pocket_soul.py` owns the body state:

- mood, energy, bond, spark
- visits and latest reply
- local memories and chat traces
- relic shelf and stash
- daily play loop and quest loop
- body scans and room rituals

## Surfaces

- TUI: `pocket-soul`
- Web room: `pocket-soul-web`
- Mind CLI: `pocket-miri`
- Services: `miri-mind`, `pocket-soul-web`, `pocket-soul-heartbeat.timer`

## Extension Points

Add new capabilities in this order:

1. Add a reusable script in `scripts/`.
2. Add or reuse a body method in `SoulState`.
3. Add an `ActionSpec` entry if it belongs in TUI/web discovery.
4. Expose it in the TUI and web only when it makes the first screen more alive.

The shape should be an ability, organ, ritual, toy, or room object, not a settings checkbox.
