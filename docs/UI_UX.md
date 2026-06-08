# Miri Deck UI/UX

This branch is a pure static Web UI.

The goal is one interactive browser room: Miri is present, the room can be touched, objects react locally, and no backend/TUI/device runtime is required.

## Product Target

Miri Deck UI should feel like an interactive diorama, not a dashboard, command app, chatbot shell, or settings surface.

First screen truth:

- the room image is the page
- Miri is the only visible life
- baked room labels are the navigation
- hover/tap/focus gives tactile feedback
- object lenses are temporary close-ups
- the bubble is Miri's current page voice

Do not add:

- Python backend
- TUI code
- device service scripts
- runtime state
- mind daemon code
- command catalogs
- split-persona routes
- dashboard navigation

## Asset Truth

Current visual truth lives in `asset/`.

Canonical room backgrounds:

- `asset/room-light.jpg`
- `asset/room-night.jpg`

Canonical room affordances baked into the images:

- `KNOCK`
- `PINBOARD`
- `SHELF`
- `DAILY`
- `BODY`
- `CRAFT`

Miri state assets:

- `asset/calm.png`
- `asset/happy.png`
- `asset/sleep.png`
- `asset/think.png`

Object source sheets:

- `asset/items.jpg`: mug, notebook, keyboard, cassette, screwdriver, star bottle, cable bundle, mini robot
- `asset/sticker.jpg`: todo note, thank-you note, photo note, polaroid, daily checklist

Cropped lens pieces:

- `asset/pieces/*.webp`

Reference assets:

- `asset/kawaii.jpg` for integrated room mood
- `asset/daily.jpg` and `asset/stick.jpg` for paper-note styling

Generated files under `output/` are not product truth and should not return to this branch.

## Page Interaction Model

The page is spatial. Users should not need to know implementation actions or slash commands.

Interaction priorities:

1. Room image and atmosphere
2. Miri
3. Miri bubble
4. Baked labels in the image
5. Hotspot glow
6. Temporary input or object lens

Page behavior:

- pointer movement creates a soft glow around active hotspots
- Miri subtly reacts to the active hotspot
- clicking Miri opens the whisper input
- clicking room objects opens close-up lenses
- clicking action zones gives a short local animation and bubble line
- typing starts the whisper input
- `Escape` closes input or lens
- mobile browser lenses become bottom sheets

## Playfulness Direction

Make the room more fun through room behavior, not extra UI.

Preferred interactions:

- Miri attention shifts toward the active object
- door knock ripple
- pinboard paper flutter
- shelf object wobble
- daily check tick
- body teal pulse
- craft sparkle
- floor dust swirl
- object pieces can be poked inside lenses
- typing feels like leaving a whisper
- night mode feels slower and warmer

Avoid:

- visible toy menus
- reward systems
- badges, counters, streaks, XP
- confetti or large effects
- mini-games inside lenses
- permanent floating controls
- lore-heavy instructional copy

## Object Lenses

Object lenses are close-ups, not pages.

Each lens should answer one question:

- Pinboard: what scraps are pinned here?
- Shelf: what objects are available?
- Daily: what is marked today?
- Body: what does the room body feel like?

Lens rules:

- one dominant object image or object map
- one compact text region
- one primary local action at most
- no nested cards
- no dashboard layout
- closing a lens returns to the room

## Bubble And Whisper

The bubble is Miri's current page voice. It is not a transcript.

Rules:

- one short line by default
- longer local output goes into the small result area
- do not let the bubble become the page
- do not cover Miri's face when avoidable
- input appears only when speaking to Miri

## Image Generation Rules

Generated bitmap assets are allowed when they improve this static room.

Use generation for:

- cleaner Miri cutouts
- new Miri state sprites
- new shelf objects
- new pinboard scraps
- new daily cards
- room time/weather variants
- object-lens illustrations

Generation invariants:

- preserve Miri's identity
- keep Miri as the only visible life
- preserve room geography unless explicitly redesigning the room
- save final assets locally under `asset/`
- do not overwrite existing assets unless replacement is requested
- update `asset/pieces/manifest.json` when adding lens pieces
- verify desktop/laptop and mobile browser readability

For sprites and props, prefer true transparent PNG/WebP or a clean chroma-key source followed by local background removal. Do not ship a white-background sprite as a final composited asset unless it is intentionally framed as paper/photo.

## Static Branch Rules

This branch should remain:

- static
- local asset based
- dependency-light
- browser-first
- easy to open with `index.html`

Allowed code:

- HTML
- CSS
- browser JavaScript
- docs
- local bitmap assets

Disallowed code:

- backend services
- TUI
- device deployment
- long-running daemons
- runtime memory/state systems
- generated output screenshots
