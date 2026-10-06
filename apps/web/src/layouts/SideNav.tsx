import { NavLink } from 'react-router-dom'

import { Icon } from '../components/icons/Icon'
import type { PageDefinition } from '../pages/definitions'

export function SideNav({
  pages,
  collapsed,
  open,
  onNavigate,
}: {
  pages: PageDefinition[]
  collapsed: boolean
  open: boolean
  onNavigate: () => void
}) {
  return (
    <aside
      aria-label="Primary"
      className={`side-nav ${collapsed ? 'is-collapsed' : ''} ${open ? 'is-open' : ''}`}
    >
      <div className="brand">
        <span className="brand-mark">
          <Icon name="bolt" />
        </span>
        <span className="brand-copy">
          <strong>Intelligent Energy</strong>
          <small>Monitoring dashboard</small>
        </span>
      </div>
      <nav>
        <ul>
          {pages.map((page) => (
            <li key={page.path}>
              <NavLink
                className={({ isActive }) =>
                  isActive ? 'nav-link active' : 'nav-link'
                }
                end={page.path === '/'}
                onClick={onNavigate}
                to={page.path}
              >
                <Icon name={page.icon} />
                <span>{page.shortTitle}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
      <p className="safety-note">
        <Icon name="info" />
        <span>Monitoring and advisory only</span>
      </p>
    </aside>
  )
}
