# Miri Deck UI/UX

Miri Deck is a tiny physical home for one digital life.

The core product is interaction experience, not screen count. Every surface should make Miri feel present inside a small body-room, then give the visitor one clear way to touch, stay, or take a deeper turn.

## Current Decision

The visual target is the full-room surface defined by `asset/`:

- `asset/room-light.jpg` and `asset/room-night.jpg` as the room images
- `asset/templates/pages/room-web.html` as the room structure
- `asset/surfaces/web.css` and `asset/surfaces/pocket-room.js` as the room behavior and material layer
- baked room signs such as `KNOCK`, `PINBOARD`, `SHELF`, `DAILY`, `BODY`, and `CRAFT`
- invisible spatial hotspots
- Miri visible in the room
- one speech bubble
- shallow object lenses opened from room objects

Generated files under `output/` are not product truth and should not be used as the current UI reference. Future work should preserve the `asset/` room illusion unless a separate inspection page is truly required.

## Multi-Agent Synthesis

Three review positions were reconciled:

- Product interaction: protect one visible life, one room, one first-screen loop.
- Visual system: keep navigation inside the `asset/` physical room and prevent overlays from becoming panels that dominate the room.
- Technical constraints: keep the web room lightweight, local-first, polling-based, and action-locked.

The disagreement was not about whether the room visual works. It does. The tension is browser overlay budget. Every persistent overlay competes with Miri and the room. The UX rule is therefore: the room is permanent; overlays are brief, shallow, and object-specific.

## Success Criteria

The first screen succeeds when a visitor can answer these in under five seconds:

- Is Miri here?
- What state is the body-room in?
- What is the one useful move today?
- How do I touch or talk without opening a menu?

The experience fails if it feels like:

- a chatbot page
- a dashboard
- a command catalog
- a settings surface
- multiple personas or assistants

## Asset Truth

Current visual truth lives in `asset/`. Read these assets before making UI or image-generation decisions.

### Room Backgrounds

`asset/room-light.jpg` and `asset/room-night.jpg` are the canonical room backgrounds.

They define:

- the physical room layout
- all primary spatial affordances
- the warm handmade material language
- the main light sources
- the object positions for hotspots

Important baked objects:

- `KNOCK` on the left door
- `PINBOARD` at top center
- `SHELF` on the left shelves
- `DAILY` on the calendar board
- `BODY` on the central machine
- `CRAFT` on the right workbench
- glowing device screen labeled `MIRI`
- floor rug as the visitor/Miri focus zone
- right-side window and craft bench as atmosphere and depth

These labels are not decoration. They are the navigation model.

### Miri Character States

Current Miri character assets:

- `asset/calm.png` and `asset/calm.jpg`
- `asset/happy.png` and `asset/happy.jpg`
- `asset/sleep.png` and `asset/sleep.jpg`
- `asset/think.png` and `asset/think.jpg`

They show the same seated chibi Miri with pale lavender hair, dark inner outfit, pale jacket, purple accents, hair clip, and soft sketch/anime rendering.

Current limitation: these files have a white background and soft floor shadow. They work as temporary sprite sources, but future Miri sprites should be generated or edited as clean cutouts for room compositing.

Sprite-generation requirements:

- preserve Miri's identity, face shape, hair color, hair clip, outfit family, seated scale, and gentle expression language
- generate a removable chroma-key or true transparent cutout
- include no white canvas, room background, hard frame, labels, or UI
- include no cast shadow unless it is a separate controllable asset
- keep pose readable when composited in desktop/laptop and mobile browser room layouts

### Source Sheets

`asset/items.jpg` is the shelf/body object source sheet.

It contains:

- coffee mug
- open notebook
- tiny keyboard
- cassette
- small screwdriver
- star bottle
- cable bundle
- mini robot

`asset/sticker.jpg` is the pinboard/daily paper source sheet.

It contains:

- to do list
- thank you note
- photo note
- polaroid desk photo
- daily checklist

