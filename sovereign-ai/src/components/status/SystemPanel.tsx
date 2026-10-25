import React, { useState, useEffect } from 'react';
import { X, Shield, Server, HardDrive, Cpu, Activity, CheckCircle2, XCircle, Terminal } from 'lucide-react';
import { getSystemStatus, type SystemStatusResponse } from '../../services/api';

interface SystemPanelProps {
  onClose: () => void;
}

const SystemPanel: React.FC<SystemPanelProps> = ({ onClose }) => {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);

  useEffect(() => {
    getSystemStatus().then(setStatus).catch(() => {});
  }, []);

  const isConnected = status?.ollama === true;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: 'absolute',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.4)',
          backdropFilter: 'blur(4px)',
        }}
      />

      {/* Panel */}
      <div
        className="card"
        style={{
          position: 'relative',
          width: '100%',
          maxWidth: 520,
          maxHeight: '85vh',
          overflowY: 'auto',
          padding: 0,
          animation: 'scale-in 0.2s ease-out',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '18px 24px',
            borderBottom: '1px solid var(--color-border)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Shield size={18} color="var(--color-accent)" />
            <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text-primary)' }}>
              SOVA Architecture & Health
            </span>
          </div>
          <button
            onClick={onClose}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 28,
              height: 28,
              borderRadius: 7,
              border: 'none',
              background: 'var(--color-bg-secondary)',
              cursor: 'pointer',
              color: 'var(--color-text-secondary)',
            }}
          >
            <X size={14} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Status Box */}
          <div
            style={{
              padding: '14px 18px',
              borderRadius: 10,
              background: isConnected ? 'rgba(16, 185, 129, 0.08)' : 'rgba(239, 68, 68, 0.08)',
              border: `1px solid ${isConnected ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            {isConnected ? (
              <CheckCircle2 size={20} color="#059669" />
            ) : (
              <XCircle size={20} color="#DC2626" />
            )}
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: isConnected ? '#059669' : '#DC2626' }}>
                {isConnected ? 'LOCAL AI ENGINE CONNECTED' : 'LOCAL AI ENGINE OFFLINE'}
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-secondary)', marginTop: 2 }}>
                {status?.message || 'Checking local Ollama daemon...'}
              </div>
            </div>
          </div>

          {/* Metrics List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 8,
                background: 'var(--color-bg-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Server size={14} color="var(--color-accent)" />
                <span style={{ fontSize: 12.5, color: 'var(--color-text-secondary)' }}>Inference Server</span>
              </div>
              <span style={{ fontSize: 12, fontWeight: 650, color: 'var(--color-text-primary)' }}>
                Ollama Local (:11434)
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 8,
                background: 'var(--color-bg-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Cpu size={14} color="#8B5CF6" />
                <span style={{ fontSize: 12.5, color: 'var(--color-text-secondary)' }}>Multimodal Model</span>
              </div>
              <span style={{ fontSize: 12, fontWeight: 650, fontFamily: 'var(--font-mono)', color: 'var(--color-text-primary)' }}>
                {status?.model || 'qwen2.5vl:3b'}
              </span>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 8,
                background: 'var(--color-bg-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <HardDrive size={14} color="#2563EB" />
                <span style={{ fontSize: 12.5, color: 'var(--color-text-secondary)' }}>Hardware Target</span>
              </div>
              <span style={{ fontSize: 12, fontWeight: 650, color: 'var(--color-text-primary)' }}>
                {status?.gpu?.name || 'NVIDIA RTX 4050'} ({status?.gpu?.vram || '6.0 GB'})
              </span>
            </div>

            {/* Routed Models Section */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Model Routing Architecture
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 6, background: 'var(--color-bg-secondary)', fontSize: 11.5 }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>👁️ Vision / P&ID:</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-accent)' }}>{status?.vision_model || 'qwen2.5vl:3b'}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 6, background: 'var(--color-bg-secondary)', fontSize: 11.5 }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>🧠 Deep Reasoning:</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#8B5CF6' }}>{status?.reasoning_model || 'deepseek-r1:7b'}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 6, background: 'var(--color-bg-secondary)', fontSize: 11.5 }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>⚡ Coder / Sandbox:</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#059669' }}>{status?.coder_model || 'qwen2.5-coder:7b'}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 12px', borderRadius: 6, background: 'var(--color-bg-secondary)', fontSize: 11.5 }}>
                <span style={{ color: 'var(--color-text-secondary)' }}>📄 Document / SOP:</span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-text-primary)' }}>{status?.document_model || 'llama3.2:3b'}</span>
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 8,
                background: 'var(--color-bg-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Activity size={14} color="#10B981" />
                <span style={{ fontSize: 12.5, color: 'var(--color-text-secondary)' }}>External Network Egress</span>
              </div>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#059669' }}>
                0 External Calls (Air-Gapped)
              </span>
            </div>
          </div>

          {/* Quick Terminal Guide */}
          <div
            style={{
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              fontSize: 11.5,
              fontFamily: 'var(--font-mono)',
              lineHeight: 1.6,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 5, color: 'var(--color-accent)', fontWeight: 600, marginBottom: 4 }}>
              <Terminal size={12} /> Ollama Quickstart
            </div>
            ollama serve<br />
            ollama pull qwen2.5vl:3b
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemPanel;
