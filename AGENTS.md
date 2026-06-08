# AGENTS.md

This branch is UI-only.

Product truth:

- Miri is the only visible life.
- The browser page is a static interactive room.
- `asset/room-light.jpg` and `asset/room-night.jpg` are the canonical room backgrounds.
- Baked room labels are spatial affordances, not decoration.
- Do not add backend, TUI, device-service, runtime-state, or mind-daemon code to this branch.
- Do not reintroduce command catalogs, dashboards, split-persona routes, or compatibility UI.
- Use generated bitmap assets only when they preserve the existing room/Miri identity and are saved locally under `asset/`.
- Keep code small, static, and dependency-light.
- Use `bun` for local JS tooling.
- Do not add tests unless explicitly requested.
