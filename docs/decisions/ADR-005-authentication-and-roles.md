# ADR-005: Opaque sessions and fixed dashboard roles

- Status: Accepted by user at the Step 8 gate on 2026-08-16
- Date: 2026-08-16

## Decision

Use Argon2id password hashes and random opaque browser sessions. Store only the
SHA-256 session-token hash, expiry, and revocation time in PostgreSQL. Deliver
the token in the fixed `energy_session` HttpOnly, SameSite=Strict cookie.
Control the cookie's `Secure` attribute with the explicit
`SESSION_COOKIE_SECURE` deployment setting: keep it `false` for the documented
private-LAN HTTP deployment, and require `true` whenever HTTPS/TLS termination
is enabled. Sessions expire after 30 minutes by default and are revoked at
logout.

The fixed authorization order is viewer < operator < admin. All roles may read;
operators and admins may acknowledge alarms; only admins may edit settings.
Gateway ingestion remains a separate machine-authenticated trust boundary.

No default user is seeded. User creation or reset requires the explicit CLI,
with the password supplied through a temporary environment variable or hidden
interactive prompt.

## Consequences

- Logout and forced expiry take effect without maintaining a process-local
  denylist and therefore work across API workers.
- Database lookup is required for each authenticated request.
- The browser never receives password hashes or a token in JSON or JavaScript.
- `SESSION_COOKIE_SECURE=true` is required for HTTPS deployments, while setting
  it incorrectly for an HTTP-only endpoint prevents the browser from sending
  the session cookie.
