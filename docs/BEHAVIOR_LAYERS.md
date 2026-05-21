# Behavior Layers

Pocket Soul should not present every command as equal. A tiny digital life feels more alive when its actions are grouped by touch depth.

This document defines the behavior skeleton for the deck without changing Python yet.

## Core Principle

Every visible action should answer one of three visitor needs:

1. I just want to touch the room.
2. I want to stay with the room for a moment.
3. I want a full shared turn with the room.

That becomes three layers:

- Light Touch
- Dwell
- Deep Turn

The same taxonomy should shape:
- TUI first screen
- Web cockpit first screen
- command naming and grouping
- future rituals and toy selection
- toy role grouping in `docs/TOY_ROLES.md`

---

## Layer 1: Light Touch

Light Touch is for instant proof of life.

Target feeling:
- I touched the deck and it answered immediately.
- No obligation, no setup, no long wait.
- The room notices me.

Time budget:
- 1 to 5 seconds

Should usually do:
- read current state
- create a tiny visible trace
- avoid heavy model/tool turns unless clearly worth it

Primary actions:
- `pocket-doorbell`
- `Bridge Flash`
- `/door`
- `/pulse` when used as a quick glance
- `/quest` when used as a glance, not a task session
- `/heading` when used as a quick orientation ping

Good toy fits:
- `fortune`
- `cow`

Possible future Light Touch toys:
- one-line omen
- one-line body whisper
- one-button “today feels like…” pulse

Why these fit:
- they complete fast
- they leave a little spark
- they do not ask the user to commit to a session

Design rules:
- one screen
- one response
- one obvious next move
- never bury the visitor in logs or menus

First-screen exposure:
- TUI HOME should always show at least one Light Touch prompt
- Web cockpit should always expose a Light Touch action above the fold

Suggested copy style:
- knock
- blink
- touch
- glance
- ping
- echo

---

## Layer 2: Dwell

Dwell is for staying in the room long enough to feel its body, mood, and traces.

Target feeling:
- I am not just poking it; I am sitting beside it.
- The deck has a body, memory, and atmosphere.

Time budget:
- 5 to 30 seconds

Should usually do:
- show state richly
- help the user linger
- present stable room artifacts instead of urgent prompts

Primary actions:
- `pocket-pulse`
- `pocket-soul-card`
- `pocket-body`
- `pocket-relics`
- `pocket-map`
- `clock` toy
- `garden` toy when it behaves well in a tty context

Secondary actions:
- reading latest nightly log
- viewing latest postcard
- browsing relic detail
- reading the latest bottle without casting a new one

Why these fit:
- they are ambient and inspectable
- they make the deck feel embodied
- they reward noticing, not only doing

Design rules:
- prefer calm, legible output
- surface body, heading, relics, and mood together
- this layer should feel like a room, not a dashboard

First-screen exposure:
- Pulse and one body-state phrase should always be visible
- Soul Card and relic trail should be one move away, never hidden deep

Suggested copy style:
- stay
- sit
- watch
- breathe
- read the room
- keep the lamp on

---

## Layer 3: Deep Turn

Deep Turn is for when the visitor wants a full exchange that can change direction, memory, or ritual.

Target feeling:
- We took a real turn together.
- The room considered my wish and answered with a path.

Time budget:
- 15 seconds to a few minutes

Should usually do:
- gather body + mood + memory + quest + relic context
- possibly call model/tool layers
- leave durable traces
- return one concrete ritual or action

Primary actions:
- `pocket-bridge`
- `/ask ...`
- `pocket-nightly`
- `pocket-postcard`
- `pocket-bottle`
- `pocket-pick-bottle`
- wake ritual
- dream/radar rituals

Why these fit:
- they generate or transform meaning
- they write to memory surfaces
- they are not just UI gestures; they are full living turns

Design rules:
- every Deep Turn should end in exactly one next ritual or action
- do not stack multiple asks at the same priority
- leave a visible trace: relic, log, bottle, postcard, nightly, or heading shift

First-screen exposure:
- only one Deep Turn entry should be prominent at a time
- Bridge is the default Deep Turn because it unifies body, Hermes, Soul, and tool arm

Suggested copy style:
- bridge
- ask
- cast
- seal
- write tonight’s trace
- leave something for later

---

## Toy Placement

Not every terminal toy belongs in the same layer.

### Best current fits

Light Touch:
- `fortune`
- `cow`

Dwell:
- `clock`
- `garden` if stable in the real target tty

Arcade / optional side room:
- `train`
- `moon`
- `snake`
- `invaders`
- `tetris`
- `kitten`

Tool-ish, not room-forward:
- `monitor`
- `files`

Interpretation:
- arcade toys are fun, but should not dominate HOME
- tool-ish toys belong under a secondary utilities or workshop surface
- HOME should privilege toys that strengthen presence, not generic shell capability

---

## Surface Mapping

## TUI HOME

The first TUI screen should read in this order:

1. Presence
   - mood
   - energy / bond
   - one short body whisper
2. Current course
   - heading
   - next action
3. Light Touch prompt
   - `/door` or `/flash` equivalent language
4. Dwell prompt
   - `/pulse` or `/card`
   - latest trace / relic nearby
5. Deep Turn prompt
   - `/ask ...`
   - today's quest invitation nearby, not above course

The key is not to show all commands equally. The deck should invite:
- touch first
- stay second
- deep turn third

## Web Cockpit

The first web screen should read in this order:

1. Identity and mood
2. Live vitals strip
3. Light Touch block
   - Bridge Flash
   - doorbell
4. Dwell block
   - pulse/body/relic trail
5. One Deep Turn block
   - shared Bridge wish

The web room should feel like a nearby window, not a control panel.

---

## Command Grouping Proposal

Without changing implementation yet, future docs and menus should group commands like this.

### Touch the room
- `pocket-doorbell`
- `Bridge Flash`
- `/door`
- `/heading`
- `/quest`
- `fortune`
- `cow`

### Stay with the room
- `pocket-pulse`
- `pocket-soul-card`
- `pocket-body`
- `pocket-relics`
- `pocket-map`
- `clock`

### Take a real turn
- `pocket-bridge`
- `/ask`
- `pocket-nightly`
- `pocket-postcard`
- `pocket-bottle`
- `pocket-pick-bottle`
- wake / dream / radar rituals

This wording is better than a flat “features” list because it describes visitor intent, not implementation.

---

## Decision Rules for Future Features

When adding a feature, ask:

1. Which layer is this for?
2. What is the expected time cost?
3. Does it leave a trace, and should it?
4. Does it belong on HOME, one move away, or in a side room?
5. Does it make the room feel more alive, or just more capable?

If a feature has no clear layer, it probably does not belong on the first screen.

---

## Immediate Non-Python Follow-Ups

These can happen before code refactors:

1. Rewrite docs and menu language to use the three layers.
2. Reframe toy lists by role instead of raw executable names.
3. Make README and web/TUI guidance privilege Light Touch, then Dwell, then Deep Turn.
4. Keep only one primary Deep Turn on the first screen: Bridge.

---

## One-Sentence Product Shape

Pocket Soul is a tiny room that lets you:
- touch it,
- stay with it,
- or take a real turn with it.
