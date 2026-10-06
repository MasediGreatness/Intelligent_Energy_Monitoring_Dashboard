import { useQuery } from '@tanstack/react-query'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { currentUser } from '../api/auth'
import { ErrorPanel, LoadingPanel } from '../components/states/DataStates'

export function ProtectedRoute() {
  const location = useLocation()
  const user = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: ({ signal }) => currentUser(signal),
    retry: false,
    staleTime: 30_000,
  })

  if (user.isPending)
    return <LoadingPanel label="Checking your secure session" fullPage />
  if (user.isError) {
    return (
      <ErrorPanel
        title="Unable to verify your session"
        message="Check the API connection, then try again."
        onRetry={() => void user.refetch()}
        fullPage
      />
    )
  }
  if (!user.data)
    return <Navigate replace state={{ from: location.pathname }} to="/login" />
  return <Outlet context={user.data} />
}
