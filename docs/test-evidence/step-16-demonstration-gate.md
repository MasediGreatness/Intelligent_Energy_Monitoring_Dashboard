# Step 16 demonstration and traceability gate evidence

Initial rehearsal: 2026-10-05

Final clean-volume retest: 2026-10-06

## Gate summary

The deterministic data preparation and recovery rehearsal passes in an
isolated disposable project. The overall Step 16 gate remains **ready for
review, not accepted**, because the assessed browser acknowledgement, timed
student demonstration, personal explanation/signatures, and physical Raspberry
Pi evidence require human/hardware execution.

No result below is presented as physical Raspberry Pi, calibrated sensor,
gateway, trained ML, or production alarm-engine evidence.

## Reproducible package

- `docs/demo.md` provides a 7-10 minute presenter flow covering normal load,
  peak, anomaly, power quality, device dropout, alarm acknowledgement and
  API/WebSocket reconnect.
- `infra/scripts/prepare-demo.sh` has guarded `--prepare`, `--power-quality`,
  `--dropout`, and read-only `--manifest` modes. Preparation refuses non-empty
  scenario data and contains no delete/reset operation.
- `docs/final-requirements-traceability.md` maps every FR, NFR and out-of-scope
  control to implementation and retained evidence without promoting pending
  checks to passes.
- `step-16-explanation-signoff.md` requires personal reproduction and
  explanation; it is intentionally unsigned.

## Isolated fresh-seed execution

The disposable Compose project `intelligent-energy-step16` ran at loopback
`127.0.0.1:18082`. It used a new named database volume, migration head `0003`,
production API/web images, and no production/user database.

Fresh `--prepare` result:

| Item | Result |
|---|---:|
| Devices | 5 |
| Measurements | 2,400 |
| Forecasts | 15 |
| Anomalies | 1 |
| Alarms | 2 |
| Overall maximum combined demand | 33.894 kW |
| Scripted peak-window maximum | 31.848 kW |
| Derived demand limit | 30.331 kW |
| Duplicate device/timestamp groups | 0 |

The demand limit equals the stored scripted peak-window maximum divided by 1.05
(rounded to three decimals), so that peak reaches 105% of the configured limit.
The overall maximum is reported separately because the later one-device anomaly
can be higher. The two alarm fixtures are sourced
`deterministic_demo_fixture`; their first crossings are calculated from stored
combined demand at 90% and 100% of the limit. This verifies fixture
traceability, not a continuous rule engine.

The final clean-volume retest's staged `--power-quality` mode then inserted one
current row per device:

- `LOAD-002` power factor: `0.7128` (the documented deterministic profile is
  approximately 0.72 and varies with the timestamp hash).
- Measurement total: `2,405`.
- Cumulative-energy continuity was preserved.
- Duplicate groups remained zero.

After the documented non-overlap wait, `--dropout` inserted 540 records. The
pump produced only the first half of its 120-second window while the other four
devices continued. Final fixture state was:

```text
measurements=2945
forecasts=20
anomalies=1
alarms=2
duplicate_groups=0
```

The API was restarted. Readiness returned ready at migration head and the final
manifest remained `2945|20|1|2|0`, demonstrating that the committed state was
not stored in the WebSocket process. The assessed browser still needs to record
the visible `Reconnecting` -> `Connected` transition and REST-refetched state.
The final counter-decrease query returned zero; `LOAD-003` was 78 seconds old
while the other four devices were 18 seconds old, satisfying the intended
offline/dropout staging boundary.

## Packaging and safety checks

- Production API and web images built with BuildKit and reached healthy state.
- Only the web service had a loopback host binding in the rehearsal. PostgreSQL
  and API had no host-published ports; web alone published
  `127.0.0.1:18082 -> 80`.
- Bash syntax validation passed for `prepare-demo.sh`.
- The packaging contract suite passed: `5 passed`.
- The final Chromium acceptance suite passed `6/6`, covering all seven routes,
  invalid settings, API failure, visible WebSocket reconnecting, 375 px mobile
  navigation, and non-echoing invalid login.
- The script's repeat-preparation guard refused an already populated scenario
  database without modifying it.
- The stage overlap guard refused a dropout whose 120-second window would
  overlap the latest record; the waited retest passed.

## Value-to-rule audit

The demonstration guide maps every presented value to its PostgreSQL/API source
and documented calculation. Key proof points are:

- current demand excludes stale/disabled/missing devices rather than treating
  them as zero;
- energy is cumulative-counter delta with baseline/reset rules;
- interval demand is time weighted and peak requires 90% completeness;
- history buckets expose sample count and completeness;
- simulator forecast/anomaly values retain seed/model/fixture labels;
- demand alarms are explicitly fixture-derived from measurements and setting;
- acknowledgement is attributed and audited;
- reconnect refetches REST because PostgreSQL/REST remains authoritative.

See `docs/demo.md` for the full field-level table and
`docs/final-requirements-traceability.md` for requirement-level mapping.

## Remaining gate actions

- [ ] Student performs the full browser flow in 7-10 minutes from a fresh demo
      volume and retains prepare/final manifests and screenshots.
- [ ] Student acknowledges an alarm through the UI with a review note, then
      shows matching actor, UTC time and immutable audit event.
- [ ] Browser visibly shows API/WebSocket `Reconnecting` -> `Connected` and the
      authoritative REST refetch after restart.
- [ ] Student and reviewer complete every explanation item and sign/date
      `step-16-explanation-signoff.md`.
- [ ] Student signs/dates the institution-compatible AI Use Declaration after
      personally verifying it.
- [ ] Reviewer completes the Step 15 physical Pi clean-install, reboot,
      clean-volume restore and controlled power-interruption checklist.

## Gate decision

Reproducible preparation, traceability, data integrity and backend restart:
**Pass in isolated local rehearsal**.

Step 16 overall: **Pending student test, explanation and review**.

Physical Raspberry Pi acceptance: **Pending hardware evidence**.
