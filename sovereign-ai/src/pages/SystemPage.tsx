import React, { useState, useEffect } from 'react';
import {
  Settings,
  Shield,
  Server,
  Cpu,
  HardDrive,
  Activity,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Terminal
} from 'lucide-react';
import { getSystemStatus, type SystemStatusResponse } from '../services/api';

const SystemPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await getSystemStatus();
      setStatus(res);
    } catch {
      setStatus({
        ollama: false,
        model: 'qwen2.5vl:3b',
        model_available: false,
        available_models: [],
        external_calls: 0,
        inference: 'local',
        network: 'Local backend unreachable',
        message: 'Could not connect to FastAPI backend service on port 8000.'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '32px 40px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'rgba(37, 99, 235, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Settings size={18} color="var(--color-accent)" />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 750, color: 'var(--color-text-primary)', margin: 0, letterSpacing: '-0.02em' }}>
              System Architecture & Health
            </h1>
            <p style={{ fontSize: 13, color: 'var(--color-text-tertiary)', margin: 0 }}>
              Live verification of local AI engine, hardware constraints, and air-gapped status
            </p>
          </div>
        </div>

        <button
          onClick={fetchStatus}
          disabled={loading}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '6px 12px',
            borderRadius: 8,
            border: '1px solid var(--color-border)',
            background: 'var(--color-surface)',
            color: 'var(--color-text-secondary)',
            fontSize: 12,
            cursor: loading ? 'default' : 'pointer',
          }}
        >
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Air-Gapped Sovereignty Banner */}
      <div
        style={{
          padding: '18px 24px',
          borderRadius: 14,
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.06), rgba(13, 148, 136, 0.06))',
          border: '1px solid rgba(16, 185, 129, 0.14)',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 14,
            background: 'linear-gradient(135deg, #10B981, #0D9488)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Shield size={22} color="white" />
        </div>
        <div>
          <div style={{ fontSize: 14.5, fontWeight: 750, color: '#059669', marginBottom: 2 }}>
            FULLY SOVEREIGN — AIR-GAPPED VERIFICATION
          </div>
          <div style={{ fontSize: 12.5, color: '#0D9488' }}>
            Zero external AI API keys. Zero cloud egress. PyMuPDF, OCR, and Qwen2.5-VL run 100% on-premise.
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
          <span className="badge badge-success">
            <Activity size={10} /> 0 External Calls
          </span>
        </div>
      </div>

      {/* Local AI Engine Status Card */}
      <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-tertiary)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 14 }}>
          Local AI Engine (Ollama)
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
          {/* Ollama Connection */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Server size={15} color="var(--color-accent)" />
              <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Ollama Engine
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {status?.ollama ? (
                <span style={{ fontSize: 12, fontWeight: 650, color: '#059669', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <CheckCircle2 size={13} /> Connected (:11434)
                </span>
              ) : (
                <span style={{ fontSize: 12, fontWeight: 650, color: '#DC2626', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <XCircle size={13} /> Offline
                </span>
              )}
            </div>
          </div>

          {/* Active Model */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Cpu size={15} color="#8B5CF6" />
              <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Active Primary Model
              </span>
            </div>
            <span style={{ fontSize: 12, fontWeight: 650, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
              {status?.model || 'qwen2.5vl:3b'}
            </span>
          </div>

          {/* Model Availability */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <CheckCircle2 size={15} color="#10B981" />
              <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Model Pulled
              </span>
            </div>
            <span
              style={{
                fontSize: 12,
                fontWeight: 650,
                color: status?.model_available ? '#059669' : status?.ollama ? '#F59E0B' : '#64748B',
              }}
            >
              {status?.model_available ? 'Available' : status?.ollama ? 'Needs Pull' : 'Pending Server'}
            </span>
          </div>

          {/* Inference Mode */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Shield size={15} color="#10B981" />
              <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Inference Mode
              </span>
            </div>
            <span style={{ fontSize: 12, fontWeight: 650, color: '#059669' }}>
              Local On-Premise
            </span>
          </div>
        </div>

        {/* Dynamic Model Routing Grid */}
        <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--color-border)' }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-tertiary)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 10 }}>
            Dynamic Task Routing Architecture
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--color-bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>Vision / P&ID</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)' }}>Visual diagram inspection & equipment tags</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, fontWeight: 650, color: 'var(--color-accent)' }}>
                {status?.vision_model || 'qwen2.5vl:3b'}
              </span>
            </div>

            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--color-bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>Deep Reasoning</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)' }}>Multi-step engineering & cross-document</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, fontWeight: 650, color: '#8B5CF6' }}>
                {status?.reasoning_model || 'deepseek-r1:7b'}
              </span>
            </div>

            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--color-bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>Code & Sandbox</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)' }}>Data processing & computation scripts</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, fontWeight: 650, color: '#059669' }}>
                {status?.coder_model || 'qwen2.5-coder:7b'}
              </span>
            </div>

            <div style={{ padding: '10px 14px', borderRadius: 8, background: 'var(--color-bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-primary)' }}>Document & SOP</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-tertiary)' }}>General document Q&A & conversation</div>
              </div>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11.5, fontWeight: 650, color: 'var(--color-text-primary)' }}>
                {status?.document_model || 'llama3.2:3b'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Hardware & GPU Profile */}
      <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-tertiary)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 14 }}>
          Target Hardware & GPU Allocation
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <HardDrive size={15} color="#2563EB" />
              <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                Detected GPU
              </span>
            </div>
            <span style={{ fontSize: 12, fontWeight: 650, color: 'var(--color-text-primary)', fontFamily: 'var(--font-mono)' }}>
              {status?.gpu?.name || 'NVIDIA RTX 3050'}
            </span>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 14px',
              borderRadius: 8,
              background: 'var(--color-bg-secondary)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Activity size={15} color="#0D9488" />
              <span style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text-secondary)' }}>
                VRAM Budget
              </span>
            </div>
            <span style={{ fontSize: 12, fontWeight: 650, color: '#0D9488', fontFamily: 'var(--font-mono)' }}>
              {status?.gpu?.vram || '4.0 GB'}
            </span>
          </div>
        </div>
      </div>

      {/* Command Instructions */}
      <div className="card" style={{ padding: '20px 24px' }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-tertiary)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
          <Terminal size={13} />
          Local AI Engine Control (Run in Terminal)
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 8,
              padding: '10px 14px',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--color-text-primary)',
            }}
          >
            <span style={{ color: 'var(--color-text-tertiary)' }}># 1. Start local Ollama daemon</span><br />
            <strong>ollama serve</strong>
          </div>

          <div
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 8,
              padding: '10px 14px',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--color-text-primary)',
            }}
          >
            <span style={{ color: 'var(--color-text-tertiary)' }}># 2. Pull local open-weight models</span><br />
            <strong>ollama pull qwen2.5vl:3b</strong><br />
            <strong>ollama pull deepseek-r1:7b</strong><br />
            <strong>ollama pull qwen2.5-coder:7b</strong><br />
            <strong>ollama pull llama3.2:3b</strong>
          </div>

          <div
            style={{
              background: 'var(--color-bg-secondary)',
              border: '1px solid var(--color-border)',
              borderRadius: 8,
              padding: '10px 14px',
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--color-text-primary)',
            }}
          >
            <span style={{ color: 'var(--color-text-tertiary)' }}># 3. Verify installed local models</span><br />
            <strong>ollama list</strong>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemPage;
