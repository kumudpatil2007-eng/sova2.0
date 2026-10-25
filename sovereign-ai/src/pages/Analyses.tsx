import React from 'react';
import { BarChart3, CheckCircle2, Clock, FileText, ArrowRight } from 'lucide-react';
import { analysisHistory } from '../data/analysisHistory';

const statusColors = {
  Completed: '#10B981',
  'In Progress': '#2563EB',
  'Pending Review': '#F59E0B',
};

const Analyses: React.FC = () => {
  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '32px 40px' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
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
            <BarChart3 size={18} color="var(--color-accent)" />
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
              Analysis History
            </h1>
            <p style={{ fontSize: 13, color: 'var(--color-text-tertiary)', margin: 0 }}>
              Previous AI-powered engineering analyses
            </p>
          </div>
        </div>
      </div>

      {/* Analysis List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {analysisHistory.map((analysis) => (
          <div
            key={analysis.id}
            className="card card-interactive"
            style={{
              padding: '18px 22px',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 14.5, fontWeight: 650, color: 'var(--color-text-primary)' }}>
                    {analysis.title}
                  </span>
                  <span
                    className="badge"
                    style={{
                      background: `${statusColors[analysis.status]}15`,
                      color: statusColors[analysis.status],
                      fontSize: 9.5,
                      padding: '2px 8px',
                    }}
                  >
                    <CheckCircle2 size={9} />
                    {analysis.status}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: 12.5,
                    color: 'var(--color-text-secondary)',
                    lineHeight: 1.5,
                    marginBottom: 10,
                  }}
                >
                  {analysis.description}
                </div>
              </div>
              <ArrowRight size={16} color="var(--color-text-tertiary)" style={{ flexShrink: 0, marginTop: 4 }} />
            </div>

            {/* Bottom meta */}
            <div
              style={{
                display: 'flex',
                gap: 20,
                paddingTop: 10,
                borderTop: '1px solid var(--color-border-light)',
                fontSize: 11.5,
                color: 'var(--color-text-tertiary)',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <Clock size={12} />
                {analysis.date} • {analysis.time}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <FileText size={12} />
                {analysis.documentsUsed} documents
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                  {analysis.deliverable}
                </span>
              </div>
              <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ fontWeight: 600, color: 'var(--color-accent)' }}>
                  {analysis.confidence}%
                </span>
                <span>confidence</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Analyses;
