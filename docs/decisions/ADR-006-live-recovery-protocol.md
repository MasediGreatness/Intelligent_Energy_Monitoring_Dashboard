# ADR-006: Sequenced live updates with REST recovery

- Status: Accepted at the Step 9 gate
- Date: 2026-08-16

## Decision

Use one authenticated WebSocket endpoint with explicit device/event
subscriptions, a server-wide monotonic sequence, and five-second heartbeats.
Publish only after database commit. Coalesce measurement updates to one event
per device per second and send the newest pending value.

The browser treats the socket as an acceleration channel, not permanent state.
It shows `Reconnecting`, retries with exponential backoff capped at 30 seconds,
and invalidates all active REST queries after reconnect or a sequence gap.

## Consequences

- A missed event cannot silently leave the dashboard stale.
- API restart resets the process sequence; the reconnect and sequence checks
  deliberately trigger REST recovery.
- The in-process connection manager matches the fixed single-worker Pi
  deployment. Multi-worker deployment would require a shared event broker and
  globally allocated sequence numbers.
