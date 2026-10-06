import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
  PermissionNotice,
  StaleBanner,
} from '../components/states/DataStates'
import { StatusBadge } from '../components/ui/StatusBadge'
import { PageHeader } from '../components/ui/PageHeader'
import type { PageDefinition } from './definitions'

export function PlaceholderPage({ page }: { page: PageDefinition }) {
  return (
    <>
      <PageHeader
        eyebrow="DASHBOARD"
        title={page.title}
        description={page.description}
        action={<StatusBadge tone="info">Foundation ready</StatusBadge>}
      />
      <StaleBanner message="Live panels arrive in the next approved build step. Stale data will always be labelled here." />
      <section
        aria-label={`${page.title} placeholder panels`}
        className="content-grid"
      >
        <article className="card span-8">
          <div className="card-header">
            <div>
              <p className="eyebrow">PRIMARY VIEW</p>
              <h2>Data panel reserved</h2>
            </div>
            <StatusBadge tone="neutral">No data</StatusBadge>
          </div>
          <EmptyState message="This route is ready for its approved data components. No values are being invented." />
        </article>
        <aside className="card span-4">
          <div className="card-header">
            <h2>Reusable states</h2>
          </div>
          <div className="state-showcase">
            <LoadingPanel label="Loading state" />
            <PermissionNotice />
            <ErrorPanel
              message="Network errors include a retry action."
              onRetry={() => undefined}
            />
          </div>
        </aside>
      </section>
    </>
  )
}
