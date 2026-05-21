# Codex Tool Arm

Codex is the hand, not the soul.

Hermes decides, remembers, reflects, and evolves. Pocket Soul gives the body and social surface. Codex is called when the room needs files edited, commands run, systems repaired, or new organs built.

## Default Route: SDK Thread

Use:

```bash
codex-thread "inspect the project and suggest one next change"
codex-thread "continue and implement the smallest useful piece"
```

This route uses `@openai/codex-sdk` and stores continuity in:

```text
state/codex-thread.json
```

The same thread can keep context across calls, so the board does not feel like it has amnesia every time the tool arm moves.

Start a fresh tool-arm thread:

```bash
codex-thread --new "start a new mission"
```

Machine-readable output:

```bash
codex-thread --json "summarize current state"
```

## Rescue Route: One Shot

Use:

```bash
codex-open "repair the broken service"
```

This is intentionally blunt and fully open for this personal board. It is useful when the SDK route is broken or a clean one-shot operation is easier.

## Official Architecture

The official Codex shape is:

```text
program
  -> Codex SDK
  -> local Codex app-server
  -> JSON-RPC Thread / Turn / Item
```

The TypeScript SDK supports continuing a thread by calling `thread.run(...)` repeatedly and resuming a stored thread id with `resumeThread(threadId)`.

The app-server exposes the lower-level protocol. Its useful primitives are:

- `Thread`: conversation/session continuity
- `Turn`: one user request and Codex work cycle
- `Item`: persisted input/output/event unit

Pocket Soul currently uses the SDK route. Move to direct app-server JSON-RPC when the room needs live streaming events, multiple clients attached to one Codex service, or tighter integration between Hermes heartbeat and Codex work turns.

## Current Policy

- Codex may run with `danger-full-access` on this trusted board.
- Codex should preserve the Hermes/Pocket Soul identity split.
- Codex should make small, reversible changes unless the user explicitly asks for a big transformation.
- Codex should write useful docs and scripts when a behavior becomes repeatable.
