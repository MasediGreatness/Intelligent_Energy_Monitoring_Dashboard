import { useState } from 'react'
import { Outlet, useOutletContext } from 'react-router-dom'

import type { UserIdentity } from '../api/auth'
import { useLiveConnection } from '../api/useLiveConnection'
import { pageDefinitions } from '../pages/definitions'
import { SideNav } from './SideNav'
import { TopBar } from './TopBar'

export function AppShell() {
  const user = useOutletContext<UserIdentity>()
  const liveState = useLiveConnection()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className={`dashboard-shell ${collapsed ? 'nav-collapsed' : ''}`}>
      <a className="skip-link" href="#main-content">
        Skip to main content
      </a>
      <SideNav
        collapsed={collapsed}
        onNavigate={() => setMobileOpen(false)}
        open={mobileOpen}
        pages={pageDefinitions}
      />
      {mobileOpen ? (
        <button
          aria-label="Close navigation"
          className="nav-scrim"
          onClick={() => setMobileOpen(false)}
        />
      ) : null}
      <div className="dashboard-body">
        <TopBar
          collapsed={collapsed}
          liveState={liveState}
          onCollapse={() => setCollapsed((value) => !value)}
          onMenu={() => setMobileOpen(true)}
          user={user}
        />
        <main className="page-content" id="main-content" tabIndex={-1}>
          <Outlet context={user} />
        </main>
      </div>
    </div>
  )
}
