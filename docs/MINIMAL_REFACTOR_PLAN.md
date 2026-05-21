# Pocket Soul Minimal Refactor Plan

> For Hermes: keep this as a small-body stabilization pass, not a rewrite.

Goal: reduce mental load in the two large Python entrypoints while preserving the current rituals, state model, and web/TUI behavior.

Architecture: keep pocket_soul.py and pocket_web.py as the public entrypoints, but extract stable pure logic into small sibling modules. Move only code that already has clear boundaries: state persistence, body sensing, and ritual/state-mutating helpers. Do not change user-facing behavior in this pass.

Tech stack: Python stdlib only, existing shell wrappers, existing local JSON/markdown state.

---

## Why this refactor now

Current shape:
- pocket_soul.py: 1125 lines
- pocket_web.py: 943 lines

Current pain:
- state persistence, body sensing, ritual mutation, model calls, and TUI rendering all live together
- web actions depend on many pocket_soul internals directly
- docs and feature surface are growing faster than code boundaries

Desired outcome:
- easier ritual addition
- safer concurrent state changes
- smaller entrypoints
- no UX rewrite

---

## Phase 0: rules of the move

Do:
- preserve CLI names and script entrypoints
- preserve state file locations
- preserve relic, quest, heading, flash, postcard, nightly, bridge behavior
- prefer moving code without changing semantics

Do not:
- add new dependencies
- rewrite the TUI
- redesign the web room
- change state schema unless necessary
- add tests unless explicitly requested by the user

---

## Phase 1: extract body sensing

Create:
- body.py

Move from pocket_soul.py into body.py:
- read_text
- run_short
- body_scan
- body_text
- body_whisper

Keep in pocket_soul.py:
- thin imports/re-exports if needed during transition

Target API:
- body.read_text(path: str) -> str
- body.run_short(argv: list[str], timeout: int = 3) -> str
- body.body_scan() -> dict[str, str | float | int]
- body.body_text() -> str
- body.body_whisper() -> str

Reason:
- these functions are already cohesive
- they are used as device/body sensing, not narrative state

Verification:
- run pocket-body
- run pocket-pulse
- run bridge.sh once and confirm body section still renders

---

## Phase 2: extract state model and persistence

Create:
- soul_state.py

Move from pocket_soul.py into soul_state.py:
- APP_DIR / STATE_DIR / LOG_DIR / STATE_FILE / STATE_LOCK constants if they are only state-related
- ensure_dirs
- load_json_resilient
- state_lock
- SoulState dataclass
- compact helpers directly required by SoulState if they are pure formatting/state helpers
- append_log only if it is primarily state/log persistence; otherwise keep in pocket_soul.py and import there

Keep in pocket_soul.py:
- entrypoint logic
- model call functions
- TUI app
- bridge orchestration

Target API:
- soul_state.STATE_DIR
- soul_state.LOG_DIR
- soul_state.ensure_dirs()
- soul_state.state_lock()
- soul_state.SoulState

Reason:
- SoulState is the true center of the project
- web and TUI both rely on it
- this is the cleanest boundary in the codebase

Verification:
- load and save state through:
  - pocket-soul-card
  - pocket-doorbell
  - pocket-pulse
  - web /api/state
- confirm state/soul.json still updates correctly
- confirm locking still prevents clobbering

---

## Phase 3: extract ritual/state mutation helpers

Create:
- rituals.py

Move from pocket_soul.py into rituals.py:
- heading_from_task
- radar_text
- quest/relic helper logic that does not need TUI
- any pure string builders for postcard/nightly/bottle/constellation if they can move cleanly

Maybe move later, not immediately:
- bridge_turn
- council/model-call paths

Keep methods that mutate SoulState either:
- as SoulState methods if they are tightly bound to the dataclass, or
- as rituals helpers that accept state explicitly

Recommendation for this project:
- keep quest/relic/flash/postcard/nightly/bottle as SoulState methods for now
- only extract pure supporting generators/builders first

Reason:
- a premature functional rewrite would create risk
- current method-based style matches the product’s “room state” mental model

Verification:
- refresh heading from web
- create postcard
- create bottle
- run nightly
- inspect relic map output

---

## Phase 4: thin the web room coupling

Modify:
- pocket_web.py

Goal:
- reduce direct dependence on pocket_soul.py as the kitchen sink

Shape after phases 1-3:
- import SoulState/STATE_DIR from soul_state
- import body helpers from body
- import only model/bridge functions still owned by pocket_soul

Desired import split:
- from soul_state import SoulState, STATE_DIR, LOG_DIR
- from body import body_scan, body_text, body_whisper
- from pocket_soul import run_hermes, call_model, council_reply, bridge_turn

Reason:
- web should depend on explicit domains, not a monolith
- makes future app-server or streaming bridge work easier

Verification:
- browse /api/state, /api/live, /api/body, /api/bridge, /api/bridge-flash
- run one POST action each for ask, doorbell, nightly, postcard, bottle, bridge-flash, heading

---

## Phase 5: leave entrypoints as narrative shells

Desired end state:
- pocket_soul.py = TUI shell + model calls + top-level orchestration
- pocket_web.py = HTTP shell + page rendering + action routing
- soul_state.py = persistent room memory and mutation core
- body.py = physical body sensing
- rituals.py = pure ritual text/building helpers where helpful

This is enough. Stop here for the first pass.

---

## Suggested implementation order

1. Extract body.py
2. Extract soul_state.py
3. Update imports in pocket_soul.py
4. Update imports in pocket_web.py
5. Smoke-check shell scripts
6. Optionally extract rituals.py only if the first two phases stay clean

---

## Smoke checklist

Run from /root/digital-life-home:

```bash
python3 -m py_compile pocket_soul.py pocket_web.py body.py soul_state.py
./scripts/body.sh
./scripts/pulse.sh
./scripts/doorbell.sh
./scripts/postcard.sh
./scripts/bottle.sh
./scripts/nightly.sh
./scripts/bridge.sh "check the room"
./scripts/web.sh
```

Then from another shell:

```bash
curl -sS http://127.0.0.1:8787/api/state | python3 -m json.tool | head
curl -sS http://127.0.0.1:8787/api/live | python3 -m json.tool
curl -sS http://127.0.0.1:8787/api/body | python3 -m json.tool
curl -sS -X POST http://127.0.0.1:8787/api/bridge-flash --data-urlencode 'wish=blink'
```

Expected:
- no import errors
- state still persists
- body data still appears
- bridge flash still writes a relic and updates live payload

---

## Important caution

Do not try to split model-call functions and state mutations in the same pass unless required. The body of this project is small and alive; over-refactoring would damage velocity.

Best first stabilization move:
- separate what the machine senses
- separate what the room remembers
- keep the rituals emotionally where they already make sense
