# Step 8 security gate

- Date: 2026-08-16
- Database migrations: `0002` applied to `energy_test` and development `energy`
- Ruff: passed
- Mypy strict mode: passed for 48 application source files
- Pytest: 63 passed, one upstream Starlette/httpx2 deprecation warning
- Frontend ESLint and Prettier: passed
- Frontend Vitest: one test passed
- TypeScript and Vite production build: passed

Security tests prove that unauthenticated dashboard reads and writes return the
standard 401 envelope, viewers cannot acknowledge alarms, operators can
acknowledge alarms but cannot edit settings, and admins can edit settings.
They also verify Argon2 hashing, HttpOnly cookies, database session expiry,
logout revocation, the OpenAPI cookie scheme, audit events for failed logins,
alarm acknowledgements and setting updates, and absence of passwords/session
tokens from captured logs.
