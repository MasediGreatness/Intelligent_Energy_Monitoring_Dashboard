import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  getAnomalies,
  getForecast,
  getHistory,
  getLatestMeasurements,
  type ForecastItem,
  type HistoryResponse,
  type Severity,
} from '../api/dashboard'
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
} from '../components/states/DataStates'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { absoluteTime, chartTime, numberOrDash } from '../utils/format'

function dateValue(offsetDays = 0) {
  return new Date(Date.now() + offsetDays * 86_400_000)
    .toISOString()
    .slice(0, 10)
}

function severityTone(severity: Severity) {
  if (severity === 'critical' || severity === 'high') return 'critical' as const
  if (severity === 'medium') return 'warning' as const
  return 'info' as const
}

function actualByTime(history?: HistoryResponse) {
  const values = new Map<string, number[]>()
  history?.series.forEach((series) =>
    series.points.forEach((point) => {
      if (point.value === null) return
      const bucket = values.get(point.bucket_at) ?? []
      bucket.push(point.value)
      values.set(point.bucket_at, bucket)
    }),
  )
  return new Map(
    [...values].map(([at, items]) => [
      at,
      items.reduce((sum, value) => sum + value, 0),
    ]),
  )
}

function forecastRows(items: ForecastItem[], history?: HistoryResponse) {
  const actual = actualByTime(history)
  const groups = new Map<string, ForecastItem[]>()
  items.forEach((item) => {
    const group = groups.get(item.target_at) ?? []
    group.push(item)
    groups.set(item.target_at, group)
  })
  return [...groups.entries()]
    .map(([at, group]) => {
      const predicted = group.reduce(
        (sum, item) => sum + item.predicted_power_kw,
        0,
      )
      const lowerValues = group.map((item) => item.lower_kw)
      const upperValues = group.map((item) => item.upper_kw)
      const lower = lowerValues.every((value) => value !== null)
        ? lowerValues.reduce((sum, value) => sum + (value ?? 0), 0)
        : undefined
      const upper = upperValues.every((value) => value !== null)
        ? upperValues.reduce((sum, value) => sum + (value ?? 0), 0)
        : undefined
      return {
        at,
        actual: actual.get(at),
        predicted,
        lower,
        confidenceBand:
          lower !== undefined && upper !== undefined
            ? upper - lower
            : undefined,
      }
    })
    .sort((a, b) => a.at.localeCompare(b.at))
}

