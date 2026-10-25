import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import Logo from '../common/Logo';
import { Lock, User, KeyRound, AlertCircle, CheckCircle2 } from 'lucide-react';

const LoginPage: React.FC = () => {
  const { login, register, checkAuthStatus } = useAuth();

  const [isSetupMode, setIsSetupMode] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Check if system has local users on first load
  useEffect(() => {
    checkAuthStatus()
      .then((res) => {
        if (!res.has_users) {
          setIsSetupMode(true);
        }
      })
      .catch(() => {
        // Fallback default
      });
  }, [checkAuthStatus]);

  const handleUnlock = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!username.trim() || !password) {
      setErrorMessage('Incorrect username or password.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await login(username, password);
      if (!res.success) {
        setErrorMessage(res.error || 'Incorrect username or password.');
      }
    } catch {
      setErrorMessage('Incorrect username or password.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanUser = username.trim();
    if (!cleanUser) {
      setErrorMessage('Please enter a username.');
      return;
    }
    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await register(cleanUser, password);
      if (!res.success) {
        setErrorMessage(res.error || 'Failed to create workspace account.');
        setIsSubmitting(false);
      } else {
        // Clear fields and return to normal lock screen
        setPassword('');
        setConfirmPassword('');
        setSuccessMessage('Local account created. Please enter your password to unlock.');
        setIsSetupMode(false);
        setIsSubmitting(false);
      }
    } catch {
      setErrorMessage('Failed to create account.');
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        width: '100vw',
        background: '#0B0D13',
        backgroundImage: 'radial-gradient(ellipse at 50% 15%, #151923 0%, #0B0D13 65%)',
        color: '#E2E8F0',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px 16px',
        position: 'relative',
        overflow: 'hidden',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif',
      }}
    >
      {/* Barely visible technical grid */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage:
            'linear-gradient(rgba(255, 255, 255, 0.015) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.015) 1px, transparent 1px)',
          backgroundSize: '48px 48px',
          maskImage: 'radial-gradient(circle at center, black 40%, transparent 80%)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Authentication Card */}
      <div
        style={{
          width: '100%',
          maxWidth: 390,
          background: '#11141D',
          border: '1px solid rgba(255, 255, 255, 0.07)',
          borderRadius: 14,
          boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.7), 0 1px 3px rgba(0, 0, 0, 0.4)',
          padding: '36px 32px 32px 32px',
          position: 'relative',
          zIndex: 5,
        }}
      >
        {/* Subtle Brand & Logo */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 26 }}>
          <div style={{ marginBottom: 14, opacity: 0.95 }}>
            <Logo size={32} />
          </div>

          <h1
            style={{
              fontSize: 19,
              fontWeight: 700,
              letterSpacing: '-0.02em',
              margin: '0 0 4px 0',
              color: '#F8FAFC',
              textAlign: 'center',
            }}
          >
            SOVA
          </h1>
          <p
            style={{
              margin: 0,
              fontSize: 12.5,
              color: '#717D96',
              letterSpacing: '-0.01em',
              textAlign: 'center',
            }}
          >
            {isSetupMode ? 'Create your local workspace' : 'Private Engineering Workspace'}
          </p>
        </div>

        {/* Quiet Error Message */}
        {errorMessage && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              borderRadius: 8,
              padding: '9px 12px',
              marginBottom: 18,
              fontSize: 12,
              color: '#F87171',
              lineHeight: 1.35,
            }}
          >
            <AlertCircle size={14} style={{ flexShrink: 0, color: '#EF4444' }} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Quiet Success Message */}
        {successMessage && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              background: 'rgba(16, 185, 129, 0.08)',
              border: '1px solid rgba(16, 185, 129, 0.25)',
              borderRadius: 8,
              padding: '9px 12px',
              marginBottom: 18,
              fontSize: 12,
              color: '#34D399',
              lineHeight: 1.35,
            }}
          >
            <CheckCircle2 size={14} style={{ flexShrink: 0, color: '#10B981' }} />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Form: Normal Lock Screen or First-Time Local Account Creation */}
        {!isSetupMode ? (
          <form onSubmit={handleUnlock} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Username Input */}
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginBottom: 6,
                  letterSpacing: '0.02em',
                }}
              >
                Username
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <User
                  size={14}
                  color="#4A5568"
                  style={{ position: 'absolute', left: 12, pointerEvents: 'none' }}
                />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Deepak"
                  autoComplete="username"
                  autoFocus
                  style={{
                    width: '100%',
                    height: 38,
                    padding: '0 12px 0 36px',
                    background: '#0D0F16',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 8,
                    color: '#F8FAFC',
                    fontSize: 13,
                    fontFamily: 'inherit',
                    outline: 'none',
                    transition: 'border-color 0.15s, box-shadow 0.15s',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'rgba(56, 189, 248, 0.8)';
                    e.target.style.boxShadow = '0 0 0 2px rgba(56, 189, 248, 0.15)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginBottom: 6,
                  letterSpacing: '0.02em',
                }}
              >
                Password
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Lock
                  size={14}
                  color="#4A5568"
                  style={{ position: 'absolute', left: 12, pointerEvents: 'none' }}
                />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  autoComplete="current-password"
                  style={{
                    width: '100%',
                    height: 38,
                    padding: '0 12px 0 36px',
                    background: '#0D0F16',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 8,
                    color: '#F8FAFC',
                    fontSize: 13,
                    fontFamily: 'inherit',
                    outline: 'none',
                    transition: 'border-color 0.15s, box-shadow 0.15s',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'rgba(56, 189, 248, 0.8)';
                    e.target.style.boxShadow = '0 0 0 2px rgba(56, 189, 248, 0.15)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>

            {/* Unlock Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                marginTop: 6,
                height: 38,
                borderRadius: 8,
                border: 'none',
                background: '#2563EB',
                color: 'white',
                fontSize: 13,
                fontWeight: 600,
                letterSpacing: '-0.01em',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 6,
                cursor: isSubmitting ? 'wait' : 'pointer',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!isSubmitting) e.currentTarget.style.background = '#1D4ED8';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#2563EB';
              }}
            >
              {isSubmitting ? 'Verifying...' : 'Unlock Workspace'}
            </button>

            {/* Toggle to Create Local Account */}
            <div style={{ textAlign: 'center', marginTop: 8 }}>
              <button
                type="button"
                onClick={() => {
                  setIsSetupMode(true);
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#64748B',
                  fontSize: 11.5,
                  cursor: 'pointer',
                  padding: 4,
                  transition: 'color 0.15s',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.color = '#94A3B8')}
                onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
              >
                Create local account
              </button>
            </div>
          </form>
        ) : (
          /* First Run / Account Setup Screen */
          <form onSubmit={handleCreateAccount} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Username */}
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginBottom: 6,
                }}
              >
                Username
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <User
                  size={14}
                  color="#4A5568"
                  style={{ position: 'absolute', left: 12, pointerEvents: 'none' }}
                />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter local username"
                  autoFocus
                  style={{
                    width: '100%',
                    height: 38,
                    padding: '0 12px 0 36px',
                    background: '#0D0F16',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 8,
                    color: '#F8FAFC',
                    fontSize: 13,
                    fontFamily: 'inherit',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginBottom: 6,
                }}
              >
                Password
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Lock
                  size={14}
                  color="#4A5568"
                  style={{ position: 'absolute', left: 12, pointerEvents: 'none' }}
                />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  style={{
                    width: '100%',
                    height: 38,
                    padding: '0 12px 0 36px',
                    background: '#0D0F16',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 8,
                    color: '#F8FAFC',
                    fontSize: 13,
                    fontFamily: 'inherit',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: 11,
                  fontWeight: 600,
                  color: '#94A3B8',
                  marginBottom: 6,
                }}
              >
                Confirm password
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <KeyRound
                  size={14}
                  color="#4A5568"
                  style={{ position: 'absolute', left: 12, pointerEvents: 'none' }}
                />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  style={{
                    width: '100%',
                    height: 38,
                    padding: '0 12px 0 36px',
                    background: '#0D0F16',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: 8,
                    color: '#F8FAFC',
                    fontSize: 13,
                    fontFamily: 'inherit',
                    outline: 'none',
                  }}
                />
              </div>
            </div>

            {/* Create Workspace Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                marginTop: 6,
                height: 38,
                borderRadius: 8,
                border: 'none',
                background: '#2563EB',
                color: 'white',
                fontSize: 13,
                fontWeight: 600,
                cursor: isSubmitting ? 'wait' : 'pointer',
                transition: 'background 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!isSubmitting) e.currentTarget.style.background = '#1D4ED8';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#2563EB';
              }}
            >
              {isSubmitting ? 'Creating Workspace...' : 'Create Workspace'}
            </button>

            {/* Return to Lock Screen */}
            <div style={{ textAlign: 'center', marginTop: 4 }}>
              <button
                type="button"
                onClick={() => {
                  setIsSetupMode(false);
                  setErrorMessage(null);
                  setSuccessMessage(null);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#64748B',
                  fontSize: 11.5,
                  cursor: 'pointer',
                  padding: 4,
                }}
              >
                Back to Unlock
              </button>
            </div>
          </form>
        )}

        {/* Minimal Enterprise Footer Notice */}
        <div
          style={{
            marginTop: 24,
            paddingTop: 16,
            borderTop: '1px solid rgba(255, 255, 255, 0.05)',
            textAlign: 'center',
            fontSize: 11,
            color: '#4B5563',
            letterSpacing: '0.02em',
          }}
        >
          {isSetupMode ? (
            <span>Your credentials remain on this machine.</span>
          ) : (
            <span>Local • Secure • On-Premise</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
