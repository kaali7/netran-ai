import React from 'react';
import { RouterProvider } from 'react-router-dom';
import router from './router';
import ErrorBoundary from './components/ui/ErrorBoundary';
import './styles/index.css';
import './styles/glass.css';
import './styles/animations.css';

export function App() {
  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
    </ErrorBoundary>
  );
}

export default App;
