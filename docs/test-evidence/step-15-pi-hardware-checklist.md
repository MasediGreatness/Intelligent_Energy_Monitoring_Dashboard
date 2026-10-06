# Step 15 Raspberry Pi hardware gate checklist

Date prepared: 2026-08-18

This checklist must be completed on a physical Raspberry Pi 4 ARM64 before
Step 15 can be accepted. Local Docker, ARM64 cross-build, restore, and abrupt
database-process tests do not substitute for the three hardware checks below.
Follow `../operations.md` and do not put credentials in this record.

## Deployment identity

- Reviewer/operator:
- Pi model and RAM:
- 64-bit OS name/version:
- Kernel and `uname -m` output:
- Private LAN address and dashboard port:
- Git commit or immutable image tag:
- Review start/end in UTC:

## A. Clean install and reboot

- [ ] Began with no application containers or application database volume.
- [ ] `pi-preflight.sh` passed without an override.
- [ ] ARM64 images built from the documented command.
- [ ] Database started, migration reached the single head, fixed devices were
      seeded if required, and the administrator was created explicitly.
- [ ] `db`, `api`, and `web` were healthy and the dashboard loaded from another
      private-LAN device.
- [ ] The Pi was rebooted normally.
- [ ] The three services returned healthy automatically after reboot.
- [ ] `integrity-check.sh` passed after reboot.

Evidence/notes:

```text
preflight result:
compose ps before reboot:
compose ps after reboot:
integrity result:
dashboard screenshot filename:
```

## B. Backup restored into a clean volume

- [ ] A custom-format backup and its SHA-256 file were copied to separate
      protected media.
- [ ] The checksum and `pg_restore --list` validation passed.
- [ ] `restore-drill.sh` created a previously absent drill volume.
- [ ] The restored revision and device/measurement/alarm counts match source.
- [ ] Duplicate `(device_id, measured_at)` groups equal zero.
- [ ] The restored dashboard displays the retained records.

Evidence/notes:

```text
backup filename and SHA-256:
source revision/devices/measurements/alarms/duplicates:
restored revision/devices/measurements/alarms/duplicates:
restored dashboard screenshot filename:
```

## C. Physical power interruption

- [ ] A verified backup exists off the Pi before this test.
- [ ] Before counts and integrity were recorded while fixed timestamped records
      were being ingested.
- [ ] Power was removed once without an operating-system shutdown and restored.
- [ ] PostgreSQL recovery and all service health checks completed.
- [ ] After counts, migration revision, and duplicate groups were recorded.
- [ ] No corrupt/partial row or second unique row exists. An in-flight
      transaction may be wholly present or absent; an identical retry may be
      reported as a duplicate.
- [ ] A new post-interruption backup validates and the dashboard shows retained
      records.

Evidence/notes:

```text
before timestamp/counts:
after timestamp/counts:
compose ps after power return:
integrity result:
post-interruption backup filename and SHA-256:
dashboard screenshot filename:
observed recovery time and behaviour:
```

## Reviewer decision

- [ ] Pass — all three hardware checks meet the documented conditions.
- [ ] Fail — defect IDs and retest requirements are recorded below.

Defects/observations:

Reviewer name/signature:
Decision date in UTC:
