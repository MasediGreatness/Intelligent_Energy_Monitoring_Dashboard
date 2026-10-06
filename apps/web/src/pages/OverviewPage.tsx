import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  getDashboardSummary,
  getHistory,
  getLatestForecast,
  getLatestMeasurements,
  getRecentAlarms,
  type ForecastItem,
  type HistoryResponse,
  type Severity,
} from '../api/dashboard'
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
  StaleBanner,
} from '../components/states/DataStates'
import { MetricCard } from '../components/dashboard/MetricCard'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import {
  absoluteTime,
  chartTime,
  numberOrDash,
  percentContext,
  relativeTime,
} from '../utils/format'

interface ChartRow {
  at: string
  actual?: number
  forecast?: number
}

function totalActual(history?: HistoryResponse): ChartRow[] {
  if (!history?.series.length) return []
  const values = new Map<string, number[]>()
  history.series.forEach((series) =>
    series.points.forEach((point) => {
      if (point.value === null) return
      const bucket = values.get(point.bucket_at) ?? []
      bucket.push(point.value)
      values.set(point.bucket_at, bucket)
    }),
  )
  return [...values.entries()]
    .map(([at, items]) => ({
      at,
      actual: Number(items.reduce((sum, value) => sum + value, 0).toFixed(3)),
    }))
    .sort((a, b) => a.at.localeCompare(b.at))
}

function totalForecast(items?: ForecastItem[]): ChartRow[] {
  if (!items?.length) return []
  const values = new Map<string, number[]>()
  items.forEach((item) => {
    const bucket = values.get(item.target_at) ?? []
    bucket.push(item.predicted_power_kw)
    values.set(item.target_at, bucket)
  })
  return [...values.entries()]
    .map(([at, predictions]) => ({
      at,
      forecast: Number(
        predictions.reduce((sum, value) => sum + value, 0).toFixed(3),
      ),
    }))
    .sort((a, b) => a.at.localeCompare(b.at))
}

function severityTone(severity: Severity) {
  if (severity === 'critical' || severity === 'high') return 'critical' as const
  if (severity === 'medium') return 'warning' as const
  return 'info' as const
}

export function OverviewPage() {
  const summary = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: ({ signal }) => getDashboardSummary(signal),
  })
  const latest = useQuery({
    queryKey: ['latest-measurements'],
    queryFn: ({ signal }) => getLatestMeasurements(signal),
  })
  const deviceIds = useMemo(
    () => latest.data?.map((item) => item.device_id) ?? [],
    [latest.data],
  )
  const history = useQuery({
    queryKey: ['overview-history', deviceIds.join(',')],
    queryFn: ({ signal }) => {
      const to = new Date()
      const from = new Date(to.getTime() - 24 * 60 * 60 * 1000)
      return getHistory(
        deviceIds,
        from.toISOString(),
        to.toISOString(),
        '15m',
        signal,
      )
    },
    enabled: deviceIds.length > 0,
  })
  const forecast = useQuery({
    queryKey: ['latest-forecast', 60],
    queryFn: ({ signal }) => getLatestForecast(signal),
  })
  const alarms = useQuery({
    queryKey: ['recent-alarms'],
    queryFn: ({ signal }) => getRecentAlarms(signal),
  })
  const chartRows = useMemo(
    () => [
      ...totalActual(history.data),
      ...totalForecast(forecast.data?.items),
    ],
    [history.data, forecast.data],
  )

  if (summary.isPending || latest.isPending)
    return <LoadingPanel fullPage label="Loading energy overview" />
  if (summary.isError || latest.isError)
    return (
      <ErrorPanel
        fullPage
        message="The overview API is unavailable. Existing values are not replaced with zero."
        onRetry={() => {
          void summary.refetch()
          void latest.refetch()
        }}
      />
    )

  const data = summary.data
  const alarmTotal = Object.values(data.active_alarms).reduce(
    (sum, count) => sum + count,
    0,
  )
  const stale = data.excluded_stale_devices > 0 || data.devices.stale > 0
  const partial = data.data_completeness_pct < 100
  const alarmBreakdown = Object.entries(data.active_alarms)
    .map(([severity, count]) => `${severity}: ${count}`)
    .join(', ')

  return (
    <>
      <PageHeader
        eyebrow="OPERATIONS"
        title="Energy overview"
        description="API-authoritative demand, energy, peak demand and operational health."
        action={<StatusBadge tone="info">Africa/Johannesburg</StatusBadge>}
      />
      {stale ? (
        <StaleBanner
          message={`${data.excluded_stale_devices} device(s) were excluded from current demand because their data is stale, offline, disabled or missing.`}
        />
      ) : null}
      {partial ? (
        <aside className="notice notice-info overview-notice" role="status">
          <div>
            <strong>Partial data</strong>
            <p>{data.data_completeness_pct.toFixed(1)}% complete today.</p>
          </div>
        </aside>
      ) : null}
      <section
        aria-label="Energy key performance indicators"
        className="kpi-grid"
      >
        <MetricCard
          label="Current demand"
          value={numberOrDash(data.current_demand_kw)}
          unit="kW"
          context={percentContext(
            data.current_demand_change_pct,
            'vs 15 min ago',
          )}
          timestamp={absoluteTime(data.generated_at)}
          tone={data.current_demand_kw === null ? 'warning' : 'normal'}
        />
        <MetricCard
          label="Energy today"
          value={numberOrDash(data.energy_today_kwh)}
          unit="kWh"
          context={percentContext(data.energy_vs_previous_pct, 'vs yesterday')}
          timestamp={absoluteTime(data.generated_at)}
          tone={data.energy_today_kwh === null ? 'warning' : 'info'}
        />
        <MetricCard
          label="Peak demand"
          value={numberOrDash(data.peak_demand_kw)}
          unit="kW"
          context={
            data.peak_demand_at
              ? `Reached ${absoluteTime(data.peak_demand_at)}`
              : 'Peak unavailable'
          }
          timestamp={absoluteTime(data.generated_at)}
          tone={data.peak_demand_kw === null ? 'warning' : 'info'}
        />
        <div title={alarmBreakdown}>
          <MetricCard
            label="Active alarms"
            value={String(alarmTotal)}
            context={`${data.active_alarms.critical} critical · ${data.active_alarms.high} high`}
            timestamp={absoluteTime(data.generated_at)}
            tone={alarmTotal > 0 ? 'critical' : 'normal'}
          />
        </div>
      </section>

      <section className="content-grid overview-grid">
        <article className="card span-8">
          <div className="card-header">
            <div>
              <p className="eyebrow">DEMAND PROFILE</p>
              <h2>Actual, forecast and threshold</h2>
            </div>
            {forecast.data?.items.length ? (
              <StatusBadge tone="info">60 min forecast</StatusBadge>
            ) : (
              <StatusBadge tone="neutral">Forecast unavailable</StatusBadge>
            )}
          </div>
          {history.isPending ? (
            <LoadingPanel label="Loading 24-hour demand" />
          ) : history.isError ? (
            <ErrorPanel
              message="Demand history could not be loaded."
              onRetry={() => void history.refetch()}
            />
          ) : chartRows.length === 0 ? (
            <EmptyState message="No actual or forecast samples exist for this period." />
          ) : (
            <div className="chart-frame" aria-label="24-hour demand chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartRows} margin={{ left: 8, right: 16 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="at"
                    tickFormatter={chartTime}
                    minTickGap={36}
                  />
                  <YAxis unit=" kW" width={62} />
                  <Tooltip
                    labelFormatter={(value) =>
                      absoluteTime(typeof value === 'string' ? value : null)
                    }
                    formatter={(value) => [`${Number(value).toFixed(1)} kW`]}
                  />
                  <Legend />
                  <Line
                    dataKey="actual"
                    name="Actual"
                    stroke="#1677FF"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                  />
                  <Line
                    dataKey="forecast"
                    name="Forecast"
                    stroke="#18A0AE"
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    dot={false}
                    connectNulls={false}
                  />
                  {data.demand_limit_kw !== null ? (
                    <ReferenceLine
                      y={data.demand_limit_kw}
                      stroke="#D64545"
                      strokeDasharray="8 4"
                      label="Demand threshold"
                    />
                  ) : null}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>

        <aside className="card span-4">
          <div className="card-header">
            <div>
              <p className="eyebrow">DEVICE HEALTH</p>
              <h2>Status summary</h2>
            </div>
          </div>
          <dl className="status-summary">
            {(['online', 'stale', 'offline', 'disabled'] as const).map(
              (status) => (
                <div key={status}>
                  <dt>
                    <StatusBadge
                      tone={
                        status === 'online'
                          ? 'normal'
                          : status === 'stale'
                            ? 'warning'
                            : status === 'offline'
                              ? 'critical'
                              : 'neutral'
                      }
                    >
                      {status}
                    </StatusBadge>
                  </dt>
                  <dd>{data.devices[status]}</dd>
                </div>
              ),
            )}
          </dl>
        </aside>

        <article className="card span-12">
          <div className="card-header">
            <div>
              <p className="eyebrow">RECENT EVENTS</p>
              <h2>Recent alarms</h2>
            </div>
          </div>
          {alarms.isPending ? (
            <LoadingPanel label="Loading recent alarms" />
          ) : alarms.isError ? (
            <ErrorPanel
              message="Recent alarms could not be loaded."
              onRetry={() => void alarms.refetch()}
            />
          ) : !alarms.data.items.length ? (
            <EmptyState
              title="No recent alarms"
              message="No alarm records are available."
            />
          ) : (
            <ul className="alarm-list">
              {alarms.data.items.map((alarm) => (
                <li key={alarm.id}>
                  <StatusBadge tone={severityTone(alarm.severity)}>
                    {alarm.severity}
                  </StatusBadge>
                  <div>
                    <strong>{alarm.message}</strong>
                    <small>
                      {alarm.status} · {relativeTime(alarm.triggered_at)}
                    </small>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>
    </>
  )
}
