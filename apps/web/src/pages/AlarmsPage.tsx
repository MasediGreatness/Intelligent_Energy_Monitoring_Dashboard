import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useOutletContext, useSearchParams } from 'react-router-dom'

import type { UserIdentity } from '../api/auth'
import {
  acknowledgeAlarm,
  getAlarms,
  getDevices,
  type AlarmItem,
  type AlarmStatus,
  type Severity,
} from '../api/dashboard'
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
  PermissionNotice,
} from '../components/states/DataStates'
import { DataTable } from '../components/ui/DataTable'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { absoluteTime } from '../utils/format'

function alarmTone(severity: Severity) {
  if (severity === 'critical' || severity === 'high') return 'critical' as const
  if (severity === 'medium') return 'warning' as const
  return 'info' as const
}

export function AlarmsPage() {
  const user = useOutletContext<UserIdentity>()
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const [selected, setSelected] = useState<AlarmItem | null>(null)
  const [note, setNote] = useState('')
  const [message, setMessage] = useState('')
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1)
  const pageSize = 20
  const status = (params.get('status') ?? '') as AlarmStatus | ''
  const severity = (params.get('severity') ?? '') as Severity | ''
  const deviceId = params.get('device') ?? ''
  const canAcknowledge = user.role === 'operator' || user.role === 'admin'

  const alarms = useQuery({
    queryKey: ['alarms', page, status, severity, deviceId],
    queryFn: ({ signal }) =>
      getAlarms(
        {
          page,
          pageSize,
          status: status || undefined,
          severity: severity || undefined,
          deviceId: deviceId || undefined,
        },
        signal,
      ),
  })
  const devices = useQuery({
    queryKey: ['devices', 'alarm-filter'],
    queryFn: ({ signal }) => getDevices(1, 200, undefined, signal),
  })
  const acknowledgement = useMutation({
    mutationFn: () => acknowledgeAlarm(selected!.id, note.trim()),
    onSuccess: async ({ alarm }) => {
      setSelected(alarm)
      setNote('')
      setMessage('Acknowledgement recorded in the audit trail.')
      await queryClient.invalidateQueries({ queryKey: ['alarms'] })
    },
  })
  const totalPages = Math.max(
    1,
    Math.ceil((alarms.data?.total ?? 0) / pageSize),
  )

  function updateFilter(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(key, value)
    else next.delete(key)
    next.set('page', '1')
    setParams(next)
    setSelected(null)
  }

  function goToPage(value: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(value))
    setParams(next)
    setSelected(null)
  }

  return (
    <>
      <PageHeader
        eyebrow="OPERATIONS"
        title="Alarms"
        description="Prioritise active conditions, inspect their context, and record accountable acknowledgements."
        action={
          <StatusBadge tone="neutral">
            {alarms.data?.total ?? 0} records
          </StatusBadge>
        }
      />
      {!canAcknowledge ? (
        <PermissionNotice message="Viewer access can inspect alarms but cannot acknowledge them." />
      ) : null}
      <form className="filter-bar" onSubmit={(event) => event.preventDefault()}>
        <label>
          Status
          <select
            value={status}
            onChange={(event) => updateFilter('status', event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="cleared">Cleared</option>
          </select>
        </label>
        <label>
          Severity
          <select
            value={severity}
            onChange={(event) => updateFilter('severity', event.target.value)}
          >
            <option value="">All severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </label>
        <label>
          Device
          <select
            value={deviceId}
            onChange={(event) => updateFilter('device', event.target.value)}
          >
            <option value="">All devices</option>
            {devices.data?.items.map((device) => (
              <option key={device.id} value={device.id}>
                {device.code}
              </option>
            ))}
          </select>
        </label>
      </form>

      <section className="operations-layout">
        <article className="card operations-table-card alarm-table-card">
          {alarms.isPending ? (
            <LoadingPanel label="Loading alarms" />
          ) : alarms.isError ? (
            <ErrorPanel
              message="Alarm records could not be loaded."
              onRetry={() => void alarms.refetch()}
            />
          ) : !alarms.data.items.length ? (
            <EmptyState
              title="No matching alarms"
              message="No alarm records match the selected filters."
            />
          ) : (
            <DataTable
              caption="Filtered alarms"
              headers={['Severity', 'Type', 'Triggered', 'Status', 'Details']}
              rows={alarms.data.items.map((alarm) => [
                <StatusBadge tone={alarmTone(alarm.severity)}>
                  {alarm.severity}
                </StatusBadge>,
                alarm.alarm_type,
                absoluteTime(alarm.triggered_at),
                alarm.status,
                <button
                  className="button button-secondary button-compact"
                  onClick={() => {
                    setSelected(alarm)
                    setMessage('')
                  }}
                  type="button"
                >
                  Review
                </button>,
              ])}
            />
          )}
          <nav className="pagination" aria-label="Alarm pages">
            <button
              className="button button-secondary"
              disabled={page <= 1}
              onClick={() => goToPage(page - 1)}
              type="button"
            >
              Previous
            </button>
            <span>
              Page {page} of {totalPages}
            </span>
            <button
              className="button button-secondary"
              disabled={page >= totalPages}
              onClick={() => goToPage(page + 1)}
              type="button"
            >
              Next
            </button>
          </nav>
        </article>

        {selected ? (
          <aside className="card details-drawer" aria-label="Alarm details">
            <div className="card-header">
              <div>
                <p className="eyebrow">ALARM DETAILS</p>
                <h2>{selected.alarm_type}</h2>
              </div>
              <button
                aria-label="Close alarm details"
                className="button button-secondary button-compact"
                onClick={() => setSelected(null)}
                type="button"
              >
                Close
              </button>
            </div>
            <dl className="detail-list">
              <div>
                <dt>Message</dt>
                <dd>{selected.message}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{selected.source}</dd>
              </div>
              <div>
                <dt>Triggered</dt>
                <dd>{absoluteTime(selected.triggered_at)}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{selected.status}</dd>
              </div>
              {selected.acknowledged_at ? (
                <div>
                  <dt>Acknowledged</dt>
                  <dd>{absoluteTime(selected.acknowledged_at)}</dd>
                </div>
              ) : null}
              {selected.acknowledgement_note ? (
                <div>
                  <dt>Operator note</dt>
                  <dd>{selected.acknowledgement_note}</dd>
                </div>
              ) : null}
            </dl>
            {message ? (
              <p className="form-success" role="status">
                {message}
              </p>
            ) : null}
            {canAcknowledge && selected.status === 'open' ? (
              <form
                className="stacked-form"
                onSubmit={(event) => {
                  event.preventDefault()
                  if (note.trim()) acknowledgement.mutate()
                }}
              >
                <label>
                  Acknowledgement note
                  <textarea
                    maxLength={2000}
                    required
                    rows={4}
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                  />
                </label>
                {acknowledgement.isError ? (
                  <p className="form-error" role="alert">
                    {acknowledgement.error.message}
                  </p>
                ) : null}
                <button
                  className="button button-primary"
                  disabled={acknowledgement.isPending || !note.trim()}
                  type="submit"
                >
                  {acknowledgement.isPending
                    ? 'Recording…'
                    : 'Acknowledge alarm'}
                </button>
              </form>
            ) : null}
          </aside>
        ) : (
          <aside className="card details-drawer empty-drawer">
            <p>Select an alarm to review its complete record.</p>
          </aside>
        )}
      </section>
    </>
  )
}
