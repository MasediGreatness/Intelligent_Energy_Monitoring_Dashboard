import { Navigate, Route, Routes } from 'react-router-dom'

import { ProtectedRoute } from './auth/ProtectedRoute'
import { AppShell } from './layouts/AppShell'
import { LoginPage } from './pages/LoginPage'
import { LiveMonitoringPage } from './pages/LiveMonitoringPage'
import { OverviewPage } from './pages/OverviewPage'
import { HistoryPage } from './pages/HistoryPage'
import { ForecastAnomaliesPage } from './pages/ForecastAnomaliesPage'
import { pageDefinitions } from './pages/definitions'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { AlarmsPage } from './pages/AlarmsPage'
import { DevicesPage } from './pages/DevicesPage'
import { SettingsPage } from './pages/SettingsPage'

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          {pageDefinitions.map((page) => (
            <Route
              key={page.path}
              path={page.path}
              element={
                page.path === '/' ? (
                  <OverviewPage />
                ) : page.path === '/live' ? (
                  <LiveMonitoringPage />
                ) : page.path === '/history' ? (
                  <HistoryPage />
                ) : page.path === '/forecast' ? (
                  <ForecastAnomaliesPage />
                ) : page.path === '/alarms' ? (
                  <AlarmsPage />
                ) : page.path === '/devices' ? (
                  <DevicesPage />
                ) : page.path === '/settings' ? (
                  <SettingsPage />
                ) : (
                  <PlaceholderPage page={page} />
                )
              }
            />
          ))}
        </Route>
      </Route>
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}
