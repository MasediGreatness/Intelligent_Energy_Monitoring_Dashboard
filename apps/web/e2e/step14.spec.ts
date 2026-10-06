import process from 'node:process'

import { expect, test, type Page } from '@playwright/test'

const email = process.env.E2E_EMAIL
const password = process.env.E2E_PASSWORD
const evidenceStep = process.env.E2E_EVIDENCE_STEP ?? '14'
const credentialsAvailable = Boolean(email && password)

async function login(page: Page) {
  await page.goto('/login')
  await page.getByLabel('Email address').fill(email!)
  await page.getByLabel('Password').fill(password!)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(
    page.getByRole('heading', { name: 'Energy overview' }),
  ).toBeVisible()
}

test.describe('Step 14 acceptance flows', () => {
  test.skip(!credentialsAvailable, 'Set E2E_EMAIL and E2E_PASSWORD.')

  test('all seven authenticated routes and admin controls are usable', async ({
    page,
  }) => {
    await login(page)
    const routes = [
      ['/', 'Energy overview'],
      ['/live', 'Live monitoring'],
      ['/history', 'Energy history'],
      ['/forecast', 'Forecast and anomalies'],
      ['/alarms', 'Alarms'],
      ['/devices', 'Devices'],
      ['/settings', 'Dashboard settings'],
    ] as const
    for (const [path, heading] of routes) {
      await page.goto(path)
      await expect(
        page.getByRole('heading', { level: 1, name: heading }),
      ).toBeVisible()
    }
    await expect(
      page.getByRole('button', { name: 'Save settings' }),
    ).toBeVisible()
    await page.screenshot({
      path: `../../docs/test-evidence/step-${evidenceStep}-desktop-settings.png`,
      fullPage: true,
    })
  })

  test('invalid settings fail before any write request', async ({ page }) => {
    await login(page)
    await page.goto('/settings')
    let patchCount = 0
    page.on('request', (request) => {
      if (request.method() === 'PATCH' && request.url().includes('/settings/'))
        patchCount += 1
    })
    await page
      .getByRole('spinbutton', { name: 'Stale timeout (seconds)' })
      .fill('5')
    await page.getByRole('button', { name: 'Save settings' }).click()
    await expect(
      page.getByText(
        'Stale timeout must be a whole number greater than online timeout.',
      ),
    ).toBeVisible()
    expect(patchCount).toBe(0)
  })

  test('API interruption shows a retryable honest error', async ({ page }) => {
    await login(page)
    await page.route('**/api/v1/dashboard/summary*', (route) => route.abort())
    await page.route('**/api/v1/measurements/latest*', (route) => route.abort())
    await page.goto('/')
    await expect(
      page.getByText(
        'The overview API is unavailable. Existing values are not replaced with zero.',
      ),
    ).toBeVisible({ timeout: 15_000 })
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible()
    await page.screenshot({
      path: `../../docs/test-evidence/step-${evidenceStep}-api-unavailable.png`,
      fullPage: true,
    })
  })

  test('WebSocket interruption is visible as reconnecting', async ({
    page,
  }) => {
    await page.routeWebSocket('**/api/v1/ws/live', (socket) => socket.close())
    await login(page)
    await expect(page.getByText('Reconnecting')).toBeVisible()
  })

  test('375 px mobile navigation reaches core workflows', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 })
    await login(page)
    await page.getByRole('button', { name: 'Open navigation' }).click()
    await page.getByRole('link', { name: 'Devices' }).click()
    await expect(
      page.getByRole('heading', { level: 1, name: 'Devices' }),
    ).toBeVisible()
    await expect(
      page.getByRole('button', { name: 'Create device' }),
    ).toBeVisible()
    await expect(page.getByText('LOAD-001')).toBeVisible()
    await page.screenshot({
      path: `../../docs/test-evidence/step-${evidenceStep}-mobile-devices.png`,
      fullPage: true,
    })
  })

  test('invalid login is rejected without echoing the password', async ({
    page,
  }) => {
    await page.goto('/login')
    await page.getByLabel('Email address').fill(email!)
    await page.getByLabel('Password').fill('definitely-wrong-password')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByRole('alert')).toHaveText(
      'The email or password is invalid.',
    )
    await expect(page.locator('body')).not.toContainText(
      'definitely-wrong-password',
    )
  })
})
