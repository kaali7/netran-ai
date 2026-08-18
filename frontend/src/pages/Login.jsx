import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Lock, Mail, UserCheck, Sparkles, AlertCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import useAuth from '../hooks/useAuth';

export const Login = () => {
  const navigate = useNavigate();
  const { login, signup, isLoading, error, clearError, isAuthenticated } = useAuth();

  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [validationError, setValidationError] = useState('');

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    clearError();

    if (!email.trim() || !password.trim()) {
      setValidationError('Please fill in both email and password.');
      return;
    }

    if (mode === 'signup') {
      if (password !== confirmPassword) {
        setValidationError('Passwords do not match.');
        return;
      }
      if (password.length < 6) {
        setValidationError('Password must be at least 6 characters long.');
        return;
      }
    }

    try {
      if (mode === 'login') {
        await login(email.trim(), password);
      } else {
        await signup(email.trim(), password);
      }
      navigate('/dashboard', { replace: true });
    } catch (err) {
      // Error handled by useAuth state
    }
  };

  const handleQuickDemo = async () => {
    setEmail('candidate@netran.ai');
    setPassword('Candidate123!');
    setValidationError('');
    clearError();
    try {
      // Try login with demo account
      await login('candidate@netran.ai', 'Candidate123!');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      // If demo account does not exist in DB yet, auto-signup demo account!
      try {
        await signup('candidate@netran.ai', 'Candidate123!');
        navigate('/dashboard', { replace: true });
      } catch (signupErr) {
        setValidationError('Could not auto-connect demo account. Please check backend connection.');
      }
    }
  };

  const toggleMode = (newMode) => {
    setMode(newMode);
    setValidationError('');
    clearError();
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 20px',
        background: 'linear-gradient(135deg, #f8f9fa 0%, #edeef0 50%, #e6e8eb 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Background Decorative Ambient Circles */}
      <div
        style={{
          position: 'absolute',
          top: '-10%',
          left: '15%',
          width: '450px',
          height: '450px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(101,89,123,0.12) 0%, rgba(255,255,255,0) 70%)',
          pointerEvents: 'none',
        }}
      />
      <div
        style={{
          position: 'absolute',
          bottom: '-10%',
          right: '15%',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(66,102,81,0.1) 0%, rgba(255,255,255,0) 70%)',
          pointerEvents: 'none',
        }}
      />

      <div style={{ maxWidth: '440px', width: '100%', position: 'relative', zIndex: 10 }}>
        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div
            style={{
              width: '54px',
              height: '54px',
              borderRadius: '16px',
              background: 'linear-gradient(135deg, #65597b 0%, #426651 100%)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 8px 24px rgba(101, 89, 123, 0.25)',
              marginBottom: '14px',
            }}
          >
            <span style={{ color: '#ffffff', fontWeight: 800, fontSize: '26px' }}>N</span>
          </div>
          <h1
            style={{
              fontFamily: 'Manrope, sans-serif',
              fontSize: '28px',
              fontWeight: 800,
              color: 'var(--on-surface)',
              letterSpacing: '-0.02em',
              margin: '0 0 6px 0',
            }}
          >
            Netran AI
          </h1>
          <p style={{ color: 'var(--on-surface-variant)', fontSize: '14px', margin: 0 }}>
            Autonomous AI Technical Interview Platform
          </p>
        </div>

        {/* Form Container Glass Card */}
        <Card
          style={{
            background: 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255, 255, 255, 0.8)',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.04)',
            padding: '32px 28px',
          }}
        >
          {/* Sign In / Sign Up Mode Selector Tabs */}
          <div
            style={{
              display: 'flex',
              background: '#f0f1f3',
              borderRadius: '12px',
              padding: '4px',
              marginBottom: '24px',
            }}
          >
            <button
              type="button"
              onClick={() => toggleMode('login')}
              style={{
                flex: 1,
                padding: '10px 0',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 200ms ease',
                background: mode === 'login' ? '#ffffff' : 'transparent',
                color: mode === 'login' ? 'var(--primary)' : 'var(--on-surface-variant)',
                boxShadow: mode === 'login' ? '0 2px 8px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => toggleMode('signup')}
              style={{
                flex: 1,
                padding: '10px 0',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 200ms ease',
                background: mode === 'signup' ? '#ffffff' : 'transparent',
                color: mode === 'signup' ? 'var(--primary)' : 'var(--on-surface-variant)',
                boxShadow: mode === 'signup' ? '0 2px 8px rgba(0,0,0,0.06)' : 'none',
              }}
            >
              Create Account
            </button>
          </div>

          {/* Error Banner Callout */}
          {(error || validationError) && (
            <div
              style={{
                background: 'rgba(186, 26, 26, 0.08)',
                border: '1px solid rgba(186, 26, 26, 0.2)',
                borderRadius: '12px',
                padding: '12px 14px',
                marginBottom: '20px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '10px',
                color: '#ba1a1a',
                fontSize: '13px',
                lineHeight: '1.4',
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: '1px' }} />
              <span>{validationError || error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit}>
            {/* Email Field */}
            <div style={{ marginBottom: '18px' }}>
              <label
                htmlFor="auth-email-input"
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--on-surface)',
                  marginBottom: '6px',
                }}
              >
                Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail
                  size={18}
                  style={{
                    position: 'absolute',
                    left: '14px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--outline)',
                  }}
                />
                <input
                  id="auth-email-input"
                  type="email"
                  placeholder="candidate@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px 12px 42px',
                    fontSize: '14px',
                    borderRadius: '10px',
                    border: '1px solid #d9dadb',
                    outline: 'none',
                    background: '#ffffff',
                    transition: 'border-color 150ms ease, box-shadow 150ms ease',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'var(--primary)';
                    e.target.style.boxShadow = '0 0 0 3px rgba(101, 89, 123, 0.15)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#d9dadb';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>

            {/* Password Field */}
            <div style={{ marginBottom: mode === 'signup' ? '18px' : '24px' }}>
              <label
                htmlFor="auth-password-input"
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: 600,
                  color: 'var(--on-surface)',
                  marginBottom: '6px',
                }}
              >
                Password
              </label>
              <div style={{ position: 'relative' }}>
                <Lock
                  size={18}
                  style={{
                    position: 'absolute',
                    left: '14px',
                    top: '50%',
                    transform: 'translateY(-50%)',
                    color: 'var(--outline)',
                  }}
                />
                <input
                  id="auth-password-input"
                  type="password"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px 12px 42px',
                    fontSize: '14px',
                    borderRadius: '10px',
                    border: '1px solid #d9dadb',
                    outline: 'none',
                    background: '#ffffff',
                    transition: 'border-color 150ms ease, box-shadow 150ms ease',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => {
                    e.target.style.borderColor = 'var(--primary)';
                    e.target.style.boxShadow = '0 0 0 3px rgba(101, 89, 123, 0.15)';
                  }}
                  onBlur={(e) => {
                    e.target.style.borderColor = '#d9dadb';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>
            </div>

            {/* Confirm Password Field (Signup only) */}
            {mode === 'signup' && (
              <div style={{ marginBottom: '24px' }}>
                <label
                  htmlFor="auth-confirm-password-input"
                  style={{
                    display: 'block',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--on-surface)',
                    marginBottom: '6px',
                  }}
                >
                  Confirm Password
                </label>
                <div style={{ position: 'relative' }}>
                  <ShieldCheck
                    size={18}
                    style={{
                      position: 'absolute',
                      left: '14px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      color: 'var(--outline)',
                    }}
                  />
                  <input
                    id="auth-confirm-password-input"
                    type="password"
                    placeholder="••••••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '12px 14px 12px 42px',
                      fontSize: '14px',
                      borderRadius: '10px',
                      border: '1px solid #d9dadb',
                      outline: 'none',
                      background: '#ffffff',
                      transition: 'border-color 150ms ease, box-shadow 150ms ease',
                      boxSizing: 'border-box',
                    }}
                    onFocus={(e) => {
                      e.target.style.borderColor = 'var(--primary)';
                      e.target.style.boxShadow = '0 0 0 3px rgba(101, 89, 123, 0.15)';
                    }}
                    onBlur={(e) => {
                      e.target.style.borderColor = '#d9dadb';
                      e.target.style.boxShadow = 'none';
                    }}
                  />
                </div>
              </div>
            )}

            {/* Primary Action Button */}
            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '12px 20px',
                fontSize: '15px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px',
              }}
            >
              {isLoading ? (
                <span>Processing...</span>
              ) : mode === 'login' ? (
                <>
                  <span>Sign In</span>
                  <ArrowRight size={16} />
                </>
              ) : (
                <>
                  <span>Create Candidate Account</span>
                  <UserCheck size={16} />
                </>
              )}
            </Button>
          </form>

          {/* Quick Demo Login Option */}
          <div
            style={{
              marginTop: '24px',
              paddingTop: '20px',
              borderTop: '1px solid #e7e8e9',
              textAlign: 'center',
            }}
          >
            <p
              style={{
                fontSize: '12px',
                color: 'var(--on-surface-variant)',
                margin: '0 0 12px 0',
                fontWeight: 500,
              }}
            >
              Testing the platform?
            </p>
            <button
              type="button"
              onClick={handleQuickDemo}
              disabled={isLoading}
              style={{
                background: '#f0f1f5',
                border: '1px solid #dcdde1',
                borderRadius: 'var(--radius-full)',
                padding: '8px 18px',
                fontSize: '13px',
                fontWeight: 600,
                color: '#65597b',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 150ms ease',
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.background = '#e6d6ff';
                e.currentTarget.style.borderColor = '#c3a5fc';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.background = '#f0f1f5';
                e.currentTarget.style.borderColor = '#dcdde1';
              }}
            >
              <Sparkles size={14} color="#65597b" />
              <span>One-Click Candidate Demo Account</span>
            </button>
          </div>
        </Card>

        {/* Footer Note */}
        <p
          style={{
            textAlign: 'center',
            fontSize: '12px',
            color: 'var(--outline)',
            marginTop: '20px',
          }}
        >
          Protected by OAuth2 & JWT Encryption • Netran AI Security
        </p>
      </div>
    </div>
  );
};

export default Login;
