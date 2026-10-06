import { afterEach, describe, expect, it, vi } from 'vitest'

import { LiveClient, type LiveConnectionState, type LiveEvent } from './live'

class FakeSocket {
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent<string>) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  sent: string[] = []

  send(data: string): void {
    this.sent.push(data)
  }

  close(): void {
    this.onclose?.({} as CloseEvent)
  }

  open(): void {
    this.onopen?.({} as Event)
  }

  message(event: LiveEvent): void {
    this.onmessage?.({ data: JSON.stringify(event) } as MessageEvent<string>)
  }
}

afterEach(() => {
  vi.useRealTimers()
})

function event(sequence: number): LiveEvent {
  return {
    type: 'heartbeat',
    emitted_at: new Date().toISOString(),
    sequence,
    payload: {},
  }
}

describe('LiveClient recovery', () => {
  it('shows Reconnecting, reconnects, and requests a REST recovery', () => {
    vi.useFakeTimers()
    const sockets: FakeSocket[] = []
    const states: LiveConnectionState[] = []
    const recover = vi.fn()
    const client = new LiveClient({
      url: 'ws://example.test/api/v1/ws/live',
      subscription: { type: 'subscribe', device_ids: [], event_types: [] },
      onEvent: () => undefined,
      onStateChange: (state) => states.push(state),
      onRecovery: recover,
      socketFactory: () => {
        const socket = new FakeSocket()
        sockets.push(socket)
        return socket
      },
    })
    client.start()
    sockets[0].open()
    sockets[0].close()
    expect(states.at(-1)).toBe('Reconnecting')
    vi.advanceTimersByTime(1000)
    sockets[1].open()
    expect(states.at(-1)).toBe('Connected')
    expect(recover).toHaveBeenCalledOnce()
    client.stop()
  })

  it('forces REST recovery when a sequence gap is detected', () => {
    const socket = new FakeSocket()
    const recover = vi.fn()
    const received: number[] = []
    const client = new LiveClient({
      url: 'ws://example.test/api/v1/ws/live',
      subscription: { type: 'subscribe', device_ids: [], event_types: [] },
      onEvent: (item) => received.push(item.sequence),
      onStateChange: () => undefined,
      onRecovery: recover,
      socketFactory: () => socket,
    })
    client.start()
    socket.open()
    socket.message(event(10))
    socket.message(event(12))
    expect(received).toEqual([10, 12])
    expect(recover).toHaveBeenCalledOnce()
    client.stop()
  })

  it('closes a connection after five seconds without a heartbeat', () => {
    vi.useFakeTimers()
    const socket = new FakeSocket()
    const close = vi.spyOn(socket, 'close')
    const client = new LiveClient({
      url: 'ws://example.test/api/v1/ws/live',
      subscription: { type: 'subscribe', device_ids: [], event_types: [] },
      onEvent: () => undefined,
      onStateChange: () => undefined,
      onRecovery: () => undefined,
      socketFactory: () => socket,
    })
    client.start()
    socket.open()
    vi.advanceTimersByTime(6000)
    expect(close).toHaveBeenCalled()
    client.stop()
  })
})
