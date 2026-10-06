# ADR-007: Responsive dashboard shell and design system

- Status: Accepted at the Step 10 gate
- Date: 2026-08-16

## Decision

Use a protected React application shell with seven fixed primary routes:
Overview, Live Monitoring, Energy History, Forecast and Anomalies, Alarms,
Devices, and Settings. The shell uses a persistent desktop navigation rail, a
collapsed tablet rail, and an off-canvas mobile menu below 720 px.

The visual contract uses navy `#102A43`, blue `#1677FF`, teal `#18A0AE`, green
`#1F9D55`, amber `#F59E0B`, red `#D64545`, and background `#F4F7FA`. Shared
tokens define typography, spacing, cards, controls, tables, and status badges.
Every status combines text with an icon or marker; color is never its only
meaning.

Reusable loading, empty, error, permission, and stale-data states must be used
instead of page-specific substitutes. Data tables own their deliberate
horizontal scrolling so the page itself never overflows on a 375 px viewport.

## Consequences

- New dashboard features inherit one navigation, responsive, and accessibility
  contract.
- Protected routes cannot render operational content before identity is known.
- Visible focus, reduced-motion support, and WCAG AA contrast remain regression
  requirements for later steps.
- Changes to route names, breakpoints, tokens, or status semantics require an
  explicit decision update so frontend and backend terminology cannot drift.
