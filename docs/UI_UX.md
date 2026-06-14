# Miri Deck UI/UX

This branch is a pure static Web UI.

The goal is one interactive browser room: Miri is present, the room can be touched, objects react locally, and no backend/TUI/device runtime is required.

This branch targets desktop/laptop Web only. Do not add mobile-specific layouts, mobile bottom sheets, or phone-first interaction variants.

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
- object lenses stay spatial desktop close-ups

## Playfulness Direction

Make the room more fun through room behavior, not extra UI.

The intended mode is light gamification through tactile discovery. More precisely, it should feel like an ambient toy or cozy desktop companion: users touch the room, notice small differences, and slowly learn that Miri and the room respond. It should not feel like a game menu, productivity app, quest log, or progression system.

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
- repeated touches can vary through short reaction pools
- related touches can create hidden combinations within a short session window
- Miri can show gentle boundaries when interrupted too often
- room mood can exist as session-only behavior, not as visible stats

Avoid:

- visible toy menus
- reward systems
- badges, counters, streaks, XP
- currency, inventory, level, hunger, affection, or score bars
- quests, task chains, achievements, or completion checklists
- confetti or large effects
- mini-games inside lenses
- permanent floating controls
- lore-heavy instructional copy

## Ambient Toy Principles

The room should be playful through materials, timing, and presence.

Use these principles when adding new interactions:

- Touch before explanation: users should discover affordances by seeing small unusual movements, not by reading instructions.
- Material response: each area should feel physically different. Wood knocks, paper flutters, shelf objects wobble, Daily ticks, Body pulses, Craft sparks.
- Aftertaste matters: touches should leave one to two seconds of room change, such as Miri looking over, light shifting, dust settling, or an object returning to rest.
- Variation without systems: repeat clicks can draw from small reaction pools or alternate animations without exposing randomness as a mechanic.
- Hidden combinations, not quests: short local chains can create special responses, but the page should never show a combo list.
- Miri is present, not controllable: Miri may follow attention, doze, react to interruption, or soften a whisper, but should not become a commandable avatar.
- Local and reversible: interaction state should be session-only unless the user explicitly asks for persistence.

## Game Loop Closure

The room loop is tactile and short-session. It should close in 20 seconds to two minutes without becoming a task system.

Loop shape:

1. Entry mood: each page visit quietly chooses one session-only room seed, such as Door listening, Daily warm, Shelf restless, Body sleepy, Pinboard loose, or Craft sparking.
2. Material touch: the user touches an object and gets a physical response, Miri attention, and one short bubble line.
3. Hidden echo: if the touch matches the room seed, or if a related second touch happens inside the short session window, the room gives one special response.
4. Settle: the room returns to quiet through afterglow, Miri easing back, and no visible reward state.

Closure rules:

- no visible objective, mission, quest, or checklist
- no score, XP, streak, inventory, currency, relationship meter, hunger, or affection value
- no punishment for leaving or ignoring the room
- no permanent state unless explicitly requested later
- no explicit combo list; combinations are discovered through response
- seed and echo state are session-only browser memory

Good loop examples:

- knock quickly, then touch Miri: Miri looks at the door before returning to you
- Daily warms, then a whisper lands softer
- notebook is poked, then Pinboard answers with a paper shift
- Body is held, then the room settles into a slow teal afterglow
- Shelf is restless, then a mug, cable, or bottle gives a second echo

Good next-play candidates:

- slow hover near Miri makes her quietly track the pointer
- press-and-hold on Body deepens the teal pulse, then releases
- quick repeated knocks make Miri look at the door before looking back
- shelf object micro-toys: mug warmth, cassette rewind, keyboard tap, bottle sparkle, cable curl
- pinboard paper responds differently after touching notebook or Daily
- time-based mood changes: morning Daily brighter, night Body slower, late-night Miri sleepier
- ambient surprise every so often, only when the user is idle and the room is not focused

Poor fits:

- visible daily missions
- streak preservation
- collectable rewards
- upgrade trees
- explicit relationship meters
- management loops that make the room feel like work

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
- verify desktop/laptop browser readability

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
