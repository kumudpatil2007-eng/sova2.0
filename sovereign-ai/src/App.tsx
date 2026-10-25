import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './components/auth/LoginPage';
import AppLayout from './components/layout/AppLayout';
import Workspace from './pages/Workspace';
import Analyses from './pages/Analyses';
import KnowledgeBase from './pages/KnowledgeBase';
import Architecture from './pages/Architecture';
import SystemPage from './pages/SystemPage';

const AppRoutes: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<Workspace />} />
          <Route path="/analyses" element={<Analyses />} />
          <Route path="/knowledge" element={<KnowledgeBase />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="/system" element={<SystemPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
};

export default App;
