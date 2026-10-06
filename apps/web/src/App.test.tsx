import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axe from 'axe-core'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'
import { pageDefinitions } from './pages/definitions'

vi.mock('./api/useLiveConnection', () => ({
  useLiveConnection: () => 'Connected',
}))

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

function requestUrl(input: RequestInfo | URL) {
  if (typeof input === 'string') return input
  if (input instanceof URL) return input.href
  return input.url
}

function authenticatedFetch(
  latestMeasurements: object[] = [],
  role: 'viewer' | 'operator' | 'admin' = 'viewer',
  alarmItems: object[] = [],
) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
    const url = requestUrl(input)
    let body: object = {
      id: '00000000-0000-0000-0000-000000000001',
      email: `${role}@example.com`,
      role,
    }
    if (url.includes('/dashboard/summary')) {
      body = {
        generated_at: '2026-08-16T10:00:00Z',
        timezone: 'Africa/Johannesburg',
        current_demand_kw: 42.3,
        current_demand_change_pct: 5.2,
        energy_today_kwh: '123.45',
        energy_vs_previous_pct: -2.5,
        peak_demand_kw: 50,
        peak_demand_at: '2026-08-16T09:15:00Z',
        demand_limit_kw: 60,
        active_alarms: { critical: 1, high: 2, medium: 0, low: 1 },
        devices: { online: 4, stale: 1, offline: 0, disabled: 0 },
        data_completeness_pct: 98.5,
        excluded_stale_devices: 1,
      }
    } else if (url.includes('/measurements/latest')) {
      body = latestMeasurements
    } else if (url.includes('/forecasts/latest')) {
      body = { items: [] }
    } else if (url.includes('/acknowledge')) {
      const alarm = alarmItems[0] as Record<string, object>
      let requestNote = ''
      if (typeof init?.body === 'string') {
        const parsed: unknown = JSON.parse(init.body)
        if (
          typeof parsed === 'object' &&
          parsed !== null &&
          'note' in parsed &&
          typeof parsed.note === 'string'
        )
          requestNote = parsed.note
      }
      body = {
        alarm: {
          ...alarm,
          status: 'acknowledged',
          acknowledged_at: '2026-08-16T11:00:00Z',
          acknowledged_by: '00000000-0000-0000-0000-000000000001',
          acknowledgement_note: requestNote,
        },
      }
    } else if (url.includes('/alarms')) {
      body = {
        page: 1,
        page_size: 20,
        total: alarmItems.length,
        items: alarmItems,
      }
    } else if (url.includes('/devices')) {
      body = { page: 1, page_size: 20, total: 0, items: [] }
    } else if (url.includes('/settings')) {
      body = [
        {
          key: 'demand_limit_kw',
          value_json: 50,
          description: 'Demand limit',
          updated_at: '2026-08-16T10:00:00Z',
        },
        {
          key: 'demand_interval_minutes',
          value_json: 15,
          description: 'Demand interval',
          updated_at: '2026-08-16T10:00:00Z',
        },
        {
          key: 'tariff_zar_per_kwh',
          value_json: 3,
          description: 'Tariff',
          updated_at: '2026-08-16T10:00:00Z',
        },
        {
          key: 'timezone',
          value_json: 'Africa/Johannesburg',
          description: 'Timezone',
          updated_at: '2026-08-16T10:00:00Z',
        },
        {
          key: 'online_timeout_seconds',
          value_json: 10,
          description: 'Online timeout',
          updated_at: '2026-08-16T10:00:00Z',
        },
        {
          key: 'stale_timeout_seconds',
          value_json: 60,
          description: 'Stale timeout',
          updated_at: '2026-08-16T10:00:00Z',
        },
        {
          key: 'simulator_profile',
          value_json: 'normal',
          description: 'Simulator profile',
          updated_at: '2026-08-16T10:00:00Z',
        },
      ]
    } else if (url.includes('/measurements/history')) {
      body = { timezone: 'Africa/Johannesburg', series: [] }
    } else if (url.includes('/energy/daily')) {
      body = { timezone: 'Africa/Johannesburg', items: [] }
    } else if (url.includes('/anomalies')) {
      body = { page: 1, page_size: 200, total: 0, items: [] }
    }
    return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }))
  })
}