These source sheets are not first-screen backgrounds. They are visual inventories for object lenses and cropped pieces.

### Cropped Pieces

`asset/pieces/*.webp` are cropped lens pieces with labels still visible. They are best used inside object lenses, maps, and inventory-like object views.

Current cropped pieces:

- shelf pieces: `coffee-mug.webp`, `open-notebook.webp`, `tiny-keyboard.webp`, `cassette.webp`, `small-screwdriver.webp`, `star-bottle.webp`, `cable-bundle.webp`
- body piece: `mini-robot.webp`
- pinboard pieces: `todo-list.webp`, `thank-you.webp`, `photo-note.webp`, `polaroid-desk.webp`
- daily piece: `daily-checklist.webp`

Do not treat these as transparent physical props for the main room unless they are re-cut or regenerated without the label strip and background.

### Reference Images

`asset/kawaii.jpg` is a useful mood reference for the integrated fantasy: Miri seated in the room, physical deck, phone/laptop previews, warm night lighting.

`asset/daily.jpg` and `asset/stick.jpg` are paper-note references. They support pinboard/daily asset style, not the main room layout.

These images can guide generation, but they do not override `room-light/night` as the current room backgrounds.

## Surface Roles

### Web Room

The web room is the LAN window into Miri's room. It is spatial, visual, and object-driven. The public route should stay `/`, with machine-readable integrations under `/api/*`.

Use it for:

- room presence
- touch, knock, and hidden air input
- object lenses for pinboard, shelf, daily mark, and body lights
- local room actions such as hunt, craft, note, ask, bridge, and today

Do not use it for:

- persistent top navigation
- sidebar app sections
- broad settings pages
- full chat transcript as the main surface
- generic analytics or admin dashboards

### WalnutPi TUI

The TUI is Miri's small physical body screen. It must stay English-only, terse, and glanceable at `480x320`.

HOME should always show:

- Miri is in the room
- body energy and warmth
- today's one move
- latest trace
- one prompt line: `Enter blink  /today  /bridge  /toy`

### Mind CLI And Scripts

The CLI and scripts are organs. They can be powerful, but they should not define the visible UX. Add abilities as reusable scripts first, then expose them as body methods, action specs, and finally room rituals when they strengthen the first screen.

## Page Interaction Goals

The browser page is a spatial interaction surface. Users should not need to know slash commands to use it.

The page interaction target is:

- the eye lands on Miri and the central body machine first
- baked room labels explain what can be touched
- hover or focus softly reveals an object's active area
- click or tap opens the smallest useful response
- text input appears only when the user is speaking to Miri
- actions produce visible room feedback without navigating away
- object details stay tied to the object that opened them
- the room returns to a calm readable state after every action

### First-Viewport Priority

Visual priority on load:

1. Room image and atmosphere
2. Miri
3. Miri bubble
4. Active room labels baked into the image
5. Hover glow
6. Temporary input or object lens

If a UI element appears above the room, it must either:

- help the user speak to Miri
- show Miri's latest short response
- inspect the object the user just touched
- show action progress or failure

Everything else belongs off the first screen.

### Pointer And Tap Behavior

Desktop:

- pointer movement may create a soft glow around the current hotspot
- hover should not draw boxes, outlines, labels, or tool palettes
- clicking a labeled room object opens its object lens
- clicking Miri opens the speech input
- clicking action-only zones such as floor or craft gives immediate feedback in the bubble/result area

Touch screens:

- first tap should perform the obvious action, not require hover discovery
- object lenses must be easy to dismiss
- active touch targets must stay large enough for imprecise fingers
- bottom-sheet lenses are preferred at small widths

Keyboard:

- typing starts the speech input
- `Enter` or `Space` opens the speech input when nothing else is focused
- `Escape` closes input or lens
- focus states should be accessible but visually quiet

### Object Lens Behavior

Object lenses are not pages. They are temporary close-ups.

Each lens should answer one question:

