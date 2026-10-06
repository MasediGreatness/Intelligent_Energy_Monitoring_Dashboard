import type { IconName } from '../components/icons/Icon'

export interface PageDefinition {
  path: string
  shortTitle: string
  title: string
  description: string
  icon: IconName
}

export const pageDefinitions: PageDefinition[] = [
  {
    path: '/',
    shortTitle: 'Overview',
    title: 'Energy overview',
    description:
      'Current demand, energy, peak demand and operational health at a glance.',
    icon: 'overview',
  },
  {
    path: '/live',
    shortTitle: 'Live monitoring',
    title: 'Live monitoring',
    description:
      'Per-device electrical measurements, connection quality and recent trends.',
    icon: 'live',
  },
  {
    path: '/history',
    shortTitle: 'Energy history',
    title: 'Energy history',
    description:
      'Explore power, energy and demand over a selected, reproducible period.',
    icon: 'history',
  },
  {
    path: '/forecast',
    shortTitle: 'Forecast & anomalies',
    title: 'Forecast and anomalies',
    description:
      'Review model forecasts, confidence and unusual operating behaviour.',
    icon: 'forecast',
  },
  {
    path: '/alarms',
    shortTitle: 'Alarms',
    title: 'Alarms',
    description:
      'Prioritise open conditions and review acknowledgement history.',
    icon: 'alarms',
  },
  {
    path: '/devices',
    shortTitle: 'Devices',
    title: 'Devices',
    description:
      'Review monitored sources, criticality, status and data quality.',
    icon: 'devices',
  },
  {
    path: '/settings',
    shortTitle: 'Settings',
    title: 'Dashboard settings',
    description:
      'Manage interpretation thresholds, tariff, timezone and simulator options.',
    icon: 'settings',
  },
]
