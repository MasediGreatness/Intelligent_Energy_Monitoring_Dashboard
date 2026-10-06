import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useOutletContext } from 'react-router-dom'

import type { UserIdentity } from '../api/auth'
import {
  getSettings,
  updateSetting,
  type SettingItem,
  type SettingKey,
} from '../api/dashboard'
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
  PermissionNotice,
} from '../components/states/DataStates'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'

type Values = Record<SettingKey, string | number>

const defaults: Values = {
  demand_limit_kw: 50,
  demand_interval_minutes: 15,
  tariff_zar_per_kwh: 3,
  timezone: 'Africa/Johannesburg',
  online_timeout_seconds: 10,
  stale_timeout_seconds: 60,
  simulator_profile: 'normal',
}

function settingValues(items: SettingItem[]): Values {
  const values = { ...defaults }
  items.forEach((item) => {
    values[item.key] = item.value_json
  })
  return values
}

function validate(values: Values) {
  const demand = Number(values.demand_limit_kw)
  const tariff = Number(values.tariff_zar_per_kwh)
  const online = Number(values.online_timeout_seconds)
  const stale = Number(values.stale_timeout_seconds)
  if (!(demand > 0 && demand <= 2000))
    return 'Demand limit must be greater than 0 and at most 2000 kW.'
  if (!(tariff >= 0 && tariff <= 100))
    return 'Tariff must be from 0 to 100 ZAR/kWh.'
  if (!Number.isInteger(online) || online < 1 || online > 86400)
    return 'Online timeout must be a whole number from 1 to 86400 seconds.'
  if (!Number.isInteger(stale) || stale <= online || stale > 86400)
    return 'Stale timeout must be a whole number greater than online timeout.'
  return ''
}

export function SettingsPage() {
  const user = useOutletContext<UserIdentity>()
  const queryClient = useQueryClient()
  const isAdmin = user.role === 'admin'
  const settings = useQuery({
    queryKey: ['settings'],
    queryFn: ({ signal }) => getSettings(signal),
  })
  const [draft, setDraft] = useState<Partial<Values>>({})
  const [validationError, setValidationError] = useState('')
  const [message, setMessage] = useState('')

  const values = { ...settingValues(settings.data ?? []), ...draft }

  const save = useMutation({
    mutationFn: async (next: Values) => {
      const current = settingValues(settings.data ?? [])
      const changed = (Object.keys(next) as SettingKey[]).filter(
        (key) => next[key] !== current[key],
      )
      const online = Number(next.online_timeout_seconds)
      const currentStale = Number(current.stale_timeout_seconds)
      changed.sort((left, right) => {
        if (online >= currentStale) {
          if (left === 'stale_timeout_seconds') return -1
          if (right === 'stale_timeout_seconds') return 1
        }
        return 0
      })
      for (const key of changed) await updateSetting(key, next[key])
      return changed.length
    },
    onSuccess: async (count) => {
      setMessage(
        count
          ? `${count} setting${count === 1 ? '' : 's'} saved and reloaded.`
          : 'No settings changed.',
      )
      await queryClient.invalidateQueries({ queryKey: ['settings'] })
      setDraft({})
    },
  })

  function setNumber(key: SettingKey, value: string) {
    setDraft({ ...draft, [key]: Number(value) })
    setValidationError('')
    setMessage('')
  }

  return (
    <>
      <PageHeader
        eyebrow="CONFIGURATION"
        title="Dashboard settings"
        description="Manage the fixed interpretation, tariff, timing, and simulation contract."
        action={<StatusBadge tone="info">Validated server-side</StatusBadge>}
      />
      {!isAdmin ? (
        <PermissionNotice message="Only administrators can change operational settings." />
      ) : null}
      {settings.isPending ? (
        <LoadingPanel label="Loading settings" />
      ) : settings.isError ? (
        <ErrorPanel
          message="Settings could not be loaded."
          onRetry={() => void settings.refetch()}
        />
      ) : !settings.data.length ? (
        <EmptyState
          title="Settings unavailable"
          message="The operational settings contract has not been initialised."
        />
      ) : (
        <form
          className="card settings-form"
          onSubmit={(event) => {
            event.preventDefault()
            const error = validate(values)
            setValidationError(error)
            setMessage('')
            if (!error) save.mutate(values)
          }}
        >
          <div className="settings-grid">
            <label>
              Demand limit (kW)
              <input
                disabled={!isAdmin}
                max={2000}
                min="0.01"
                step="0.01"
                type="number"
                value={values.demand_limit_kw}
                onChange={(event) =>
                  setNumber('demand_limit_kw', event.target.value)
                }
              />
              <small>Warning threshold, not a load-control command.</small>
            </label>
            <label>
              Demand interval
              <select
                disabled={!isAdmin}
                value={values.demand_interval_minutes}
                onChange={(event) =>
                  setNumber('demand_interval_minutes', event.target.value)
                }
              >
                {[1, 5, 15, 30, 60].map((minutes) => (
                  <option key={minutes} value={minutes}>
                    {minutes} minutes
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tariff (ZAR/kWh)
              <input
                disabled={!isAdmin}
                max={100}
                min={0}
                step="0.01"
                type="number"
                value={values.tariff_zar_per_kwh}
                onChange={(event) =>
                  setNumber('tariff_zar_per_kwh', event.target.value)
                }
              />
            </label>
            <label>
              Timezone
              <select
                disabled={!isAdmin}
                value={values.timezone}
                onChange={(event) =>
                  setDraft({ ...draft, timezone: event.target.value })
                }
              >
                <option value="Africa/Johannesburg">Africa/Johannesburg</option>
                <option value="UTC">UTC</option>
              </select>
            </label>
            <label>
              Online timeout (seconds)
              <input
                disabled={!isAdmin}
                max={86400}
                min={1}
                step={1}
                type="number"
                value={values.online_timeout_seconds}
                onChange={(event) =>
                  setNumber('online_timeout_seconds', event.target.value)
                }
              />
            </label>
            <label>
              Stale timeout (seconds)
              <input
                aria-label="Stale timeout (seconds)"
                disabled={!isAdmin}
                max={86400}
                min={1}
                step={1}
                type="number"
                value={values.stale_timeout_seconds}
                onChange={(event) =>
                  setNumber('stale_timeout_seconds', event.target.value)
                }
              />
              <small>Must be greater than the online timeout.</small>
            </label>
            <label>
              Simulator profile
              <select
                disabled={!isAdmin}
                value={values.simulator_profile}
                onChange={(event) =>
                  setDraft({
                    ...draft,
                    simulator_profile: event.target.value,
                  })
                }
              >
                <option value="normal">Normal</option>
                <option value="peak_demand">Peak demand</option>
                <option value="low_power_factor">Low power factor</option>
                <option value="sudden_overconsumption">
                  Sudden overconsumption
                </option>
                <option value="device_dropout">Device dropout</option>
                <option value="meter_reset">Meter reset</option>
              </select>
            </label>
          </div>
          {validationError ? (
            <p className="form-error" role="alert">
              {validationError}
            </p>
          ) : null}
          {save.isError ? (
            <p className="form-error" role="alert">
              {save.error.message}
            </p>
          ) : null}
          {message ? (
            <p className="form-success" role="status">
              {message}
            </p>
          ) : null}
          {isAdmin ? (
            <button
              className="button button-primary settings-save"
              disabled={save.isPending}
              type="submit"
            >
              {save.isPending ? 'Saving…' : 'Save settings'}
            </button>
          ) : null}
        </form>
      )}
    </>
  )
}
