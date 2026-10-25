import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

interface AppLayoutProps {
  onLoadSample?: () => void;
  isProcessing?: boolean;
}

const AppLayout: React.FC<AppLayoutProps> = ({ onLoadSample, isProcessing = false }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', overflow: 'hidden' }}>
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          minWidth: 0,
        }}
      >
        <TopBar onLoadSample={onLoadSample} isProcessing={isProcessing} />
        <main
          className="bg-grid bg-radial-glow"
          style={{
            flex: 1,
            overflow: 'auto',
            background: 'var(--color-bg-primary)',
          }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
