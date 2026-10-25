import React from 'react';
import Logo from '../common/Logo';

const TypingIndicator: React.FC = () => {
  return (
    <div
      style={{
        display: 'flex',
        gap: 14,
        maxWidth: 780,
        width: '100%',
        margin: '0 auto',
        padding: '16px 0',
        animation: 'fade-in 0.3s ease-out',
      }}
    >
      {/* Avatar */}
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 9,
          background: 'linear-gradient(135deg, #2563EB, #0D9488)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        <Logo size={20} />
      </div>

      {/* Typing */}
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: 'var(--color-text-secondary)',
            marginBottom: 8,
          }}
        >
          SOVA
        </div>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 10,
            padding: '12px 18px',
            borderRadius: 12,
            background: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border-light)',
          }}
        >
          <div style={{ display: 'flex', gap: 4 }}>
            <div className="typing-dot" />
            <div className="typing-dot" />
            <div className="typing-dot" />
          </div>
          <span
            style={{
              fontSize: 12,
              color: 'var(--color-text-tertiary)',
              fontWeight: 500,
            }}
          >
            Analyzing inspection report...
          </span>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
