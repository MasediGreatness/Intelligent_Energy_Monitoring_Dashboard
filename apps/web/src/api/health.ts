export interface HealthResponse {
  status: 'ok'
  service: 'energy-dashboard-api'
  version: string
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? ''

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, { signal })
  if (!response.ok) {
    throw new Error(`Health check failed with HTTP ${response.status}`)
  }
  return (await response.json()) as HealthResponse
}
