type StatusTone = 'normal' | 'warning' | 'critical' | 'info' | 'neutral'

export function StatusBadge({
  tone,
  children,
}: {
  tone: StatusTone
  children: React.ReactNode
}) {
  return (
    <span className={`status-badge status-${tone}`}>
      <span aria-hidden="true" className="badge-dot" />
      {children}
    </span>
  )
}
