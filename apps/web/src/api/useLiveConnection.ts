import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'

import { LiveClient, liveUrl, type LiveConnectionState } from './live'

export function useLiveConnection(): LiveConnectionState {
  const queryClient = useQueryClient()
  const [state, setState] = useState<LiveConnectionState>('Connecting')

  useEffect(() => {
    const client = new LiveClient({
      url: liveUrl(),
      subscription: {
        type: 'subscribe',
        device_ids: [],
        event_types: [
          'measurement.new',
          'alarm.changed',
          'device.status',
          'heartbeat',
        ],
      },
      onEvent: (event) => {
        if (
          event.type === 'measurement.new' ||
          event.type === 'device.status'
        ) {
          void queryClient.invalidateQueries({
            queryKey: ['latest-measurements'],
          })
          void queryClient.invalidateQueries({
            queryKey: ['dashboard-summary'],
          })
          void queryClient.invalidateQueries({ queryKey: ['overview-history'] })
          void queryClient.invalidateQueries({ queryKey: ['live-history'] })
        }
        if (event.type === 'alarm.changed') {
          void queryClient.invalidateQueries({
            queryKey: ['dashboard-summary'],
          })
          void queryClient.invalidateQueries({ queryKey: ['recent-alarms'] })
        }
      },
      onStateChange: setState,
      onRecovery: () => {
        void queryClient.invalidateQueries()
      },
    })
    client.start()
    return () => client.stop()
  }, [queryClient])

  return state
}
