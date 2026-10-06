const configuredBase = import.meta.env.VITE_API_BASE_URL ?? ''
const apiBase = configuredBase.endsWith('/api/v1')
  ? configuredBase
  : `${configuredBase}/api/v1`

export type DeviceStatus = 'online' | 'stale' | 'offline' | 'disabled'
export type Severity = 'critical' | 'high' | 'medium' | 'low'
export type AlarmStatus = 'open' | 'acknowledged' | 'cleared'

export interface DashboardSummary {
  generated_at: string
  timezone: string
  current_demand_kw: number | null
  current_demand_change_pct: number | null
  energy_today_kwh: string | number | null
  energy_vs_previous_pct: number | null
  peak_demand_kw: number | null
  peak_demand_at: string | null
  demand_limit_kw: number | null
  active_alarms: Record<Severity, number>
  devices: Record<DeviceStatus, number>
  data_completeness_pct: number
  excluded_stale_devices: number
}

export interface LatestMeasurement {
  device_id: string
  device_code: string
  measured_at: string | null
  active_power_kw: number | null
  voltage_v: number | null
  current_a: number | null
  power_factor: number | null
  frequency_hz: number | null
  data_quality: string | null
  status: DeviceStatus
}

export interface HistoryPoint {
  bucket_at: string
  value: number | null
  sample_count: number
  completeness_pct: number
}

export interface HistorySeries {
  device_id: string
  metric: string
  interval: string
  points: HistoryPoint[]
}

export interface HistoryResponse {
  timezone: string
  series: HistorySeries[]
}

export interface ForecastItem {
  device_id: string | null
  generated_at: string
  target_at: string
  horizon_minutes: number
  predicted_power_kw: number
  lower_kw: number | null
  upper_kw: number | null
  model_version: string
}

export interface DailyEnergyItem {
  day: string
  device_id: string | null
  energy_kwh: string | number | null
  peak_demand_kw: number | null
  completeness_pct: number
}

export interface AnomalyItem {
  id: string
  device_id: string
  detected_at: string
  anomaly_type: string
  severity: Severity
  metric: string
  actual_value: number | null
  expected_value: number | null
  score: number
  explanation: string
  status: 'open' | 'reviewed' | 'cleared'
}

export interface AlarmItem {
  id: string
  device_id: string | null
  source: string
  alarm_type: string
  severity: Severity
  message: string
  triggered_at: string
  acknowledged_at: string | null
  acknowledged_by: string | null
  acknowledgement_note: string | null
  cleared_at: string | null
  status: AlarmStatus
}

export interface DeviceItem {
  id: string
  code: string
  name: string
  location: string
  phase_type: 'single_phase' | 'three_phase'
  rated_power_kw: number
  criticality: 'low' | 'medium' | 'high' | 'critical'
  enabled: boolean
  last_seen_at: string | null
  status: DeviceStatus
}

export interface DeviceInput {
  code: string
  name: string
  location: string
  phase_type: DeviceItem['phase_type']
  rated_power_kw: number
  criticality: DeviceItem['criticality']
  enabled: boolean
}

export type SettingKey =
  | 'demand_limit_kw'
  | 'demand_interval_minutes'
  | 'tariff_zar_per_kwh'
  | 'timezone'
  | 'online_timeout_seconds'
  | 'stale_timeout_seconds'
  | 'simulator_profile'

export interface SettingItem {
  key: SettingKey
  value_json: string | number
  description: string
  updated_at: string
}

interface ApiErrorBody {
  error?: { message?: string }
}

export interface Page<T> {
  page: number
  page_size: number
  total: number
  items: T[]
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    credentials: 'include',
    signal,
  })
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorBody
    throw new Error(
      body.error?.message ?? `Request failed with HTTP ${response.status}`,
    )
  }
  return (await response.json()) as T
}

async function sendJson<T>(
  path: string,
  method: 'POST' | 'PATCH',
  body: object,
): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as ApiErrorBody
    throw new Error(
      payload.error?.message ?? `Request failed with HTTP ${response.status}`,
    )
  }
  return (await response.json()) as T
}

