import { StatusBadge } from '../ui/StatusBadge'

export function MetricCard({
  label,
  value,
  unit,
  context,
  timestamp,
  tone = 'neutral',
}: {
  label: string
  value: string
  unit?: string
  context: string
  timestamp: string
  tone?: 'normal' | 'warning' | 'critical' | 'info' | 'neutral'
}) {
  return (
    <article className="card metric-card">
      <div className="metric-heading">
        <p className="eyebrow">{label}</p>
        <StatusBadge tone={tone}>{context}</StatusBadge>
      </div>
      <p className="metric-value">
        {value} {unit ? <span>{unit}</span> : null}
      </p>
      <p className="metric-timestamp">Calculated {timestamp}</p>
    </article>
  )
}