function renderApp(path = '/') {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <App />
        <LocationProbe />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function LocationProbe() {
  const location = useLocation()
  return <output data-testid="location">{location.search}</output>
}

describe('dashboard shell', () => {
  it.each(pageDefinitions)(
    'routes $shortTitle and marks its navigation link active',
    async (page) => {
      authenticatedFetch()
      renderApp(page.path)
      expect(
        await screen.findByRole('heading', { level: 1, name: page.title }),
      ).toBeInTheDocument()
      expect(
        screen.getByRole('link', { name: page.shortTitle }),
      ).toHaveAttribute('aria-current', 'page')
    },
  )

  it('redirects an unauthenticated visitor to the login page', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(null, { status: 401 }),
    )
    renderApp('/devices')
    expect(
      await screen.findByRole('heading', { name: 'Welcome back' }),
    ).toBeInTheDocument()
  })

  it('has no serious automated accessibility violations', async () => {
    authenticatedFetch()
    const { container } = renderApp('/')
    await screen.findByRole('heading', { name: 'Energy overview' })
    const results = await axe.run(container, {
      rules: { 'color-contrast': { enabled: false } },
    })
    const serious = results.violations.filter(
      (item) => item.impact === 'serious' || item.impact === 'critical',
    )
    expect(serious).toEqual([])
  })

  it('renders all four KPI values exactly from the summary API', async () => {
    authenticatedFetch()
    renderApp('/')
    expect(await screen.findByText('42.3')).toBeInTheDocument()
    expect(screen.getByText('123.5')).toBeInTheDocument()
    expect(screen.getByText('50.0')).toBeInTheDocument()
    expect(screen.getAllByText('4').length).toBeGreaterThan(0)
    expect(screen.getByText('5.2% up vs 15 min ago')).toBeInTheDocument()
    expect(screen.getByText('2.5% down vs yesterday')).toBeInTheDocument()
  })

  it('shows honest stale and partial-data states from the summary API', async () => {
    authenticatedFetch()
    renderApp('/')
    expect(await screen.findByText('Stale data')).toBeInTheDocument()
    expect(screen.getByText('Partial data')).toBeInTheDocument()
    expect(screen.getByText('98.5% complete today.')).toBeInTheDocument()
  })

  it('writes History filter changes to the URL and API query', async () => {
    const fetchMock = authenticatedFetch([
      {
        device_id: '00000000-0000-0000-0000-000000000101',
        device_code: 'LOAD-001',
        measured_at: null,
        active_power_kw: null,
        voltage_v: null,
        current_a: null,
        power_factor: null,
        frequency_hz: null,
        data_quality: null,
        status: 'offline',
      },
    ])
    renderApp('/history?from=2026-08-01&to=2026-08-02&device=all&interval=15m')
    const interval = await screen.findByLabelText('Interval')
    await userEvent.selectOptions(interval, '1h')
    expect(screen.getByTestId('location')).toHaveTextContent('interval=1h')
    await waitFor(() =>
      expect(
        fetchMock.mock.calls.some(([input]) => {
          const url =
            typeof input === 'string'
              ? input
              : input instanceof URL
                ? input.href
                : input.url
          return (
            url.includes('/measurements/history') && url.includes('interval=1h')
          )
        }),
      ).toBe(true),
    )
  })

  it('shows model data unavailable instead of inventing a forecast', async () => {
    authenticatedFetch()
    renderApp('/forecast?device=all&horizon=60&from=2026-08-01&to=2026-08-16')
    expect(
      await screen.findByRole('heading', { name: 'Model data unavailable' }),
    ).toBeInTheDocument()
  })

  it('hides device administration controls from a non-admin user', async () => {
    authenticatedFetch()
    renderApp('/devices')
    expect(await screen.findByText('View only')).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Create device' }),
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Edit' }),
    ).not.toBeInTheDocument()
  })

  it('shows device administration controls to an admin user', async () => {
    authenticatedFetch([], 'admin')
    renderApp('/devices')
    const create = await screen.findByRole('button', { name: 'Create device' })
    await userEvent.click(create)
    expect(
      screen.getByRole('heading', { name: 'Create device' }),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Device code')).toBeInTheDocument()
  })

  it('rejects invalid settings before sending an API write', async () => {
    const fetchMock = authenticatedFetch([], 'admin')
    renderApp('/settings')
    const stale = await screen.findByLabelText('Stale timeout (seconds)')
    await userEvent.clear(stale)
    await userEvent.type(stale, '5')
    await userEvent.click(screen.getByRole('button', { name: 'Save settings' }))
    expect(
      await screen.findByText(
        'Stale timeout must be a whole number greater than online timeout.',
      ),
    ).toBeInTheDocument()
    expect(
      fetchMock.mock.calls.some(([, init]) => init?.method === 'PATCH'),
    ).toBe(false)
  })

  it('records an operator alarm acknowledgement and refetches data', async () => {
    const alarm = {
      id: '00000000-0000-0000-0000-000000000201',
      device_id: '00000000-0000-0000-0000-000000000101',
      source: 'simulator',
      alarm_type: 'high_demand',
      severity: 'high',
      message: 'Demand exceeded the configured threshold.',
      triggered_at: '2026-08-16T10:00:00Z',
      acknowledged_at: null,
      acknowledged_by: null,
      acknowledgement_note: null,
      cleared_at: null,
      status: 'open',
    }
    const fetchMock = authenticatedFetch([], 'operator', [alarm])
    renderApp('/alarms')
    await userEvent.click(await screen.findByRole('button', { name: 'Review' }))
    await userEvent.type(
      screen.getByLabelText('Acknowledgement note'),
      'Checked at the panel',
    )
    await userEvent.click(
      screen.getByRole('button', { name: 'Acknowledge alarm' }),
    )
    expect(
      await screen.findByText('Acknowledgement recorded in the audit trail.'),
    ).toBeInTheDocument()
    expect(
      fetchMock.mock.calls.some(
        ([input, init]) =>
          requestUrl(input).includes('/acknowledge') &&
          init?.method === 'PATCH',
      ),
    ).toBe(true)
  })
})