export function getDashboardSummary(signal?: AbortSignal) {
  return getJson<DashboardSummary>(
    '/dashboard/summary?timezone=Africa%2FJohannesburg',
    signal,
  )
}

export function getLatestMeasurements(signal?: AbortSignal) {
  return getJson<LatestMeasurement[]>('/measurements/latest', signal)
}

export function getHistory(
  deviceIds: string[],
  from: string,
  to: string,
  interval: 'raw' | '10s' | '1m' | '15m' | '1h' | '1d',
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({
    from,
    to,
    interval,
    metric: 'active_power_kw',
    timezone: 'Africa/Johannesburg',
  })
  deviceIds.forEach((id) => query.append('device_id', id))
  return getJson<HistoryResponse>(`/measurements/history?${query}`, signal)
}

export function getLatestForecast(signal?: AbortSignal) {
  return getJson<{ items: ForecastItem[] }>(
    '/forecasts/latest?horizon_minutes=60',
    signal,
  )
}

export function getForecast(
  horizonMinutes: number,
  deviceId?: string,
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({
    horizon_minutes: String(horizonMinutes),
  })
  if (deviceId) query.set('device_id', deviceId)
  return getJson<{ items: ForecastItem[] }>(
    `/forecasts/latest?${query}`,
    signal,
  )
}

export function getDailyEnergy(
  fromDate: string,
  toDate: string,
  deviceId?: string,
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({
    from_date: fromDate,
    to_date: toDate,
    timezone: 'Africa/Johannesburg',
  })
  if (deviceId) query.set('device_id', deviceId)
  return getJson<{ timezone: string; items: DailyEnergyItem[] }>(
    `/energy/daily?${query}`,
    signal,
  )
}

export function getAnomalies(
  filters: {
    deviceId?: string
    severity?: Severity
    from?: string
    to?: string
  },
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({ page: '1', page_size: '200' })
  if (filters.deviceId) query.set('device_id', filters.deviceId)
  if (filters.severity) query.set('severity', filters.severity)
  if (filters.from) query.set('from', filters.from)
  if (filters.to) query.set('to', filters.to)
  return getJson<Page<AnomalyItem>>(`/anomalies?${query}`, signal)
}

export function getRecentAlarms(signal?: AbortSignal) {
  return getJson<Page<AlarmItem>>('/alarms?page=1&page_size=5', signal)
}

export function getAlarms(
  filters: {
    page: number
    pageSize: number
    status?: AlarmStatus
    severity?: Severity
    deviceId?: string
  },
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({
    page: String(filters.page),
    page_size: String(filters.pageSize),
  })
  if (filters.status) query.set('status', filters.status)
  if (filters.severity) query.set('severity', filters.severity)
  if (filters.deviceId) query.set('device_id', filters.deviceId)
  return getJson<Page<AlarmItem>>(`/alarms?${query}`, signal)
}

export function acknowledgeAlarm(alarmId: string, note: string) {
  return sendJson<{ alarm: AlarmItem }>(
    `/alarms/${alarmId}/acknowledge`,
    'PATCH',
    { note },
  )
}

export function getDevices(
  page = 1,
  pageSize = 50,
  enabled?: boolean,
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  })
  if (enabled !== undefined) query.set('enabled', String(enabled))
  return getJson<Page<DeviceItem>>(`/devices?${query}`, signal)
}

export function createDevice(input: DeviceInput) {
  return sendJson<{ device: DeviceItem }>('/devices', 'POST', input)
}

export function updateDevice(deviceId: string, input: Partial<DeviceInput>) {
  return sendJson<{ device: DeviceItem }>(
    `/devices/${deviceId}`,
    'PATCH',
    input,
  )
}

export function getSettings(signal?: AbortSignal) {
  return getJson<SettingItem[]>('/settings', signal)
}

export function updateSetting(key: SettingKey, value: string | number) {
  return sendJson<{ setting: SettingItem }>(`/settings/${key}`, 'PATCH', {
    value,
  })
}
