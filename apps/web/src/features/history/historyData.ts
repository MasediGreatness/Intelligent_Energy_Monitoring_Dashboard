import type { HistoryResponse } from '../../api/dashboard'

export type HistoryInterval = 'raw' | '10s' | '1m' | '15m' | '1h' | '1d'

const intervalRank: Record<HistoryInterval, number> = {
  raw: 0,
  '10s': 1,
  '1m': 2,
  '15m': 3,
  '1h': 4,
  '1d': 5,
}

export function minimumInterval(
  fromDate: string,
  toDate: string,
): HistoryInterval {
  const days = Math.max(
    0,
    (Date.parse(`${toDate}T23:59:59Z`) - Date.parse(`${fromDate}T00:00:00Z`)) /
      86_400_000,
  )
  if (days > 14) return '1h'
  if (days > 2) return '15m'
  if (days > 1) return '1m'
  return 'raw'
}

export function safeInterval(
  selected: HistoryInterval,
  fromDate: string,
  toDate: string,
): HistoryInterval {
  const minimum = minimumInterval(fromDate, toDate)
  return intervalRank[selected] < intervalRank[minimum] ? minimum : selected
}

export function buildHistoryCsv(history: HistoryResponse): string {
  const lines = [
    'timestamp_utc,device_id,active_power_kw,sample_count,completeness_pct',
  ]
  history.series.forEach((series) => {
    series.points.forEach((point) => {
      lines.push(
        [
          new Date(point.bucket_at).toISOString(),
          series.device_id,
          point.value ?? '',
          point.sample_count,
          point.completeness_pct,
        ].join(','),
      )
    })
  })
  return `${lines.join('\r\n')}\r\n`
}

export function downloadHistoryCsv(history: HistoryResponse): void {
  const url = URL.createObjectURL(
    new Blob([buildHistoryCsv(history)], { type: 'text/csv;charset=utf-8' }),
  )
  const link = document.createElement('a')
  link.href = url
  link.download = 'energy-history.csv'
  link.click()
  URL.revokeObjectURL(url)
}