export function ForecastAnomaliesPage() {
  const [params, setParams] = useSearchParams()
  const device = params.get('device') ?? 'all'
  const horizon = Number(params.get('horizon') ?? '60')
  const from = params.get('from') ?? dateValue(-7)
  const to = params.get('to') ?? dateValue()
  const severity = (params.get('severity') ?? '') as Severity | ''

  useEffect(() => {
    if (
      !params.has('device') ||
      !params.has('horizon') ||
      !params.has('from') ||
      !params.has('to')
    ) {
      setParams(
        { device, horizon: String(horizon), from, to, severity },
        { replace: true },
      )
    }
  }, [device, from, horizon, params, setParams, severity, to])

  const latest = useQuery({
    queryKey: ['latest-measurements'],
    queryFn: ({ signal }) => getLatestMeasurements(signal),
  })
  const selectedIds = useMemo(
    () =>
      device === 'all'
        ? (latest.data?.map((item) => item.device_id) ?? [])
        : [device],
    [device, latest.data],
  )
  const forecast = useQuery({
    queryKey: ['forecast-analysis', device, horizon],
    queryFn: ({ signal }) =>
      getForecast(horizon, device === 'all' ? undefined : device, signal),
  })
  const forecastRange = useMemo(() => {
    if (!forecast.data?.items.length) return null
    const timestamps = forecast.data.items.flatMap((item) => [
      Date.parse(item.generated_at),
      Date.parse(item.target_at),
    ])
    return {
      from: new Date(Math.min(...timestamps) - 60_000).toISOString(),
      to: new Date(Math.max(...timestamps) + 60_000).toISOString(),
    }
  }, [forecast.data])
  const actual = useQuery({
    queryKey: ['forecast-actual', selectedIds.join(','), forecastRange],
    queryFn: ({ signal }) =>
      getHistory(
        selectedIds,
        forecastRange!.from,
        forecastRange!.to,
        '1m',
        signal,
      ),
    enabled: selectedIds.length > 0 && forecastRange !== null,
  })
  const anomalies = useQuery({
    queryKey: ['anomalies', device, severity, from, to],
    queryFn: ({ signal }) =>
      getAnomalies(
        {
          deviceId: device === 'all' ? undefined : device,
          severity: severity || undefined,
          from: new Date(`${from}T00:00:00+02:00`).toISOString(),
          to: new Date(`${to}T23:59:59.999+02:00`).toISOString(),
        },
        signal,
      ),
  })
  const rows = useMemo(
    () => forecastRows(forecast.data?.items ?? [], actual.data),
    [actual.data, forecast.data],
  )
  const versions = [
    ...new Set(forecast.data?.items.map((item) => item.model_version) ?? []),
  ]

  function updateFilter(key: string, value: string) {
    const next = new URLSearchParams(params)
    next.set(key, value)
    setParams(next)
  }

  return (
    <>
      <PageHeader
        eyebrow="MODEL REVIEW"
        title="Forecast and anomalies"
        description="Compare actual power with model output and investigate explained anomaly records."
        action={<StatusBadge tone="info">No invented predictions</StatusBadge>}
      />
      <form className="filter-bar" onSubmit={(event) => event.preventDefault()}>
        <label>
          Device
          <select
            value={device}
            onChange={(event) => updateFilter('device', event.target.value)}
          >
            <option value="all">All devices</option>
            {latest.data?.map((item) => (
              <option value={item.device_id} key={item.device_id}>
                {item.device_code}
              </option>
            ))}
          </select>
        </label>
        <label>
          Forecast horizon
          <select
            value={horizon}
            onChange={(event) => updateFilter('horizon', event.target.value)}
          >
            <option value={60}>60 minutes</option>
            <option value={1440}>24 hours</option>
          </select>
        </label>
        <label>
          Anomalies from
          <input
            type="date"
            value={from}
            max={to}
            onChange={(event) => updateFilter('from', event.target.value)}
          />
        </label>
        <label>
          Anomalies to
          <input
            type="date"
            value={to}
            min={from}
            onChange={(event) => updateFilter('to', event.target.value)}
          />
        </label>
        <label>
          Severity
          <select
            value={severity}
            onChange={(event) => updateFilter('severity', event.target.value)}
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
      </form>

      <section className="analysis-stack">
        <article className="card">
          <div className="card-header">
            <div>
              <p className="eyebrow">FORECAST</p>
              <h2>Actual versus forecast</h2>
            </div>
            {versions.length ? (
              <StatusBadge tone="info">Model {versions.join(', ')}</StatusBadge>
            ) : null}
          </div>
          {forecast.isPending || latest.isPending ? (
            <LoadingPanel label="Loading model data" />
          ) : forecast.isError ? (
            <ErrorPanel
              message="Forecast data could not be loaded."
              onRetry={() => void forecast.refetch()}
            />
          ) : !forecast.data.items.length ? (
            <EmptyState
              title="Model data unavailable"
              message="No forecast exists for the selected device and horizon. No prediction has been invented."
            />
          ) : (
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={rows}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="at"
                    tickFormatter={chartTime}
                    minTickGap={34}
                  />
                  <YAxis unit=" kW" width={62} />
                  <Tooltip
                    labelFormatter={(value) =>
                      absoluteTime(typeof value === 'string' ? value : null)
                    }
                    formatter={(value) => [`${numberOrDash(Number(value))} kW`]}
                  />
                  <Legend />
                  <Area
                    dataKey="lower"
                    stackId="confidence"
                    stroke="none"
                    fill="transparent"
                    name="Lower bound"
                  />
                  <Area
                    dataKey="confidenceBand"
                    stackId="confidence"
                    stroke="none"
                    fill="#B8E3E7"
                    fillOpacity={0.7}
                    name="Confidence band"
                  />
                  <Line
                    dataKey="predicted"
                    name="Forecast"
                    stroke="#18A0AE"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    dataKey="actual"
                    name="Actual"
                    stroke="#1677FF"
                    strokeWidth={2}
                    dot={false}
                    connectNulls={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>

        <article className="card">
          <div className="card-header">
            <div>
              <p className="eyebrow">ANOMALY TIMELINE</p>
              <h2>Detected unusual behaviour</h2>
            </div>
            <StatusBadge tone="neutral">
              {anomalies.data?.total ?? 0} records
            </StatusBadge>
          </div>
          {anomalies.isPending ? (
            <LoadingPanel label="Loading anomalies" />
          ) : anomalies.isError ? (
            <ErrorPanel
              message="Anomaly records could not be loaded."
              onRetry={() => void anomalies.refetch()}
            />
          ) : !anomalies.data.items.length ? (
            <EmptyState
              title="No anomalies"
              message="No anomaly records match these filters."
            />
          ) : (
            <ol className="anomaly-timeline">
              {anomalies.data.items.map((anomaly) => (
                <li key={anomaly.id}>
                  <span className="timeline-marker" aria-hidden="true" />
                  <div className="anomaly-heading">
                    <div>
                      <strong>{anomaly.anomaly_type}</strong>
                      <small>
                        {absoluteTime(anomaly.detected_at)} · {anomaly.status}
                      </small>
                    </div>
                    <StatusBadge tone={severityTone(anomaly.severity)}>
                      {anomaly.severity}
                    </StatusBadge>
                  </div>
                  <dl className="anomaly-values">
                    <div>
                      <dt>Metric</dt>
                      <dd>{anomaly.metric}</dd>
                    </div>
                    <div>
                      <dt>Expected</dt>
                      <dd>{numberOrDash(anomaly.expected_value)}</dd>
                    </div>
                    <div>
                      <dt>Actual</dt>
                      <dd>{numberOrDash(anomaly.actual_value)}</dd>
                    </div>
                    <div>
                      <dt>Score</dt>
                      <dd>{numberOrDash(anomaly.score, 2)}</dd>
                    </div>
                  </dl>
                  <p>{anomaly.explanation}</p>
                </li>
              ))}
            </ol>
          )}
        </article>
      </section>
    </>
  )
}
