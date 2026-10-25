import React from 'react';
import {
  User, FileText, Eye, GitBranch, Brain, Database, Code2, FileOutput,
  ShieldOff, CloudOff, ArrowDownUp, Cpu, ChevronDown,
} from 'lucide-react';
import Logo from '../components/common/Logo';

interface ArchNode {
  icon: React.ReactNode;
  label: string;
  sublabel?: string;
  accent?: boolean;
  teal?: boolean;
}

const pipelineNodes: ArchNode[] = [
  { icon: <User size={16} />, label: 'User / Engineer', sublabel: 'Upload documents, ask questions' },
  { icon: <Logo size={18} />, label: 'SOVA Workbench', sublabel: 'Central orchestration layer', accent: true },
  { icon: <FileText size={16} />, label: 'Document / Image / Query', sublabel: 'PDF, P&ID, photograph, spreadsheet, text' },
  { icon: <Eye size={16} />, label: 'Local OCR + Vision', sublabel: 'Tesseract + Qwen2.5-VL 3B' },
  { icon: <GitBranch size={16} />, label: 'Model Router', sublabel: 'Task classification & routing', accent: true },
  { icon: <Brain size={16} />, label: 'Local Open-Weight Models', sublabel: 'Qwen-VL / DeepSeek-R1 / LLaMA / Coder' },
  { icon: <Database size={16} />, label: 'Local Knowledge Base / RAG', sublabel: 'In-memory chunk retriever', teal: true },
  { icon: <Code2 size={16} />, label: 'Deterministic Telemetry Engine', sublabel: 'Pandas data extraction & verification' },
  { icon: <FileOutput size={16} />, label: 'Generated Deliverable', sublabel: 'PDF, Word, Excel, engineering note', teal: true },
];

const guarantees = [
  { icon: <ShieldOff size={18} />, label: 'NO EXTERNAL API', detail: 'Zero third-party API calls. All inference runs locally.' },
  { icon: <CloudOff size={18} />, label: 'NO CLOUD', detail: 'Fully air-gapped. No internet connection required.' },
  { icon: <ArrowDownUp size={18} />, label: 'NO DATA EGRESS', detail: 'Zero bytes leave the on-premise network.' },
];

const Architecture: React.FC = () => {
  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '32px 40px' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
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
            <Cpu size={18} color="var(--color-accent)" />
          </div>
          <div>
            <h1
              style={{
                fontSize: 20,
                fontWeight: 750,
                color: 'var(--color-text-primary)',
                margin: 0,
                letterSpacing: '-0.02em',
              }}
            >
              System Architecture
            </h1>
            <p style={{ fontSize: 13, color: 'var(--color-text-tertiary)', margin: 0 }}>
              End-to-end sovereign processing pipeline
            </p>
          </div>
        </div>
      </div>

      {/* Pipeline Diagram */}
      <div
        className="card"
        style={{
          padding: '32px 40px',
          marginBottom: 24,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <div
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--color-text-tertiary)',
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            marginBottom: 24,
          }}
        >
          Processing Pipeline
        </div>

        {pipelineNodes.map((node, i) => (
          <React.Fragment key={i}>
            <div
              className={`arch-node ${node.accent ? 'arch-node-accent' : ''} ${node.teal ? 'arch-node-teal' : ''}`}
              style={{
                width: '100%',
                maxWidth: 420,
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                textAlign: 'left',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  opacity: node.accent || node.teal ? 1 : 0.7,
                }}
              >
                {node.icon}
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{node.label}</div>
                {node.sublabel && (
                  <div
                    style={{
                      fontSize: 11,
                      fontWeight: 400,
                      opacity: 0.7,
                      marginTop: 2,
                    }}
                  >
                    {node.sublabel}
                  </div>
                )}
              </div>
            </div>
            {i < pipelineNodes.length - 1 && (
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  margin: '0',
                }}
              >
                <div className="arch-connector" />
                <ChevronDown size={14} color="var(--color-text-tertiary)" style={{ marginTop: -4 }} />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Sovereignty Guarantees */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
        }}
      >
        {guarantees.map((g) => (
          <div
            key={g.label}
            className="card"
            style={{
              padding: '20px',
              textAlign: 'center',
              borderTop: '3px solid #10B981',
            }}
          >
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: 'rgba(16, 185, 129, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                margin: '0 auto 12px',
                color: '#10B981',
              }}
            >
              {g.icon}
            </div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 750,
                color: '#059669',
                letterSpacing: '0.02em',
                marginBottom: 6,
              }}
            >
              {g.label}
            </div>
            <div
              style={{
                fontSize: 12,
                color: 'var(--color-text-tertiary)',
                lineHeight: 1.5,
              }}
            >
              {g.detail}
            </div>
          </div>
        ))}
      </div>

      {/* Tech Stack */}
      <div className="card" style={{ padding: '20px 24px', marginTop: 16 }}>
        <div
          style={{
            fontSize: 11,
            fontWeight: 600,
            color: 'var(--color-text-tertiary)',
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            marginBottom: 14,
          }}
        >
          Technology Stack
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
            gap: 8,
          }}
        >
          {[
            { label: 'Vision Model', value: 'qwen2.5vl:3b' },
            { label: 'Reasoning Model', value: 'deepseek-r1:7b' },
            { label: 'General / SOP Model', value: 'llama3.2:3b' },
            { label: 'Coding / Analytics', value: 'qwen2.5-coder:7b' },
            { label: 'Local Inference', value: 'Ollama (127.0.0.1:11434)' },
            { label: 'Telemetry Engine', value: 'Deterministic Pandas' },
            { label: 'Verification', value: '7-Point Grounding Gate' },
            { label: 'Hardware', value: 'NVIDIA RTX 4050 (6GB VRAM)' },
          ].map((item) => (
            <div
              key={item.label}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '8px 12px',
                borderRadius: 8,
                background: 'var(--color-bg-secondary)',
                fontSize: 12,
              }}
            >
              <span style={{ color: 'var(--color-text-tertiary)', fontWeight: 500 }}>{item.label}</span>
              <span
                style={{
                  fontWeight: 600,
                  color: 'var(--color-text-primary)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: 11,
                }}
              >
                {item.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Architecture;