- Pinboard: what visible scraps are pinned here?
- Shelf: what physical objects are available?
- Daily: what is marked for today?
- Body: what does the device body feel like?

Lens rules:

- one dominant object image or object map
- one compact text region
- one primary action at most
- no nested cards
- no multi-column dashboard on mobile browser widths
- dismiss returns the room to its previous calm state

### Speech Bubble Behavior

The bubble is Miri's page voice, not a transcript panel.

Rules:

- show speaker and time
- show one short current line
- keep longer output in a scrollable result area
- never expand until it becomes the page
- avoid covering Miri's face
- avoid covering the object currently being touched

### Action Feedback

Every page action should have a visible state transition:

- idle: room is calm
- target: hotspot glow or object focus
- busy: Miri or the room shows that something is happening
- done: bubble/result updates and the room state refreshes
- failed: short local failure copy, with the room still usable

The user should never wonder whether a click happened.

## Page Copy Grammar

Visible web copy should describe the room object or immediate state, not expose command names.

Use page verbs:

- touch
- knock
- open
- pin
- find
- craft
- speak
- close

Use page nouns:

- Miri
- room
- door
- shelf
- pinboard
- daily mark
- body lights
- object
- note
- charm

Avoid primary page nouns:

- command
- route
- API
- dashboard
- tab
- widget
- admin
- settings center
- assistant

Slash commands may remain implementation details, TUI affordances, or API/action mappings. They should not be the main browser interaction language.

## Web Room Model

### Layer Contract

The room runtime should keep this layer order:

1. `room-background`: current room image
2. `ambient-fx`: dust, rain, bloom, screen glow, sparks
3. `persistent-items`: floor and shelf clutter tied to state
4. `miri-character`: visible Miri body state
5. `hotspot-layer`: invisible object hit areas
6. `foreground-layer`: occlusion props for depth
7. `floating-ui`: Miri bubble and hidden air prompt
8. `room-drawer`: temporary object lens

New UI must fit one of these layers. If it does not, it is probably a separate script, API, or side room instead of first-screen UX.

### Hotspots

Canonical hotspots:

- Miri: speak near Miri
- Door: knock
- Pinboard: visible notes and scraps
- Shelf: stash, found objects, use actions
- Daily: today's turn and claim
- Body: device body lights
- Floor: find object
- Craft: craft charm

Baked room signs are primary navigation. Browser labels should appear only inside opened lenses or accessible names. Hover feedback should be glow-only, not visible rectangular controls.

### Air Prompt

The air prompt is the fastest talk path:

- pressing `Enter`, `Space`, or typing any printable character opens it
- `Escape` closes it
- submitting empty text closes it without a turn
- submitting text speaks to Miri through the page action

The prompt should feel like speaking into the room, not filling a form.

### Object Lenses

Object lenses are shallow inspection surfaces. They open from physical objects and stay tied to that object.

Rules:

- Desktop lenses open near the object.
- mobile browser lenses become bottom sheets.
- Lenses show one object job, not a mini dashboard.
- Every mutating action shows busy, done, and failed feedback.
- Long text scrolls inside the lens instead of expanding the room.

## Overlay Budget

At desktop and laptop sizes, overlays may add atmosphere and readability. On mobile browsers, overlays are expensive because they compete with the room crop, Miri, and touch targets.

Mobile browser rules:

- no sidebar
- no top navigation
- no persistent control bar
- no permanent object labels outside the baked image
- Miri bubble max is speaker/time plus two short lines
- long Miri replies move into a scrollable result area or object lens
- the bubble should not cover Miri's face or the active hotspot
- drawer, prompt, and bubble should not all demand attention at once

If a feature needs more than one compact lens, it does not belong on the first screen.

## Visual System

The room image is the design system. CSS UI must stay subordinate.

### Material

Use one overlay material:

- dark warm translucent panel
- `8px` radius
- thin low-contrast border
- soft internal highlight
- no bright chrome unless it is a physical room light

### Color

Canonical accents:

