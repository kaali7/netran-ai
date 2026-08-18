import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Setup from './pages/Setup';
import Interview from './pages/Interview';
import Report from './pages/Report';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/dashboard',
    element: <Dashboard />,
  },
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/setup',
    element: <Setup />,
  },
  {
    path: '/interview/:sessionId',
    element: <Interview />,
  },
  {
    path: '/report/:sessionId',
    element: <Report />,
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
]);

export default router;
