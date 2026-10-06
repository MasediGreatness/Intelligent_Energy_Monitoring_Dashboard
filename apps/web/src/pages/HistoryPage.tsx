import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import {
  getDailyEnergy,
  getHistory,
  getLatestMeasurements,
  type DailyEnergyItem,
  type HistoryResponse,
} from '../api/dashboard'
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
} from '../components/states/DataStates'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import {
  downloadHistoryCsv,
  safeInterval,
  type HistoryInterval,
} from '../features/history/historyData'
import { absoluteTime, chartTime, numberOrDash } from '../utils/format'

const intervals: HistoryInterval[] = ['raw', '10s', '1m', '15m', '1h', '1d']
const colours = ['#1677FF', '#18A0AE', '#1F9D55', '#F59E0B', '#D64545']

function dateValue(offsetDays = 0) {
  const value = new Date(Date.now() + offsetDays * 86_400_000)
  return value.toISOString().slice(0, 10)
}

function utcStart(date: string) {
  return new Date(`${date}T00:00:00+02:00`).toISOString()
}

function utcEnd(date: string) {
  return new Date(`${date}T23:59:59.999+02:00`).toISOString()
}

function seriesRows(history?: HistoryResponse) {
  const rows = new Map<string, Record<string, number | string>>()
  history?.series.forEach((series) =>
    series.points.forEach((point) => {
      const row = rows.get(point.bucket_at) ?? { at: point.bucket_at }
      if (point.value !== null) row[series.device_id] = point.value
      row[`${series.device_id}-complete`] = point.completeness_pct
      rows.set(point.bucket_at, row)
    }),
  )
  return [...rows.values()].sort((a, b) =>
    String(a.at).localeCompare(String(b.at)),
  )
}

function completeness(history?: HistoryResponse) {
  const points = history?.series.flatMap((series) => series.points) ?? []
  const incomplete = points.filter(
    (point) => point.completeness_pct < 90,
  ).length
  return { incomplete, total: points.length }
}

function dailyEnergyRows(items?: DailyEnergyItem[]) {
  const rows = new Map<string, Record<string, number | string>>()
  items?.forEach((item) => {
    const row = rows.get(item.day) ?? { day: item.day }
    if (item.device_id && item.energy_kwh !== null) {
      row[item.device_id] = Number(item.energy_kwh)
      row[`${item.device_id}-complete`] = item.completeness_pct
    }
    rows.set(item.day, row)
  })
  return [...rows.values()].sort((a, b) =>
    String(a.day).localeCompare(String(b.day)),
  )
}

