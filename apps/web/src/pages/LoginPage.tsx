import { useMutation, useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import { login } from '../api/auth'
import { Icon } from '../components/icons/Icon'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const cachedUser = queryClient.getQueryData(['auth', 'me'])
  const signIn = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: async (result) => {
      queryClient.setQueryData(['auth', 'me'], result.user)
      await queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
      const destination =
        (location.state as { from?: string } | null)?.from ?? '/'
      void navigate(destination, { replace: true })
    },
  })
  if (cachedUser) return <Navigate replace to="/" />

  function submit(event: FormEvent) {
    event.preventDefault()
    signIn.mutate()
  }

  return (
    <main className="login-page">
      <section aria-labelledby="login-title" className="login-card">
        <div className="login-brand">
          <span className="brand-mark">
            <Icon name="bolt" />
          </span>
          <span>
            <strong>Intelligent Energy</strong>
            <small>Industrial monitoring dashboard</small>
          </span>
        </div>
        <div className="login-heading">
          <p className="eyebrow">SECURE ACCESS</p>
          <h1 id="login-title">Welcome back</h1>
          <p>Sign in to view live energy and engineering status.</p>
        </div>
        <form onSubmit={submit}>
          <label htmlFor="email">Email address</label>
          <input
            autoComplete="username"
            id="email"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
          <label htmlFor="password">Password</label>
          <input
            autoComplete="current-password"
            id="password"
            minLength={12}
            onChange={(event) => setPassword(event.target.value)}
            required
            type="password"
            value={password}
          />
          {signIn.isError ? (
            <p className="form-error" role="alert">
              {signIn.error.message}
            </p>
          ) : null}
          <button
            className="button button-primary"
            disabled={signIn.isPending}
            type="submit"
          >
            {signIn.isPending ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="login-safety">
          <Icon name="info" />
          Monitoring and advisory only. No load-control commands.
        </p>
      </section>
    </main>
  )
}
