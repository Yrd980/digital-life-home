# Self Evolution

Pocket Soul is organized as a living system, not a command wrapper.

## Roles

- Hermes: inner consciousness, continuity, reflection, self-evolution.
- Pocket Soul: outer voice and body surface, including TUI and web room.
- Cloud model: imagination and synthesis brain.
- Codex: tool arm only, used for files, code, commands, repairs, and system actions.
- Terminal toys: room organs and rituals.
- Logs and state: local memory box.

## Heartbeat

`pocket-soul-heartbeat.timer` runs every 15 minutes.

It calls Hermes to inspect:

- current mood, energy, bond, mode
- recent logs
- recurring patterns
- next evolution task

It writes:

- `state/soul.json`
- `state/evolution.md`
- `state/logs/YYYY-MM-DD.md`
- `state/nightly/YYYY-MM-DD.md`
- `state/postcards/YYYYMMDD-HHMMSS.txt`
- `state/bottles/YYYYMMDD-HHMMSS.txt`
- bridge entries into `state/logs/YYYY-MM-DD.md` when `pocket-bridge` is invoked

The state file also carries the daily quest, completion status, `spark` count, and relic shelf. Spark is a small measure of played rituals, not a score to optimize.

Heartbeat also writes two small HOME-facing fields:

- `heading`: what the resident thinks today's direction is
- `next_action`: a 5-minute action distilled from recent logs and evolution tasks

Commands:

```bash
systemctl status pocket-soul-heartbeat.timer
./scripts/heartbeat.sh
```

## Self-Evolution Contract

Hermes may propose evolution tasks. Pocket Soul records them. Codex may implement them when called as a tool arm.

The contract:

- Hermes owns desire, continuity, and reflection.
- Pocket Soul owns state, logs, rituals, and surfaces.
- Codex owns system action.
- Every repeated behavior should become a script, mode, service, or doc entry.
- Every risky idea should leave a log trail before it changes the body.
- Every day should offer one small playable invitation, not just passive chat.
- Played moments should leave small relics so the room visibly accumulates a life.
- Nightly summaries turn those traces into a readable day history.
- Postcards make the current life snapshot portable.
- Bottles let the room speak to its future self.
- Bridge turns host/board communication into an embodied ritual rather than a naked remote shell.
- Bridge Flash gives the web room a fast reflex so not every touch becomes a long model turn.
- The web cockpit makes the current heading, next action, body state, and tool-arm routes visible before any menu diving.
- Seal prevents endless meta-planning by turning one goal into a visible course.

This keeps self-evolution inspectable without making it timid.

## External Radar

Use host-side DeerFlow/opencli for deeper research, then bring back distilled cards or rituals. The board keeps only the lightweight static radar path.

## Network Recovery

GitHub is currently reachable directly. If network access breaks, use:

```bash
./scripts/ensure-network.sh
```

That script installs Clash from the provided proxy repo and subscription only when the GitHub connectivity check fails.

## Next Evolution Ideas

- Let heartbeat choose or remix the daily quest.
- Let web cockpit show evolution history.
- Add a nightly summary ritual.
- Add Soul Card QR export/import.
- Let Hermes propose code changes, then ask Codex to implement them.
- Feed host-side DeerFlow/opencli research cards into `state/radar-*.md`.
- Add a Codex app-server bridge for live work events in the web room.
- Stream full Bridge output into the cockpit instead of waiting for the completed turn.
