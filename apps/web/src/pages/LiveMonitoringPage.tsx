import { useQuery } from '@tanstack/react-query'
import { useMemo } from 'react'
import {
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
  getHistory,
  getLatestMeasurements,
  type DeviceStatus,
} from '../api/dashboard'
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
  StaleBanner,
} from '../components/states/DataStates'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import {
  absoluteTime,
  chartTime,
  numberOrDash,
  relativeTime,
} from '../utils/format'

const chartColours = ['#1677FF', '#18A0AE', '#1F9D55', '#F59E0B', '#D64545']

function statusTone(status: DeviceStatus) {
  if (status === 'online') return 'normal' as const
  if (status === 'stale') return 'warning' as const
  if (status === 'offline') return 'critical' as const
  return 'neutral' as const
}

export function LiveMonitoringPage() {
  const latest = useQuery({
    queryKey: ['latest-measurements'],
    queryFn: ({ signal }) => getLatestMeasurements(signal),
  })
  const deviceIds = useMemo(
    () => latest.data?.map((item) => item.device_id) ?? [],
    [latest.data],
  )
  const history = useQuery({
    queryKey: ['live-history', deviceIds.join(',')],
    queryFn: ({ signal }) => {
      const to = new Date()
      const from = new Date(to.getTime() - 60 * 60 * 1000)
      return getHistory(
        deviceIds,
        from.toISOString(),
        to.toISOString(),
        '1m',
        signal,
      )
    },
    enabled: deviceIds.length > 0,
  })
  const chartData = useMemo(() => {
    const rows = new Map<string, Record<string, number | string>>()
    history.data?.series.forEach((series) =>
      series.points.forEach((point) => {
        if (point.value === null) return
        const row = rows.get(point.bucket_at) ?? { at: point.bucket_at }
        row[series.device_id] = point.value
        rows.set(point.bucket_at, row)
      }),
    )
    return [...rows.values()].sort((a, b) =>
      String(a.at).localeCompare(String(b.at)),
    )
  }, [history.data])

  if (latest.isPending)
    return <LoadingPanel fullPage label="Loading live measurements" />
  if (latest.isError)
    return (
      <ErrorPanel
        fullPage
        message="Live measurements could not be loaded. Values are not replaced with zero."
        onRetry={() => void latest.refetch()}
      />
    )

  const devices = latest.data
  const staleCount = devices.filter(
    (item) => item.status === 'stale' || item.status === 'offline',
  ).length
  const partialCount = devices.filter(
    (item) =>
      item.measured_at === null ||
      item.active_power_kw === null ||
      item.voltage_v === null ||
      item.current_a === null ||
      item.power_factor === null ||
      item.frequency_hz === null,
  ).length

  return (
    <>
      <PageHeader
        eyebrow="LIVE OPERATIONS"
        title="Live monitoring"
        description="Latest API measurements and a WebSocket-refreshed 60-minute power trend."
        action={<StatusBadge tone="info">60 minute window</StatusBadge>}
      />
      {staleCount > 0 ? (
        <StaleBanner
          message={`${staleCount} device(s) are stale or offline. Their last values are labelled and must not be interpreted as live.`}
        />
      ) : null}
      {partialCount > 0 ? (
        <aside className="notice notice-info overview-notice" role="status">
          <div>
            <strong>Partial data</strong>
            <p>
              {partialCount} device(s) have one or more missing measurements,
              displayed as '-'.
            </p>
          </div>
        </aside>
      ) : null}
      {!devices.length ? (
        <EmptyState
          title="No monitored devices"
          message="The API returned no configured devices."
        />
      ) : (
        <>
          <section
            aria-label="Latest device measurements"
            className="device-card-grid"
          >
            {devices.map((device) => (
              <article className="card device-live-card" key={device.device_id}>
                <div className="card-header">
                  <div>
                    <p className="eyebrow">{device.device_code}</p>
                    <h2>{numberOrDash(device.active_power_kw)} kW</h2>
                  </div>
                  <StatusBadge tone={statusTone(device.status)}>
                    {device.status}
                  </StatusBadge>
                </div>
                <dl className="measurement-grid">
                  <div>
                    <dt>Voltage</dt>
                    <dd>{numberOrDash(device.voltage_v)} V</dd>
                  </div>
                  <div>
                    <dt>Current</dt>
                    <dd>{numberOrDash(device.current_a, 2)} A</dd>
                  </div>
                  <div>
                    <dt>Power factor</dt>
                    <dd>{numberOrDash(device.power_factor, 2)}</dd>
                  </div>
                  <div>
                    <dt>Frequency</dt>
                    <dd>{numberOrDash(device.frequency_hz, 2)} Hz</dd>
                  </div>
                  <div>
                    <dt>Quality</dt>
                    <dd>{device.data_quality ?? '-'}</dd>
                  </div>
                  <div title={absoluteTime(device.measured_at)}>
                    <dt>Last seen</dt>
                    <dd>{relativeTime(device.measured_at)}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </section>
          <article className="card live-trend-card">
            <div className="card-header">
              <div>
                <p className="eyebrow">POWER TREND</p>
                <h2>Active power by device</h2>
              </div>
              <StatusBadge tone="normal">WebSocket refreshed</StatusBadge>
            </div>
            {history.isPending ? (
              <LoadingPanel label="Loading 60-minute trend" />
            ) : history.isError ? (
              <ErrorPanel
                message="The live trend could not be loaded."
                onRetry={() => void history.refetch()}
              />
            ) : chartData.length === 0 ? (
              <EmptyState message="No valid power samples exist in the last 60 minutes." />
            ) : (
              <div
                className="chart-frame"
                aria-label="60-minute active power chart"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ left: 8, right: 16 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="at"
                      tickFormatter={chartTime}
                      minTickGap={32}
                    />
                    <YAxis unit=" kW" width={62} />
                    <Tooltip
                      labelFormatter={(value) =>
                        absoluteTime(typeof value === 'string' ? value : null)
                      }
                      formatter={(value) => [`${Number(value).toFixed(1)} kW`]}
                    />
                    <Legend />
                    {devices.map((device, index) => (
                      <Line
                        key={device.device_id}
                        dataKey={device.device_id}
                        name={device.device_code}
                        stroke={chartColours[index % chartColours.length]}
                        strokeWidth={2}
                        dot={false}
                        connectNulls={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </article>
        </>
      )}
    </>
  )
}