export function HistoryPage() {
  const [params, setParams] = useSearchParams()
  const from = params.get('from') ?? dateValue(-7)
  const to = params.get('to') ?? dateValue()
  const device = params.get('device') ?? 'all'
  const requestedInterval = (params.get('interval') ?? '15m') as HistoryInterval
  const interval = intervals.includes(requestedInterval)
    ? requestedInterval
    : '15m'

  useEffect(() => {
    if (!params.has('from') || !params.has('to') || !params.has('interval')) {
      setParams({ from, to, device, interval }, { replace: true })
    }
  }, [device, from, interval, params, setParams, to])

  const latest = useQuery({
    queryKey: ['latest-measurements'],
    queryFn: ({ signal }) => getLatestMeasurements(signal),
  })
  const deviceIds = useMemo(() => {
    if (!latest.data) return []
    return device === 'all'
      ? latest.data.map((item) => item.device_id)
      : [device]
  }, [device, latest.data])
  const rangeStart = utcStart(from)
  const rangeEnd = utcEnd(to)
  const power = useQuery({
    queryKey: ['history-power', deviceIds.join(','), from, to, interval],
    queryFn: ({ signal }) =>
      getHistory(deviceIds, rangeStart, rangeEnd, interval, signal),
    enabled: deviceIds.length > 0,
  })
  const demand = useQuery({
    queryKey: ['history-demand', deviceIds.join(','), from, to],
    queryFn: ({ signal }) =>
      getHistory(deviceIds, rangeStart, rangeEnd, '15m', signal),
    enabled: deviceIds.length > 0,
  })
  const energy = useQuery({
    queryKey: ['daily-energy', device, from, to],
    queryFn: ({ signal }) =>
      getDailyEnergy(from, to, device === 'all' ? undefined : device, signal),
  })
  const powerRows = useMemo(() => seriesRows(power.data), [power.data])
  const demandRows = useMemo(() => seriesRows(demand.data), [demand.data])
  const energyRows = useMemo(
    () => dailyEnergyRows(energy.data?.items),
    [energy.data],
  )
  const powerCompleteness = completeness(power.data)

  function updateFilters(changes: Record<string, string>) {
    const next = new URLSearchParams(params)
    Object.entries(changes).forEach(([key, value]) => next.set(key, value))
    const nextFrom = next.get('from') ?? from
    const nextTo = next.get('to') ?? to
    const nextInterval = (next.get('interval') ?? interval) as HistoryInterval
    next.set('interval', safeInterval(nextInterval, nextFrom, nextTo))
    setParams(next)
  }

  const hasError =
    latest.isError || power.isError || demand.isError || energy.isError

  return (
    <>
      <PageHeader
        eyebrow="ENGINEERING ANALYSIS"
        title="Energy history"
        description="Reproducible power, daily energy and 15-minute demand views using backend buckets."
        action={<StatusBadge tone="info">UTC export</StatusBadge>}
      />
      <form className="filter-bar" onSubmit={(event) => event.preventDefault()}>
        <label>
          From
          <input
            type="date"
            value={from}
            max={to}
            onChange={(event) => updateFilters({ from: event.target.value })}
          />
        </label>
        <label>
          To
          <input
            type="date"
            value={to}
            min={from}
            onChange={(event) => updateFilters({ to: event.target.value })}
          />
        </label>
        <label>
          Device
          <select
            value={device}
            onChange={(event) => updateFilters({ device: event.target.value })}
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
          Interval
          <select
            value={interval}
            onChange={(event) =>
              updateFilters({ interval: event.target.value })
            }
          >
            {intervals.map((item) => (
              <option value={item} key={item}>
                {item}
              </option>
            ))}
          </select>
        </label>
        <button
          className="button button-secondary"
          type="button"
          disabled={!power.data}
          onClick={() => power.data && downloadHistoryCsv(power.data)}
        >
          Export CSV
        </button>
      </form>

      {hasError ? (
        <ErrorPanel
          message="One or more historical datasets could not be loaded."
          onRetry={() => {
            void latest.refetch()
            void power.refetch()
            void demand.refetch()
            void energy.refetch()
          }}
        />
      ) : null}
      <section className="analysis-stack">
        <article className="card">
          <div className="card-header">
            <div>
              <p className="eyebrow">POWER HISTORY</p>
              <h2>Active power</h2>
            </div>
            <StatusBadge
              tone={powerCompleteness.incomplete ? 'warning' : 'normal'}
            >
              {powerCompleteness.incomplete} incomplete of{' '}
              {powerCompleteness.total}
            </StatusBadge>
          </div>
          {power.isPending || latest.isPending ? (
            <LoadingPanel label="Loading power history" />
          ) : !powerRows.length ? (
            <EmptyState message="No valid power buckets exist for these filters." />
          ) : (
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={powerRows}>
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
                  {deviceIds.map((id, index) => (
                    <Line
                      key={id}
                      dataKey={id}
                      name={
                        latest.data?.find((item) => item.device_id === id)
                          ?.device_code ?? id
                      }
                      stroke={colours[index % colours.length]}
                      dot={false}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>

        <article className="card">
          <div className="card-header">
            <div>
              <p className="eyebrow">ENERGY</p>
              <h2>Daily energy</h2>
            </div>
            <StatusBadge tone="info">Backend counter deltas</StatusBadge>
          </div>
          {energy.isPending ? (
            <LoadingPanel label="Loading daily energy" />
          ) : !energyRows.some((row) => Object.keys(row).length > 1) ? (
            <EmptyState message="Daily energy is unavailable for this selection." />
          ) : (
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={energyRows}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="day" />
                  <YAxis unit=" kWh" width={70} />
                  <Tooltip
                    formatter={(value) => [
                      `${numberOrDash(Number(value))} kWh`,
                    ]}
                  />
                  <Legend />
                  {deviceIds.map((id, index) => (
                    <Bar
                      key={id}
                      dataKey={id}
                      name={
                        latest.data?.find((item) => item.device_id === id)
                          ?.device_code ?? id
                      }
                      fill={colours[index % colours.length]}
                    />
                  ))}
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>

        <article className="card">
          <div className="card-header">
            <div>
              <p className="eyebrow">DEMAND</p>
              <h2>15-minute demand</h2>
            </div>
            <StatusBadge tone="info">15m backend buckets</StatusBadge>
          </div>
          {demand.isPending ? (
            <LoadingPanel label="Loading demand buckets" />
          ) : !demandRows.length ? (
            <EmptyState message="No valid 15-minute demand buckets exist for these filters." />
          ) : (
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={demandRows}>
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
                    formatter={(value) => [`${numberOrDash(Number(value))} kW`]}
                  />
                  {deviceIds.map((id, index) => (
                    <Line
                      key={id}
                      dataKey={id}
                      name={
                        latest.data?.find((item) => item.device_id === id)
                          ?.device_code ?? id
                      }
                      stroke={colours[index % colours.length]}
                      dot={false}
                      connectNulls={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>
      </section>
    </>
  )
}
