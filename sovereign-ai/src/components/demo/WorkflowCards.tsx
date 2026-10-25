import React from 'react';
import { ClipboardCheck, PenTool, FileText, ScanSearch } from 'lucide-react';

interface WorkflowCardsProps {
  onSelect: (workflow: string) => void;
}

const workflows = [
  {
    id: 'inspection',
    title: 'Analyze Inspection Report',
    description: 'Extract findings, identify anomalies and generate an engineering summary.',
    icon: ClipboardCheck,
    color: '#2563EB',
    bgColor: 'rgba(37, 99, 235, 0.06)',
  },
  {
    id: 'pid',
    title: 'P&ID Intelligence',
    description: 'Detect equipment, valves, pumps and instrument tags from P&ID drawings.',
    icon: PenTool,
    color: '#8B5CF6',
    bgColor: 'rgba(139, 92, 246, 0.06)',
  },
  {
    id: 'engineering-note',
    title: 'Engineering Note',
    description: 'Generate an approval-ready engineering note with calculation evidence.',
    icon: FileText,
    color: '#0D9488',
    bgColor: 'rgba(13, 148, 136, 0.06)',
  },
  {
    id: 'document',
    title: 'Document Intelligence',
    description: 'Read scanned documents, handwritten notes and technical photographs.',
    icon: ScanSearch,
    color: '#F59E0B',
    bgColor: 'rgba(245, 158, 11, 0.06)',
  },
];

const WorkflowCards: React.FC<WorkflowCardsProps> = ({ onSelect }) => {
  return (
    <div style={{ maxWidth: 720, width: '100%', margin: '0 auto' }}>
      <div
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--color-text-tertiary)',
          letterSpacing: '0.04em',
          marginBottom: 12,
          textTransform: 'uppercase',
        }}
      >
        Suggested Workflows
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 10,
        }}
      >
        {workflows.map((wf) => {
          const Icon = wf.icon;
          return (
            <button
              key={wf.id}
              onClick={() => onSelect(wf.id)}
              className="card card-interactive"
              style={{
                padding: '16px 18px',
                textAlign: 'left',
                cursor: 'pointer',
                border: '1px solid var(--color-border)',
                background: 'var(--color-surface)',
                display: 'flex',
                gap: 14,
                alignItems: 'flex-start',
              }}
            >
              <div
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  background: wf.bgColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
              >
                <Icon size={17} color={wf.color} />
              </div>
              <div>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 650,
                    color: 'var(--color-text-primary)',
                    marginBottom: 4,
                    lineHeight: 1.3,
                  }}
                >
                  {wf.title}
                </div>
                <div
                  style={{
                    fontSize: 12,
                    color: 'var(--color-text-tertiary)',
                    lineHeight: 1.5,
                  }}
                >
                  {wf.description}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default WorkflowCards;
