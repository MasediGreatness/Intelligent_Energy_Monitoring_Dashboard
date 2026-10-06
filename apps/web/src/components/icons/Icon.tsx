import type { SVGProps } from 'react'

export type IconName =
  | 'overview'
  | 'live'
  | 'history'
  | 'forecast'
  | 'alarms'
  | 'devices'
  | 'settings'
  | 'menu'
  | 'user'
  | 'bolt'
  | 'refresh'
  | 'info'
  | 'warning'
  | 'error'

const paths: Record<IconName, string> = {
  overview: 'M4 13h6V4H4v9Zm0 7h6v-5H4v5Zm10 0h6v-9h-6v9Zm0-16v5h6V4h-6Z',
  live: 'M4 12h3l2-5 4 10 2-5h5',
  history: 'M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5M12 7v5l3 2',
  forecast: 'm4 17 5-5 4 3 7-8M16 7h4v4',
  alarms: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4',
  devices: 'M7 2h10v6H7V2Zm-2 9h14v11H5V11Zm4 4h6',
  settings:
    'M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Zm8-3.5 2-1-2-4-2 .5-1.5-1L16 4h-4l-.5 2.5-1.5 1L8 7 6 11l2 1v2l-2 1 2 4 2-.5 1.5 1L12 22h4l.5-2.5 1.5-1 2 .5 2-4-2-1v-2Z',
  menu: 'M4 7h16M4 12h16M4 17h16',
  user: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 8a7 7 0 0 0-14 0',
  bolt: 'm13 2-9 12h7l-1 8 9-12h-7l1-8Z',
  refresh:
    'M20 6v5h-5M4 18v-5h5M6.1 9a7 7 0 0 1 11.6-2.6L20 11M4 13l2.3 4.6A7 7 0 0 0 18 15',
  info: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Zm0-11v6m0-10h.01',
  warning: 'M12 3 2 20h20L12 3Zm0 6v5m0 3h.01',
  error: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Zm-3-7 6-6m0 6-6-6',
}

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName
}

export function Icon({ name, ...props }: IconProps) {
  return (
    <svg aria-hidden="true" fill="none" viewBox="0 0 24 24" {...props}>
      <path
        d={paths[name]}
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="1.8"
      />
    </svg>
  )
}
