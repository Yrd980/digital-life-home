# Miri Deck UI

This branch is the UI-only room for Miri Deck.

It contains a static browser experience:

- one full-room visual surface
- Miri as the only visible life
- baked room labels as spatial affordances
- local hover, touch, keyboard, bubble, and object-lens interactions
- local assets under `asset/`

There is no Python backend, TUI, device service, mind daemon, runtime state, or deployment script in this branch.

## Open

Open `index.html` in a browser.

For a local server:

```sh
bun run dev
```

Then open `http://127.0.0.1:8787`.

## Files

- `index.html`: static room entry
- `asset/surfaces/web.css`: room material, layout, and animation
- `asset/surfaces/pocket-room.js`: local page interactions
- `asset/room-light.jpg`, `asset/room-night.jpg`: canonical room backgrounds
- `asset/*.png`, `asset/*.jpg`: Miri states and visual references
- `asset/pieces/*.webp`: object-lens pieces
- `docs/UI_UX.md`: UI direction and asset rules

## Product Rule

The page should feel like touching a digital-life room, not using a dashboard or command app.
