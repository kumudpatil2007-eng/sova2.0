import React from 'react';

interface LogoProps {
  size?: number;
  showText?: boolean;
  variant?: 'light' | 'dark';
}

const Logo: React.FC<LogoProps> = ({ size = 32, showText = false, variant = 'dark' }) => {
  const textColor = variant === 'dark' ? '#1E293B' : '#F1F5F9';
  const subtitleColor = variant === 'dark' ? '#64748B' : '#94A3B8';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: showText ? 12 : 0 }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Shield / hexagonal shape */}
        <rect x="2" y="2" width="36" height="36" rx="10" fill="url(#logo-grad)" />
        {/* Inner circuit pattern */}
        <path
          d="M12 14h4v2h-4zM24 14h4v2h-4zM12 24h4v2h-4zM24 24h4v2h-4z"
          fill="rgba(255,255,255,0.3)"
        />
        {/* Central AI node */}
        <circle cx="20" cy="20" r="5" fill="rgba(255,255,255,0.9)" />
        <circle cx="20" cy="20" r="2.5" fill="url(#logo-grad)" />
        {/* Connection lines */}
        <line x1="15" y1="20" x2="10" y2="20" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
        <line x1="25" y1="20" x2="30" y2="20" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
        <line x1="20" y1="15" x2="20" y2="10" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
        <line x1="20" y1="25" x2="20" y2="30" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
        {/* Corner nodes */}
        <circle cx="10" cy="20" r="1.5" fill="rgba(255,255,255,0.6)" />
        <circle cx="30" cy="20" r="1.5" fill="rgba(255,255,255,0.6)" />
        <circle cx="20" cy="10" r="1.5" fill="rgba(255,255,255,0.6)" />
        <circle cx="20" cy="30" r="1.5" fill="rgba(255,255,255,0.6)" />
        <defs>
          <linearGradient id="logo-grad" x1="0" y1="0" x2="40" y2="40">
            <stop offset="0%" stopColor="#2563EB" />
            <stop offset="100%" stopColor="#0D9488" />
          </linearGradient>
        </defs>
      </svg>
      {showText && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span
            style={{
              fontSize: 16,
              fontWeight: 700,
              color: textColor,
              letterSpacing: '-0.02em',
              lineHeight: 1.2,
            }}
          >
            SOVA
          </span>
          <span
            style={{
              fontSize: 10.5,
              fontWeight: 500,
              color: subtitleColor,
              letterSpacing: '0.02em',
            }}
          >
            Industrial AI Workbench
          </span>
        </div>
      )}
    </div>
  );
};

export default Logo;
