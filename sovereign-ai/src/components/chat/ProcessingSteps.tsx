import React from 'react';
import { Check, Loader2 } from 'lucide-react';
import type { ProcessingStep } from '../../data/demoConversation';

interface ProcessingStepsProps {
  steps: ProcessingStep[];
}

const ProcessingSteps: React.FC<ProcessingStepsProps> = ({ steps }) => {
  const hasAnyProcessing = steps.some((s) => s.status !== 'pending');
  if (!hasAnyProcessing) return null;

  return (
    <div
      style={{
        marginTop: 14,
        padding: '14px 16px',
        borderRadius: 12,
        background: 'var(--color-bg-secondary)',
        border: '1px solid var(--color-border-light)',
      }}
    >
      <div
        style={{
          fontSize: 11,
          fontWeight: 600,
          color: 'var(--color-text-tertiary)',
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
          marginBottom: 10,
        }}
      >
        Processing Pipeline
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {steps.map((step) => {
          if (step.status === 'pending') return null;
          return (
            <div
              key={step.id}
              className="step-appear"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '6px 8px',
                borderRadius: 8,
              }}
            >
              {step.status === 'complete' ? (
                <div
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: 6,
                    background: 'rgba(16, 185, 129, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Check size={12} color="#10B981" strokeWidth={3} />
                </div>
              ) : (
                <div
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: 6,
                    background: 'rgba(37, 99, 235, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Loader2
                    size={12}
                    color="#2563EB"
                    style={{ animation: 'spin 1s linear infinite' }}
                  />
                </div>
              )}
              <span
                style={{
                  fontSize: 12.5,
                  fontWeight: step.status === 'complete' ? 500 : 600,
                  color:
                    step.status === 'complete'
                      ? 'var(--color-text-secondary)'
                      : 'var(--color-text-primary)',
                }}
              >
                {step.label}
              </span>
              {step.detail && (
                <span
                  style={{
                    fontSize: 11,
                    color: 'var(--color-text-tertiary)',
                    fontFamily: 'var(--font-mono)',
                    marginLeft: 'auto',
                  }}
                >
                  {step.detail}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ProcessingSteps;
