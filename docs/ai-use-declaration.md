# AI Use Declaration - Student Completion Template

> **Status: UNSIGNED TEMPLATE - NOT A COMPLETED DECLARATION**
>
> The student must compare this template with the institution/module's current
> official declaration wording, correct it to match actual use, describe their
> own verification in their own words, then sign and date it. Do not submit this
> file unchanged as proof of personal verification.

## Student and work identification

| Item | Student to complete |
|---|---|
| Student full name | `[enter]` |
| Student number | `[enter]` |
| Module/course | `[enter exact module title/code]` |
| Assessment/project | Intelligent Industrial Energy Monitoring and Predictive Load Management System - dashboard subsystem |
| Institution | `[enter]` |
| Declaration policy/version consulted | `[enter document title/version/date]` |

## Draft disclosure - verify and rewrite if necessary

I used an AI-assisted coding tool (OpenAI Codex) as a supportive implementation
aid for the dashboard subsystem. Subject to my verification below, assistance
included interpreting the supplied implementation specification, proposing and
editing source code and configuration, creating automated tests, running local
commands, diagnosing failures, and drafting technical handoff documentation.

The AI tool did not provide measured hardware results, trained machine-learning
results, or evidence from a physical Raspberry Pi. Those items are not claimed
as complete. The monitoring-only subsystem contains no real load-control path.

I understand that AI output is not evidence of correctness or personal
understanding. I remain responsible for checking the implementation, evidence,
citations, calculations, security/safety boundaries, and every statement made in
my submission. My final academic explanation, engineering judgement,
conclusions, and defence are my own.

**Student correction/confirmation of the paragraph above:**

`[Describe the AI systems actually used, dates/scope, and any material use not
captured above. Delete claims that are not true. Use your own words.]`

## Use record

Complete this table from the actual conversation/repository history. Add rows
where needed; do not invent prompt text or results.

| AI system/version (if known) | Date/range | Purpose | Artifact(s) affected | What the student changed/accepted/rejected |
|---|---|---|---|---|
| OpenAI Codex `[verify model/version if required]` | `[enter]` | Requirements-to-code implementation support | `[enter paths/steps]` | `[enter]` |
| OpenAI Codex `[verify]` | `[enter]` | Test generation/execution and failure diagnosis | `[enter evidence]` | `[enter]` |
| OpenAI Codex `[verify]` | `[enter]` | Technical README/architecture/contract/runbook drafting | `[enter]` | `[enter]` |

## Personal verification performed

Only tick an item after personally performing it. Enter commands, evidence paths,
dates, and outcomes rather than writing "checked" without support.

### Requirements, design, and safety

- [ ] I read the controlling build specification and can map the implemented
      subsystem to its in-scope and out-of-scope requirements.
- [ ] I reviewed every ADR and can explain the selected option, alternatives,
      consequences, and any unresolved trade-off.
- [ ] I verified there is no enabled relay, contactor, load-shed, restore, or
      industrial-load control path.
- [ ] I reconciled the architecture, API contract, data dictionary, generated
      OpenAPI/types, migrations, and implementation for contract drift.

Evidence/notes in my own words:

`[enter]`

### Engineering calculations and data meaning

- [ ] I independently reproduced at least one controlled fixture for current
      demand, cumulative energy across a reset, time-weighted demand, peak demand,
      completeness, equal-period comparison, and estimated cost.
- [ ] I can explain why missing/stale data is excluded or marked rather than
      represented as zero.
- [ ] I checked the UTC/local-time boundary, SI units, display precision, and
      cumulative-meter reset meaning.

Fixture identifiers, manual calculations, tolerances, and outcomes:

`[enter - attach or link the student's own calculation record]`

### Code and automated verification

- [ ] I reviewed the changed backend, frontend, migration, deployment, and test
      files and can explain the critical paths without generated text.
- [ ] I personally ran the documented backend tests, static checks, frontend
      tests/build, and Playwright flows from a clean checkout.
- [ ] I inspected failures and test evidence rather than relying only on an AI
      summary.
- [ ] I confirmed no password, token, ingest key, `.env`, database volume, or
      backup is committed.

Commands, environment, date, exact results, and evidence paths:

`[enter]`

### Demonstration and failure behaviour

- [ ] I prepared a fresh deterministic seed and personally demonstrated normal
      load, peak, anomaly, device dropout, alarm acknowledgement, and reconnect.
- [ ] I traced displayed values to source records, backend rules, API responses,
      and UI formatting.
- [ ] I can explain what the user sees for loading, empty, error, stale, partial,
      offline, permission, and reconnect states.

Demonstration date, seed, observations, and retained evidence:

`[enter]`

### Raspberry Pi and operational verification

- [ ] I completed the physical Raspberry Pi clean-install and reboot checks.
- [ ] I restored a verified backup into a clean Pi volume and confirmed records
      in the dashboard.
- [ ] I completed the controlled physical power-interruption test and verified
      row integrity/duplicate counts afterward.
- [ ] I recorded target Pi performance/resources and confirmed LAN exposure.

Physical Pi evidence and signed checklist:

`[PENDING unless docs/test-evidence/step-15-pi-hardware-checklist.md is fully
completed and signed]`

## Limitations acknowledged

I reviewed `docs/limitations.md` and will not present the following as completed
evidence unless separately implemented and verified:

- physical sensor/gateway integration and calibration;
- trained forecasting/anomaly models or their accuracy;
- real automatic/manual load control;
- public-internet or production-security certification;
- billing-grade metering or tariff accuracy;
- Raspberry Pi acceptance while the physical checklist is incomplete.

Additional limitations I identified personally:

`[enter]`

## Source and originality confirmation

- [ ] I identified and cited external sources according to the institution's
      referencing rules.
- [ ] I verified that no unsupported or fabricated citation, test result, or
      hardware observation is included.
- [ ] I wrote the final academic analysis, evaluation, conclusions, and oral
      explanation myself and did not submit generated text without critical
      review and permitted attribution.
- [ ] My declaration matches the institution/module's official policy; where
      that policy requires a separate form or exact wording, I used it.

## Student declaration and signature

I declare that the disclosure above is complete and accurate, that I personally
performed the verification I marked, and that I take responsibility for the
submitted work and claims.

| Field | Student to complete personally |
|---|---|
| Full name | `[enter]` |
| Signature | `[sign]` |
| Date | `[YYYY-MM-DD]` |
| Supervisor/reviewer acknowledgement, if required | `[enter/sign]` |

Until the student completes and signs this section, this document is a workflow
aid only and must not be represented as a signed AI Use Declaration.
