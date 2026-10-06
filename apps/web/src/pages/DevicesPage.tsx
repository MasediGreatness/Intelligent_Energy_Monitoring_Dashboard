import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useOutletContext, useSearchParams } from 'react-router-dom'

import type { UserIdentity } from '../api/auth'
import {
  createDevice,
  getDevices,
  updateDevice,
  type DeviceInput,
  type DeviceItem,
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

const emptyDevice: DeviceInput = {
  code: '',
  name: '',
  location: '',
  phase_type: 'three_phase',
  rated_power_kw: 1,
  criticality: 'medium',
  enabled: true,
}

function deviceTone(status: DeviceItem['status']) {
  if (status === 'online') return 'normal' as const
  if (status === 'stale') return 'warning' as const
  if (status === 'offline') return 'critical' as const
  return 'neutral' as const
}

export function DevicesPage() {
  const user = useOutletContext<UserIdentity>()
  const queryClient = useQueryClient()
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page') ?? '1') || 1)
  const pageSize = 20
  const enabledFilter = params.get('enabled') ?? ''
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editorOpen, setEditorOpen] = useState(false)
  const [form, setForm] = useState<DeviceInput>(emptyDevice)
  const [message, setMessage] = useState('')
  const isAdmin = user.role === 'admin'
  const devices = useQuery({
    queryKey: ['devices', page, enabledFilter],
    queryFn: ({ signal }) =>
      getDevices(
        page,
        pageSize,
        enabledFilter === '' ? undefined : enabledFilter === 'true',
        signal,
      ),
  })
  const save = useMutation({
    mutationFn: (input: DeviceInput) =>
      editingId ? updateDevice(editingId, input) : createDevice(input),
    onSuccess: async ({ device }) => {
      setEditingId(null)
      setEditorOpen(false)
      setForm(emptyDevice)
      setMessage(`${device.code} saved. The device table was refreshed.`)
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })
  const disable = useMutation({
    mutationFn: (device: DeviceItem) =>
      updateDevice(device.id, { enabled: false }),
    onSuccess: async ({ device }) => {
      setMessage(`${device.code} disabled without deleting its history.`)
      await queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })
  const totalPages = Math.max(
    1,
    Math.ceil((devices.data?.total ?? 0) / pageSize),
  )

  function beginEdit(device?: DeviceItem) {
    setEditorOpen(true)
    if (device) {
      setEditingId(device.id)
      setForm({
        code: device.code,
        name: device.name,
        location: device.location,
        phase_type: device.phase_type,
        rated_power_kw: device.rated_power_kw,
        criticality: device.criticality,
        enabled: device.enabled,
      })
    } else {
      setEditingId(null)
      setForm(emptyDevice)
    }
    setMessage('')
  }

  function goToPage(value: number) {
    const next = new URLSearchParams(params)
    next.set('page', String(value))
    setParams(next)
  }

  return (
    <>
      <PageHeader
        eyebrow="ASSET REGISTER"
        title="Devices"
        description="Review monitored assets and administer metadata without removing historical records."
        action={
          isAdmin ? (
            <button
              className="button button-primary"
              onClick={() => beginEdit()}
              type="button"
            >
              Create device
            </button>
          ) : null
        }
      />
      {!isAdmin ? (
        <PermissionNotice message="Only administrators can create, edit, or disable devices." />
      ) : null}
      {message ? (
        <p className="form-success" role="status">
          {message}
        </p>
      ) : null}
      <form className="filter-bar" onSubmit={(event) => event.preventDefault()}>
        <label>
          Enabled state
          <select
            value={enabledFilter}
            onChange={(event) => {
              const next = new URLSearchParams(params)
              if (event.target.value) next.set('enabled', event.target.value)
              else next.delete('enabled')
              next.set('page', '1')
              setParams(next)
            }}
          >
            <option value="">All devices</option>
            <option value="true">Enabled</option>
            <option value="false">Disabled</option>
          </select>
        </label>
      </form>
      <section className="operations-layout">
        <article className="card operations-table-card">
          {devices.isPending ? (
            <LoadingPanel label="Loading devices" />
          ) : devices.isError ? (
            <ErrorPanel
              message="Device records could not be loaded."
              onRetry={() => void devices.refetch()}
            />
          ) : !devices.data.items.length ? (
            <EmptyState
              title="No matching devices"
              message="No device records match this filter."
            />
          ) : (
            <DataTable
              caption="Device status and metadata"
              headers={[
                'Code',
                'Name',
                'Location',
                'Rated kW',
                'Criticality',
                'Status',
                ...(isAdmin ? ['Administration'] : []),
              ]}
              rows={devices.data.items.map((device) => [
                device.code,
                <span>
                  <strong>{device.name}</strong>
                  <small className="table-secondary">
                    Last seen {absoluteTime(device.last_seen_at)}
                  </small>
                </span>,
                device.location,
                device.rated_power_kw.toFixed(1),
                device.criticality,
                <StatusBadge tone={deviceTone(device.status)}>
                  {device.status}
                </StatusBadge>,
                ...(isAdmin
                  ? [
                      <div className="table-actions">
                        <button
                          className="button button-secondary button-compact"
                          onClick={() => beginEdit(device)}
                          type="button"
                        >
                          Edit
                        </button>
                        {device.enabled ? (
                          <button
                            className="button button-secondary button-compact"
                            disabled={disable.isPending}
                            onClick={() => disable.mutate(device)}
                            type="button"
                          >
                            Disable
                          </button>
                        ) : null}
                      </div>,
                    ]
                  : []),
              ])}
            />
          )}
          <nav className="pagination" aria-label="Device pages">
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

        {isAdmin && editorOpen ? (
          <aside className="card details-drawer" aria-label="Device editor">
            <div className="card-header">
              <div>
                <p className="eyebrow">ADMINISTRATION</p>
                <h2>{editingId ? 'Edit device' : 'Create device'}</h2>
              </div>
              <button
                className="button button-secondary button-compact"
                onClick={() => {
                  setEditingId(null)
                  setEditorOpen(false)
                  setForm(emptyDevice)
                }}
                type="button"
              >
                Cancel
              </button>
            </div>
            <form
              className="stacked-form"
              onSubmit={(event) => {
                event.preventDefault()
                save.mutate(form)
              }}
            >
              <label>
                Device code
                <input
                  maxLength={64}
                  pattern="[A-Za-z0-9][A-Za-z0-9_-]*"
                  required
                  value={form.code}
                  onChange={(event) =>
                    setForm({ ...form, code: event.target.value.toUpperCase() })
                  }
                />
              </label>
              <label>
                Name
                <input
                  maxLength={160}
                  required
                  value={form.name}
                  onChange={(event) =>
                    setForm({ ...form, name: event.target.value })
                  }
                />
              </label>
              <label>
                Location
                <input
                  maxLength={255}
                  required
                  value={form.location}
                  onChange={(event) =>
                    setForm({ ...form, location: event.target.value })
                  }
                />
              </label>
              <div className="form-row">
                <label>
                  Phase type
                  <select
                    value={form.phase_type}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        phase_type: event.target
                          .value as DeviceInput['phase_type'],
                      })
                    }
                  >
                    <option value="single_phase">Single phase</option>
                    <option value="three_phase">Three phase</option>
                  </select>
                </label>
                <label>
                  Rated power (kW)
                  <input
                    max={2000}
                    min="0.01"
                    required
                    step="0.01"
                    type="number"
                    value={form.rated_power_kw}
                    onChange={(event) =>
                      setForm({
                        ...form,
                        rated_power_kw: Number(event.target.value),
                      })
                    }
                  />
                </label>
              </div>
              <label>
                Criticality
                <select
                  value={form.criticality}
                  onChange={(event) =>
                    setForm({
                      ...form,
                      criticality: event.target
                        .value as DeviceInput['criticality'],
                    })
                  }
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </label>
              <label className="checkbox-label">
                <input
                  checked={form.enabled}
                  onChange={(event) =>
                    setForm({ ...form, enabled: event.target.checked })
                  }
                  type="checkbox"
                />
                Enabled for monitoring
              </label>
              {save.isError ? (
                <p className="form-error" role="alert">
                  {save.error.message}
                </p>
              ) : null}
              <button
                className="button button-primary"
                disabled={save.isPending}
                type="submit"
              >
                {save.isPending ? 'Saving…' : 'Save device'}
              </button>
            </form>
          </aside>
        ) : null}
      </section>
    </>
  )
}
