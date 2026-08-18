import React from 'react';
import { RouterProvider } from 'react-router-dom';
import router from './router';
import './styles/index.css';
import './styles/glass.css';
import './styles/animations.css';

export function App() {
  return <RouterProvider router={router} />;
}

export default App;