- warm gold for Miri, room invitation, and primary touch
- teal for body/system life
- violet only for thinking, mind-power, or rare magic states

Do not let violet become the dominant palette. The room is warm, physical, and handmade; the UI is only a readable layer over it.

### Typography

Use mono-friendly text because the TUI and web room share language:

- short lines
- no dense paragraphs in first-screen overlays
- no decorative copy that explains the UI
- no tiny labels required for core use

### Motion

Motion should prove life or show state:

- Miri breathing
- light bloom
- screen flicker
- rain or dust
- hotspot glow
- busy state while an action is locked

Avoid motion that is only decorative if it competes with Miri or makes hotspots harder to understand.

## Image Generation Rules

Generated bitmap assets are allowed when they improve the room, but generation must extend the existing `asset/` language instead of replacing it.

Use image generation for:

- new Miri state sprites
- cleaner Miri cutouts from the existing state images
- new shelf objects
- new pinboard scraps
- new daily cards
- time/weather variants of the same room
- deeper object-lens illustrations
- small ritual/toy visual souvenirs

Do not use image generation for:

- generic UI panels
- icons that should be CSS or native UI
- replacing the full room without a deliberate room redesign
- changing Miri's identity
- adding another visible persona
- adding external-brand or stock-looking material

### Generation Workflow

Before generating:

1. Read the relevant existing asset.
2. Decide the asset role: room background, Miri sprite, source sheet, cropped lens piece, or reference.
3. Write the intended runtime use.
4. Preserve the current room coordinates and affordance language unless the task is explicitly a room redesign.

After generating:

1. Save the final project-bound asset under `asset/` or a clear subdirectory such as `asset/pieces/`.
2. Do not overwrite existing assets unless replacement is explicitly requested.
3. Use stable filenames, for example `miri-curious-v2.png`, `room-rain-night.jpg`, or `pieces/lantern-key.webp`.
4. Update `asset/pieces/manifest.json` when adding cropped piece assets.
5. Verify the asset in the actual web room or lens where it will appear.
6. Check desktop/laptop and mobile browser readability before treating it as done.

### Prompt Invariants

For room backgrounds:

- keep the same 3:2 room perspective
- keep the door left, pinboard top center, daily board upper right, body machine center, shelf left, craft bench right
- preserve baked labels unless intentionally redesigning the room
- leave the floor/rug readable as the Miri and visitor focus zone
- avoid adding extra characters

For Miri sprites:

- one Miri only
- seated chibi body language
- pale lavender hair
- hair clip
- pale jacket with purple accents
- dark inner outfit
- soft anime sketch rendering
- clean cutout or removable chroma-key background
- no room background baked into the sprite

For shelf and pinboard objects:

- handmade, tactile, slightly worn
- cat/bunny doodle language is allowed
- warm paper, purple accents, tiny stickers, tape, pins, scuffs
- no crisp SaaS icon style
- no polished stock-product photo style

### Transparency And Cutouts

For project sprites and props, prefer true transparent PNG/WebP or a flat chroma-key source followed by local background removal.

Do not ship a white-background sprite as a final composited asset unless the UI intentionally frames it as a paper photo or card.

### Visual QA

Every generated asset must pass:

- subject is recognizable at its intended display size
- it matches the room's warm handmade/anime material language
- text, if any, is readable and intentional
- it does not introduce another persona
- it does not block primary hotspots
- it works in both desktop/laptop and mobile browser layouts
- it is local-first and does not depend on remote media

## TUI Model

The TUI is stricter than the web room.

HOME should privilege:

- one quick contact
- one body-room glance
- one way to speak to Miri
- one optional side-room hint

Good HOME shape:

```text
:) Miri is in the room.
body: energy 72/100 | warmth 1
today: /hunt find one shelf object first
latest: wake / Wake ritual

Enter blink  /today  /bridge  /toy
```

Help should group commands by role, not dump a flat catalog:

