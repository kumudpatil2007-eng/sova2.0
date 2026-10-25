import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import Logo from '../common/Logo';
import {
  LayoutDashboard,
  BarChart3,
  BookOpen,
  Cpu,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Zap,
  User,
} from 'lucide-react';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const navItems = [
  { path: '/', label: 'Workspace', icon: LayoutDashboard },
  { path: '/analyses', label: 'Analyses', icon: BarChart3 },
  { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
  { path: '/architecture', label: 'Architecture', icon: Cpu },
  { path: '/system', label: 'System', icon: Settings },
];

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onToggle }) => {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <aside
      style={{
        width: collapsed ? 68 : 240,
        minWidth: collapsed ? 68 : 240,
        height: '100vh',
        background: 'var(--color-sidebar-bg)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden',
        position: 'relative',
        zIndex: 20,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: collapsed ? '20px 14px 16px' : '20px 18px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: collapsed ? 'center' : 'space-between',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
        }}
      >
        <Logo size={collapsed ? 28 : 30} showText={!collapsed} variant="light" />
        <button
          onClick={onToggle}
          style={{
            display: collapsed ? 'none' : 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 26,
            height: 26,
            borderRadius: 6,
            border: 'none',
            background: 'rgba(255,255,255,0.06)',
            color: 'var(--color-sidebar-text)',
            cursor: 'pointer',
            transition: 'background 0.15s',
            flexShrink: 0,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
        >
          <ChevronLeft size={14} />
        </button>
      </div>

      {/* Collapsed toggle */}
      {collapsed && (
        <button
          onClick={onToggle}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: 26,
            height: 26,
            borderRadius: 6,
            border: 'none',
            background: 'rgba(255,255,255,0.06)',
            color: 'var(--color-sidebar-text)',
            cursor: 'pointer',
            margin: '8px auto 0',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.1)')}
          onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(255,255,255,0.06)')}
        >
          <ChevronRight size={14} />
        </button>
      )}

      {/* Navigation */}
      <nav style={{ flex: 1, padding: collapsed ? '16px 10px' : '16px 12px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <button
                key={item.path}
                className={`sidebar-link ${isActive ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
                style={{
                  border: 'none',
                  background: isActive ? 'var(--color-sidebar-active)' : 'transparent',
                  justifyContent: collapsed ? 'center' : 'flex-start',
                  padding: collapsed ? '10px' : undefined,
                }}
                title={collapsed ? item.label : undefined}
              >
                <Icon size={18} style={{ flexShrink: 0 }} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Bottom Section */}
      <div
        style={{
          padding: collapsed ? '16px 10px' : '16px 14px',
          borderTop: '1px solid rgba(255,255,255,0.06)',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {/* Status indicators */}
        <div
          style={{
            display: 'flex',
            alignItems: collapsed ? 'center' : 'flex-start',
            flexDirection: 'column',
            gap: 6,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 11,
              fontWeight: 600,
              color: '#10B981',
              letterSpacing: '0.04em',
            }}
          >
            <Shield size={13} style={{ flexShrink: 0 }} />
            {!collapsed && <span>AIR-GAPPED</span>}
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 11,
              fontWeight: 600,
              color: '#14B8A6',
              letterSpacing: '0.04em',
            }}
          >
            <Zap size={13} style={{ flexShrink: 0 }} />
            {!collapsed && <span>LOCAL INFERENCE</span>}
          </div>
        </div>

        {/* User profile */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 4px',
            borderTop: '1px solid rgba(255,255,255,0.06)',
            marginTop: 4,
            justifyContent: collapsed ? 'center' : 'flex-start',
          }}
        >
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 8,
              background: 'linear-gradient(135deg, #2563EB, #0D9488)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <User size={14} color="white" />
          </div>
          {!collapsed && (
            <div style={{ overflow: 'hidden' }}>
              <div
                style={{
                  fontSize: 12.5,
                  fontWeight: 600,
                  color: 'var(--color-sidebar-text-active)',
                  whiteSpace: 'nowrap',
                }}
              >
                Chief Inspector
              </div>
              <div
                style={{
                  fontSize: 10.5,
                  color: 'var(--color-sidebar-text)',
                  whiteSpace: 'nowrap',
                }}
              >
                Inspection Dept.
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
