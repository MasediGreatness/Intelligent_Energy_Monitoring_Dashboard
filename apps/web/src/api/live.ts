export type LiveConnectionState =
  'Connecting' | 'Connected' | 'Reconnecting' | 'Stopped'

export interface LiveEvent {
  type: string
  emitted_at: string
  sequence: number
  payload: Record<string, unknown>
}

export interface LiveSubscription {
  type: 'subscribe'
  device_ids: string[]
  event_types: string[]
}

interface WebSocketLike {
  onopen: ((event: Event) => void) | null
  onmessage: ((event: MessageEvent<string>) => void) | null
  onclose: ((event: CloseEvent) => void) | null
  onerror: ((event: Event) => void) | null
  send(data: string): void
  close(): void
}

type SocketFactory = (url: string) => WebSocketLike

export interface LiveClientOptions {
  url: string
  subscription: LiveSubscription
  onEvent: (event: LiveEvent) => void
  onStateChange: (state: LiveConnectionState) => void
  onRecovery: () => void
  socketFactory?: SocketFactory
}

export class LiveClient {
  private socket: WebSocketLike | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectDelayMs = 1000
  private lastMessageAt = Date.now()
  private lastSequence: number | null = null
  private connectedBefore = false
  private stopped = false

  constructor(private readonly options: LiveClientOptions) {}

  start(): void {
    this.stopped = false
    this.options.onStateChange(
      this.connectedBefore ? 'Reconnecting' : 'Connecting',
    )
    this.connect()
  }

  stop(): void {
    this.stopped = true
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer)
    this.socket?.close()
    this.options.onStateChange('Stopped')
  }

  private connect(): void {
    const factory: SocketFactory =
      this.options.socketFactory ?? ((url) => new WebSocket(url))
    const socket = factory(this.options.url)
    this.socket = socket
    socket.onopen = () => {
      const recovering = this.connectedBefore
      this.connectedBefore = true
      this.reconnectDelayMs = 1000
      this.lastMessageAt = Date.now()
      socket.send(JSON.stringify(this.options.subscription))
      this.options.onStateChange('Connected')
      if (recovering) this.options.onRecovery()
      this.startHeartbeatWatchdog()
    }
    socket.onmessage = (message) => {
      this.lastMessageAt = Date.now()
      const event = JSON.parse(message.data) as LiveEvent
      if (
        this.lastSequence !== null &&
        event.sequence !== this.lastSequence + 1
      ) {
        this.options.onRecovery()
      }
      this.lastSequence = event.sequence
      this.options.onEvent(event)
    }
    socket.onerror = () => socket.close()
    socket.onclose = () => {
      if (this.heartbeatTimer) clearInterval(this.heartbeatTimer)
      if (!this.stopped) this.scheduleReconnect()
    }
  }

  private startHeartbeatWatchdog(): void {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer)
    this.heartbeatTimer = setInterval(() => {
      if (Date.now() - this.lastMessageAt > 5000) this.socket?.close()
    }, 1000)
  }

  private scheduleReconnect(): void {
    this.options.onStateChange('Reconnecting')
    const delay = this.reconnectDelayMs
    this.reconnectDelayMs = Math.min(this.reconnectDelayMs * 2, 30_000)
    this.reconnectTimer = setTimeout(() => this.connect(), delay)
  }
}

export function liveUrl(): string {
  const configured = import.meta.env.VITE_WS_URL ?? '/api/v1/ws/live'
  if (/^wss?:\/\//.test(configured)) return configured
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}${configured}`
}
