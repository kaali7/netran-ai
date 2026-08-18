import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Setup from './pages/Setup';
import Interview from './pages/Interview';
import Processing from './pages/Processing';
import Report from './pages/Report';
import { useAuthStore } from './store/authStore';

/**
 * Route guard component for authenticated candidate pages.
 */
const ProtectedRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

/**
 * Route guard component for public-only auth pages.
 */
const PublicRoute = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
};

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/login',
    element: (
      <PublicRoute>
        <Login />
      </PublicRoute>
    ),
  },
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  {
    path: '/setup',
    element: (
      <ProtectedRoute>
        <Setup />
      </ProtectedRoute>
    ),
  },
  {
    path: '/interview/:sessionId',
    element: (
      <ProtectedRoute>
        <Interview />
      </ProtectedRoute>
    ),
  },
  {
    path: '/processing/:sessionId',
    element: (
      <ProtectedRoute>
        <Processing />
      </ProtectedRoute>
    ),
  },
  {
    path: '/report/:sessionId',
    element: (
      <ProtectedRoute>
        <Report />
      </ProtectedRoute>
    ),
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
], {
  future: {
    v7_startTransition: true,
    v7_relativeSplatPath: true,
  },
});

export default router;
