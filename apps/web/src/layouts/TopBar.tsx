import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { logout, type UserIdentity } from '../api/auth'
import type { LiveConnectionState } from '../api/live'
import { Icon } from '../components/icons/Icon'
import { ConnectionBadge } from '../components/ui/ConnectionBadge'

export function TopBar({
  user,
  liveState,
  onMenu,
  onCollapse,
  collapsed,
}: {
  user: UserIdentity
  liveState: LiveConnectionState
  onMenu: () => void
  onCollapse: () => void
  collapsed: boolean
}) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const signOut = useMutation({
    mutationFn: logout,
    onSuccess: async () => {
      await queryClient.resetQueries({ queryKey: ['auth'] })
      void navigate('/login', { replace: true })
    },
  })
  return (
    <header className="top-bar">
      <div className="top-actions-left">
        <button
          aria-label="Open navigation"
          className="icon-button mobile-menu"
          onClick={onMenu}
        >
          <Icon name="menu" />
        </button>
        <button
          aria-label={collapsed ? 'Expand navigation' : 'Collapse navigation'}
          className="icon-button desktop-collapse"
          onClick={onCollapse}
        >
          <Icon name="menu" />
        </button>
        <ConnectionBadge state={liveState} />
      </div>
      <details className="user-menu">
        <summary>
          <span className="avatar" aria-hidden="true">
            <Icon name="user" />
          </span>
          <span className="user-copy">
            <strong>{user.email}</strong>
            <small>{user.role}</small>
          </span>
        </summary>
        <div className="menu-popover">
          <p>
            Signed in as <strong>{user.role}</strong>
          </p>
          <button
            className="button button-secondary"
            disabled={signOut.isPending}
            onClick={() => signOut.mutate()}
          >
            {signOut.isPending ? 'Signing out…' : 'Sign out'}
          </button>
          {signOut.isError ? (
            <small role="alert">Unable to sign out.</small>
          ) : null}
        </div>
      </details>
    </header>
  )
}
