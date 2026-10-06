# ADR-009: Shareable analysis filters and CSV contract

- Status: Accepted at the Step 12 gate
- Date: 2026-08-16

## Decision

History analysis stores `from`, `to`, `device`, and `interval` in the browser
query string. Forecast and anomaly analysis stores `device`, `horizon`,
`from`, `to`, and `severity` there. A filter change updates the URL immediately
and the URL values form the corresponding REST query, making a view shareable
and reproducible.

Long ranges enforce a minimum aggregation before a request is issued: more than
one day uses at least one-minute buckets, more than two days uses at least
15-minute buckets, and more than 14 days uses at least hourly buckets. The
backend's 31-day maximum remains authoritative.

History CSV uses RFC 4180-compatible comma-separated rows with CRLF endings.
Its fixed headings are `timestamp_utc`, `device_id`, `active_power_kw`,
`sample_count`, and `completeness_pct`. The timestamp is ISO 8601 UTC and the
power unit is explicit in the heading. Missing power is an empty field, never
numeric zero. Export serializes the same filtered backend buckets rendered by
the chart.

## Consequences

- Analysis links can be bookmarked, shared, and reproduced.
- Large ranges remain bounded without silently requesting raw data.
- Spreadsheet users receive explicit time basis, units, and data-quality
  evidence.
- Changing query names or CSV headings is a contract change requiring a test
  and decision update.
