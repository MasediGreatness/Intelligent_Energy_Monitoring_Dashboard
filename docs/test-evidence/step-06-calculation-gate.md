# Step 6 calculation gate

- Date: 2026-08-15
- Ruff: passed (`ruff check apps/api`)
- Mypy strict mode: passed (`mypy apps/api/app`)
- Pytest: 50 passed, 2 upstream deprecation warnings

The hand-calculated fixtures cover device status boundaries, current demand,
cumulative energy with a counter reset, missing baselines, completeness and gap
counts, time-weighted 15-minute demand, completeness-qualified peak demand,
equal-period comparison, estimated cost, all six aggregation intervals, empty
buckets, and raw/aggregate history-range limits.

The two warnings originate in the installed FastAPI/Starlette test stack and do
not indicate calculation or test failures.
