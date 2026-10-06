export type UserRole = 'viewer' | 'operator' | 'admin'

export interface UserIdentity {
  id: string
  email: string
  role: UserRole
}

interface LoginResponse {
  user: UserIdentity
  expires_at: string
}

const configuredBase = import.meta.env.VITE_API_BASE_URL ?? ''
const apiBase = configuredBase.endsWith('/api/v1')
  ? configuredBase
  : `${configuredBase}/api/v1`

export async function currentUser(
  signal?: AbortSignal,
): Promise<UserIdentity | null> {
  const response = await fetch(`${apiBase}/auth/me`, {
    credentials: 'include',
    signal,
  })
  if (response.status === 401) return null
  if (!response.ok)
    throw new Error(`Session check failed with HTTP ${response.status}`)
  return (await response.json()) as UserIdentity
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  const response = await fetch(`${apiBase}/auth/login`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) throw new Error('The email or password is invalid.')
  return (await response.json()) as LoginResponse
}

export async function logout(): Promise<void> {
  const response = await fetch(`${apiBase}/auth/logout`, {
    method: 'POST',
    credentials: 'include',
  })
  if (!response.ok) throw new Error('Unable to sign out. Please try again.')
}
