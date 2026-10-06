# Step 9 live-update gate

- Date: 2026-08-16
- Ruff: passed
- Mypy strict mode: passed for 51 application source files
- Pytest: 66 passed, one upstream Starlette/httpx2 deprecation warning
- Frontend ESLint and Prettier: passed
- Frontend Vitest: two files and four tests passed
- TypeScript and Vite production build: passed

The backend integration test authenticates a viewer, subscribes by device and
event type, commits a simulator-shaped ingestion record, and receives the typed
`measurement.new` event with the next sequence in under two seconds. Separate
tests verify unauthenticated close code 4401 and latest-value coalescing at no
more than one measurement event per device per second.

Browser-client tests deterministically stop and reconnect a fake socket without
reloading the page, verify the visible `Reconnecting` state, and prove REST
recovery is requested after reconnection. A forced sequence jump from 10 to 12
also triggers REST recovery. A missing heartbeat closes the socket after five
seconds. The local in-app browser confirmed the updated dashboard visibly shows
`Live updates: Reconnecting` when no authenticated session is present.

The final live-recovery demonstration should be repeated with a real signed-in
browser after the Step 10 authentication UI exists. This does not affect the
protocol/client gate, which is covered deterministically here.
