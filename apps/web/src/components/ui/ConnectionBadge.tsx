import type { LiveConnectionState } from '../../api/live'
import { StatusBadge } from './StatusBadge'

export function ConnectionBadge({ state }: { state: LiveConnectionState }) {
  const tone =
    state === 'Connected'
      ? 'normal'
      : state === 'Reconnecting'
        ? 'warning'
        : 'info'

  return <StatusBadge tone={tone}>{state}</StatusBadge>
}
