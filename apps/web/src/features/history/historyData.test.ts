import { describe, expect, it } from 'vitest'

import type { HistoryResponse } from '../../api/dashboard'
import { buildHistoryCsv, safeInterval } from './historyData'

describe('history analysis helpers', () => {
  it('exports filtered values with UTC timestamp and explicit units', () => {
    const history: HistoryResponse = {
      timezone: 'Africa/Johannesburg',
      series: [
        {
          device_id: 'device-1',
          metric: 'active_power_kw',
          interval: '15m',
          points: [
            {
              bucket_at: '2026-08-15T19:30:00Z',
              value: 2.71,
              sample_count: 900,
              completeness_pct: 100,
            },
            {
              bucket_at: '2026-08-15T19:45:00Z',
              value: null,
              sample_count: 0,
              completeness_pct: 0,
            },
          ],
        },
      ],
    }

    expect(buildHistoryCsv(history)).toBe(
      'timestamp_utc,device_id,active_power_kw,sample_count,completeness_pct\r\n' +
        '2026-08-15T19:30:00.000Z,device-1,2.71,900,100\r\n' +
        '2026-08-15T19:45:00.000Z,device-1,,0,0\r\n',
    )
  })

  it('forces aggregation for large date ranges', () => {
    expect(safeInterval('raw', '2026-08-01', '2026-08-31')).toBe('1h')
    expect(safeInterval('1m', '2026-08-01', '2026-08-08')).toBe('15m')
    expect(safeInterval('raw', '2026-08-01', '2026-08-01')).toBe('raw')
  })
})
