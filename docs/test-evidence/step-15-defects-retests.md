# Step 15 defect and retest log

Date: 2026-08-18

| ID | Initial severity | Observation | Resolution | Retest/result | State |
|---|---|---|---|---|---|
| D15-001 | Medium | The first API builder upgraded pip without a declared version, adding avoidable build drift. | Removed the upgrade; the builder installs only the declared runtime requirements. | Native and actual ARM64 API targets build successfully; the final runtime starts healthy. | Closed |
| D15-002 | High | The setup CLI accepted an address that the login `EmailStr` contract rejected, which could create an administrator unable to log in. | Reused Pydantic `EmailStr` validation and the same normalization rule in explicit user setup. | New unit cases cover valid normalization and invalid domains; 102 backend tests and final admin/E2E setup pass. | Closed |
| D15-003 | Medium | `docker kill` models an operator stop, so `unless-stopped` intentionally did not restart PostgreSQL in the first abrupt-stop experiment. | Added init wrappers and changed the guarded drill to SIGKILL the PostgreSQL child, leaving Docker to observe unexpected PID 1 exit. | DB restart count incremented to one; readiness, 600 measurements, and zero duplicates were preserved. | Closed |
| D15-004 | Medium | The original web ARM64 cross-build ran Vite under QEMU and stalled. | Run the architecture-independent Node build stages on `$BUILDPLATFORM`; retain the requested target platform for final Nginx. | Actual `linux/arm64` production web target completed in 1m47s; native production build also passes. | Closed |
| D15-005 | Low | The first API ARM64 retry failed while resolving `files.pythonhosted.org`. | Verified ARM64 container DNS separately and reran without a source change. | Actual `linux/arm64` API target completed with ARM64 binary wheels in 10m20s. | Closed |
| D15-006 | Low | A disposable final E2E user could not be deleted while immutable audit/session foreign keys still referenced it. | Verified all four user foreign-key consumers, confirmed zero alarm/settings references, then removed only its five sessions, five audit rows, and user in one transaction. | Fixture count is zero; source/restore remain 2 users and all integrity counts match. | Closed |

## Environment observations

| ID | Severity | Observation | Disposition |
|---|---|---|---|
| O15-001 | Low | Docker Desktop needed one restart after the two cross-builds. | Restored the development and pre-existing unrelated containers to their prior running state. Both Step 15 projects auto-restarted, remained healthy, and retained exact counts. This is not attributed to application code. |
| O15-002 | Low | Vite reports a 743.07 kB main production chunk (220.00 kB gzip). | Retain the previously accepted optimization debt; all browser flows pass. |
| O15-003 | Low | Starlette emits its existing future `httpx2` test-client deprecation warning. | Track during dependency maintenance; all 102 tests pass. |

No critical/high implementation defect remains open. Physical Pi evidence is a
gate prerequisite, not an implementation defect.
