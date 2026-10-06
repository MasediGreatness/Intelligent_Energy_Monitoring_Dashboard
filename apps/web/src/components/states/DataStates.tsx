import { Icon } from '../icons/Icon'

interface StateProps {
  title?: string
  message?: string
  fullPage?: boolean
}

export function LoadingPanel({
  label = 'Loading data',
  fullPage = false,
}: {
  label?: string
  fullPage?: boolean
}) {
  return (
    <main
      aria-busy="true"
      aria-live="polite"
      className={fullPage ? 'state-page' : 'state-panel'}
    >
      <div aria-hidden="true" className="spinner" />
      <p>{label}</p>
      <div aria-hidden="true" className="skeleton-lines">
        <span />
        <span />
        <span />
      </div>
    </main>
  )
}

export function EmptyState({
  title = 'No data available',
  message = 'There is nothing to display for this selection.',
}: StateProps) {
  return (
    <section className="state-panel">
      <Icon name="info" />
      <h3>{title}</h3>
      <p>{message}</p>
    </section>
  )
}

export function ErrorPanel({
  title = 'Something went wrong',
  message = 'The data could not be loaded.',
  onRetry,
  fullPage = false,
}: StateProps & { onRetry?: () => void }) {
  return (
    <main className={fullPage ? 'state-page' : 'state-panel'}>
      <Icon name="error" />
      <h3>{title}</h3>
      <p>{message}</p>
      {onRetry ? (
        <button className="button button-secondary" onClick={onRetry}>
          <Icon name="refresh" />
          Try again
        </button>
      ) : null}
    </main>
  )
}

export function PermissionNotice({
  message = 'Your role does not permit this action.',
}: {
  message?: string
}) {
  return (
    <aside className="notice notice-info">
      <Icon name="info" />
      <div>
        <strong>View only</strong>
        <p>{message}</p>
      </div>
    </aside>
  )
}

export function StaleBanner({
  message = 'Some sources are stale. Values may not reflect current conditions.',
}: {
  message?: string
}) {
  return (
    <aside className="notice notice-warning" role="status">
      <Icon name="warning" />
      <div>
        <strong>Stale data</strong>
        <p>{message}</p>
      </div>
    </aside>
  )
}