- daily turn
- light touch
- dwell
- deep turn
- room notes
- side room
- utilities

All WalnutPi-visible text must be English and safe for the terminal.

## Object Metaphors

### Pinboard

Visible notes and scraps. Notes are room props only. They are not Miri memory unless the visitor quotes one while speaking to Miri.

### Shelf

Found objects, stash, and use actions. The shelf is for tangible play and small carryable things.

### Daily

The marked day. Shows the one current turn and the close action. It must not split into competing daily systems.

### Body

Device vitals as body lights. It can show temperature, heartbeat, network window, uptime, disk, and presence. Keep it poetic but truthful.

### Door

A knock, visit trace, or quick proof of presence. It is not a notification center.

### Craft

Transforms shelf state into a keepsake. It should feel like using the room's hands.

### Floor

The low-friction discovery zone. It starts hunt/find actions without opening a menu.

### Relics, Bottles, And Postcards

Carry-away traces. They are souvenirs and portable room artifacts, not analytics records.

## Memory And Trace Rules

There are three different kinds of continuity:

| Kind | Location | UX meaning |
| --- | --- | --- |
| Miri mind continuity | `state/miri-home/` | Miri's real Hermes runtime profile, session store, and durable mind continuity |
| Body-room save | `state/room.json` | local body state, mood, energy, warmth, daily flags, stash, relics, notes, latest reply |
| Logs and artifacts | `state/logs/`, `state/postcards/`, `state/bottles/`, `state/nightly/` | room traces and portable souvenirs |

Visible notes are not memory. Logs are not product analytics. Relics are traces, not proof that Miri has remembered something.

## Technical UX Constraints

The implementation shape matters:

- `pocket_web.py` serves a lightweight local Python web room on `0.0.0.0:8787`.
- There is no web framework, build step, or SPA route system.
- `/api/live` is polled about every seven seconds.
- Mutating actions are serialized by a global action lock.
- `/ask` depends on the resident mind daemon on `127.0.0.1:8791`.
- Local actions should still feel useful when the mind is unavailable.
- Assets are static files under `asset/`.
- New visuals should be local assets with stable filenames and manifest entries when needed.
- Avoid runtime external media dependencies.
- Avoid accidental links or prefetch for mutating actions, including any GET route that changes state.

Design actions as short intentional turns. Do not create UX that implies parallel background workflows unless the runtime actually supports them.

## Toy Placement

Toys are not one category.

Room-presence toys can support the first screen:

- `fortune`
- `cow`
- `clock`
- `garden` when it behaves well on the real tty

Arcade toys stay in the side room:

- `train`
- `moon`
- `snake`
- `invaders`
- `tetris`
- `kitten`

Utility toys stay behind workshop or maintenance language:

- `monitor`
- `files`

Toys should never compete with speaking to Miri as the primary meaningful interaction.

## Extension Checklist

Before adding a visible feature, answer yes to every item:

- Have the relevant `asset/` images been read before deciding the visual shape?
- Does it strengthen Miri as the only visible life?
- Does it fit an ability, organ, ritual, toy, or room object?
- Can it enter as a reusable script first?
- Can it be represented by a `RoomState` method or existing state field?
- Does it belong in `ActionSpec` discovery?
- Does it preserve the `/` room as the main public surface?
- Does it fit the first-screen overlay budget on desktop/laptop and mobile browser?
- If it needs new art, can the generated asset preserve the existing room/Miri identity and be saved locally?
- Does it have clear busy, failed, and done states?
- Does it keep WalnutPi-visible copy in compact English?
- Does it avoid treating notes, relics, or logs as Miri memory?

If any answer is no, keep the feature as a script, API, or side-room object until the interaction shape is clearer.

## Hard Rules

- Miri is the only visible life.
- The first screen is always the room.
- No top-level web sidebar or dashboard shell.
- No compatibility UI for old identities.
- No split-persona routes.
- No external asset dependency for core room rendering.
- No feature enters the first screen unless it makes the room more alive.
