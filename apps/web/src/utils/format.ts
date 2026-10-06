const johannesburgDateTime = new Intl.DateTimeFormat('en-ZA', {
  timeZone: 'Africa/Johannesburg',
  dateStyle: 'medium',
  timeStyle: 'short',
})

const johannesburgTime = new Intl.DateTimeFormat('en-ZA', {
  timeZone: 'Africa/Johannesburg',
  hour: '2-digit',
  minute: '2-digit',
})

export function numberOrDash(value: number | string | null, digits = 1) {
  if (value === null || value === '') return '-'
  const numeric = Number(value)
  return Number.isFinite(numeric) ? numeric.toFixed(digits) : '-'
}

export function percentContext(value: number | null, label: string) {
  if (value === null) return `Comparison ${label} unavailable`
  const direction = value > 0 ? 'up' : value < 0 ? 'down' : 'unchanged'
  return `${Math.abs(value).toFixed(1)}% ${direction} ${label}`
}

export function absoluteTime(value: string | null) {
  return value ? johannesburgDateTime.format(new Date(value)) : '-'
}

export function chartTime(value: string) {
  return johannesburgTime.format(new Date(value))
}

export function relativeTime(value: string | null, now = Date.now()) {
  if (!value) return 'Never seen'
  const seconds = Math.max(0, Math.floor((now - Date.parse(value)) / 1000))
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}
