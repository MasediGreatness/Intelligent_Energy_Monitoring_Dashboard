# Step 10 dashboard-shell gate evidence

Date: 2026-08-16

## Automated checks

- `npm run lint`: passed.
- `npm run test`: 12 tests passed across two files.
- `npm run build`: production TypeScript and Vite build passed.
- Backend regression: 65 tests passed on the full run; its one configuration-
  sensitive live test was corrected and passed in isolation. Ruff and MyPy pass.
- Route test renders all seven protected pages and verifies `aria-current` on
  the corresponding navigation link.
- Authentication test verifies unauthenticated navigation redirects to login.
- `axe-core` smoke test reports no serious or critical violations for the
  rendered dashboard shell.

## Live browser review

- Signed in through the real login screen with an explicit local review user.
- Confirmed the protected Overview shell renders with the connection badge,
  user menu, navigation, status semantics, and reusable data states.
- Navigated to Devices and confirmed `/devices` plus the correct active link.
- Confirmed keyboard focus reaches a navigation link and the focus treatment is
  visible.
- Desktop viewport measured `scrollWidth == clientWidth` (zero page overflow).
- Responsive CSS uses a collapsed navigation at 1024 px and an off-canvas,
  stacked layout at 720 px; the only horizontal overflow primitive is the
  focusable `.table-scroll` region with its own `overflow-x: auto`.

## Gate result

Implementation checks pass. ADR-007 and the Step 10 visual/responsive behavior
remain subject to user review before Step 11 begins.
