import React, { useState, useEffect, useRef } from 'react';
import {
  Shield,
  Radio,
  ExternalLink,
  Play,
  Cpu,
  ChevronDown,
  LogOut,
  BadgeCheck,
} from 'lucide-react';
import Logo from '../common/Logo';
import SystemPanel from '../status/SystemPanel';
import { getSystemStatus, type SystemStatusResponse } from '../../services/api';
import { useAuth } from '../../context/AuthContext';

interface TopBarProps {
  onLoadSample?: () => void;
  isProcessing?: boolean;
}

const TopBar: React.FC<TopBarProps> = ({ onLoadSample, isProcessing = false }) => {
  const { currentUser, logout } = useAuth();
  const [showSystemPanel, setShowSystemPanel] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getSystemStatus().then(setStatus).catch(() => {});
    const interval = setInterval(() => {
      getSystemStatus().then(setStatus).catch(() => {});
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  // Close user dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showUserMenu]);

  const isConnected = status?.ollama === true;

  return (
    <>
      <header
        style={{
          height: 54,
          background: 'var(--color-surface)',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          zIndex: 15,
          flexShrink: 0,
        }}
      >
        {/* Left */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <Logo size={24} />
          <span
            style={{
              fontSize: 14,
              fontWeight: 700,
              color: 'var(--color-text-primary)',
              letterSpacing: '-0.01em',
            }}
          >
            SOVA
          </span>
          <span className="badge badge-dark" style={{ marginLeft: 4 }}>
            <Shield size={10} />
            SECURE ENGINEERING WORKBENCH
          </span>
        </div>

        {/* Center-Right Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Real Ollama Status Badge */}
          <button
            onClick={() => setShowSystemPanel(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: 6,
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-secondary)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
            title={isConnected ? 'Ollama local engine connected' : 'Ollama local engine offline'}
          >
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                background: isConnected ? '#10B981' : '#EF4444',
                boxShadow: isConnected ? '0 0 6px rgba(16, 185, 129, 0.4)' : 'none',
              }}
            />
            <span
              style={{
                fontSize: 11.5,
                fontWeight: 650,
                color: isConnected ? '#059669' : '#DC2626',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              {isConnected ? 'Ollama Active' : 'Ollama Offline'}
            </span>
          </button>

          {/* Model tag */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              fontSize: 11.5,
              fontFamily: 'var(--font-mono)',
              color: 'var(--color-text-secondary)',
              background: 'var(--color-bg-secondary)',
              padding: '3px 8px',
              borderRadius: 6,
            }}
          >
            <Cpu size={12} color="var(--color-accent)" />
            <span>{status?.model || 'qwen2.5vl:3b'}</span>
          </div>

          {/* External calls */}
          <button
            onClick={() => setShowSystemPanel(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '4px 8px',
              borderRadius: 6,
              transition: 'background 0.15s',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-secondary)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'none')}
          >
            <ExternalLink size={12} color="var(--color-text-tertiary)" />
            <span
              style={{
                fontSize: 11.5,
                fontWeight: 600,
                color: 'var(--color-text-secondary)',
                letterSpacing: '0.03em',
              }}
            >
              0 EXTERNAL CALLS
            </span>
          </button>

          {/* Network Air-Gapped */}
          <div
            className="badge badge-success"
            style={{ cursor: 'pointer' }}
            onClick={() => setShowSystemPanel(true)}
          >
            <Radio size={10} />
            AIR-GAPPED
          </div>

          {/* Divider */}
          <div
            style={{
              width: 1,
              height: 24,
              background: 'var(--color-border)',
            }}
          />

          {/* Load Sample Inspection Button */}
          {onLoadSample && (
            <button
              onClick={onLoadSample}
              disabled={isProcessing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 7,
                padding: '7px 14px',
                borderRadius: 10,
                border: 'none',
                background: isProcessing
                  ? 'var(--color-bg-secondary)'
                  : 'linear-gradient(135deg, #2563EB, #1D4ED8)',
                color: isProcessing ? 'var(--color-text-tertiary)' : 'white',
                fontSize: 12,
                fontWeight: 600,
                cursor: isProcessing ? 'default' : 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isProcessing ? 'none' : '0 2px 8px rgba(37, 99, 235, 0.25)',
              }}
              title="Loads real inspection PDF into the actual processing pipeline"
            >
              <Play size={12} fill="currentColor" />
              <span>{isProcessing ? 'Processing...' : 'Load Sample PDF'}</span>
            </button>
          )}

          {/* Personalized User Badge & Dropdown */}
          <div style={{ position: 'relative' }} ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: showUserMenu ? 'var(--color-bg-secondary)' : 'none',
                border: '1px solid var(--color-border)',
                borderRadius: 10,
                padding: '4px 10px 4px 4px',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--color-border-hover)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--color-border)')}
              title={`Logged in as ${currentUser?.name || 'Engineer'}`}
            >
              {/* Avatar Initials */}
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 7,
                  background: currentUser?.badgeColor || 'linear-gradient(135deg, #2563EB, #0D9488)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 11.5,
                  fontWeight: 700,
                  color: 'white',
                  flexShrink: 0,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
                }}
              >
                {currentUser?.initials || 'EN'}
              </div>

              {/* Greeting Name */}
              <div style={{ textAlign: 'left', lineHeight: 1.15 }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--color-text-primary)' }}>
                  Hello, {currentUser?.name || 'Engineer'}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    fontFamily: 'var(--font-mono, monospace)',
                    color: currentUser?.clearanceCode === 'L3' ? '#D97706' : '#059669',
                    fontWeight: 600,
                  }}
                >
                  {currentUser?.clearanceCode || 'L3'} Clearance
                </div>
              </div>

              <ChevronDown
                size={14}
                color="var(--color-text-tertiary)"
                style={{
                  transform: showUserMenu ? 'rotate(180deg)' : 'none',
                  transition: 'transform 0.2s',
                  marginLeft: 2,
                }}
              />
            </button>

            {/* Profile Popover Menu */}
            {showUserMenu && (
              <div
                style={{
                  position: 'absolute',
                  top: 'calc(100% + 8px)',
                  right: 0,
                  width: 310,
                  background: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 14,
                  boxShadow: '0 16px 36px -8px rgba(0, 0, 0, 0.2), 0 0 1px rgba(0, 0, 0, 0.1)',
                  padding: 16,
                  zIndex: 100,
                  animation: 'fade-in 0.15s ease-out',
                }}
              >
                {/* User Summary Card */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    paddingBottom: 12,
                    borderBottom: '1px solid var(--color-border)',
                  }}
                >
                  <div
                    style={{
                      width: 42,
                      height: 42,
                      borderRadius: 10,
                      background: currentUser?.badgeColor || 'linear-gradient(135deg, #2563EB, #0D9488)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: 14,
                      fontWeight: 700,
                      color: 'white',
                      flexShrink: 0,
                    }}
                  >
                    {currentUser?.initials || 'EN'}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: 'var(--color-text-primary)',
                        }}
                      >
                        {currentUser?.fullName || currentUser?.name}
                      </span>
                      <span
                        style={{
                          fontSize: 10,
                          fontFamily: 'var(--font-mono, monospace)',
                          padding: '1px 5px',
                          borderRadius: 4,
                          background: 'var(--color-bg-secondary)',
                          color: 'var(--color-accent)',
                          fontWeight: 600,
                        }}
                      >
                        {currentUser?.employeeId}
                      </span>
                    </div>

                    <div
                      style={{
                        fontSize: 11.5,
                        color: 'var(--color-text-secondary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        marginTop: 2,
                      }}
                    >
                      {currentUser?.role}
                    </div>

                    <div
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        fontSize: 10.5,
                        fontWeight: 600,
                        color: currentUser?.clearanceCode === 'L3' ? '#D97706' : '#059669',
                        marginTop: 4,
                      }}
                    >
                      <BadgeCheck size={12} />
                      <span>{currentUser?.clearance}</span>
                    </div>
                  </div>
                </div>

                {/* Lock Terminal Action */}
                <div style={{ marginTop: 14, paddingTop: 10, borderTop: '1px solid var(--color-border)' }}>
                  <button
                    onClick={() => {
                      logout();
                      setShowUserMenu(false);
                    }}
                    style={{
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 8,
                      padding: '8px 12px',
                      borderRadius: 8,
                      border: '1px solid rgba(239, 68, 68, 0.25)',
                      background: 'rgba(239, 68, 68, 0.06)',
                      color: '#DC2626',
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: 'pointer',
                      transition: 'background 0.15s',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.12)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'rgba(239, 68, 68, 0.06)')}
                  >
                    <LogOut size={13} />
                    <span>Lock Workspace</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Quick Lock Button directly beside profile */}
          <button
            onClick={() => logout()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '6px 10px',
              borderRadius: 8,
              border: '1px solid var(--color-border)',
              background: 'transparent',
              color: 'var(--color-text-secondary)',
              fontSize: 11.5,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
              e.currentTarget.style.color = '#EF4444';
              e.currentTarget.style.background = 'rgba(239, 68, 68, 0.06)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border)';
              e.currentTarget.style.color = 'var(--color-text-secondary)';
              e.currentTarget.style.background = 'transparent';
            }}
            title="Lock workspace immediately"
          >
            <LogOut size={12} />
            <span>Lock</span>
          </button>
        </div>
      </header>

      {/* System Panel Overlay */}
      {showSystemPanel && <SystemPanel onClose={() => setShowSystemPanel(false)} />}
    </>
  );
};

export default TopBar;
